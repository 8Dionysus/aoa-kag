from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.generate_repo_local_kag_index import (
    REPOSITORY_INDEX_FILENAMES,
    build_index,
    build_repository_indexes,
    main,
    payload_digest,
)
from scripts.generate_repo_local_kag_coverage import source_index_matches_owner
from scripts.generation.provider_map import _is_repo_local_meta_index_payload


REPO_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_INDEX_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-repository-index.schema.json"
)
DOMAIN_INDEX_CATALOG_SCHEMA_PATH = REPO_ROOT / "schemas" / "domain-index-catalog.schema.json"
DOMAIN_INDEX_CATALOG_EXAMPLE_PATH = REPO_ROOT / "examples" / "domain_index_catalog.example.json"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_fixture(root: Path) -> None:
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "docs" / "decisions").mkdir(parents=True)
    (root / "kag" / "receipts").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
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
    (root / "kag" / "receipts" / "validation_receipt.json").write_text(
        json.dumps({"result": "valid"}),
        encoding="utf-8",
    )
    (root / "future.unknown").write_bytes(b"future")


class RepoLocalKagRepositoryIndexTests(unittest.TestCase):
    def test_repository_index_family_matches_schema(self) -> None:
        schema = load_json(REPOSITORY_INDEX_SCHEMA_PATH)
        assert isinstance(schema, dict)
        Draft202012Validator.check_schema(schema)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index)

        self.assertEqual({"entity", "artifact", "event"}, set(family))
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
            family = build_repository_indexes(source_index)

        source_count = source_index["coverage_summary"]["record_count"]
        self.assertEqual(source_count, family["entity"]["summary"]["entry_count"])
        self.assertEqual(source_count, family["artifact"]["summary"]["entry_count"])
        entity = next(
            entry for entry in family["entity"]["entries"] if entry["label"] == "future.unknown"
        )
        artifact = next(
            entry for entry in family["artifact"]["entries"] if entry["path"] == "future.unknown"
        )
        self.assertEqual("artifact", entity["entity_kind"])
        self.assertEqual("unknown", artifact["artifact_kind"])

    def test_event_index_separates_producers_declarations_and_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            family = build_repository_indexes(build_index(root))

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
        self.assertEqual("100", release["heading_ref"]["anchor"])

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

    def test_domain_index_catalog_example_matches_schema(self) -> None:
        schema = load_json(DOMAIN_INDEX_CATALOG_SCHEMA_PATH)
        payload = load_json(DOMAIN_INDEX_CATALOG_EXAMPLE_PATH)
        assert isinstance(schema, dict)
        Draft202012Validator.check_schema(schema)
        self.assertEqual([], list(Draft202012Validator(schema).iter_errors(payload)))

    def test_repository_indexes_are_separate_from_provider_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            family = build_repository_indexes(build_index(root))

        for payload in family.values():
            self.assertTrue(_is_repo_local_meta_index_payload(payload))
        self.assertTrue(_is_repo_local_meta_index_payload(load_json(DOMAIN_INDEX_CATALOG_EXAMPLE_PATH)))
        self.assertFalse(_is_repo_local_meta_index_payload({"record_class": "index"}))


if __name__ == "__main__":
    unittest.main()
