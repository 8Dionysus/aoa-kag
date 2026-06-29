from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts import generate_repo_local_kag_coverage as coverage_generation
from scripts.generate_repo_local_kag_coverage import build_coverage
from scripts.generate_repo_local_kag_index import build_index, payload_digest


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-index.schema.json"
COVERAGE_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-coverage.schema.json"
EXAMPLE_PATH = REPO_ROOT / "examples" / "repo_local_kag_index.example.json"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class RepoLocalKagIndexTests(unittest.TestCase):
    def validate_with_schema(self, payload: object, schema_path: Path) -> None:
        schema = load_json(schema_path)
        assert isinstance(schema, dict)
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(payload),
            key=lambda error: list(error.path),
        )
        self.assertEqual([], errors)

    def test_example_matches_repo_local_kag_index_schema(self) -> None:
        self.validate_with_schema(load_json(EXAMPLE_PATH), INDEX_SCHEMA_PATH)

    def test_generator_indexes_documents_mechanics_commands_and_schema_posture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Demo\n\n## Route\n", encoding="utf-8")
            (root / "mechanics" / "alpha" / "PARTS.md").parent.mkdir(parents=True)
            (root / "mechanics" / "alpha" / "PARTS.md").write_text("# Parts\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "validate_demo.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "schemas").mkdir()
            (root / "schemas" / "demo.schema.json").write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "https://example.test/demo.schema.json",
                        "type": "object",
                    }
                ),
                encoding="utf-8",
            )

            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))

        self.validate_with_schema(payload, INDEX_SCHEMA_PATH)
        self.assertEqual(payload["index_identity"]["content_digest"], payload_digest(payload))
        summary = payload["coverage_summary"]
        self.assertGreaterEqual(summary["document_count"], 2)
        self.assertGreaterEqual(summary["heading_count"], 2)
        self.assertGreaterEqual(summary["mechanics_count"], 1)
        self.assertGreaterEqual(summary["command_count"], 1)
        self.assertGreaterEqual(summary["schema_count"], 1)

        records_by_path = {
            record["identity"]["path"]: record for record in payload["records"]
        }
        self.assertEqual("readme", records_by_path["README.md"]["document_role"])
        self.assertEqual("parts", records_by_path["mechanics/alpha/PARTS.md"]["document_role"])
        self.assertEqual(
            "mechanic_package",
            records_by_path["mechanics/alpha/PARTS.md"]["mechanics_role"],
        )
        self.assertEqual(
            "validator",
            records_by_path["scripts/validate_demo.py"]["command_role"],
        )
        self.assertEqual(
            "https://example.test/demo.schema.json",
            records_by_path["schemas/demo.schema.json"]["abi"]["contract_version"],
        )

    def test_aoa_kag_generated_index_covers_goal_surfaces(self) -> None:
        payload = build_index(REPO_ROOT, output=Path("kag/indexes/source_surface_index.json"))
        self.validate_with_schema(payload, INDEX_SCHEMA_PATH)
        summary = payload["coverage_summary"]
        self.assertGreater(summary["document_count"], 0)
        self.assertGreater(summary["mechanics_count"], 0)
        self.assertGreater(summary["command_count"], 0)
        self.assertGreater(summary["validator_count"], 0)
        self.assertGreater(summary["test_count"], 0)
        self.assertGreater(summary["schema_count"], 0)

        records_by_path = {
            record["identity"]["path"]: record for record in payload["records"]
        }
        self.assertEqual("security", records_by_path["SECURITY.md"]["artifact_kind"])
        self.assertEqual(
            "authored_source",
            records_by_path["kag/indexes/provider_readiness_index.json"]["surface_state"],
        )
        self.assertEqual(
            "authored_source",
            records_by_path["generated/AGENTS.md"]["surface_state"],
        )
        self.assertEqual(
            "",
            records_by_path["generated/AGENTS.md"]["provenance"]["generated_by"],
        )
        for module_path in (
            "scripts/generation/provider_map.py",
            "scripts/validators/repo_local_kag_index.py",
        ):
            self.assertEqual("none", records_by_path[module_path]["command_role"])
            self.assertEqual([], records_by_path[module_path]["toolchain"]["owner_commands"])
        coverage_record = records_by_path["generated/repo_local_kag_coverage.json"]
        self.assertEqual(
            "scripts/generate_repo_local_kag_coverage.py",
            coverage_record["provenance"]["generated_by"],
        )
        self.assertEqual([], coverage_record["provenance"]["materials"])
        part_generated_record = records_by_path[
            "mechanics/agon/parts/promotion-candidates/generated/"
            "agon_kag_promotion_candidate_registry.min.json"
        ]
        self.assertEqual(
            "mechanics/agon/parts/promotion-candidates/scripts/"
            "build_promotion_candidate_registry.py",
            part_generated_record["provenance"]["generated_by"],
        )
        for support_module_path in (
            "tests/support/generation_patch.py",
            "tests/support/topology_inventory.py",
        ):
            self.assertEqual("source_code", records_by_path[support_module_path]["artifact_kind"])
            self.assertEqual("source_module", records_by_path[support_module_path]["code_role"])
            self.assertEqual("none", records_by_path[support_module_path]["command_role"])
            self.assertEqual([], records_by_path[support_module_path]["toolchain"]["owner_commands"])
        for decision_index_path in (
            "docs/decisions/indexes/by-number.md",
            "docs/decisions/indexes/index_contract.yaml",
        ):
            self.assertEqual(
                "generated_readmodel",
                records_by_path[decision_index_path]["surface_state"],
            )
            self.assertEqual(
                "scripts/generate_decision_indexes.py",
                records_by_path[decision_index_path]["provenance"]["generated_by"],
            )
        self.assertEqual(
            [
                "python scripts/ci_gate.py --mode source-fast",
                "python scripts/ci_gate.py --mode generated",
            ],
            records_by_path["scripts/ci_gate.py"]["toolchain"]["owner_commands"],
        )

    def test_generator_excludes_absolute_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            output = root / "kag" / "indexes" / "source_surface_index.json"
            output.parent.mkdir(parents=True)
            output.write_text('{"stale": true}\n', encoding="utf-8")

            payload = build_index(root, output=output)

        paths = {record["identity"]["path"] for record in payload["records"]}
        self.assertIn("README.md", paths)
        self.assertNotIn("kag/indexes/source_surface_index.json", paths)

    def test_generator_uses_git_index_and_excludes_untracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            (root / "untracked.md").write_text("# WIP\n", encoding="utf-8")

            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))

        paths = {record["identity"]["path"] for record in payload["records"]}
        self.assertIn("README.md", paths)
        self.assertNotIn("untracked.md", paths)
        self.assertEqual("git-index-source-tree", payload["repo"]["git_ref"])
        for record in payload["records"]:
            self.assertEqual("git-index-source-tree", record["identity"]["git_ref"])
            self.assertEqual("git-index-source-tree", record["freshness"]["checked_ref"])

    def test_generator_indexes_tracked_files_deleted_from_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            (root / "README.md").unlink()

            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))

        records_by_path = {
            record["identity"]["path"]: record for record in payload["records"]
        }
        self.assertIn("README.md", records_by_path)
        self.assertEqual(
            "git-index-source-tree",
            records_by_path["README.md"]["identity"]["git_ref"],
        )

    def test_os_wide_coverage_report_has_owner_status_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            organ = root / "aoa-demo"
            connector = root / "connectors" / "aoa-demo-connector"
            bundle = root / "bundles" / "aoa-demo-bundle"
            for owner in (organ, connector, bundle):
                (owner / "kag" / "indexes").mkdir(parents=True)
                (owner / "README.md").write_text("# Owner\n", encoding="utf-8")
            (organ / "kag" / "indexes" / "source_surface_index.json").write_text(
                json.dumps(
                    build_index(
                        organ,
                        output=Path("kag/indexes/source_surface_index.json"),
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (connector / "kag" / "indexes" / "source_inventory.json").write_text(
                json.dumps({"schema_version": "connector-source-inventory-v1"}),
                encoding="utf-8",
            )

            payload = build_coverage(root)

        self.validate_with_schema(payload, COVERAGE_SCHEMA_PATH)
        statuses = {owner["repo"]: owner["index_status"] for owner in payload["owners"]}
        self.assertEqual("passed", statuses["aoa-demo"])
        self.assertEqual("owner-specific", statuses["aoa-demo-connector"])
        self.assertEqual("missing", statuses["aoa-demo-bundle"])

    def test_coverage_rejects_index_with_wrong_repo_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            organ = root / "aoa-demo"
            organ.mkdir()
            (organ / "README.md").write_text("# Owner\n", encoding="utf-8")
            payload = build_index(organ, output=Path("kag/indexes/source_surface_index.json"))
            payload["repo"]["name"] = "aoa-other"
            index_path = organ / "kag" / "indexes" / "source_surface_index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(json.dumps(payload), encoding="utf-8")

            coverage = build_coverage(root)

        statuses = {owner["repo"]: owner["index_status"] for owner in coverage["owners"]}
        self.assertEqual("migration-needed", statuses["aoa-demo"])

    def test_coverage_rejects_index_missing_tracked_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            organ = root / "aoa-demo"
            organ.mkdir()
            subprocess.run(["git", "init"], cwd=organ, check=True, capture_output=True)
            (organ / "README.md").write_text("# Owner\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=organ, check=True)
            payload = build_index(organ, output=Path("kag/indexes/source_surface_index.json"))
            index_path = organ / "kag" / "indexes" / "source_surface_index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(json.dumps(payload), encoding="utf-8")
            subprocess.run(
                ["git", "add", "kag/indexes/source_surface_index.json"],
                cwd=organ,
                check=True,
            )
            (organ / "NEW.md").write_text("# New\n", encoding="utf-8")
            subprocess.run(["git", "add", "NEW.md"], cwd=organ, check=True)

            coverage = build_coverage(root)

        statuses = {owner["repo"]: owner["index_status"] for owner in coverage["owners"]}
        self.assertEqual("migration-needed", statuses["aoa-demo"])

    def test_coverage_rejects_index_with_wrong_content_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            organ = root / "aoa-demo"
            organ.mkdir()
            (organ / "README.md").write_text("# Owner\n", encoding="utf-8")
            payload = build_index(organ, output=Path("kag/indexes/source_surface_index.json"))
            payload["index_identity"]["content_digest"] = "0" * 64
            index_path = organ / "kag" / "indexes" / "source_surface_index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(json.dumps(payload), encoding="utf-8")

            coverage = build_coverage(root)

        statuses = {owner["repo"]: owner["index_status"] for owner in coverage["owners"]}
        self.assertEqual("migration-needed", statuses["aoa-demo"])

    def test_coverage_rejects_index_with_stale_coverage_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            organ = root / "aoa-demo"
            organ.mkdir()
            (organ / "README.md").write_text("# Owner\n", encoding="utf-8")
            payload = build_index(organ, output=Path("kag/indexes/source_surface_index.json"))
            payload["coverage_summary"]["document_count"] = 0
            payload["index_identity"]["content_digest"] = payload_digest(payload)
            index_path = organ / "kag" / "indexes" / "source_surface_index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(json.dumps(payload), encoding="utf-8")

            coverage = build_coverage(root)

        statuses = {owner["repo"]: owner["index_status"] for owner in coverage["owners"]}
        self.assertEqual("migration-needed", statuses["aoa-demo"])

    def test_coverage_counts_tracked_source_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            organ = root / "aoa-demo"
            organ.mkdir()
            subprocess.run(["git", "init"], cwd=organ, check=True, capture_output=True)
            (organ / "README.md").write_text("# Owner\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=organ, check=True)
            (organ / ".aoa").mkdir()
            (organ / ".aoa" / "runtime-note.md").write_text("# Runtime\n", encoding="utf-8")
            (organ / "untracked.md").write_text("# WIP\n", encoding="utf-8")

            payload = build_coverage(root)

        owners = {owner["repo"]: owner for owner in payload["owners"]}
        self.assertEqual(1, owners["aoa-demo"]["coverage"]["documents"])

    def test_provider_coverage_can_carry_committed_row_for_unmounted_root(self) -> None:
        cached_owner = {
            "repo": "aoa-private",
            "owner_type": "organ",
            "root": "/srv/AbyssOS/aoa-private",
            "kag_home": "/srv/AbyssOS/aoa-private/kag",
            "index_status": "passed",
            "index_files": ["kag/indexes/source_surface_index.json"],
            "coverage": {
                "documents": 1,
                "mechanics": 0,
                "commands": 0,
                "validators": 0,
                "tests": 0,
                "scripts": 0,
                "schemas": 0,
                "generated": 0,
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            payload = coverage_generation.build_coverage(
                Path(tmpdir),
                owner_roots=[("aoa-private", Path(tmpdir) / "missing")],
                cached_owner_rows={"aoa-private": cached_owner},
            )

        self.assertEqual([cached_owner], payload["owners"])
        self.assertEqual(1, payload["coverage_summary"]["passed"])


if __name__ == "__main__":
    unittest.main()
