from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from scripts.build_repo_local_kag_retrieval_plan import _write_or_compare_json
from scripts.generate_repo_local_kag_index import build_index, build_repository_indexes
from scripts.repo_local.bundle import (
    build_retrieval_bundle_manifest,
    retrieval_bundle_matches,
    write_retrieval_bundle,
)
from scripts.repo_local.projections import (
    build_federated_retrieval_plan,
    build_repo_retrieval_documents,
    materialize_vector_points,
)
from tests.test_repo_local_kag_repository_indexes import write_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = REPO_ROOT / "schemas" / "repo-local-kag-retrieval-plan.schema.json"
BUNDLE_SCHEMA = REPO_ROOT / "schemas" / "repo-local-kag-retrieval-bundle.schema.json"
EMBEDDING_PROFILE = {
    "id": "test-embedding-v1",
    "model": "test/embedding",
    "revision": "sha256:test",
    "dimensions": 3,
    "distance": "cosine",
    "normalization": "l2",
    "provider_contract": "test-embedding-port-v1"
}


class DeterministicEmbeddingPort:
    profile_id = "test-embedding-v1"
    dimensions = 3

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [
            [float(len(text)), float(text.count(" ") + 1), float(text.count("\n") + 1)]
            for text in texts
        ]


class RepoKagProjectionTests(unittest.TestCase):
    def test_retrieval_plan_file_write_and_check_stream_json(self) -> None:
        payload = {"owners": ["aoa-first", "aoa-second"], "version": 1}
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "plan.json"
            with patch(
                "scripts.build_repo_local_kag_retrieval_plan.json.dumps",
                side_effect=AssertionError("monolithic serialization"),
            ):
                self.assertTrue(
                    _write_or_compare_json(
                        output,
                        payload,
                        pretty=False,
                        check=False,
                    )
                )
                self.assertTrue(
                    _write_or_compare_json(
                        output,
                        payload,
                        pretty=False,
                        check=True,
                    )
                )
                self.assertFalse(
                    _write_or_compare_json(
                        output,
                        {**payload, "version": 2},
                        pretty=False,
                        check=True,
                    )
                )
            self.assertEqual([], list(output.parent.glob(".*.tmp-*")))

    def test_retrieval_documents_are_anchor_bounded_and_source_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            write_fixture(root)
            (root / "assets").mkdir()
            (root / "assets" / "diagram.svg").write_text(
                "<svg><path d=\"M 1.234,5.678 L 9.012,3.456\"/></svg>\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)
            documents = build_repo_retrieval_documents(root, source, family)

        usage = next(
            document
            for document in documents
            if document["path"] == "docs/guides/usage.md"
            and document["label"] == "Usage"
        )
        helper = next(
            document
            for document in documents
            if document["path"] == "src/demo.py" and document["label"] == "helper"
        )
        self.assertIn("Run the demo", usage["text"])
        self.assertIn("def helper", helper["text"])
        self.assertEqual("anchor", usage["node_class"])
        self.assertEqual("digest-only", usage["signs"]["verification_state"])
        self.assertEqual("current", usage["freshness"]["state"])
        self.assertEqual(len(documents), len({document["id"] for document in documents}))
        self.assertTrue(all(document["text_digest"] for document in documents))
        asset = next(
            document for document in documents if document["path"] == "assets/diagram.svg"
        )
        self.assertEqual("asset", asset["kind"])
        self.assertIn("Repository asset:", asset["text"])
        self.assertIn("MIME type: image/svg+xml", asset["text"])
        self.assertIn("Content digest: sha256:", asset["text"])
        self.assertNotIn("<path", asset["text"])

    def test_federated_retrieval_plan_is_deterministic_and_schema_valid(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            roots = {
                "aoa-first": Path(first_tmp),
                "aoa-second": Path(second_tmp),
            }
            bundles = {}
            for repo, root in roots.items():
                write_fixture(root)
                (root / "kag" / "manifest.json").write_text(
                    json.dumps({"repo": repo}), encoding="utf-8"
                )
                source = build_index(root)
                bundles[repo] = (
                    source,
                    build_repository_indexes(source, repo_root=root),
                )
            plan = build_federated_retrieval_plan(
                roots,
                bundles,
                embedding_profile=EMBEDDING_PROFILE,
            )
            repeated = build_federated_retrieval_plan(
                roots,
                bundles,
                embedding_profile=EMBEDDING_PROFILE,
            )

        schema = json.loads(PLAN_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(plan)
        self.assertEqual(plan, repeated)
        digest_material = copy.deepcopy(plan)
        digest_material["projection_identity"]["content_digest"] = "0" * 64
        expected_digest = hashlib.sha256(
            json.dumps(
                digest_material,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(
            expected_digest,
            plan["projection_identity"]["content_digest"],
        )
        self.assertEqual(2, plan["summary"]["owner_count"])
        self.assertEqual(
            plan["summary"]["document_count"],
            len(plan["documents"]),
        )
        self.assertEqual(
            {"exact", "lexical", "vector", "hybrid", "graph"},
            set(plan["projection_lanes"]),
        )

    def test_vector_materialization_keeps_profile_and_source_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            (root / "kag" / "manifest.json").write_text(
                json.dumps({"repo": "aoa-vector"}), encoding="utf-8"
            )
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)
            plan = build_federated_retrieval_plan(
                {"aoa-vector": root},
                {"aoa-vector": (source, family)},
                embedding_profile=EMBEDDING_PROFILE,
            )

        points = materialize_vector_points(plan, DeterministicEmbeddingPort(), batch_size=7)
        self.assertEqual(len(plan["documents"]), len(points))
        self.assertEqual(3, len(points[0]["vector"]))
        self.assertEqual("test-embedding-v1", points[0]["payload"]["embedding_profile_id"])
        self.assertTrue(points[0]["payload"]["source_record_ids"])
        self.assertTrue(points[0]["payload"]["anchor_ids"])

    def test_retrieval_bundle_is_streamable_deterministic_and_self_verifying(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as bundle_tmp:
            root = Path(repo_tmp)
            write_fixture(root)
            (root / "kag" / "manifest.json").write_text(
                json.dumps({"repo": "aoa-bundle"}), encoding="utf-8"
            )
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)
            plan = build_federated_retrieval_plan(
                {"aoa-bundle": root},
                {"aoa-bundle": (source, family)},
                embedding_profile=EMBEDDING_PROFILE,
            )
            bundle_root = Path(bundle_tmp)
            manifest = write_retrieval_bundle(plan, bundle_root)

            schema = json.loads(BUNDLE_SCHEMA.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(manifest)
            self.assertTrue(retrieval_bundle_matches(plan, bundle_root))
            documents = [
                json.loads(line)
                for line in (bundle_root / "documents.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(plan["documents"], documents)
            for key in ("owners", "nodes", "relations", "external_references"):
                records = [
                    json.loads(line)
                    for line in (bundle_root / f"{key}.jsonl").read_text(
                        encoding="utf-8"
                    ).splitlines()
                ]
                self.assertEqual(plan["federation"][key], records)
            with (bundle_root / "documents.jsonl").open("a", encoding="utf-8") as handle:
                handle.write("{}\n")
            self.assertFalse(retrieval_bundle_matches(plan, bundle_root))

    def test_retrieval_bundle_carries_cross_repo_relations(self) -> None:
        with (
            tempfile.TemporaryDirectory() as first_tmp,
            tempfile.TemporaryDirectory() as second_tmp,
            tempfile.TemporaryDirectory() as bundle_tmp,
        ):
            roots = {
                "aoa-first": Path(first_tmp),
                "aoa-second": Path(second_tmp),
            }
            bundles = {}
            for repo, root in roots.items():
                write_fixture(root)
                (root / "kag" / "manifest.json").write_text(
                    json.dumps({"repo": repo}), encoding="utf-8"
                )
            (roots["aoa-first"] / "README.md").write_text(
                "# First\n\n"
                "See [Second demo](https://github.com/8Dionysus/aoa-second/"
                "blob/main/README.md#demo).\n",
                encoding="utf-8",
            )
            for repo, root in roots.items():
                source = build_index(root)
                bundles[repo] = (
                    source,
                    build_repository_indexes(source, repo_root=root),
                )
            plan = build_federated_retrieval_plan(
                roots,
                bundles,
                embedding_profile=EMBEDDING_PROFILE,
            )
            manifest = write_retrieval_bundle(plan, Path(bundle_tmp))
            relations = [
                json.loads(line)
                for line in (Path(bundle_tmp) / "relations.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]

        self.assertEqual(1, len(plan["federation"]["cross_repo_relations"]))
        self.assertEqual(
            [
                *plan["federation"]["relations"],
                *plan["federation"]["cross_repo_relations"],
            ],
            relations,
        )
        self.assertEqual(
            plan["federation"]["summary"]["relation_count"],
            manifest["files"]["relations"]["record_count"],
        )

    def test_retrieval_bundle_rejects_unresolved_federation_before_writing(self) -> None:
        with (
            tempfile.TemporaryDirectory() as first_tmp,
            tempfile.TemporaryDirectory() as second_tmp,
            tempfile.TemporaryDirectory() as bundle_tmp,
        ):
            roots = {
                "aoa-first": Path(first_tmp),
                "aoa-second": Path(second_tmp),
            }
            bundles = {}
            for repo, root in roots.items():
                write_fixture(root)
                (root / "kag" / "manifest.json").write_text(
                    json.dumps({"repo": repo}), encoding="utf-8"
                )
            (roots["aoa-first"] / "README.md").write_text(
                "# First\n\nSee [missing](repo://aoa-second/docs/missing.md).\n",
                encoding="utf-8",
            )
            for repo, root in roots.items():
                source = build_index(root)
                bundles[repo] = (
                    source,
                    build_repository_indexes(source, repo_root=root),
                )
            plan = build_federated_retrieval_plan(
                roots,
                bundles,
                embedding_profile=EMBEDDING_PROFILE,
            )
            bundle_root = Path(bundle_tmp)

            self.assertEqual(1, plan["federation"]["summary"]["unresolved_reference_count"])
            with self.assertRaisesRegex(ValueError, "unresolved"):
                build_retrieval_bundle_manifest(plan, files={})
            with self.assertRaisesRegex(ValueError, "unresolved"):
                write_retrieval_bundle(plan, bundle_root)
            self.assertEqual([], list(bundle_root.iterdir()))
            self.assertFalse(retrieval_bundle_matches(plan, bundle_root))


if __name__ == "__main__":
    unittest.main()
