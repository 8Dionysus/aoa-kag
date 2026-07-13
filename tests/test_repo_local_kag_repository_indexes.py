from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from jsonschema import Draft202012Validator

from scripts.generate_repo_local_kag_index import (
    REPOSITORY_INDEX_FILENAMES,
    build_index,
    build_index_incremental,
    build_repository_indexes,
    build_repository_indexes_incremental,
    effective_history_ref,
    main,
    payload_digest,
)
from scripts.generate_repo_local_kag_coverage import source_index_matches_owner
from scripts.generation.provider_map import _is_repo_local_meta_index_payload
from scripts.repo_local.query import RepoKagQuery
from scripts.validators.common import ValidationError
from scripts.validators.repo_local_kag_index import (
    repo_local_kag_index_digest_without_self,
    validate_repo_local_kag_repository_index_family,
    validate_repo_local_kag_repository_index_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_INDEX_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-repository-index.schema.json"
)
QUERY_RESULT_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-query-result.schema.json"
DOMAIN_INDEX_CATALOG_SCHEMA_PATH = REPO_ROOT / "schemas" / "domain-index-catalog.schema.json"
DOMAIN_INDEX_CATALOG_EXAMPLE_PATH = REPO_ROOT / "examples" / "domain_index_catalog.example.json"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_fixture(root: Path) -> None:
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "docs" / "decisions").mkdir(parents=True)
    (root / "docs" / "guides").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "kag" / "receipts").mkdir(parents=True)
    (root / "mechanics" / "demo" / "parts" / "runner").mkdir(parents=True)
    (root / "schemas").mkdir()
    (root / "scripts").mkdir()
    (root / "src").mkdir()
    (root / "config" / "pipeline.yaml").write_text(
        "jobs:\n"
        "  build:\n"
        "    steps:\n"
        "      - name: first\n"
        "        uses: owner/first@v1\n"
        "      - name: second\n"
        "        uses: owner/second@v1\n"
        "      - name: script\n"
        "        run: |\n"
        "          echo 'status: first'\n"
        "          echo 'status: second'\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# Demo\n\nSee [usage](docs/guides/usage.md#usage).\n",
        encoding="utf-8",
    )
    (root / "docs" / "guides" / "usage.md").write_text(
        "# Guide\n\n## Usage\n\nRun the demo.\n",
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.0.0]\n",
        encoding="utf-8",
    )
    (root / ".github" / "workflows" / "validate.yml").write_text(
        "name: Validate\n",
        encoding="utf-8",
    )
    (root / "docs" / "decisions" / "D-0001.md").write_text(
        "# Decision\n",
        encoding="utf-8",
    )
    (root / "scripts" / "validate_demo.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    (root / "src" / "demo.py").write_text(
        "class Demo:\n"
        "    def run(self) -> str:\n"
        "        return helper()\n\n"
        "def helper() -> str:\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )
    (root / "schemas" / "demo.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$defs": {"Demo": {"type": "object"}},
            }
        ),
        encoding="utf-8",
    )
    (root / "mechanics" / "demo" / "README.md").write_text(
        "# Demo mechanic\n",
        encoding="utf-8",
    )
    (root / "mechanics" / "demo" / "parts" / "runner" / "README.md").write_text(
        "# Runner part\n",
        encoding="utf-8",
    )
    (root / "kag" / "receipts" / "validation_receipt.json").write_text(
        json.dumps({"result": "valid"}),
        encoding="utf-8",
    )
    (root / "future.unknown").write_bytes(b"future")


