from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.generate_repo_local_kag_index import (
    build_index,
    build_repository_indexes,
    payload_digest,
)
from scripts.repo_local.federation import RepoKagFederation, git_ref_names
from tests.test_repo_local_kag_repository_indexes import write_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]
FEDERATION_SCHEMA = REPO_ROOT / "schemas" / "repo-local-kag-federation.schema.json"
QUERY_SCHEMA = REPO_ROOT / "schemas" / "repo-local-kag-query-result.schema.json"


def owner_bundle(root: Path, repo: str, *, readme: str | None = None) -> tuple[dict, dict]:
    write_fixture(root)
    (root / "kag" / "manifest.json").write_text(
        json.dumps({"repo": repo}), encoding="utf-8"
    )
    if readme is not None:
        (root / "README.md").write_text(readme, encoding="utf-8")
    source = build_index(root)
    return source, build_repository_indexes(source, repo_root=root)


class RepoKagFederationTests(unittest.TestCase):
    def test_git_ref_names_preserve_slash_delimited_branch_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(
                ("git", "config", "user.email", "kag@example.test"),
                cwd=root,
                check=True,
            )
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            subprocess.run(("git", "add", "README.md"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial"), cwd=root, check=True)
            subprocess.run(("git", "branch", "feature/x"), cwd=root, check=True)
            subprocess.run(("git", "tag", "v1"), cwd=root, check=True)

            refs = git_ref_names(root)

        self.assertIn("main", refs)
        self.assertIn("feature/x", refs)
        self.assertIn("v1", refs)

    def test_federation_resolves_cross_repo_reference_with_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first_root = Path(first_tmp)
            second_root = Path(second_tmp)
            first = owner_bundle(
                first_root,
                "aoa-first",
                readme=(
                    "# First\n\n"
                    "See [Second demo](https://github.com/8Dionysus/aoa-second/blob/main/README.md#demo).\n"
                    "See [Second pull request](https://github.com/8Dionysus/aoa-second/pull/7).\n"
                ),
            )
            second = owner_bundle(second_root, "aoa-second")
            federation = RepoKagFederation(
                {"aoa-first": first, "aoa-second": second}
            )

        projection = federation.projection()
        repeated = federation.projection()
        schema = json.loads(FEDERATION_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(projection)
        self.assertEqual(projection, repeated)
        self.assertEqual(2, projection["summary"]["owner_count"])
        self.assertEqual(
            projection["summary"]["node_count"],
            len({node["id"] for node in projection["nodes"]}),
        )
        cross = projection["cross_repo_relations"]
        self.assertEqual(1, len(cross))
        self.assertEqual("aoa-first", cross[0]["source_repo"])
        self.assertEqual("aoa-second", cross[0]["target_repo"])
        self.assertTrue(cross[0]["evidence_anchor_ids"])
        self.assertEqual(0, projection["summary"]["unresolved_reference_count"])
        self.assertEqual(1, projection["summary"]["external_reference_count"])
        self.assertEqual(
            "github-object",
            projection["external_references"][0]["reference_kind"],
        )
        node_ids = {node["id"] for node in projection["nodes"]}
        self.assertIn(cross[0]["from_id"], node_ids)
        self.assertIn(cross[0]["to_id"], node_ids)

    def test_federation_resolves_historical_source_path_through_git_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = owner_bundle(
                Path(first_tmp),
                "aoa-first",
                readme=(
                    "# First\n\n"
                    "See [moved guide](https://github.com/8Dionysus/aoa-second/blob/main/"
                    "docs/guides/usage.md#usage).\n"
                ),
            )
            second_root = Path(second_tmp)
            subprocess.run(("git", "init", "-q"), cwd=second_root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=second_root, check=True)
            subprocess.run(
                ("git", "config", "user.email", "kag@example.test"),
                cwd=second_root,
                check=True,
            )
            write_fixture(second_root)
            (second_root / "kag" / "manifest.json").write_text(
                json.dumps({"repo": "aoa-second"}), encoding="utf-8"
            )
            subprocess.run(("git", "add", "."), cwd=second_root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial"), cwd=second_root, check=True)
            (second_root / "mechanics" / "guide").mkdir(parents=True)
            subprocess.run(
                (
                    "git",
                    "mv",
                    "docs/guides/usage.md",
                    "mechanics/guide/usage.md",
                ),
                cwd=second_root,
                check=True,
            )
            subprocess.run(("git", "commit", "-qm", "move guide"), cwd=second_root, check=True)
            second_source = build_index(second_root)
            second_family = build_repository_indexes(second_source, repo_root=second_root)
            federation = RepoKagFederation(
                {
                    "aoa-first": first,
                    "aoa-second": (second_source, second_family),
                }
            )

        usage_anchor = next(
            entry
            for entry in second_family["anchor"]["entries"]
            if entry["anchor_kind"] == "markdown_heading" and entry["label"] == "Usage"
        )
        projection = federation.projection()
        self.assertEqual([], projection["unresolved_references"])
        self.assertEqual(usage_anchor["id"], projection["cross_repo_relations"][0]["to_id"])

    def test_github_blob_ref_is_removed_before_target_path_matching(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = owner_bundle(
                Path(first_tmp),
                "aoa-first",
                readme=(
                    "# First\n\n"
                    "See [usage](https://github.com/8Dionysus/aoa-second/"
                    "blob/feature/x/docs/guides/usage.md).\n"
                ),
            )
            second_root = Path(second_tmp)
            write_fixture(second_root)
            (second_root / "kag" / "manifest.json").write_text(
                json.dumps({"repo": "aoa-second"}), encoding="utf-8"
            )
            colliding = second_root / "x" / "docs" / "guides"
            colliding.mkdir(parents=True)
            (colliding / "usage.md").write_text("# Wrong target\n", encoding="utf-8")
            second_source = build_index(second_root)
            second_family = build_repository_indexes(second_source, repo_root=second_root)
            projection = RepoKagFederation(
                {
                    "aoa-first": first,
                    "aoa-second": (second_source, second_family),
                },
                github_refs_by_repo={"aoa-second": ("feature/x",)},
            ).projection()

        intended = next(
            entry
            for entry in second_family["artifact"]["entries"]
            if entry["path"] == "docs/guides/usage.md"
        )
        self.assertEqual(1, len(projection["cross_repo_relations"]))
        self.assertEqual(
            intended["anchor_id"],
            projection["cross_repo_relations"][0]["to_id"],
        )

    def test_federation_resolves_directory_target_to_directory_entity(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = owner_bundle(
                Path(first_tmp),
                "aoa-first",
                readme="# First\n\nSee [docs](repo://aoa-second/docs).\n",
            )
            second = owner_bundle(Path(second_tmp), "aoa-second")
            projection = RepoKagFederation(
                {"aoa-first": first, "aoa-second": second}
            ).projection()

        docs_entity = next(
            entry
            for entry in second[1]["entity"]["entries"]
            if entry["semantic_key"] == "directory:docs"
        )
        self.assertEqual([], projection["unresolved_references"])
        self.assertEqual(1, len(projection["cross_repo_relations"]))
        self.assertEqual(
            docs_entity["id"],
            projection["cross_repo_relations"][0]["to_id"],
        )

    def test_federated_graph_query_crosses_owner_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = owner_bundle(
                Path(first_tmp),
                "aoa-first",
                readme=(
                    "# First\n\n"
                    "See [Second demo](https://github.com/8Dionysus/aoa-second/blob/main/README.md#demo).\n"
                ),
            )
            second = owner_bundle(Path(second_tmp), "aoa-second")
            federation = RepoKagFederation(
                {"aoa-first": first, "aoa-second": second}
            )

        result = federation.query("Second demo", mode="graph", limit=20)
        Draft202012Validator(json.loads(QUERY_SCHEMA.read_text(encoding="utf-8"))).validate(
            result
        )
        self.assertEqual("aoa-repo-local-kag-federated-query-result-v1", result["schema_version"])
        second_hit = next(
            hit
            for hit in result["hits"]
            if hit["repo"]["name"] == "aoa-second" and hit["label"] == "Demo"
        )
        self.assertTrue(second_hit["evidence"]["relation_ids"])
        self.assertTrue(second_hit["evidence"]["anchor_ids"])

    def test_federation_rejects_owner_namespace_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = owner_bundle(Path(tmpdir), "aoa-source")

        with self.assertRaisesRegex(ValueError, "owner key"):
            RepoKagFederation({"aoa-alias": bundle})

    def test_federated_query_keeps_owner_access_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = owner_bundle(Path(first_tmp), "aoa-first")
            second_source, _ = owner_bundle(Path(second_tmp), "aoa-second")
            for record in second_source["records"]:
                record["access"]["scope"] = "private"
            second_source["index_identity"]["content_digest"] = payload_digest(second_source)
            second = (
                second_source,
                build_repository_indexes(second_source, repo_root=Path(second_tmp)),
            )
            federation = RepoKagFederation(
                {"aoa-first": first, "aoa-second": second}
            )

        public = federation.query("README.md", mode="exact", limit=20)
        private = federation.query(
            "README.md",
            mode="exact",
            limit=20,
            access_scopes={"private"},
        )
        self.assertTrue(public["hits"])
        self.assertTrue(private["hits"])
        self.assertEqual({"aoa-first"}, {hit["repo"]["name"] for hit in public["hits"]})
        self.assertEqual({"aoa-second"}, {hit["repo"]["name"] for hit in private["hits"]})


if __name__ == "__main__":
    unittest.main()