class RepoLocalKagRepositoryIndexTests(unittest.TestCase):
    def test_environment_history_ref_is_scoped_to_its_owner(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                "AOA_REPO_LOCAL_KAG_HISTORY_REPO": "another-owner",
                "AOA_REPO_LOCAL_KAG_HISTORY_REF": "stable-head",
            },
        ):
            self.assertIsNone(effective_history_ref(REPO_ROOT))
            self.assertEqual(
                "explicit-head",
                effective_history_ref(REPO_ROOT, "explicit-head"),
            )

    def test_repository_index_family_matches_schema(self) -> None:
        schema = load_json(REPOSITORY_INDEX_SCHEMA_PATH)
        assert isinstance(schema, dict)
        Draft202012Validator.check_schema(schema)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)

        self.assertEqual(
            {"entity", "artifact", "anchor", "event", "assertion", "relation"},
            set(family),
        )
        for index_kind, payload in family.items():
            with self.subTest(index_kind=index_kind):
                errors = list(Draft202012Validator(schema).iter_errors(payload))
                self.assertEqual([], errors)
                self.assertEqual(index_kind, payload["index_identity"]["index_kind"])
                self.assertEqual(
                    payload_digest(payload),
                    payload["index_identity"]["content_digest"],
                )
                self.assertEqual(
                    source_index["index_identity"]["content_digest"],
                    payload["source_index"]["content_digest"],
                )

    def test_entity_and_artifact_indexes_cover_unknown_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)

        source_count = source_index["coverage_summary"]["record_count"]
        self.assertGreater(family["entity"]["summary"]["entry_count"], 0)
        self.assertEqual(source_count, family["artifact"]["summary"]["entry_count"])
        artifact = next(
            entry for entry in family["artifact"]["entries"] if entry["path"] == "future.unknown"
        )
        self.assertEqual("unknown", artifact["artifact_kind"])
        self.assertNotIn("future.unknown", {entry["label"] for entry in family["entity"]["entries"]})

    def test_assertions_keep_subject_object_and_source_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)

        readme = next(
            record for record in source_index["records"]
            if record["identity"]["path"] == "README.md"
        )
        classification = next(
            entry for entry in family["assertion"]["entries"]
            if entry["subject_id"] == readme["identity"]["id"]
            and entry["predicate"] == "classified_as"
        )
        self.assertEqual("literal", classification["object"]["kind"])
        self.assertEqual("document", classification["object"]["value"])
        self.assertEqual([readme["identity"]["id"]], classification["source_record_ids"])
        self.assertTrue(classification["evidence_anchor_ids"])
        self.assertEqual("accepted", classification["quality_state"])
        self.assertEqual("deterministic", classification["trust_ref"])

    def test_repository_ids_are_owner_qualified(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = Path(first_tmp)
            second = Path(second_tmp)
            write_fixture(first)
            write_fixture(second)
            (first / "kag" / "manifest.json").write_text(
                json.dumps({"repo": "aoa-first"}), encoding="utf-8"
            )
            (second / "kag" / "manifest.json").write_text(
                json.dumps({"repo": "aoa-second"}), encoding="utf-8"
            )
            first_index = build_index(first)
            second_index = build_index(second)

        first_readme = next(
            record for record in first_index["records"] if record["identity"]["path"] == "README.md"
        )
        second_readme = next(
            record for record in second_index["records"] if record["identity"]["path"] == "README.md"
        )
        self.assertNotEqual(first_readme["identity"]["id"], second_readme["identity"]["id"])
        self.assertTrue(first_readme["identity"]["id"].startswith("aoa:aoa-first:artifact:"))
        self.assertTrue(second_readme["identity"]["id"].startswith("aoa:aoa-second:artifact:"))

    def test_logical_artifact_identity_survives_staged_rename(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.email", "kag@example.test"), cwd=root, check=True)
            write_fixture(root)
            (root / "kag" / "manifest.json").write_text(
                json.dumps({"repo": "aoa-rename"}), encoding="utf-8"
            )
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial"), cwd=root, check=True)
            before = build_index(root)
            subprocess.run(("git", "mv", "README.md", "OVERVIEW.md"), cwd=root, check=True)
            after = build_index(root)

        before_id = next(
            record["identity"]["id"]
            for record in before["records"]
            if record["identity"]["path"] == "README.md"
        )
        after_id = next(
            record["identity"]["id"]
            for record in after["records"]
            if record["identity"]["path"] == "OVERVIEW.md"
        )
        self.assertEqual(before_id, after_id)

    def test_reintroduced_path_gets_stable_distinct_logical_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.email", "kag@example.test"), cwd=root, check=True)
            write_fixture(root)
            (root / "kag" / "manifest.json").write_text(
                json.dumps({"repo": "aoa-reintroduced"}), encoding="utf-8"
            )
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial"), cwd=root, check=True)
            initial = build_index(root)
            subprocess.run(("git", "mv", "README.md", "OVERVIEW.md"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "move overview"), cwd=root, check=True)
            (root / "README.md").write_text("# New front door\n", encoding="utf-8")
            subprocess.run(("git", "add", "README.md"), cwd=root, check=True)
            staged = build_index(root)
            subprocess.run(("git", "commit", "-qm", "restore front door"), cwd=root, check=True)
            committed = build_index(root)

        initial_id = next(
            record["identity"]["id"]
            for record in initial["records"]
            if record["identity"]["path"] == "README.md"
        )
        staged_ids = {
            record["identity"]["path"]: record["identity"]["id"]
            for record in staged["records"]
        }
        committed_ids = {
            record["identity"]["path"]: record["identity"]["id"]
            for record in committed["records"]
        }
        self.assertEqual(initial_id, staged_ids["OVERVIEW.md"])
        self.assertNotEqual(initial_id, staged_ids["README.md"])
        self.assertEqual(staged_ids, committed_ids)
        self.assertEqual(len(staged_ids.values()), len(set(staged_ids.values())))

    def test_incremental_source_build_matches_full_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.email", "kag@example.test"), cwd=root, check=True)
            write_fixture(root)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial"), cwd=root, check=True)
            previous = build_index(root)
            (root / "src" / "demo.py").write_text(
                "def changed() -> str:\n    return 'changed'\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "add", "src/demo.py"), cwd=root, check=True)

            with mock.patch(
                "scripts.generate_repo_local_kag_index.build_record",
                wraps=__import__(
                    "scripts.generate_repo_local_kag_index",
                    fromlist=["build_record"],
                ).build_record,
            ) as build_record_spy:
                incremental = build_index_incremental(root, previous)
            full = build_index(root)

        self.assertEqual(full, incremental)
        self.assertEqual(1, build_record_spy.call_count)

    def test_incremental_family_build_matches_full_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.email", "kag@example.test"), cwd=root, check=True)
            write_fixture(root)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial"), cwd=root, check=True)
            previous_source = build_index(root)
            previous_family = build_repository_indexes(previous_source, repo_root=root)
            (root / "src" / "demo.py").write_text(
                "def changed() -> str:\n    return 'changed'\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "add", "src/demo.py"), cwd=root, check=True)
            current_source = build_index_incremental(root, previous_source)

            with mock.patch(
                "scripts.generate_repo_local_kag_index.extract_structure",
                wraps=__import__(
                    "scripts.generate_repo_local_kag_index",
                    fromlist=["extract_structure"],
                ).extract_structure,
            ) as extract_spy:
                incremental = build_repository_indexes_incremental(
                    current_source,
                    previous_family,
                    repo_root=root,
                )
            full = build_repository_indexes(current_source, repo_root=root)

        self.assertEqual(full, incremental)
        self.assertEqual(1, extract_spy.call_count)

    def test_structural_indexes_cover_anchors_entities_and_relations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)

        anchor_kinds = {entry["anchor_kind"] for entry in family["anchor"]["entries"]}
        entity_kinds = {entry["entity_kind"] for entry in family["entity"]["entries"]}
        relation_kinds = {entry["relation_kind"] for entry in family["relation"]["entries"]}
        self.assertTrue(
            {"artifact", "markdown_heading", "markdown_link", "python_symbol", "json_pointer"}
            .issubset(anchor_kinds)
        )
        self.assertTrue(
            {"python_class", "python_function", "schema_definition",
             "repository", "directory", "mechanic_package", "mechanic_part"}.issubset(entity_kinds)
        )
        self.assertTrue({"contains", "defines", "references", "calls"}.issubset(relation_kinds))

        node_ids = {
            entry["id"]
            for kind in ("artifact", "anchor", "entity", "event")
            for entry in family[kind]["entries"]
        }
        for relation in family["relation"]["entries"]:
            self.assertIn(relation["from_id"], node_ids)
            self.assertIn(relation["to_id"], node_ids)
            self.assertTrue(relation["evidence_anchor_ids"])
            self.assertTrue(set(relation["evidence_anchor_ids"]).issubset(node_ids))
        repository = next(
            entry for entry in family["entity"]["entries"] if entry["entity_kind"] == "repository"
        )
        docs_directory = next(
            entry
            for entry in family["entity"]["entries"]
            if entry["entity_kind"] == "directory" and entry["semantic_key"] == "directory:docs"
        )
        self.assertTrue(
            any(
                relation["relation_kind"] == "contains"
                and relation["from_id"] == repository["id"]
                and relation["to_id"] == docs_directory["id"]
                for relation in family["relation"]["entries"]
            )
        )
        source_by_id = {
            record["identity"]["id"]: record["identity"]["path"]
            for record in source_index["records"]
        }
        yaml_anchors = [
            entry
            for entry in family["anchor"]["entries"]
            if source_by_id[entry["source_record_id"]] == "config/pipeline.yaml"
            and entry["anchor_kind"] == "yaml_path"
        ]
        pointers = {entry["locator"]["pointer"] for entry in yaml_anchors}
        self.assertIn("/jobs/build/steps/0/name", pointers)
        self.assertIn("/jobs/build/steps/1/name", pointers)
        self.assertIn("/jobs/build/steps/2/run", pointers)
        self.assertNotIn("/jobs/build/steps/2/run/status", pointers)
        self.assertEqual(len(yaml_anchors), len({entry["id"] for entry in yaml_anchors}))

    def test_redefined_python_symbols_keep_distinct_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            (root / "src" / "redefined.py").write_text(
                "def normalize(value: str) -> str:\n"
                "    return value.strip()\n\n"
                "def normalize(value: str) -> str:\n"
                "    return value.lower()\n",
                encoding="utf-8",
            )
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)

        source_by_id = {
            record["identity"]["id"]: record["identity"]["path"]
            for record in source_index["records"]
        }
        anchors = [
            entry
            for entry in family["anchor"]["entries"]
            if source_by_id[entry["source_record_id"]] == "src/redefined.py"
            and entry["qualified_name"] == "normalize"
        ]
        self.assertEqual(2, len(anchors))
        self.assertEqual(2, len({entry["id"] for entry in anchors}))
        self.assertEqual(
            {
                "python:function:normalize",
                "python:function:normalize#occurrence-2",
            },
            {entry["semantic_key"] for entry in anchors},
        )

    def test_event_index_separates_producers_declarations_and_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            family = build_repository_indexes(build_index(root), repo_root=root)

        events = family["event"]["entries"]
        kinds = {entry["event_kind"] for entry in events}
        roles = {entry["event_role"] for entry in events}
        self.assertTrue(
            {
                "workflow_run",
                "validation_run",
                "decision_record",
                "release_lane",
                "release_declaration",
                "validation_receipt",
            }.issubset(kinds)
        )
        self.assertEqual({"producer", "declaration", "receipt"}, roles)
        release = next(entry for entry in events if entry["event_kind"] == "release_declaration")
        self.assertEqual("[1.0.0]", release["label"])
        self.assertTrue(release["anchor_ids"])

    def test_event_index_covers_git_lifecycle_and_staged_change_sets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.email", "kag@example.test"), cwd=root, check=True)
            write_fixture(root)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial"), cwd=root, check=True)
            initial_source = build_index(root)
            initial_ids = {
                record["identity"]["path"]: record["identity"]["id"]
                for record in initial_source["records"]
            }

            (root / "README.md").write_text("# Demo changed\n", encoding="utf-8")
            subprocess.run(
                ("git", "mv", "docs/guides/usage.md", "docs/guides/run.md"),
                cwd=root,
                check=True,
            )
            (root / "future.unknown").unlink()
            (root / "new.txt").write_text("new\n", encoding="utf-8")
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "lifecycle"), cwd=root, check=True)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            repeated = build_repository_indexes(source_index, repo_root=root)

            (root / "new.txt").write_text("staged\n", encoding="utf-8")
            subprocess.run(("git", "add", "new.txt"), cwd=root, check=True)
            staged_source = build_index(root)
            staged_family = build_repository_indexes(staged_source, repo_root=root)
            subprocess.run(("git", "commit", "-qm", "staged source"), cwd=root, check=True)
            committed_source = build_index(root)
            committed_family = build_repository_indexes(committed_source, repo_root=root)

        lifecycle = next(
            event
            for event in family["event"]["entries"]
            if event["event_kind"] == "repository_snapshot_change_set"
        )
        self.assertEqual({"add", "delete", "modify", "rename"}, {
            change["change_kind"] for change in lifecycle["changes"]
        })
        rename = next(change for change in lifecycle["changes"] if change["change_kind"] == "rename")
        delete = next(change for change in lifecycle["changes"] if change["change_kind"] == "delete")
        current_ids = {
            record["identity"]["path"]: record["identity"]["id"]
            for record in source_index["records"]
        }
        self.assertEqual(initial_ids["docs/guides/usage.md"], rename["object_id"])
        self.assertEqual(current_ids["docs/guides/run.md"], rename["object_id"])
        self.assertEqual(initial_ids["future.unknown"], delete["object_id"])
        self.assertEqual(family, repeated)
        snapshot = next(
            event
            for event in staged_family["event"]["entries"]
            if event["event_kind"] == "repository_snapshot_change_set"
        )
        self.assertEqual(
            [{"kind": "repository_snapshot", "ref": "source-tree-snapshot"}],
            snapshot["evidence_refs"],
        )
        self.assertEqual(staged_source, committed_source)
        self.assertEqual(staged_family, committed_family)

    def test_family_outputs_do_not_enter_the_source_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            write_fixture(root)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            self.assertEqual(0, main(["--repo-root", str(root), "--index-family"]))
            before = load_json(root / "kag" / "indexes" / "source_surface_index.json")
            subprocess.run(("git", "add", "kag/indexes"), cwd=root, check=True)
            after = build_index(root)
            matches_owner = source_index_matches_owner(root, after)

        self.assertEqual(before, after)
        indexed_paths = {record["identity"]["path"] for record in after["records"]}
        self.assertTrue(
            {
                f"kag/indexes/{filename}" for filename in REPOSITORY_INDEX_FILENAMES.values()
            }.isdisjoint(indexed_paths)
        )
        self.assertTrue(matches_owner)

    def test_family_serialization_keeps_each_canonical_record_on_one_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            self.assertEqual(0, main(["--repo-root", str(root), "--index-family"]))
            paths = [
                root / "kag" / "indexes" / "source_surface_index.json",
                *(
                    root / "kag" / "indexes" / filename
                    for filename in REPOSITORY_INDEX_FILENAMES.values()
                ),
            ]
            for path in paths:
                payload = load_json(path)
                assert isinstance(payload, dict)
                key = "records" if "records" in payload else "entries"
                items = payload[key]
                assert isinstance(items, list)
                rendered = path.read_text(encoding="utf-8")
                with self.subTest(path=path.name):
                    if items:
                        compact = json.dumps(
                            items[0],
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        self.assertIn(f"    {compact}", rendered)
                    self.assertLessEqual(len(rendered.splitlines()), len(items) + 250)

    def test_event_index_omits_commits_with_only_family_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.email", "kag@example.test"), cwd=root, check=True)
            write_fixture(root)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "source"), cwd=root, check=True)
            source_index = build_index(root)
            before = build_repository_indexes(source_index, repo_root=root)
            self.assertEqual(0, main(["--repo-root", str(root), "--index-family"]))
            subprocess.run(("git", "add", "kag/indexes"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "indexes only"), cwd=root, check=True)

            source_index = build_index(root)
            after = build_repository_indexes(source_index, repo_root=root)

        labels = {
            event["label"]
            for event in after["event"]["entries"]
            if event["event_kind"] == "git_commit"
        }
        self.assertEqual(before, after)
        self.assertNotIn("source", labels)
        self.assertNotIn("indexes only", labels)

    def test_event_index_history_ref_ignores_synthetic_merge_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.email", "kag@example.test"), cwd=root, check=True)
            write_fixture(root)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "base"), cwd=root, check=True)
            subprocess.run(("git", "checkout", "-qb", "feature"), cwd=root, check=True)
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\nFeature.\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "add", "README.md"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "feature"), cwd=root, check=True)
            feature_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            source_index = build_index(root, history_ref=feature_sha)
            feature_family = build_repository_indexes(
                source_index,
                repo_root=root,
                history_ref=feature_sha,
            )

            subprocess.run(("git", "checkout", "-q", "main"), cwd=root, check=True)
            subprocess.run(
                ("git", "merge", "--no-ff", "feature", "-m", "synthetic pull request merge"),
                cwd=root,
                check=True,
                capture_output=True,
            )
            merge_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            with mock.patch.dict(
                "os.environ",
                {
                    "AOA_REPO_LOCAL_KAG_HISTORY_REPO": root.name,
                    "AOA_REPO_LOCAL_KAG_HISTORY_REF": feature_sha,
                },
            ):
                merge_source_index = build_index(root)
                merge_family = build_repository_indexes(
                    merge_source_index,
                    repo_root=root,
                )

        def git_commit_refs(family: dict[str, dict[str, Any]]) -> set[str]:
            return {
                str(ref["ref"])
                for event in family["event"]["entries"]
                for ref in event["evidence_refs"]
                if ref["kind"] == "git_commit"
            }

        self.assertEqual(feature_family, merge_family)
        self.assertEqual(git_commit_refs(feature_family), git_commit_refs(merge_family))
        self.assertNotIn(merge_sha, git_commit_refs(merge_family))

    def test_relation_index_resolves_local_directory_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            (root / "kag" / "manifest.json").write_text(
                json.dumps({"repo": "aoa-directory-links"}), encoding="utf-8"
            )
            (root / "README.md").write_text(
                "# Demo\n\nSee [docs](docs).\n",
                encoding="utf-8",
            )
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)

        docs_entity = next(
            entry
            for entry in family["entity"]["entries"]
            if entry["semantic_key"] == "directory:docs"
        )
        readme_entity = next(
            entry
            for entry in family["entity"]["entries"]
            if entry["semantic_key"] == "README.md"
        )
        self.assertTrue(
            any(
                relation["relation_kind"] == "references"
                and relation["from_id"] == readme_entity["id"]
                and relation["to_id"] == docs_entity["id"]
                for relation in family["relation"]["entries"]
            )
        )

    def test_custom_family_outputs_remain_stable_after_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            write_fixture(root)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            args = [
                "--repo-root",
                str(root),
                "--output",
                "custom/indexes/source.json",
                "--index-family",
            ]
            self.assertEqual(0, main(args))
            subprocess.run(("git", "add", "custom/indexes"), cwd=root, check=True)
            self.assertEqual(0, main([*args, "--check"]))
            payload = load_json(root / "custom" / "indexes" / "source.json")
            family = {
                index_kind: load_json(root / "custom" / "indexes" / filename)
                for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items()
            }

        indexed_paths = {record["identity"]["path"] for record in payload["records"]}
        self.assertTrue(
            {
                "custom/indexes/source.json",
                *(
                    f"custom/indexes/{filename}"
                    for filename in REPOSITORY_INDEX_FILENAMES.values()
                ),
            }.isdisjoint(indexed_paths)
        )
        self.assertEqual(
            {"custom/indexes/source.json"},
            {index["source_index"]["path"] for index in family.values()},
        )

    def test_domain_index_catalog_example_matches_schema(self) -> None:
        schema = load_json(DOMAIN_INDEX_CATALOG_SCHEMA_PATH)
        payload = load_json(DOMAIN_INDEX_CATALOG_EXAMPLE_PATH)
        assert isinstance(schema, dict)
        Draft202012Validator.check_schema(schema)
        self.assertEqual([], list(Draft202012Validator(schema).iter_errors(payload)))

    def test_repository_index_validation_rejects_stale_source_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            entity_index = build_repository_indexes(source_index, repo_root=root)["entity"]
        entity_index["source_index"]["content_digest"] = "0" * 64
        entity_index["index_identity"]["content_digest"] = (
            repo_local_kag_index_digest_without_self(entity_index)
        )

        with self.assertRaisesRegex(ValidationError, "source index digest"):
            validate_repo_local_kag_repository_index_payload(
                entity_index,
                source_payload=source_index,
                label="entity index",
                expected_index_kind="entity",
            )

    def test_repository_index_validation_rejects_missing_source_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            artifact_index = build_repository_indexes(source_index, repo_root=root)["artifact"]
        artifact_index["entries"][0]["id"] = "aoa:missing:artifact:0000"
        artifact_index["index_identity"]["content_digest"] = (
            repo_local_kag_index_digest_without_self(artifact_index)
        )

        with self.assertRaisesRegex(ValidationError, "current source records"):
            validate_repo_local_kag_repository_index_payload(
                artifact_index,
                source_payload=source_index,
                label="artifact index",
                expected_index_kind="artifact",
            )

    def test_repository_indexes_are_separate_from_provider_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            family = build_repository_indexes(build_index(root), repo_root=root)

        for payload in family.values():
            self.assertTrue(_is_repo_local_meta_index_payload(payload))
        self.assertTrue(_is_repo_local_meta_index_payload(load_json(DOMAIN_INDEX_CATALOG_EXAMPLE_PATH)))
        self.assertFalse(_is_repo_local_meta_index_payload({"record_class": "index"}))

    def test_family_validation_rejects_dangling_relation_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
        family["relation"]["entries"][0]["to_id"] = "aoa:missing:entity:missing:0000"
        family["relation"]["index_identity"]["content_digest"] = (
            repo_local_kag_index_digest_without_self(family["relation"])
        )

        with self.assertRaisesRegex(ValidationError, "relation endpoints"):
            validate_repo_local_kag_repository_index_family(
                family,
                source_payload=source_index,
                label="repository family",
            )

    def test_family_validation_rejects_entity_without_current_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
        family["entity"]["entries"][0]["anchor_ids"] = ["aoa:missing:anchor:missing:0000"]
        family["entity"]["index_identity"]["content_digest"] = (
            repo_local_kag_index_digest_without_self(family["entity"])
        )

        with self.assertRaisesRegex(ValidationError, "current anchors"):
            validate_repo_local_kag_repository_index_family(
                family,
                source_payload=source_index,
                label="repository family",
            )

    def test_family_validation_rejects_unknown_profile_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
        family["anchor"]["entries"][0]["parser_ref"] = "missing@1"
        family["anchor"]["index_identity"]["content_digest"] = (
            repo_local_kag_index_digest_without_self(family["anchor"])
        )

        with self.assertRaisesRegex(ValidationError, "parser profiles"):
            validate_repo_local_kag_repository_index_family(
                family,
                source_payload=source_index,
                label="repository family",
            )

    def test_every_repository_record_resolves_common_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)

        for index_kind, payload in family.items():
            with self.subTest(index_kind=index_kind):
                self.assertEqual(
                    {"declared", "deterministic", "inferred", "observed"},
                    set(payload["profiles"]["trust"]),
                )
                for entry in payload["entries"]:
                    self.assertIn(entry["provenance_ref"], payload["profiles"]["provenance"])
                    self.assertIn(entry["temporal_ref"], payload["profiles"]["temporal"])
                    self.assertIn(entry["trust_ref"], payload["profiles"]["trust"])

    def test_family_validation_rejects_unknown_trust_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
        family["entity"]["entries"][0]["trust_ref"] = "missing"
        family["entity"]["index_identity"]["content_digest"] = (
            repo_local_kag_index_digest_without_self(family["entity"])
        )

        with self.assertRaisesRegex(ValidationError, "trust profiles"):
            validate_repo_local_kag_repository_index_family(
                family,
                source_payload=source_index,
                label="repository family",
            )

    def test_query_core_returns_owner_freshness_and_source_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            query = RepoKagQuery(source_index, family)

        exact = query.query("README.md", mode="exact", limit=3)
        lexical = query.query("helper", mode="lexical", limit=5)
        hybrid = query.query("demo helper", mode="hybrid", limit=5)
        self.assertEqual(source_index["repo"], exact["repo"])
        self.assertEqual(
            source_index["index_identity"]["content_digest"],
            exact["source_index"]["content_digest"],
        )
        self.assertEqual("README.md", exact["hits"][0]["path"])
        self.assertEqual("deterministic", exact["hits"][0]["trust"]["class"])
        self.assertEqual("current", exact["hits"][0]["temporal"]["state"])
        self.assertEqual("source_snapshot", exact["hits"][0]["sources"][0]["freshness"]["mode"])
        self.assertEqual("digest-only", exact["hits"][0]["sources"][0]["signs"]["verification_state"])
        self.assertEqual("stable", exact["hits"][0]["sources"][0]["abi"]["compatibility"])
        helper = next(
            hit
            for hit in lexical["hits"]
            if hit["label"] == "helper" and hit["node_class"] == "entity"
        )
        self.assertEqual("python_function", helper["kind"])
        self.assertTrue(helper["source_record_ids"])
        self.assertTrue(helper["anchor_ids"])
        self.assertTrue(hybrid["hits"])
        self.assertEqual(hybrid, query.query("demo helper", mode="hybrid", limit=5))
        Draft202012Validator(load_json(QUERY_RESULT_SCHEMA_PATH)).validate(hybrid)

    def test_query_core_discovers_reads_and_filters_canonical_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            query = RepoKagQuery(source_index, family)

        discovery = query.discover()
        self.assertEqual(source_index["repo"], discovery["repo"])
        self.assertEqual(
            {"artifact", "anchor", "entity", "event", "assertion", "relation"},
            set(discovery["node_counts"]),
        )
        relation_id = family["relation"]["entries"][0]["id"]
        relation = query.read(relation_id, access_scopes={"public"})
        self.assertIsNotNone(relation)
        self.assertEqual("relation", relation["node_class"])
        self.assertEqual(relation_id, relation["record"]["id"])
        filtered = query.filter(
            node_classes={"artifact"},
            abi_compatibilities={"stable"},
            sign_states={"digest-only"},
            provenance_modes={"deterministic"},
            temporal_states={"current"},
            access_scopes={"public"},
        )
        self.assertTrue(filtered)
        self.assertTrue(all(hit["node_class"] == "artifact" for hit in filtered))

    def test_query_cli_emits_schema_valid_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            index_root = root / "kag" / "indexes"
            index_root.mkdir(parents=True, exist_ok=True)
            (index_root / "source_surface_index.json").write_text(
                json.dumps(source_index), encoding="utf-8"
            )
            for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items():
                (index_root / filename).write_text(
                    json.dumps(family[index_kind]), encoding="utf-8"
                )
            completed = subprocess.run(
                (
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "query_repo_local_kag.py"),
                    "helper",
                    "--repo-root",
                    str(root),
                    "--mode",
                    "hybrid",
                    "--limit",
                    "5",
                ),
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)
        Draft202012Validator(load_json(QUERY_RESULT_SCHEMA_PATH)).validate(payload)
        self.assertTrue(payload["hits"])

    def test_family_validator_cli_accepts_complete_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            index_root = root / "kag" / "indexes"
            index_root.mkdir(parents=True, exist_ok=True)
            (index_root / "source_surface_index.json").write_text(
                json.dumps(source_index), encoding="utf-8"
            )
            for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items():
                (index_root / filename).write_text(
                    json.dumps(family[index_kind]), encoding="utf-8"
                )
            completed = subprocess.run(
                (
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "validate_repo_local_kag_family.py"),
                    "--repo-root",
                    str(root),
                ),
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn(
            f"[repo-local-kag-family] valid owner={root.name}",
            completed.stdout,
        )

    def test_query_core_traverses_reference_with_relation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            query = RepoKagQuery(source_index, family)

        readme_id = next(
            entry["id"]
            for entry in family["artifact"]["entries"]
            if entry["path"] == "README.md"
        )
        traversed = query.traverse(
            [readme_id],
            relation_kinds={"represents", "references"},
            max_hops=2,
        )
        usage = next(hit for hit in traversed if hit["label"] == "Usage")
        self.assertEqual("markdown_heading", usage["kind"])
        self.assertTrue(usage["evidence"]["relation_ids"])
        self.assertTrue(usage["evidence"]["anchor_ids"])


if __name__ == "__main__":
    unittest.main()
