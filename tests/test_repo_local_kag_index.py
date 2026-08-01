from __future__ import annotations

import copy
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from jsonschema import Draft202012Validator

from scripts import coverage_run
from scripts import generate_repo_local_kag_coverage as coverage_generation
from scripts.generate_repo_local_kag_coverage import build_coverage, canonical_owner_root
from scripts.generate_repo_local_kag_index import (
    ARCHIVE_SUFFIXES,
    ASSET_SUFFIXES,
    DATA_TABLE_SUFFIXES,
    HTML_SUFFIXES,
    OwnerSourceSnapshot,
    PORTABLE_MIME_BY_SUFFIX,
    PORTABLE_TEXT_BASENAMES,
    RECORD_LOG_SUFFIXES,
    SERVICE_UNIT_SUFFIXES,
    SourceReadMetrics,
    SOURCE_CODE_SUFFIXES,
    SPREADSHEET_SUFFIXES,
    SourceSnapshotError,
    TEXT_ARTIFACT_SUFFIXES,
    TEXT_WRAPPER_SUFFIXES,
    build_index,
    build_repository_indexes,
    mime_for,
    normalized_json,
    owner_type_for,
    payload_digest,
    REPOSITORY_INDEX_FILENAMES,
)
from scripts.validators import repo_local_kag_index as repo_local_kag_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-index.schema.json"
COVERAGE_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-coverage.schema.json"
LOCAL_PROVIDER_MAP_SCHEMA_PATH = REPO_ROOT / "schemas" / "local-kag-provider-map.schema.json"
EXAMPLE_PATH = REPO_ROOT / "examples" / "repo_local_kag_index.example.json"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def coverage_identity_for_payload(
    payload: dict[str, object],
    *,
    epoch: str = "stable",
) -> dict[str, object]:
    owners = payload["owners"]
    assert isinstance(owners, list)

    def digest(label: str) -> str:
        return coverage_generation._sha256_digest(label.encode("utf-8"))

    snapshots: list[dict[str, str]] = []
    for position, owner_payload in enumerate(owners):
        assert isinstance(owner_payload, dict)
        owner = owner_payload["repo"]
        root = owner_payload["root"]
        assert isinstance(owner, str)
        assert isinstance(root, str)
        head_commit = f"{position + 1:040x}"
        snapshots.append(
            {
                "owner": owner,
                "root": root,
                "expected_ref": head_commit,
                "head_commit": head_commit,
                "index_tree": f"{position + 101:040x}",
                "worktree_digest": digest(f"{epoch}:{owner}:worktree"),
                "manifest_digest": digest(f"{epoch}:{owner}:manifest"),
                "family_content_digest": digest(
                    f"{epoch}:{owner}:family"
                ).removeprefix("sha256:"),
                "source_snapshot": digest(f"{epoch}:{owner}:source"),
                "event_content_digest": digest(
                    f"{epoch}:{owner}:event"
                ).removeprefix("sha256:"),
            }
        )
    return {
        "schema_version": coverage_generation.COVERAGE_IDENTITY_SCHEMA_VERSION,
        "run_scope_id": "0" * 32,
        "lane": "test",
        "display_os_root": payload["root"],
        "canonicalization_epoch": epoch,
        "index_schema_epoch": coverage_generation.INDEX_SCHEMA_VERSION,
        "provider_registry_digest": digest(f"{epoch}:registry"),
        "coverage_schema_digest": digest(f"{epoch}:coverage-schema"),
        "family_manifest_schema_digest": digest(f"{epoch}:family-schema"),
        "repository_index_schema_digest": digest(f"{epoch}:repository-schema"),
        "runtime_inputs_digest": digest(f"{epoch}:runtime"),
        "owner_snapshots": snapshots,
    }


def write_repository_index_family(
    owner_root: Path,
    *,
    history_ref: str | None = None,
) -> dict[str, object]:
    source_path = Path("kag/indexes/source_surface_index.json")
    source_index = build_index(owner_root, output=source_path)
    index_root = owner_root / source_path.parent
    index_root.mkdir(parents=True, exist_ok=True)
    (owner_root / source_path).write_text(normalized_json(source_index), encoding="utf-8")
    for index_kind, payload in build_repository_indexes(
        source_index,
        source_index_path=source_path,
        repo_root=owner_root,
        history_ref=history_ref,
        event_history_ref=history_ref,
    ).items():
        (index_root / REPOSITORY_INDEX_FILENAMES[index_kind]).write_text(
            normalized_json(payload),
            encoding="utf-8",
        )
    return source_index


def owner_specific_index_payload(repo: str = "aoa-demo-connector") -> dict[str, object]:
    return {
        "schema_version": "aoa-local-kag-record-v1",
        "repo": repo,
        "local_id": "index:demo:source-inventory",
        "record_class": "index",
        "source_refs": [
            {
                "repo": repo,
                "path": "README.md",
                "source_class": "connector_source",
                "role": "primary",
                "authority": "authored_source",
            }
        ],
        "source_owner": repo,
        "provenance_mode": "strict_source_linked",
        "derived_method": "local provider source inventory",
        "generated_or_authored": "generated_from_source",
        "status": "active",
        "owner_return_route": {
            "repo": repo,
            "surface": "README.md",
            "route_kind": "authored_meaning",
        },
        "freshness": {
            "mode": "source_snapshot",
            "state": "current",
            "checked_ref": "README.md",
        },
        "builder": {
            "route": "local validation lane",
            "surface": "scripts/validate_provider.py",
        },
        "validator": {
            "route": "aoa-kag local subtree validator",
            "lane": "local-kag",
        },
        "storage_posture": {
            "git_surface": "portable_records",
            "payload_class": "index",
            "runtime_route": "source-repo",
        },
        "consumer_route": "aoa-kag provider map",
        "index_kind": "inventory",
        "indexed_record_classes": ["node", "edge"],
        "source_record_ids": ["node:demo:readme"],
    }


def owner_specific_record_base(repo: str, local_id: str, record_class: str) -> dict[str, object]:
    return {
        "schema_version": "aoa-local-kag-record-v1",
        "repo": repo,
        "local_id": local_id,
        "record_class": record_class,
        "source_refs": [
            {
                "repo": repo,
                "path": "README.md",
                "source_class": "connector_source",
                "role": "primary",
                "authority": "authored_source",
            }
        ],
        "source_owner": repo,
        "provenance_mode": "strict_source_linked",
        "derived_method": "local provider record fixture",
        "generated_or_authored": "generated_from_source",
        "status": "active",
        "owner_return_route": {
            "repo": repo,
            "surface": "README.md",
            "route_kind": "authored_meaning",
        },
        "freshness": {
            "mode": "source_snapshot",
            "state": "current",
            "checked_ref": "README.md",
        },
        "builder": {
            "route": "local validation lane",
            "surface": "scripts/validate_provider.py",
        },
        "validator": {
            "route": "aoa-kag local subtree validator",
            "lane": "local-kag",
        },
        "storage_posture": {
            "git_surface": "portable_records",
            "payload_class": record_class,
            "runtime_route": "source-repo",
        },
        "consumer_route": "aoa-kag provider map",
    }


def write_owner_specific_provider_records(
    owner_root: Path,
    *,
    repo: str = "aoa-demo-connector",
    index_name: str = "source_inventory.json",
    index_payload: dict[str, object] | None = None,
) -> None:
    records = owner_root / "kag"
    for group in ("nodes", "edges", "indexes", "projections", "receipts"):
        (records / group).mkdir(parents=True, exist_ok=True)
    payload = index_payload or owner_specific_index_payload(repo=repo)
    (records / "nodes" / "readme.json").write_text(
        json.dumps(
            owner_specific_record_base(repo, "node:demo:readme", "node")
            | {
                "node_kind": "document",
                "label": "Demo README",
            }
        ),
        encoding="utf-8",
    )
    (records / "edges" / "readme-self.json").write_text(
        json.dumps(
            owner_specific_record_base(repo, "edge:demo:readme-self", "edge")
            | {
                "from_id": "node:demo:readme",
                "to_id": "node:demo:readme",
                "edge_kind": "routes_to",
                "edge_trace": "README.md",
            }
        ),
        encoding="utf-8",
    )
    (records / "indexes" / index_name).write_text(json.dumps(payload), encoding="utf-8")
    (records / "projections" / "readme.json").write_text(
        json.dumps(
            owner_specific_record_base(repo, "projection:demo:readme", "projection")
            | {
                "projection_kind": "mcp_packet",
                "source_record_ids": ["node:demo:readme"],
                "consumer_shape": "resource",
            }
        ),
        encoding="utf-8",
    )
    (records / "receipts" / "validation.json").write_text(
        json.dumps(
            owner_specific_record_base(repo, "receipt:demo:validation", "receipt")
            | {
                "receipt_kind": "validation",
                "result": "valid",
                "fallback_route": "aoa-kag:scripts/validate_kag.py",
            }
        ),
        encoding="utf-8",
    )


class RepoLocalKagIndexTests(unittest.TestCase):
    def test_owner_source_snapshot_batches_staged_files_and_preserves_symlink_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            (root / "one.txt").write_text("staged\n", encoding="utf-8")
            (root / "two.txt").write_text("staged\n", encoding="utf-8")
            (root / "link.txt").symlink_to("one.txt")
            subprocess.run(
                ("git", "add", "one.txt", "two.txt", "link.txt"),
                cwd=root,
                check=True,
            )
            (root / "one.txt").write_text("worktree-only\n", encoding="utf-8")
            (root / "link.txt").unlink()
            (root / "link.txt").symlink_to("two.txt")

            snapshot = OwnerSourceSnapshot.capture(root)

        self.assertEqual(b"staged\n", snapshot.read_bytes(Path("one.txt")))
        self.assertEqual(b"staged\n", snapshot.read_bytes(Path("two.txt")))
        self.assertEqual(b"one.txt", snapshot.read_bytes(Path("link.txt")))
        self.assertEqual(3, snapshot.git_invocation_count)
        self.assertEqual(2, snapshot.unique_object_count)
        self.assertEqual(3, snapshot.telemetry()["cache_hit_count"])

    def test_owner_source_snapshot_fails_closed_for_missing_git_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            missing = "1" * 40
            subprocess.run(
                (
                    "git",
                    "update-index",
                    "--add",
                    "--info-only",
                    "--cacheinfo",
                    f"100644,{missing},missing.txt",
                ),
                cwd=root,
                check=True,
            )

            with self.assertRaisesRegex(
                SourceSnapshotError,
                "missing or malformed Git blob",
            ):
                OwnerSourceSnapshot.capture(root)

    def test_owner_source_snapshot_fails_closed_for_malformed_batch_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".git").mkdir()
            object_id = "2" * 40
            results = (
                subprocess.CompletedProcess(
                    args=("git", "rev-parse"),
                    returncode=0,
                    stdout=root.as_posix() + "\n",
                ),
                subprocess.CompletedProcess(
                    args=("git", "ls-files"),
                    returncode=0,
                    stdout=f"100644 {object_id} 0\tREADME.md\0".encode("ascii"),
                ),
                subprocess.CompletedProcess(
                    args=("git", "cat-file"),
                    returncode=0,
                    stdout=f"{object_id} blob invalid\n".encode("ascii"),
                ),
            )
            with patch(
                "scripts.generate_repo_local_kag_index.subprocess.run",
                side_effect=results,
            ):
                with self.assertRaisesRegex(SourceSnapshotError, "invalid Git blob size"):
                    OwnerSourceSnapshot.capture(root)

    def test_self_coverage_root_is_checkout_path_independent(self) -> None:
        self.assertEqual(
            Path("/workspace/os/aoa-kag"),
            canonical_owner_root(Path("/workspace/os"), "aoa-kag"),
        )

    def test_runtime_source_coverage_uses_canonical_source_root(self) -> None:
        self.assertEqual(
            Path("/home/dionysus/src/abyss-stack"),
            canonical_owner_root(Path("/workspace/os"), "abyss-stack"),
        )
        self.assertEqual(
            Path("/workspace/os/abyss-machine"),
            canonical_owner_root(Path("/workspace/os"), "abyss-machine"),
        )

    def test_runtime_source_owner_type_is_checkout_path_independent(self) -> None:
        for repo in ("abyss-machine", "abyss-stack"):
            with self.subTest(repo=repo):
                self.assertEqual(
                    "runtime_source",
                    owner_type_for(repo, Path("/tmp/worktrees") / repo),
                )

    def test_mime_detection_uses_portable_explicit_mappings(self) -> None:
        self.assertEqual("application/x-sh", mime_for(Path("hook.sh")))
        self.assertEqual("application/x-ndjson", mime_for(Path("events.jsonl")))
        self.assertEqual("application/x-tar", mime_for(Path("release.tar.gz")))
        self.assertEqual("application/x-tar", mime_for(Path("release.tar.xz")))
        self.assertEqual("application/x-tar", mime_for(Path("release.v1.tar.gz")))
        self.assertEqual("application/gzip", mime_for(Path("release.gz")))
        self.assertEqual("text/plain", mime_for(Path(".env.example")))
        self.assertEqual(
            "application/x-sh",
            mime_for(Path("pre-push"), b"#!/usr/bin/env bash\nset -eu\n"),
        )
        self.assertEqual(
            "text/x-python",
            mime_for(Path("repo-tool"), b"#!/usr/bin/env python3\n"),
        )
        self.assertEqual(
            "text/plain",
            mime_for(Path("repo-tool"), b"#!/usr/bin/env future-runtime\n"),
        )
        self.assertEqual(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            mime_for(Path("table.XLSX")),
        )
        self.assertEqual("application/octet-stream", mime_for(Path("future.unknown")))
        supported_artifact_suffixes = (
            ASSET_SUFFIXES
            | ARCHIVE_SUFFIXES
            | SPREADSHEET_SUFFIXES
            | DATA_TABLE_SUFFIXES
            | RECORD_LOG_SUFFIXES
            | TEXT_ARTIFACT_SUFFIXES
            | TEXT_WRAPPER_SUFFIXES
            | HTML_SUFFIXES
            | SERVICE_UNIT_SUFFIXES
            | SOURCE_CODE_SUFFIXES
        )
        self.assertLessEqual(supported_artifact_suffixes, set(PORTABLE_MIME_BY_SUFFIX))
        for suffix in supported_artifact_suffixes:
            with self.subTest(suffix=suffix):
                self.assertNotEqual("application/octet-stream", mime_for(Path(f"artifact{suffix}")))
        for name in PORTABLE_TEXT_BASENAMES:
            with self.subTest(name=name):
                self.assertEqual("text/plain", mime_for(Path(name)))

    def test_generated_provenance_names_only_a_real_builder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "scripts").mkdir()
            (root / "generated").mkdir()
            (root / "scripts" / "build_workspace_map.py").write_text(
                'OUTPUT = "write generated/workspace_map.min.json now"\n',
                encoding="utf-8",
            )
            (root / "scripts" / "build_nearby_map.py").write_text(
                'OUTPUT = "generated/unowned.min.jsonl"\n',
                encoding="utf-8",
            )
            (root / "scripts" / "build_dashboard.py").write_text(
                'INPUT = "generated/unowned.min.json"\n',
                encoding="utf-8",
            )
            (root / "scripts" / "build_reader_only.py").write_text(
                'INPUT_PATH = "generated/reader-only.min.json"\n',
                encoding="utf-8",
            )
            (root / "scripts" / "generate_all.py").write_text(
                'OUTPUT = "generated/consolidated.min.json"\n',
                encoding="utf-8",
            )
            (root / "scripts" / "build_kebab_case_index.py").write_text(
                'PATH = "generated/kebab-case.min.json"\n',
                encoding="utf-8",
            )
            (root / "scripts" / "build_consumer.py").write_text(
                'manifest = {"source_files": ["generated/upstream.min.json"]}\n'
                "dump_json(manifest)\n",
                encoding="utf-8",
            )
            (root / "scripts" / "build_direct_writer.py").write_text(
                'write_json("generated/direct.min.json", {})\n',
                encoding="utf-8",
            )
            (root / "scripts" / "generate_method_writer.py").write_text(
                'from pathlib import Path\n'
                'path = Path("generated/method-open.min.json")\n'
                'path.open("w")\n',
                encoding="utf-8",
            )
            (root / "scripts" / "build_method_reader.py").write_text(
                'from pathlib import Path\n'
                'path = Path("generated/method-reader.min.json")\n'
                'path.open("r")\n',
                encoding="utf-8",
            )
            (root / "generated" / "workspace_map.min.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "generated" / "unowned.min.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "generated" / "reader-only.min.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "generated" / "consolidated.min.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "generated" / "kebab-case.min.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "generated" / "upstream.min.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "generated" / "direct.min.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "generated" / "method-open.min.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (root / "generated" / "method-reader.min.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "init"), cwd=root, check=True, capture_output=True)
            subprocess.run(("git", "add", "."), cwd=root, check=True)

            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))

        records = {record["identity"]["path"]: record for record in payload["records"]}
        self.assertEqual(
            "scripts/build_workspace_map.py",
            records["generated/workspace_map.min.json"]["provenance"]["generated_by"],
        )
        self.assertEqual(
            "",
            records["generated/unowned.min.json"]["provenance"]["generated_by"],
        )
        self.assertEqual(
            "",
            records["generated/reader-only.min.json"]["provenance"]["generated_by"],
        )
        self.assertEqual(
            "scripts/generate_all.py",
            records["generated/consolidated.min.json"]["provenance"]["generated_by"],
        )
        self.assertEqual(
            "scripts/build_kebab_case_index.py",
            records["generated/kebab-case.min.json"]["provenance"]["generated_by"],
        )
        self.assertEqual(
            "",
            records["generated/upstream.min.json"]["provenance"]["generated_by"],
        )
        self.assertEqual(
            "scripts/build_direct_writer.py",
            records["generated/direct.min.json"]["provenance"]["generated_by"],
        )
        self.assertEqual(
            "scripts/generate_method_writer.py",
            records["generated/method-open.min.json"]["provenance"]["generated_by"],
        )
        self.assertEqual(
            "",
            records["generated/method-reader.min.json"]["provenance"]["generated_by"],
        )

    def test_decision_index_provenance_requires_one_tracked_builder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            index_path = root / "docs" / "decisions" / "indexes" / "by-number.md"
            index_path.parent.mkdir(parents=True)
            index_path.write_text("# By number\n", encoding="utf-8")
            subprocess.run(("git", "init"), cwd=root, check=True, capture_output=True)
            subprocess.run(("git", "add", "."), cwd=root, check=True)

            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))
            record = next(
                item
                for item in payload["records"]
                if item["identity"]["path"] == index_path.relative_to(root).as_posix()
            )
            self.assertEqual("", record["provenance"]["generated_by"])

            nested_builder = root / "scripts" / "decisions" / "generate_decision_indexes.py"
            nested_builder.parent.mkdir(parents=True)
            nested_builder.write_text("print('build indexes')\n", encoding="utf-8")
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))
            record = next(
                item
                for item in payload["records"]
                if item["identity"]["path"] == index_path.relative_to(root).as_posix()
            )
            self.assertEqual(
                "scripts/decisions/generate_decision_indexes.py",
                record["provenance"]["generated_by"],
            )

            second_builder = root / "scripts" / "build_decision_indexes.py"
            second_builder.write_text("print('other builder')\n", encoding="utf-8")
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))
            record = next(
                item
                for item in payload["records"]
                if item["identity"]["path"] == index_path.relative_to(root).as_posix()
            )
            self.assertEqual("", record["provenance"]["generated_by"])

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

    def test_v1_schemas_accept_payloads_without_common_surface_profiles(self) -> None:
        coverage = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(coverage, dict)
        owners = coverage["owners"]
        assert isinstance(owners, list)
        for owner in owners:
            assert isinstance(owner, dict)
            owner.pop("common_surface_profile", None)
        self.validate_with_schema(coverage, COVERAGE_SCHEMA_PATH)

        provider_map = load_json(REPO_ROOT / "generated" / "local_kag_provider_map.json")
        assert isinstance(provider_map, dict)
        provider_map.pop("provider_common_surface_profiles", None)
        providers = provider_map["providers"]
        assert isinstance(providers, list)
        for provider in providers:
            assert isinstance(provider, dict)
            repo_local_index = provider["repo_local_index"]
            assert isinstance(repo_local_index, dict)
            repo_local_index.pop("common_surface_profile", None)
        self.validate_with_schema(provider_map, LOCAL_PROVIDER_MAP_SCHEMA_PATH)

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

    def test_generator_classifies_common_os_artifact_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / ".github").mkdir()
            (root / ".github" / "CODEOWNERS").write_text("* @owners\n", encoding="utf-8")
            (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
            (root / ".env.example").write_text("TOKEN=\n", encoding="utf-8")
            (root / "requirements-dev.txt").write_text("jsonschema\n", encoding="utf-8")
            (root / ".agents" / "skills" / "demo" / "assets").mkdir(parents=True)
            (root / ".agents" / "skills" / "demo" / "assets" / "logo.svg").write_text(
                "<svg />\n",
                encoding="utf-8",
            )
            (root / "memo" / "local").mkdir(parents=True)
            (root / "memo" / "local" / ".gitkeep").write_text("", encoding="utf-8")
            (root / ".aoa" / "live_receipts").mkdir(parents=True)
            (root / ".aoa" / "live_receipts" / "events.jsonl").write_text(
                '{"event":"ok"}\n',
                encoding="utf-8",
            )
            (root / "kag" / "receipts").mkdir(parents=True)
            (root / "kag" / "receipts" / "validation.jsonl").write_text(
                '{"result":"valid"}\n',
                encoding="utf-8",
            )
            (root / "data").mkdir()
            (root / "data" / "nodes.csv").write_text("id,label\n1,Demo\n", encoding="utf-8")
            (root / "connector" / "fixtures" / "html").mkdir(parents=True)
            (root / "connector" / "fixtures" / "html" / "topic.html").write_text(
                "<html><body>Demo</body></html>\n",
                encoding="utf-8",
            )
            (root / "archive").mkdir()
            (root / "archive" / "seed.zip").write_bytes(b"PK\x03\x04")
            (root / "carriers").mkdir()
            (root / "carriers" / "table.xlsx").write_bytes(b"xlsx")
            (root / "systemd").mkdir()
            (root / "systemd" / "demo.service").write_text("[Service]\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "start_demo.ps1").write_text("Write-Output ok\n", encoding="utf-8")
            (root / "scripts" / "sync_demo.py").write_text("print('sync')\n", encoding="utf-8")
            (root / "scripts" / "validate_demo.ps1").write_text("Write-Output ok\n", encoding="utf-8")
            (root / "scripts" / "aoa-tool").write_text(
                "#!/usr/bin/env bash\nset -eu\n",
                encoding="utf-8",
            )
            (root / "scripts" / "validate_tool").write_text(
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
                encoding="utf-8",
            )
            (root / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
            (root / "styles.css").write_text("body { color: black; }\n", encoding="utf-8")
            (root / "index.html").write_text("<main>Demo</main>\n", encoding="utf-8")
            (root / "config.alloy").write_text("logging {}\n", encoding="utf-8")
            (root / "service.env.example").write_text("PORT=1\n", encoding="utf-8")
            (root / ".deps" / "foreign").mkdir(parents=True)
            (root / ".deps" / "foreign" / "README.md").write_text("# Foreign\n", encoding="utf-8")

            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))

        self.validate_with_schema(payload, INDEX_SCHEMA_PATH)
        records_by_path = {
            record["identity"]["path"]: record for record in payload["records"]
        }
        expected_kinds = {
            ".github/CODEOWNERS": "owner_metadata",
            ".gitignore": "owner_metadata",
            ".env.example": "config",
            "requirements-dev.txt": "dependency_manifest",
            ".agents/skills/demo/assets/logo.svg": "asset",
            "memo/local/.gitkeep": "directory_marker",
            ".aoa/live_receipts/events.jsonl": "record_log",
            "kag/receipts/validation.jsonl": "receipt",
            "data/nodes.csv": "data_table",
            "connector/fixtures/html/topic.html": "fixture",
            "archive/seed.zip": "archive",
            "carriers/table.xlsx": "spreadsheet",
            "systemd/demo.service": "service_unit",
            "scripts/start_demo.ps1": "script",
            "scripts/sync_demo.py": "script",
            "scripts/validate_demo.ps1": "validator",
            "scripts/aoa-tool": "script",
            "scripts/validate_tool": "validator",
            "Dockerfile": "config",
            "styles.css": "source_code",
            "index.html": "source_code",
            "config.alloy": "config",
            "service.env.example": "config",
        }
        for path, expected_kind in expected_kinds.items():
            record = records_by_path[path]
            self.assertEqual(expected_kind, record["artifact_kind"], path)
            expected_primary = "command" if path.startswith("scripts/") else "artifact"
            if expected_kind in {"config", "source_code"}:
                expected_primary = "surface"
            self.assertEqual(expected_primary, record["classification"]["primary_kind"], path)
            self.assertEqual("high", record["classification"]["confidence"], path)
        self.assertEqual("legacy", records_by_path["archive/seed.zip"]["surface_state"])
        self.assertEqual("receipt", records_by_path["kag/receipts/validation.jsonl"]["surface_state"])
        self.assertEqual(
            "authored_source",
            records_by_path[".agents/skills/demo/assets/logo.svg"]["surface_state"],
        )
        self.assertEqual(
            "generated_receipt",
            records_by_path["kag/receipts/validation.jsonl"]["provenance"]["source_refs"][0]["authority"],
        )
        self.assertEqual("script", records_by_path["scripts/start_demo.ps1"]["command_role"])
        self.assertEqual("script", records_by_path["scripts/sync_demo.py"]["command_role"])
        self.assertEqual("validator", records_by_path["scripts/validate_demo.ps1"]["command_role"])
        self.assertEqual(
            ["pwsh scripts/start_demo.ps1"],
            records_by_path["scripts/start_demo.ps1"]["toolchain"]["owner_commands"],
        )
        self.assertEqual(
            ["python scripts/sync_demo.py"],
            records_by_path["scripts/sync_demo.py"]["toolchain"]["owner_commands"],
        )
        self.assertEqual(
            ["pwsh scripts/validate_demo.ps1"],
            records_by_path["scripts/validate_demo.ps1"]["toolchain"]["owner_commands"],
        )
        self.assertIn("pwsh", records_by_path["scripts/start_demo.ps1"]["toolchain"]["required_tools"])
        self.assertEqual("script", records_by_path["scripts/aoa-tool"]["command_role"])
        self.assertEqual("validator", records_by_path["scripts/validate_tool"]["command_role"])
        self.assertEqual(["bash"], records_by_path["scripts/aoa-tool"]["toolchain"]["required_tools"])
        self.assertEqual(
            ["python"],
            records_by_path["scripts/validate_tool"]["toolchain"]["required_tools"],
        )
        self.assertNotIn(".deps/foreign/README.md", records_by_path)
        self.assertEqual(0, payload["coverage_summary"]["unknown_count"])
        self.assertEqual(1, payload["classification_summary"]["artifact_kind"]["asset"])
        self.assertEqual(1, payload["classification_summary"]["artifact_kind"]["receipt"])
        self.assertEqual(1, payload["classification_summary"]["artifact_kind"]["record_log"])

    def test_generator_distinguishes_owner_skill_source_from_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "aoa-owner"
            source = root / "skills" / "aoa-owner" / "SKILL.md"
            projection = root / ".agents" / "skills" / "aoa-owner" / "SKILL.md"
            source.parent.mkdir(parents=True)
            projection.parent.mkdir(parents=True)
            skill_text = "---\nname: aoa-owner\ndescription: Owner task.\n---\n# Owner\n"
            source.write_text(skill_text, encoding="utf-8")
            projection.write_text(skill_text, encoding="utf-8")
            (root / "skills" / "port.manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa_skill_home_port_v1",
                        "contract_ref": "aoa-skills:schemas/skill-home-port.schema.json",
                        "owner_repo": "aoa-owner",
                        "owner_ref": "AGENTS.md",
                        "bundles": [
                            {
                                "name": "aoa-owner",
                                "path": "skills/aoa-owner",
                                "version": "0.1.0",
                                "lifecycle": "admitted",
                                "visibility": "advertised",
                                "admission_ref": "docs/decisions/OWNER-D-0001.md",
                            }
                        ],
                        "projection": {
                            "runtime": "codex",
                            "scope": "repo",
                            "root": ".agents/skills",
                            "mode": "generated-copy",
                            "skills": ["aoa-owner"],
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "add", "."), cwd=root, check=True)

            payload = build_index(
                root,
                output=Path("kag/indexes/source_surface_index.json"),
            )
            previous_payload = json.loads(json.dumps(payload))
            previous_projection = next(
                record
                for record in previous_payload["records"]
                if record["identity"]["path"]
                == ".agents/skills/aoa-owner/SKILL.md"
            )
            previous_projection["surface_state"] = "authored_source"
            previous_projection["observed_form"] = "file"
            previous_projection["provenance"]["source_refs"][0]["path"] = (
                ".agents/skills/aoa-owner/SKILL.md"
            )
            previous_projection["provenance"]["materials"] = []
            previous_projection["provenance"]["generated_by"] = ""
            previous_projection["owner_return_route"]["surface"] = (
                ".agents/skills/aoa-owner/SKILL.md"
            )
            incremental_payload = build_index(
                root,
                output=Path("kag/indexes/source_surface_index.json"),
                previous_index=previous_payload,
            )
            family = build_repository_indexes(
                payload,
                source_index_path=Path("kag/indexes/source_surface_index.json"),
                repo_root=root,
            )

        self.validate_with_schema(payload, INDEX_SCHEMA_PATH)
        records_by_path = {
            record["identity"]["path"]: record for record in payload["records"]
        }
        source_record = records_by_path["skills/aoa-owner/SKILL.md"]
        projection_record = records_by_path[".agents/skills/aoa-owner/SKILL.md"]
        self.assertEqual("authored_source", source_record["surface_state"])
        self.assertEqual("generated_projection", projection_record["surface_state"])
        self.assertEqual("generated_output", projection_record["observed_form"])
        self.assertEqual("generated", projection_record["abi"]["compatibility"])
        self.assertEqual(
            [
                {
                    "repo": "aoa-owner",
                    "path": "skills/aoa-owner/SKILL.md",
                    "role": "primary",
                    "authority": "authored_source",
                }
            ],
            projection_record["provenance"]["source_refs"],
        )
        self.assertEqual(
            [
                {
                    "repo": "aoa-owner",
                    "path": "skills/port.manifest.json",
                    "role": "material",
                    "authority": "authored_source",
                }
            ],
            projection_record["provenance"]["materials"],
        )
        self.assertEqual(
            "aoa-skills:scripts/build_home_skill_projection.py",
            projection_record["provenance"]["generated_by"],
        )
        self.assertIn(
            "aoa-skills:scripts/validate_home_skill_port.py",
            projection_record["provenance"]["validated_by"],
        )
        self.assertEqual(
            {
                "repo": "aoa-owner",
                "surface": "skills/aoa-owner/SKILL.md",
                "route_kind": "document_owner",
            },
            projection_record["owner_return_route"],
        )
        self.assertEqual(
            1,
            payload["classification_summary"]["surface_state"][
                "generated_projection"
            ],
        )
        self.assertEqual(payload, incremental_payload)
        relation_entries = family["relation"]["entries"]
        self.assertTrue(
            any(
                relation["relation_kind"] == "derives_from"
                and relation["from_id"] == projection_record["identity"]["id"]
                and relation["to_id"] == source_record["identity"]["id"]
                for relation in relation_entries
            )
        )

    def test_generator_rejects_divergent_owner_skill_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "aoa-owner"
            source = root / "skills" / "aoa-owner" / "SKILL.md"
            projection = root / ".agents" / "skills" / "aoa-owner" / "SKILL.md"
            source.parent.mkdir(parents=True)
            projection.parent.mkdir(parents=True)
            source.write_text("# canonical\n", encoding="utf-8")
            projection.write_text("# drifted\n", encoding="utf-8")
            (root / "skills" / "port.manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa_skill_home_port_v1",
                        "bundles": [
                            {"name": "aoa-owner", "path": "skills/aoa-owner"}
                        ],
                        "projection": {
                            "root": ".agents/skills",
                            "mode": "generated-copy",
                            "skills": ["aoa-owner"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "add", "."), cwd=root, check=True)

            with self.assertRaisesRegex(
                ValueError,
                "does not match canonical source skills/aoa-owner/SKILL.md",
            ):
                build_index(root)

    def test_generator_indexes_os_user_exposed_owner_skill_without_repo_projection(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "aoa-owner"
            source = root / "skills" / "aoa-owner" / "SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "---\nname: aoa-owner\ndescription: Owner task.\n---\n# Owner\n",
                encoding="utf-8",
            )
            (root / "skills" / "port.manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa_skill_home_port_v2",
                        "contract_ref": "aoa-skills:schemas/skill-home-port.schema.json",
                        "owner_repo": "aoa-owner",
                        "owner_ref": "AGENTS.md",
                        "bundles": [
                            {
                                "name": "aoa-owner",
                                "path": "skills/aoa-owner",
                                "version": "0.2.0",
                                "lifecycle": "admitted",
                                "visibility": "advertised",
                                "admission_ref": "docs/decisions/OWNER-D-0002.md",
                            }
                        ],
                        "exposure": {
                            "runtime": "codex",
                            "scope": "user",
                            "profile": "os-user-default",
                            "mode": "profile-selected",
                            "skills": ["aoa-owner"],
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "add", "."), cwd=root, check=True)

            payload = build_index(root)

        self.validate_with_schema(payload, INDEX_SCHEMA_PATH)
        records_by_path = {
            record["identity"]["path"]: record for record in payload["records"]
        }
        source_record = records_by_path["skills/aoa-owner/SKILL.md"]
        self.assertEqual("authored_source", source_record["surface_state"])
        self.assertEqual("skill", source_record["document_role"])
        self.assertNotIn(".agents/skills/aoa-owner/SKILL.md", records_by_path)

    def test_generator_rejects_os_user_exposed_same_name_repo_projection(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "aoa-owner"
            source = root / "skills" / "aoa-owner" / "SKILL.md"
            projection = root / ".agents" / "skills" / "aoa-owner" / "SKILL.md"
            source.parent.mkdir(parents=True)
            projection.parent.mkdir(parents=True)
            source.write_text("# canonical\n", encoding="utf-8")
            projection.write_text("# duplicate\n", encoding="utf-8")
            (root / "skills" / "port.manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa_skill_home_port_v2",
                        "bundles": [
                            {"name": "aoa-owner", "path": "skills/aoa-owner"}
                        ],
                        "exposure": {
                            "runtime": "codex",
                            "scope": "user",
                            "profile": "os-user-default",
                            "mode": "profile-selected",
                            "skills": ["aoa-owner"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "add", "."), cwd=root, check=True)

            with self.assertRaisesRegex(
                ValueError,
                "OS user-exposed skill aoa-owner has a same-name repo projection",
            ):
                build_index(root)

    def test_generator_classifies_tracked_symlinks_from_git_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / "README.link").symlink_to("README.md")
            subprocess.run(("git", "add", "."), cwd=root, check=True)

            payload = build_index(root)

        self.validate_with_schema(payload, INDEX_SCHEMA_PATH)
        record = next(
            item for item in payload["records"] if item["identity"]["path"] == "README.link"
        )
        self.assertEqual("symlink", record["artifact_kind"])
        self.assertEqual("symlink", record["observed_form"])
        self.assertEqual("inode/symlink", record["identity"]["mime"])
        self.assertEqual("artifact", record["classification"]["primary_kind"])

    def test_common_surface_profile_recomputes_counts_from_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "validate_demo.py").write_text("print('ok')\n", encoding="utf-8")
            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))
            payload["classification_summary"] = {
                "artifact_kind": {"document": 99},
                "primary_kind": {"document": 99},
                "surface_state": {"authored_source": 99},
                "document_role": {"readme": 99},
                "mechanics_role": {"none": 99},
                "command_role": {"none": 99},
            }
            payload["coverage_summary"] = {
                "record_count": 99,
                "unknown_count": 99,
                "generated_count": 99,
                "validator_count": 0,
            }
            index_path = root / "kag" / "indexes" / "source_surface_index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(json.dumps(payload), encoding="utf-8")

            profile = coverage_generation.common_surface_profile(root, index_status="passed")

        self.assertEqual("source_surface_index", profile["source"])
        self.assertEqual(1, profile["counts"]["artifact_kind"]["document"])
        self.assertEqual(1, profile["counts"]["artifact_kind"]["validator"])
        self.assertEqual(1, profile["counts"]["command_role"]["validator"])
        self.assertEqual(0, profile["quality"]["unknown_count"])
        self.assertFalse(profile["quality"]["has_generated_readmodels"])

    def test_common_surface_profile_scans_tree_for_malformed_source_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            index_path = root / "kag" / "indexes" / "source_surface_index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(
                json.dumps(
                    {
                        "schema_version": "aoa-repo-local-kag-index-v1",
                        "repo": "malformed",
                        "records": [],
                    }
                ),
                encoding="utf-8",
            )

            profile = coverage_generation.common_surface_profile(
                root,
                index_status="migration-needed",
            )

        self.assertEqual("source_tree_scan", profile["source"])
        self.assertEqual(1, profile["counts"]["artifact_kind"]["document"])
        self.assertEqual(0, profile["quality"]["unknown_count"])

    def test_generator_qualifies_external_kag_routes_and_preserves_generated_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / "kag" / "indexes").mkdir(parents=True)
            (root / "kag" / "projections").mkdir(parents=True)
            (root / "kag" / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa-local-kag-manifest-v1",
                        "repo": "aoa-demo-connector",
                        "validation_routes": [
                            {"route": "scripts/validate_connector.py", "lane": "owner-local"},
                            {"route": "aoa-kag:scripts/validate_kag.py", "lane": "local-kag"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / "kag" / "indexes" / "source_inventory.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa-local-kag-record-v1",
                        "record_class": "index",
                        "generated_or_authored": "generated_from_source",
                    }
                ),
                encoding="utf-8",
            )
            (root / "kag" / "projections" / "source_return.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa-local-kag-record-v1",
                        "record_class": "projection",
                        "generated_or_authored": "generated_from_source",
                    }
                ),
                encoding="utf-8",
            )
            (root / "pyproject.toml").write_text(
                "[tool.pytest.ini_options]\npythonpath = ['src']\n",
                encoding="utf-8",
            )
            (root / "src" / "demo").mkdir(parents=True)
            (root / "src" / "demo" / "__init__.py").write_text("", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("def test_demo():\n    assert True\n", encoding="utf-8")

            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))

        self.validate_with_schema(payload, INDEX_SCHEMA_PATH)
        records_by_path = {
            record["identity"]["path"]: record for record in payload["records"]
        }
        readme_record = records_by_path["README.md"]
        self.assertEqual(
            "aoa-kag:scripts/generate_repo_local_kag_index.py",
            readme_record["provenance"]["observed_by"],
        )
        self.assertEqual(
            ["aoa-kag:scripts/validate_kag.py"],
            readme_record["provenance"]["validated_by"],
        )
        self.assertEqual(
            "aoa-kag:scripts/validate_kag.py",
            readme_record["validator_route"]["surface"],
        )
        self.assertEqual("aoa-kag", readme_record["validator_route"]["repo"])
        self.assertEqual("aoa-kag", readme_record["consumer_route"]["repo"])
        self.assertEqual(
            "aoa-demo-connector",
            readme_record["owner_return_route"]["repo"],
        )

        inventory_record = records_by_path["kag/indexes/source_inventory.json"]
        projection_record = records_by_path["kag/projections/source_return.json"]
        for record in (inventory_record, projection_record):
            self.assertEqual("generated_readmodel", record["surface_state"])
            self.assertEqual(
                "derived_readmodel",
                record["provenance"]["source_refs"][0]["authority"],
            )
            self.assertEqual("generated", record["abi"]["compatibility"])
            self.assertEqual(
                "scripts/validate_connector.py",
                record["provenance"]["generated_by"],
            )
        self.assertGreaterEqual(payload["coverage_summary"]["generated_count"], 2)
        self.assertEqual(
            ["PYTHONPATH=src python -m pytest -q"],
            records_by_path["tests/test_demo.py"]["toolchain"]["owner_commands"],
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
        self.assertEqual(0, summary["unknown_count"])
        self.assertEqual(
            summary["record_count"],
            sum(payload["classification_summary"]["artifact_kind"].values()),
        )

        records_by_path = {
            record["identity"]["path"]: record for record in payload["records"]
        }
        self.assertEqual("owner_metadata", records_by_path[".github/CODEOWNERS"]["artifact_kind"])
        self.assertEqual("owner_metadata", records_by_path[".gitignore"]["artifact_kind"])
        skill_record = records_by_path["skills/aoa-kag/SKILL.md"]
        self.assertEqual("document", skill_record["artifact_kind"])
        self.assertEqual("skill", skill_record["document_role"])
        self.assertEqual("authored_source", skill_record["surface_state"])
        self.assertEqual(
            {
                "repo": "aoa-kag",
                "surface": "skills/aoa-kag/SKILL.md",
                "route_kind": "document_owner",
            },
            skill_record["owner_return_route"],
        )
        skill_manifest_record = records_by_path["skills/port.manifest.json"]
        self.assertEqual("config", skill_manifest_record["artifact_kind"])
        self.assertEqual(
            "aoa_skill_home_port_v2",
            skill_manifest_record["abi"]["schema_version"],
        )
        self.assertFalse(
            any(path.startswith(".agents/skills/") for path in records_by_path)
        )
        self.assertEqual("security", records_by_path["SECURITY.md"]["artifact_kind"])
        self.assertEqual(
            "generated_readmodel",
            records_by_path["kag/indexes/provider_readiness_index.json"]["surface_state"],
        )
        self.assertEqual(
            "kag/manifest.json",
            records_by_path["kag/indexes/provider_readiness_index.json"]["provenance"][
                "generated_by"
            ],
        )
        self.assertEqual(
            "generated_readmodel",
            records_by_path["kag/projections/mcp_contract_resource.json"]["surface_state"],
        )
        self.assertEqual(
            "kag/manifest.json",
            records_by_path["kag/projections/mcp_contract_resource.json"]["provenance"][
                "generated_by"
            ],
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
        provider_runner = records_by_path["scripts/sync_provider_checkouts.py"]
        self.assertEqual("script", provider_runner["artifact_kind"])
        self.assertEqual("entrypoint", provider_runner["code_role"])
        self.assertEqual("script", provider_runner["command_role"])
        self.assertEqual(
            ["python scripts/sync_provider_checkouts.py"],
            provider_runner["toolchain"]["owner_commands"],
        )
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
            "application/yaml",
            records_by_path["docs/decisions/indexes/index_contract.yaml"]["identity"]["mime"],
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

    def test_generator_excludes_canonical_self_index_with_external_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory() as outdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            index = root / "kag" / "indexes" / "source_surface_index.json"
            index.parent.mkdir(parents=True)
            index.write_text('{"stale": true}\n', encoding="utf-8")

            payload = build_index(root, output=Path(outdir) / "candidate.json")

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

    def test_generator_uses_manifest_repo_identity_in_git_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "aoa-kag-source-surface-index-worktree"
            root.mkdir()
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / "kag").mkdir()
            (root / "kag" / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa-local-kag-manifest-v1",
                        "repo": "aoa-kag",
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", "README.md", "kag/manifest.json"],
                cwd=root,
                check=True,
            )

            payload = build_index(root, output=Path("kag/indexes/source_surface_index.json"))
            self.assertTrue(coverage_generation.source_index_matches_owner(root, payload))

        self.assertEqual("aoa-kag", payload["repo"]["name"])
        records_by_path = {
            record["identity"]["path"]: record for record in payload["records"]
        }
        readme_record = records_by_path["README.md"]
        self.assertEqual("aoa-kag", readme_record["identity"]["repo"])
        self.assertEqual(
            "aoa-kag",
            readme_record["provenance"]["source_refs"][0]["repo"],
        )

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
            bundle_provider = root / "bundles" / "aoa-demo-bundle-provider"
            current_bundle_provider = root / "bundles" / "aoa-demo-current-bundle-provider"
            for owner in (organ, connector, bundle, bundle_provider, current_bundle_provider):
                (owner / "kag" / "indexes").mkdir(parents=True)
                (owner / "README.md").write_text("# Owner\n", encoding="utf-8")
            write_repository_index_family(organ)
            write_owner_specific_provider_records(connector)
            stale_bundle_index = build_index(
                bundle_provider,
                output=Path("kag/indexes/source_surface_index.json"),
            )
            stale_bundle_index["coverage_summary"]["document_count"] = 0
            stale_bundle_index["index_identity"]["content_digest"] = payload_digest(stale_bundle_index)
            (bundle_provider / "kag" / "indexes" / "source_surface_index.json").write_text(
                json.dumps(stale_bundle_index),
                encoding="utf-8",
            )
            write_owner_specific_provider_records(
                bundle_provider,
                repo="aoa-demo-bundle-provider",
                index_name="session_memory_source_inventory.json",
            )
            write_owner_specific_provider_records(
                current_bundle_provider,
                repo="aoa-demo-current-bundle-provider",
                index_name="session_memory_source_inventory.json",
            )
            write_repository_index_family(current_bundle_provider)

            payload = build_coverage(root)

        self.validate_with_schema(payload, COVERAGE_SCHEMA_PATH)
        statuses = {owner["repo"]: owner["index_status"] for owner in payload["owners"]}
        self.assertEqual("passed", statuses["aoa-demo"])
        self.assertEqual("owner-specific", statuses["aoa-demo-connector"])
        self.assertEqual("missing", statuses["aoa-demo-bundle"])
        self.assertEqual("migration-needed", statuses["aoa-demo-bundle-provider"])
        self.assertEqual("passed", statuses["aoa-demo-current-bundle-provider"])
        owners = {owner["repo"]: owner for owner in payload["owners"]}
        expected_family = {
            "source": "kag/indexes/source_surface_index.json",
            "entity": "kag/indexes/repo_entity_index.json",
            "artifact": "kag/indexes/repo_artifact_index.json",
            "anchor": "kag/indexes/repo_anchor_index.json",
            "event": "kag/indexes/repo_event_index.json",
            "assertion": "kag/indexes/repo_assertion_index.json",
            "relation": "kag/indexes/repo_relation_index.json",
        }
        self.assertEqual(expected_family, owners["aoa-demo"]["repository_index_family"])
        self.assertEqual("", owners["aoa-demo"]["domain_index_catalog_ref"])
        self.assertEqual(
            "source_surface_index",
            owners["aoa-demo"]["common_surface_profile"]["source"],
        )
        self.assertEqual(
            "source_surface_index",
            owners["aoa-demo-current-bundle-provider"]["common_surface_profile"]["source"],
        )
        self.assertIn(
            "kag/indexes/session_memory_source_inventory.json",
            owners["aoa-demo-current-bundle-provider"]["index_files"],
        )
        self.assertEqual(
            expected_family,
            owners["aoa-demo-current-bundle-provider"]["repository_index_family"],
        )
        self.assertEqual(
            "source_tree_scan",
            owners["aoa-demo-connector"]["common_surface_profile"]["source"],
        )
        self.assertTrue(
            owners["aoa-demo-connector"]["common_surface_profile"]["quality"]["has_kag_home"]
        )
        self.assertIn(
            "artifact_kind",
            owners["aoa-demo"]["common_surface_profile"]["counts"],
        )

    def test_coverage_requires_complete_repository_index_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            organ = root / "aoa-demo"
            organ.mkdir()
            (organ / "README.md").write_text("# Owner\n", encoding="utf-8")
            source_index = build_index(
                organ,
                output=Path("kag/indexes/source_surface_index.json"),
            )
            index_path = organ / "kag" / "indexes" / "source_surface_index.json"
            index_path.parent.mkdir(parents=True)
            index_path.write_text(normalized_json(source_index), encoding="utf-8")

            coverage = build_coverage(root)

        owner = coverage["owners"][0]
        self.assertEqual("migration-needed", owner["index_status"])
        self.assertEqual(
            {"source": "kag/indexes/source_surface_index.json"},
            owner["repository_index_family"],
        )

    def test_coverage_rejects_reproducible_family_with_dangling_event_object(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "aoa-demo"
            (root / "scripts").mkdir(parents=True)
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "README.md").write_text("# Owner\n", encoding="utf-8")
            (root / "scripts" / "run.py").write_text(
                "print('run')\n",
                encoding="utf-8",
            )
            (root / ".github" / "workflows" / "validate.yml").write_text(
                "name: Validate\n",
                encoding="utf-8",
            )
            source_index = write_repository_index_family(root)
            family = {
                index_kind: load_json(
                    root / "kag" / "indexes" / filename
                )
                for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items()
            }
            event = family["event"]
            event["entries"][0]["object_ids"] = [
                "aoa:aoa-demo:artifact:dangling"
            ]
            event["index_identity"]["content_digest"] = payload_digest(event)
            (root / "kag" / "indexes" / REPOSITORY_INDEX_FILENAMES["event"]).write_text(
                normalized_json(event),
                encoding="utf-8",
            )

            with patch.object(
                coverage_generation,
                "build_repository_indexes",
                return_value=family,
            ):
                self.assertFalse(
                    coverage_generation.repository_index_family_matches_owner(
                        root,
                        source_index,
                    )
                )

    def test_coverage_reuses_exact_family_validation_from_same_run(self) -> None:
        root = Path("/srv/AbyssOS/aoa-demo")
        source_index: dict[str, object] = {}
        family = {index_kind: {} for index_kind in REPOSITORY_INDEX_FILENAMES}
        manifest = {
            "family_identity": {
                "content_digest": "a" * 64,
            }
        }
        metrics = SourceReadMetrics()
        snapshot = SimpleNamespace(metrics=metrics)

        with coverage_run.coverage_run_scope(lane="test", force_new=True):
            repo_local_kag_validator.record_run_validated_portable_family(
                root,
                manifest,
            )
            with patch.object(
                coverage_generation,
                "build_repository_indexes",
                return_value=family,
            ), patch.object(
                coverage_generation,
                "repository_event_history_ref",
                return_value=None,
            ), patch.object(
                coverage_generation,
                "_portable_bundle",
                return_value=(source_index, family, manifest),
            ), patch.object(
                repo_local_kag_validator,
                "validate_repo_local_kag_repository_index_family",
            ) as validate:
                matches = coverage_generation.repository_index_family_matches_owner(
                    root,
                    source_index,
                    source_snapshot=snapshot,
                )

        self.assertTrue(matches)
        validate.assert_not_called()
        self.assertEqual(1, metrics.family_validation_cache_hits)
        self.assertEqual(0, metrics.family_validation_cache_misses)

    def test_semantic_proof_reuses_only_exact_same_run_family_identity(self) -> None:
        root = Path("/srv/AbyssOS/aoa-demo")
        manifest = {"family_identity": {"content_digest": "a" * 64}}
        changed = {"family_identity": {"content_digest": "b" * 64}}

        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            self.assertFalse(
                repo_local_kag_validator.portable_family_semantic_proof_in_current_run(
                    root,
                    manifest,
                )
            )
            repo_local_kag_validator.record_run_portable_family_semantic_proof(
                root,
                manifest,
            )
            self.assertTrue(
                repo_local_kag_validator.portable_family_semantic_proof_in_current_run(
                    root,
                    manifest,
                )
            )
            self.assertFalse(
                repo_local_kag_validator.portable_family_semantic_proof_in_current_run(
                    root,
                    changed,
                )
            )
            summary = coverage_run.coverage_run_summary(run)

        proof_summary = summary["same_run_semantic_proof"]
        self.assertEqual(1, proof_summary["hit_count"])
        self.assertEqual(1, proof_summary["issued_count"])
        self.assertEqual(2, proof_summary["miss_count"])
        self.assertEqual(0, proof_summary["reject_count"])
        self.assertEqual(
            ["identity-mismatch", "proof-absent"],
            proof_summary["reasons"],
        )

    def test_semantic_proof_rejects_validator_epoch_change(self) -> None:
        root = Path("/srv/AbyssOS/aoa-demo")
        manifest = {"family_identity": {"content_digest": "a" * 64}}

        with coverage_run.coverage_run_scope(lane="test", force_new=True):
            with patch.object(
                repo_local_kag_validator,
                "_portable_family_semantic_validator_digest",
                return_value="sha256:" + "1" * 64,
            ):
                repo_local_kag_validator.record_run_portable_family_semantic_proof(
                    root,
                    manifest,
                )
            with patch.object(
                repo_local_kag_validator,
                "_portable_family_semantic_validator_digest",
                return_value="sha256:" + "2" * 64,
            ):
                self.assertFalse(
                    repo_local_kag_validator.portable_family_semantic_proof_in_current_run(
                        root,
                        manifest,
                    )
                )

    def test_semantic_proof_epoch_binds_repository_schema_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_path = Path(temp_dir) / "repository-index.schema.json"
            schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
            with patch.object(
                repo_local_kag_validator,
                "REPO_LOCAL_KAG_REPOSITORY_INDEX_SCHEMA_PATH",
                schema_path,
            ):
                before = (
                    repo_local_kag_validator._portable_family_semantic_validator_digest()
                )
                schema_path.write_text('{"type":"string"}\n', encoding="utf-8")
                after = (
                    repo_local_kag_validator._portable_family_semantic_validator_digest()
                )

        self.assertNotEqual(before, after)

    def test_semantic_proof_corruption_and_symlink_fall_back_cold(self) -> None:
        root = Path("/srv/AbyssOS/aoa-demo")
        manifest = {"family_identity": {"content_digest": "a" * 64}}
        with tempfile.TemporaryDirectory() as temp_dir:
            external = Path(temp_dir) / "external.json"
            external.write_text("{}\n", encoding="utf-8")
            with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
                path = (
                    run.scope_dir
                    / repo_local_kag_validator.PORTABLE_FAMILY_SEMANTIC_PROOF_FILENAME
                )
                path.write_text("not-json\n", encoding="utf-8")
                self.assertFalse(
                    repo_local_kag_validator.portable_family_semantic_proof_in_current_run(
                        root,
                        manifest,
                    )
                )
                path.unlink()
                path.symlink_to(external)
                self.assertFalse(
                    repo_local_kag_validator.portable_family_semantic_proof_in_current_run(
                        root,
                        manifest,
                    )
                )
                repo_local_kag_validator.record_run_portable_family_semantic_proof(
                    root,
                    manifest,
                )
                self.assertTrue(path.is_symlink())

    def test_semantic_proof_force_cold_switch_disables_issue_and_consume(self) -> None:
        root = Path("/srv/AbyssOS/aoa-demo")
        manifest = {"family_identity": {"content_digest": "a" * 64}}
        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run, patch.dict(
            os.environ,
            {repo_local_kag_validator.FORCE_COLD_SEMANTIC_VALIDATION_ENV: "1"},
        ):
            repo_local_kag_validator.record_run_portable_family_semantic_proof(
                root,
                manifest,
            )
            self.assertFalse(
                repo_local_kag_validator.portable_family_semantic_proof_in_current_run(
                    root,
                    manifest,
                )
            )
            self.assertFalse(
                (
                    run.scope_dir
                    / repo_local_kag_validator.PORTABLE_FAMILY_SEMANTIC_PROOF_FILENAME
                ).exists()
            )
            summary = coverage_run.coverage_run_summary(run)

        self.assertEqual(
            ["forced-cold"],
            summary["same_run_semantic_proof"]["reasons"],
        )

    def test_generated_family_semantic_phase_consumes_exact_run_proof(self) -> None:
        from scripts.repo_local import portable_family

        payload: dict[str, object] = {}
        family = {index_kind: {} for index_kind in REPOSITORY_INDEX_FILENAMES}
        manifest = {"family_identity": {"content_digest": "a" * 64}}
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "index_family.manifest.json"
            manifest_path.write_text("{}\n", encoding="utf-8")
            with patch.object(
                repo_local_kag_validator,
                "REPO_LOCAL_KAG_FAMILY_MANIFEST_PATH",
                manifest_path,
            ), patch.object(
                portable_family,
                "load_portable_family",
                return_value=(payload, family, manifest),
            ), patch.object(
                repo_local_kag_validator,
                "repo_local_kag_validate_payload",
            ), patch.object(
                repo_local_kag_validator,
                "validate_repo_local_kag_index_payload",
            ), patch.object(
                repo_local_kag_validator,
                "build_index",
                return_value=payload,
            ), patch.object(
                repo_local_kag_validator,
                "build_repository_indexes",
                return_value=family,
            ), patch.object(
                repo_local_kag_validator,
                "portable_family_semantic_proof_in_current_run",
                return_value=True,
            ), patch.object(
                repo_local_kag_validator,
                "validate_repo_local_kag_repository_index_family",
            ) as semantic_validate, patch.object(
                portable_family,
                "build_portable_family",
                return_value=(manifest, {}),
            ), patch.object(
                portable_family,
                "check_portable_output",
                return_value=True,
            ):
                repo_local_kag_validator.validate_repo_local_kag_index_generated_payload()

        semantic_validate.assert_not_called()

    def test_repo_local_schema_compilation_reuses_only_exact_schema_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_path = Path(temp_dir) / "schema.json"
            schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
            repo_local_kag_validator._cached_repo_local_schema_validator.cache_clear()

            repo_local_kag_validator.repo_local_kag_validate_payload(
                {},
                schema_path=schema_path,
                label="demo",
            )
            repo_local_kag_validator.repo_local_kag_validate_payload(
                {},
                schema_path=schema_path,
                label="demo",
            )
            cache_info = repo_local_kag_validator._cached_repo_local_schema_validator.cache_info()
            self.assertEqual(1, cache_info.misses)
            self.assertEqual(1, cache_info.hits)

            schema_path.write_text('{"type":"string"}\n', encoding="utf-8")
            with self.assertRaisesRegex(
                repo_local_kag_validator.ValidationError,
                "does not match schema",
            ):
                repo_local_kag_validator.repo_local_kag_validate_payload(
                    {},
                    schema_path=schema_path,
                    label="demo",
                )
            changed_info = repo_local_kag_validator._cached_repo_local_schema_validator.cache_info()
            self.assertEqual(2, changed_info.misses)

    def test_force_cold_schema_compilation_bypasses_same_process_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_path = Path(temp_dir) / "schema.json"
            schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
            repo_local_kag_validator._cached_repo_local_schema_validator.cache_clear()
            with patch.dict(
                os.environ,
                {repo_local_kag_validator.FORCE_COLD_SCHEMA_COMPILATION_ENV: "1"},
            ):
                for _ in range(2):
                    repo_local_kag_validator.repo_local_kag_validate_payload(
                        {},
                        schema_path=schema_path,
                        label="demo",
                    )

            cache_info = repo_local_kag_validator._cached_repo_local_schema_validator.cache_info()
            self.assertEqual(0, cache_info.misses)
            self.assertEqual(0, cache_info.hits)

    def test_coverage_validates_family_without_same_run_identity(self) -> None:
        root = Path("/srv/AbyssOS/aoa-demo")
        source_index: dict[str, object] = {}
        family = {index_kind: {} for index_kind in REPOSITORY_INDEX_FILENAMES}
        manifest = {
            "family_identity": {
                "content_digest": "b" * 64,
            }
        }
        metrics = SourceReadMetrics()
        snapshot = SimpleNamespace(metrics=metrics)

        with coverage_run.coverage_run_scope(lane="test", force_new=True), patch.object(
            coverage_generation,
            "build_repository_indexes",
            return_value=family,
        ), patch.object(
            coverage_generation,
            "repository_event_history_ref",
            return_value=None,
        ), patch.object(
            coverage_generation,
            "_portable_bundle",
            return_value=(source_index, family, manifest),
        ), patch.object(
            repo_local_kag_validator,
            "validate_repo_local_kag_repository_index_family",
        ) as validate:
            matches = coverage_generation.repository_index_family_matches_owner(
                root,
                source_index,
                source_snapshot=snapshot,
            )

        self.assertTrue(matches)
        validate.assert_called_once()
        self.assertEqual(0, metrics.family_validation_cache_hits)
        self.assertEqual(1, metrics.family_validation_cache_misses)

    def test_coverage_recovers_landed_snapshot_history_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "aoa-demo"
            root.mkdir()
            subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            (root / "README.md").write_text("# Owner\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "Base"], cwd=root, check=True, capture_output=True)
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(["git", "switch", "-c", "feature"], cwd=root, check=True, capture_output=True)
            (root / "SOURCE.md").write_text("# Source\n", encoding="utf-8")
            subprocess.run(["git", "add", "SOURCE.md"], cwd=root, check=True)
            write_repository_index_family(root, history_ref=base)
            subprocess.run(["git", "add", "kag"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "Feature"], cwd=root, check=True, capture_output=True)
            tree = subprocess.run(
                ["git", "rev-parse", "HEAD^{tree}"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            squash = subprocess.run(
                ["git", "commit-tree", tree, "-p", base],
                cwd=root,
                input="Landed feature\n",
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(["git", "switch", "--detach", squash], cwd=root, check=True, capture_output=True)

            status, _ = coverage_generation.index_status(root)

        self.assertEqual("passed", status)

    def test_coverage_recovers_history_boundary_from_second_merge_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "aoa-demo"
            root.mkdir()

            def git(*args: str) -> str:
                return subprocess.run(
                    ("git", *args),
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            git("init", "-b", "main")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.com")
            (root / "README.md").write_text("# Owner\n", encoding="utf-8")
            git("add", "README.md")
            git("commit", "-m", "Base")
            base = git("rev-parse", "HEAD")
            git("update-ref", "refs/remotes/origin/main", base)
            git(
                "symbolic-ref",
                "refs/remotes/origin/HEAD",
                "refs/remotes/origin/main",
            )
            git("switch", "-c", "feature")
            (root / "FEATURE.md").write_text("# Feature\n", encoding="utf-8")
            git("add", "FEATURE.md")
            git("commit", "-m", "Feature")
            git("switch", "main")
            (root / "MAIN.md").write_text("# Main\n", encoding="utf-8")
            git("add", "MAIN.md")
            git("commit", "-m", "Main")
            main_tip = git("rev-parse", "HEAD")
            git("update-ref", "refs/remotes/origin/main", main_tip)
            git("switch", "feature")
            git("merge", "--no-ff", "main", "-m", "Merge main")
            write_repository_index_family(root, history_ref=main_tip)

            self.assertEqual(
                main_tip,
                coverage_generation.repository_event_history_ref(root),
            )
            status, _ = coverage_generation.index_status(root)

        self.assertEqual("passed", status)

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

    def test_coverage_owner_timing_reports_snapshot_cpu_rss_and_cache_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            organ = root / "aoa-demo"
            organ.mkdir()
            subprocess.run(("git", "init", "-q"), cwd=organ, check=True)
            (organ / "README.md").write_text("# Owner\n", encoding="utf-8")
            subprocess.run(("git", "add", "README.md"), cwd=organ, check=True)
            owner_timings: list[dict[str, object]] = []

            build_coverage(root, owner_timings=owner_timings)

        self.assertEqual(1, len(owner_timings))
        timing = owner_timings[0]
        self.assertEqual("aoa-demo", timing["owner"])
        self.assertGreaterEqual(timing["cpu_user_ms"], 0)
        self.assertGreaterEqual(timing["cpu_system_ms"], 0)
        self.assertGreater(timing["process_peak_rss_kib"], 0)
        snapshot = timing["source_snapshot"]
        assert isinstance(snapshot, dict)
        self.assertEqual("git-index-source-tree", snapshot["backend"])
        self.assertEqual(1, snapshot["tracked_file_count"])
        self.assertEqual(1, snapshot["files_read_count"])
        self.assertEqual(1, snapshot["unique_object_count"])
        self.assertEqual(3, snapshot["git_invocation_count"])
        self.assertGreaterEqual(snapshot["read_request_count"], 1)
        self.assertEqual(snapshot["read_request_count"], snapshot["cache_hit_count"])

    def test_coverage_progress_reports_owner_scan_to_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            organ = root / "aoa-demo"
            organ.mkdir()
            (organ / "README.md").write_text("# Owner\n", encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                payload = coverage_generation.build_coverage(root, progress=True)

        self.assertEqual(["aoa-demo"], [owner["repo"] for owner in payload["owners"]])
        self.assertEqual(
            (
                "[repo-local-kag-coverage] owners 1\n"
                "[repo-local-kag-coverage] owner 1/1 aoa-demo\n"
            ),
            stderr.getvalue(),
        )

    def test_provider_home_fusion_builds_exact_payload_without_cold_reload(self) -> None:
        payload = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(payload, dict)
        identity = coverage_identity_for_payload(payload)
        owners = payload["owners"]
        assert isinstance(owners, list)
        owner_payloads = {
            owner["repo"]: owner
            for owner in owners
            if isinstance(owner, dict) and isinstance(owner.get("repo"), str)
        }
        roots = [
            (snapshot["owner"], Path(snapshot["root"]))
            for snapshot in identity["owner_snapshots"]
        ]

        def build_owner(
            owner: str,
            _owner_root: Path,
            *,
            display_root: Path,
            portable_bundle: object,
        ) -> tuple[dict[str, object], dict[str, object]]:
            self.assertIsNotNone(portable_bundle)
            self.assertEqual(owner_payloads[owner]["root"], display_root.as_posix())
            return copy.deepcopy(owner_payloads[owner]), {
                "owner": owner,
                "duration_ms": 1,
                "cpu_user_ms": 1,
                "cpu_system_ms": 0,
                "process_peak_rss_kib": 1024,
                "source_snapshot": {},
            }

        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            identity["run_scope_id"] = run.run_scope_id
            with patch.object(
                coverage_generation,
                "coverage_packet_identity",
                side_effect=(identity, identity),
            ), patch.object(
                coverage_generation,
                "configured_owner_roots",
                return_value=roots,
            ), patch.object(
                coverage_generation,
                "_build_owner_coverage",
                side_effect=build_owner,
            ) as owner_build, patch.object(
                coverage_generation,
                "build_coverage",
            ) as cold_build:
                with coverage_generation.provider_coverage_prebuild_scope():
                    for snapshot, (owner, owner_root) in reversed(
                        list(zip(identity["owner_snapshots"], roots))
                    ):
                        coverage_generation.prebuild_provider_coverage_owner(
                            owner,
                            owner_root,
                            (
                                {},
                                {},
                                {
                                    "family_identity": {
                                        "content_digest": snapshot[
                                            "family_content_digest"
                                        ]
                                    }
                                },
                            ),
                        )
                    actual = coverage_generation.build_provider_coverage()
                    summary = coverage_run.coverage_run_summary(run)

        self.assertEqual(payload, actual)
        self.assertEqual(len(roots), owner_build.call_count)
        cold_build.assert_not_called()
        self.assertEqual(["provider-home-fused"], summary["build_strategies"])
        self.assertEqual(len(roots), summary["prebuilt_owner_count"])
        self.assertEqual(len(roots), summary["owner_scan_count"])

    def test_provider_home_fusion_rejects_incomplete_owner_set_without_packet(self) -> None:
        payload = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(payload, dict)
        identity = coverage_identity_for_payload(payload)
        snapshots = identity["owner_snapshots"]
        assert isinstance(snapshots, list)
        roots = [(item["owner"], Path(item["root"])) for item in snapshots]
        owner_payloads = {
            owner["repo"]: owner
            for owner in payload["owners"]
            if isinstance(owner, dict) and isinstance(owner.get("repo"), str)
        }

        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            identity["run_scope_id"] = run.run_scope_id
            with patch.object(
                coverage_generation,
                "coverage_packet_identity",
                return_value=identity,
            ), patch.object(
                coverage_generation,
                "configured_owner_roots",
                return_value=roots,
            ), patch.object(
                coverage_generation,
                "_build_owner_coverage",
                side_effect=lambda owner, *_args, **_kwargs: (
                    copy.deepcopy(owner_payloads[owner]),
                    {
                        "owner": owner,
                        "duration_ms": 1,
                        "source_snapshot": {},
                    },
                ),
            ):
                with coverage_generation.provider_coverage_prebuild_scope():
                    first = snapshots[0]
                    coverage_generation.prebuild_provider_coverage_owner(
                        first["owner"],
                        Path(first["root"]),
                        (
                            {},
                            {},
                            {
                                "family_identity": {
                                    "content_digest": first[
                                        "family_content_digest"
                                    ]
                                }
                            },
                        ),
                    )
                    with self.assertRaisesRegex(RuntimeError, "owner membership"):
                        coverage_generation.build_provider_coverage()
                    self.assertFalse(run.packet_path.exists())
                    summary = coverage_run.coverage_run_summary(run)

        self.assertEqual(1, summary["build_failure_count"])
        self.assertEqual(0, summary["coverage_build_count"])

    def test_provider_home_fusion_rejects_identity_mutation(self) -> None:
        payload = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(payload, dict)
        initial = coverage_identity_for_payload(payload, epoch="initial")
        changed = coverage_identity_for_payload(payload, epoch="changed")
        snapshots = initial["owner_snapshots"]
        assert isinstance(snapshots, list)
        roots = [(item["owner"], Path(item["root"])) for item in snapshots]
        owner_payloads = {
            owner["repo"]: owner
            for owner in payload["owners"]
            if isinstance(owner, dict) and isinstance(owner.get("repo"), str)
        }

        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            initial["run_scope_id"] = run.run_scope_id
            changed["run_scope_id"] = run.run_scope_id
            with patch.object(
                coverage_generation,
                "coverage_packet_identity",
                side_effect=(initial, changed),
            ), patch.object(
                coverage_generation,
                "configured_owner_roots",
                return_value=roots,
            ), patch.object(
                coverage_generation,
                "_build_owner_coverage",
                side_effect=lambda owner, *_args, **_kwargs: (
                    copy.deepcopy(owner_payloads[owner]),
                    {
                        "owner": owner,
                        "duration_ms": 1,
                        "source_snapshot": {},
                    },
                ),
            ):
                with coverage_generation.provider_coverage_prebuild_scope():
                    for snapshot, (owner, owner_root) in zip(snapshots, roots):
                        coverage_generation.prebuild_provider_coverage_owner(
                            owner,
                            owner_root,
                            (
                                {},
                                {},
                                {
                                    "family_identity": {
                                        "content_digest": snapshot[
                                            "family_content_digest"
                                        ]
                                    }
                                },
                            ),
                        )
                    with self.assertRaisesRegex(RuntimeError, "inputs changed"):
                        coverage_generation.build_provider_coverage()
                    self.assertFalse(run.packet_path.exists())
                    summary = coverage_run.coverage_run_summary(run)

        self.assertEqual(1, summary["packet_reject_count"])
        self.assertEqual(0, summary["coverage_build_count"])

    def test_transient_portable_bundle_is_root_exact_and_released(self) -> None:
        owner_root = Path("/srv/AbyssOS/aoa-demo")
        other_root = Path("/srv/AbyssOS/aoa-other")
        injected = ({"source": "injected"}, {}, {"manifest": "injected"})
        disk = ({"source": "disk"}, {}, {"manifest": "disk"})

        with patch.object(
            coverage_generation,
            "_portable_bundle_from_disk",
            return_value=disk,
        ) as load_disk:
            with coverage_generation._transient_portable_bundle(
                owner_root,
                injected,
            ):
                self.assertIs(
                    injected,
                    coverage_generation._portable_bundle(owner_root),
                )
                self.assertIs(
                    disk,
                    coverage_generation._portable_bundle(other_root),
                )
            self.assertIs(
                disk,
                coverage_generation._portable_bundle(owner_root),
            )

        self.assertEqual(2, load_disk.call_count)

    def test_provider_failure_scope_writes_no_coverage_packet(self) -> None:
        payload = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(payload, dict)
        identity = coverage_identity_for_payload(payload)
        snapshots = identity["owner_snapshots"]
        assert isinstance(snapshots, list)
        roots = [(item["owner"], Path(item["root"])) for item in snapshots]

        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            identity["run_scope_id"] = run.run_scope_id
            with patch.object(
                coverage_generation,
                "coverage_packet_identity",
                return_value=identity,
            ), patch.object(
                coverage_generation,
                "configured_owner_roots",
                return_value=roots,
            ):
                with self.assertRaisesRegex(RuntimeError, "provider failed"):
                    with coverage_generation.provider_coverage_prebuild_scope():
                        raise RuntimeError("provider failed")
            self.assertFalse(run.packet_path.exists())
            summary = coverage_run.coverage_run_summary(run)

        self.assertEqual(0, summary["coverage_build_count"])
        self.assertEqual(0, summary["packet_hit_count"])
        self.assertEqual(0, summary["packet_miss_count"])

    def test_provider_home_fusion_rejects_wrong_root_and_family_digest(self) -> None:
        payload = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(payload, dict)
        identity = coverage_identity_for_payload(payload)
        snapshots = identity["owner_snapshots"]
        assert isinstance(snapshots, list)
        roots = [(item["owner"], Path(item["root"])) for item in snapshots]
        first = snapshots[0]

        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            identity["run_scope_id"] = run.run_scope_id
            with patch.object(
                coverage_generation,
                "coverage_packet_identity",
                return_value=identity,
            ), patch.object(
                coverage_generation,
                "configured_owner_roots",
                return_value=roots,
            ):
                with coverage_generation.provider_coverage_prebuild_scope():
                    with self.assertRaisesRegex(RuntimeError, "unexpected owner root"):
                        coverage_generation.prebuild_provider_coverage_owner(
                            first["owner"],
                            Path(first["root"]) / "wrong",
                            (
                                {},
                                {},
                                {
                                    "family_identity": {
                                        "content_digest": first[
                                            "family_content_digest"
                                        ]
                                    }
                                },
                            ),
                        )
                    with self.assertRaisesRegex(RuntimeError, "identity mismatch"):
                        coverage_generation.prebuild_provider_coverage_owner(
                            first["owner"],
                            Path(first["root"]),
                            (
                                {},
                                {},
                                {
                                    "family_identity": {
                                        "content_digest": "f" * 64,
                                    }
                                },
                            ),
                        )
            self.assertFalse(run.packet_path.exists())

    def test_provider_coverage_packet_reuses_one_verified_input_epoch(self) -> None:
        payload = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(payload, dict)
        identity = coverage_identity_for_payload(payload)
        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run, patch.object(
            coverage_generation,
            "coverage_packet_identity",
            return_value=identity,
        ), patch.object(
            coverage_generation,
            "configured_owner_roots",
            return_value=[],
        ), patch.object(
            coverage_generation,
            "build_coverage",
            return_value=payload,
        ) as build:
            first = coverage_generation.build_provider_coverage()
            second = coverage_generation.build_provider_coverage()
            summary = coverage_run.coverage_run_summary(run)

        self.assertEqual(payload, first)
        self.assertEqual(payload, second)
        self.assertEqual(1, build.call_count)
        self.assertEqual(1, summary["coverage_build_count"])
        self.assertEqual(1, summary["packet_hit_count"])
        self.assertEqual(1, summary["packet_miss_count"])
        self.assertEqual(
            [coverage_generation._json_digest(payload)],
            summary["payload_digests"],
        )

    def test_coverage_run_summary_aggregates_owner_resource_and_snapshot_metrics(self) -> None:
        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            coverage_run.record_coverage_event(
                {
                    "event": "build",
                    "duration_ms": 29,
                    "owner_timings": [
                        {
                            "owner": "aoa-demo",
                            "duration_ms": 23,
                            "cpu_user_ms": 17,
                            "cpu_system_ms": 3,
                            "process_peak_rss_kib": 4096,
                            "source_snapshot": {
                                "git_invocation_count": 3,
                                "files_read_count": 11,
                                "unique_object_count": 9,
                                "bytes_read": 2048,
                                "family_validation_cache_hit_count": 1,
                                "family_validation_cache_miss_count": 0,
                            },
                        }
                    ],
                }
            )
            summary = coverage_run.coverage_run_summary(run)

        self.assertEqual(17, summary["owner_cpu_user_ms"])
        self.assertEqual(3, summary["owner_cpu_system_ms"])
        self.assertEqual(4096, summary["process_peak_rss_kib"])
        self.assertEqual(3, summary["source_snapshot_git_invocation_count"])
        self.assertEqual(11, summary["source_snapshot_files_read_count"])
        self.assertEqual(9, summary["source_snapshot_unique_object_count"])
        self.assertEqual(2048, summary["source_snapshot_bytes_read"])
        self.assertEqual(1, summary["family_validation_cache_hit_count"])
        self.assertEqual(0, summary["family_validation_cache_miss_count"])

    def test_validation_timing_is_typed_and_additive_to_coverage_receipt(self) -> None:
        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            with coverage_run.validation_timing(
                component_type="provider-home",
                component_id="aoa-demo",
                details={"repo_root": "/tmp/aoa-demo"},
            ):
                pass
            summary = coverage_run.coverage_run_summary(run)

        telemetry = summary["validation_telemetry"]
        self.assertEqual(
            coverage_run.VALIDATION_TIMING_SCHEMA_VERSION,
            telemetry["schema_version"],
        )
        self.assertEqual(1, telemetry["timing_count"])
        self.assertEqual(0, telemetry["failed_timing_count"])
        self.assertEqual(
            telemetry["timings"][0]["duration_ms"],
            telemetry["wall_ms_by_component_type"]["provider-home"],
        )
        self.assertEqual("aoa-demo", telemetry["timings"][0]["component_id"])
        self.assertEqual(
            {"repo_root": "/tmp/aoa-demo"},
            telemetry["timings"][0]["details"],
        )
        self.assertEqual(
            [
                {
                    "component_id": "aoa-demo",
                    "duration_ms": telemetry["timings"][0]["duration_ms"],
                    "status": "passed",
                }
            ],
            telemetry["top_slowest_by_component_type"]["provider-home"],
        )

    def test_failed_validation_timing_preserves_failure_and_records_status(self) -> None:
        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            with self.assertRaisesRegex(RuntimeError, "proof failed"):
                with coverage_run.validation_timing(
                    component_type="repo-local-index-phase",
                    component_id="semantic-validation",
                ):
                    raise RuntimeError("proof failed")
            summary = coverage_run.coverage_run_summary(run)

        telemetry = summary["validation_telemetry"]
        self.assertEqual(1, telemetry["failed_timing_count"])
        self.assertEqual("failed", telemetry["timings"][0]["status"])

    def test_validation_telemetry_publication_failure_is_degraded(self) -> None:
        stderr = io.StringIO()
        with patch.object(
            coverage_run,
            "record_coverage_event",
            side_effect=OSError("receipt unavailable"),
        ), redirect_stderr(stderr):
            coverage_run.record_validation_timing(
                component_type="provider-home",
                component_id="aoa-demo",
                duration_ms=1,
                cpu_user_ms=1,
                cpu_system_ms=0,
                process_peak_rss_kib=1024,
                status="passed",
            )

        self.assertIn("[aoa-kag-validation-telemetry-degraded]", stderr.getvalue())
        self.assertIn("receipt unavailable", stderr.getvalue())

    def test_coverage_run_receipt_appends_bounded_github_step_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            step_summary = Path(temp_dir) / "step-summary.md"
            with patch.dict(
                os.environ,
                {coverage_run.GITHUB_STEP_SUMMARY_ENV: step_summary.as_posix()},
            ):
                with coverage_run.coverage_run_scope(lane="test", force_new=True):
                    pass

            rendered = step_summary.read_text(encoding="utf-8")

        self.assertIn("### KAG coverage run receipt: `test`", rendered)
        encoded = rendered.split("```json\n", 1)[1].split("\n```", 1)[0]
        receipt = json.loads(encoded)
        self.assertEqual(
            coverage_run.COVERAGE_RECEIPT_SCHEMA_VERSION,
            receipt["schema_version"],
        )
        self.assertEqual("test", receipt["lane"])
        self.assertEqual(0, receipt["coverage_build_count"])

    def test_coverage_run_receipt_reports_step_summary_failure_as_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            unavailable = Path(temp_dir) / "missing" / "step-summary.md"
            stderr = io.StringIO()
            with patch.dict(
                os.environ,
                {coverage_run.GITHUB_STEP_SUMMARY_ENV: unavailable.as_posix()},
            ), redirect_stderr(stderr):
                with coverage_run.coverage_run_scope(lane="test", force_new=True):
                    pass

        output = stderr.getvalue()
        self.assertIn("[aoa-kag-coverage-run-receipt]", output)
        self.assertIn(
            "[aoa-kag-coverage-run-receipt-summary-degraded]",
            output,
        )

    def test_coverage_run_receipt_refuses_oversized_step_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            step_summary = Path(temp_dir) / "step-summary.md"
            stderr = io.StringIO()
            with patch.dict(
                os.environ,
                {coverage_run.GITHUB_STEP_SUMMARY_ENV: step_summary.as_posix()},
            ), patch.object(
                coverage_run,
                "GITHUB_STEP_SUMMARY_RECEIPT_MAX_BYTES",
                1,
            ), redirect_stderr(stderr):
                with coverage_run.coverage_run_scope(lane="test", force_new=True):
                    pass

        self.assertFalse(step_summary.exists())
        self.assertIn("bounded maximum is 1", stderr.getvalue())

    def test_provider_coverage_packet_rebuilds_only_for_a_new_input_epoch(self) -> None:
        payload = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(payload, dict)
        first_identity = coverage_identity_for_payload(payload, epoch="first")
        second_identity = coverage_identity_for_payload(payload, epoch="second")
        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run, patch.object(
            coverage_generation,
            "coverage_packet_identity",
            side_effect=(
                first_identity,
                first_identity,
                second_identity,
                second_identity,
            ),
        ), patch.object(
            coverage_generation,
            "configured_owner_roots",
            return_value=[],
        ), patch.object(
            coverage_generation,
            "build_coverage",
            return_value=payload,
        ) as build:
            coverage_generation.build_provider_coverage()
            coverage_generation.build_provider_coverage()
            summary = coverage_run.coverage_run_summary(run)

        self.assertEqual(2, build.call_count)
        self.assertEqual(2, summary["coverage_build_count"])
        self.assertEqual(2, summary["packet_miss_count"])
        self.assertEqual(0, summary["packet_hit_count"])
        self.assertEqual(0, summary["packet_reject_count"])

    def test_coverage_packet_rejects_tamper_and_incompatible_schema(self) -> None:
        payload = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(payload, dict)
        identity = coverage_identity_for_payload(payload)
        with coverage_run.coverage_run_scope(lane="test", force_new=True) as run:
            coverage_generation.write_coverage_packet(
                run.packet_path,
                identity=identity,
                payload=payload,
            )
            packet = load_json(run.packet_path)
            assert isinstance(packet, dict)
            packet["coverage"]["owners"][0]["coverage"]["documents"] += 1
            run.packet_path.write_text(json.dumps(packet), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "payload digest mismatch"):
                coverage_generation.load_coverage_packet(run.packet_path)

            coverage_generation.write_coverage_packet(
                run.packet_path,
                identity=identity,
                payload=payload,
            )
            packet = load_json(run.packet_path)
            assert isinstance(packet, dict)
            packet["schema_version"] = "unsupported-packet"
            run.packet_path.write_text(json.dumps(packet), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "schema is incompatible"):
                coverage_generation.load_coverage_packet(run.packet_path)

            coverage_generation.write_coverage_packet(
                run.packet_path,
                identity=identity,
                payload=payload,
            )
            packet = load_json(run.packet_path)
            assert isinstance(packet, dict)
            packet["identity"]["schema_version"] = "unsupported-identity"
            run.packet_path.write_text(json.dumps(packet), encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeError,
                "identity schema is incompatible",
            ):
                coverage_generation.load_coverage_packet(run.packet_path)

    def test_coverage_packet_rejects_incomplete_owner_payload(self) -> None:
        payload = load_json(REPO_ROOT / "generated" / "repo_local_kag_coverage.json")
        assert isinstance(payload, dict)
        identity = coverage_identity_for_payload(payload)
        incomplete_payload = json.loads(json.dumps(payload))
        incomplete_payload["owners"].pop()
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(
                RuntimeError,
                "owner membership or order",
            ):
                coverage_generation.write_coverage_packet(
                    Path(tmpdir) / "coverage.packet.json",
                    identity=identity,
                    payload=incomplete_payload,
                )

    def test_coverage_packet_provider_snapshot_rejects_stale_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init"), cwd=root, check=True, capture_output=True)
            subprocess.run(
                ("git", "config", "user.email", "test@example.com"),
                cwd=root,
                check=True,
            )
            subprocess.run(
                ("git", "config", "user.name", "Test"),
                cwd=root,
                check=True,
            )
            (root / "README.md").write_text("# Owner\n", encoding="utf-8")
            subprocess.run(("git", "add", "README.md"), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-m", "Base"),
                cwd=root,
                check=True,
                capture_output=True,
            )
            with self.assertRaisesRegex(RuntimeError, "provider pin mismatch"):
                coverage_generation._provider_snapshot(
                    "aoa-demo",
                    root,
                    expected_ref="f" * 40,
                )

    def test_coverage_packet_provider_snapshot_rejects_missing_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_root = Path(tmpdir) / "missing-owner"
            with self.assertRaisesRegex(RuntimeError, "provider root is unavailable"):
                coverage_generation._provider_snapshot(
                    "aoa-demo",
                    missing_root,
                    expected_ref="f" * 40,
                )

    def test_coverage_runtime_identity_tracks_schema_and_config_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "config" / "validation.json"
            schema_path = root / "schemas" / "coverage.schema.json"
            config_path.parent.mkdir(parents=True)
            schema_path.parent.mkdir(parents=True)
            config_path.write_text('{"lane":"full"}\n', encoding="utf-8")
            schema_path.write_text('{"type":"object"}\n', encoding="utf-8")
            with patch.object(
                coverage_generation,
                "REPO_ROOT",
                root,
            ), patch.object(
                coverage_generation,
                "COVERAGE_RUNTIME_INPUT_PATHS",
                (
                    Path("config/validation.json"),
                    Path("schemas/coverage.schema.json"),
                ),
            ):
                baseline = coverage_generation._coverage_runtime_inputs_digest()
                config_path.write_text('{"lane":"local"}\n', encoding="utf-8")
                config_changed = (
                    coverage_generation._coverage_runtime_inputs_digest()
                )
                config_path.write_text('{"lane":"full"}\n', encoding="utf-8")
                schema_path.write_text(
                    '{"type":"object","additionalProperties":false}\n',
                    encoding="utf-8",
                )
                schema_changed = (
                    coverage_generation._coverage_runtime_inputs_digest()
                )

        self.assertNotEqual(baseline, config_changed)
        self.assertNotEqual(baseline, schema_changed)

    def test_coverage_packet_identity_tracks_head_index_and_dirty_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init"), cwd=root, check=True, capture_output=True)
            subprocess.run(
                ("git", "config", "user.email", "test@example.com"),
                cwd=root,
                check=True,
            )
            subprocess.run(
                ("git", "config", "user.name", "Test"),
                cwd=root,
                check=True,
            )
            (root / "README.md").write_text("# Owner\n", encoding="utf-8")
            subprocess.run(("git", "add", "README.md"), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-m", "Base"),
                cwd=root,
                check=True,
                capture_output=True,
            )

            clean_head = coverage_generation._git_head("demo", root)
            clean_tree = coverage_generation._git_index_tree("demo", root)
            clean_worktree = coverage_generation._git_worktree_digest("demo", root)
            subprocess.run(
                ("git", "commit", "--allow-empty", "-m", "History"),
                cwd=root,
                check=True,
                capture_output=True,
            )
            history_head = coverage_generation._git_head("demo", root)
            history_tree = coverage_generation._git_index_tree("demo", root)
            history_worktree = coverage_generation._git_worktree_digest("demo", root)
            (root / "README.md").write_text("# Dirty owner\n", encoding="utf-8")
            dirty_worktree = coverage_generation._git_worktree_digest("demo", root)
            (root / "UNTRACKED.md").write_text("# Untracked\n", encoding="utf-8")
            untracked_worktree = coverage_generation._git_worktree_digest("demo", root)

        self.assertNotEqual(clean_head, history_head)
        self.assertEqual(clean_tree, history_tree)
        self.assertEqual(clean_worktree, history_worktree)
        self.assertNotEqual(history_worktree, dirty_worktree)
        self.assertNotEqual(dirty_worktree, untracked_worktree)

    def test_coverage_packet_identity_requires_each_owner_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaisesRegex(RuntimeError, "portable family manifest"):
                coverage_generation._portable_manifest_identity("aoa-demo", root)

    def test_provider_coverage_keeps_invalid_common_index_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_surface_index.json").write_text("{not-json\n", encoding="utf-8")
            write_owner_specific_provider_records(checkout)

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])

    def test_provider_coverage_requires_usable_owner_specific_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_surface_index.json").write_text("{not-json\n", encoding="utf-8")
            (indexes / "source_inventory.json").write_text("[\"not\", \"a\", \"record\"]\n", encoding="utf-8")

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])

    def test_provider_coverage_requires_schema_valid_owner_specific_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_surface_index.json").write_text("{not-json\n", encoding="utf-8")
            (indexes / "source_inventory.json").write_text(
                json.dumps(
                    {
                        "schema_version": "aoa-local-kag-record-v1",
                        "record_class": "index",
                        "generated_or_authored": "generated_from_source",
                        "builder": {
                            "route": "local validation lane",
                            "surface": "scripts/validate_provider.py",
                        },
                    }
                ),
                encoding="utf-8",
            )

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])

    def test_provider_coverage_requires_owner_specific_checked_ref_to_be_source_linked(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_surface_index.json").write_text("{not-json\n", encoding="utf-8")
            owner_payload = owner_specific_index_payload()
            owner_payload["freshness"]["checked_ref"] = "unlinked-generated-snapshot.json"
            write_owner_specific_provider_records(checkout, index_payload=owner_payload)

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])

    def test_provider_coverage_requires_owner_specific_source_record_ids_to_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_surface_index.json").write_text("{not-json\n", encoding="utf-8")
            owner_payload = owner_specific_index_payload()
            owner_payload["source_record_ids"] = ["node:demo:missing"]
            write_owner_specific_provider_records(checkout, index_payload=owner_payload)

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])

    def test_provider_coverage_requires_owner_specific_records_to_match_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_surface_index.json").write_text("{not-json\n", encoding="utf-8")
            write_owner_specific_provider_records(checkout)
            projection_path = checkout / "kag" / "projections" / "readme.json"
            projection = json.loads(projection_path.read_text(encoding="utf-8"))
            projection["source_record_ids"] = [{}]
            projection_path.write_text(json.dumps(projection), encoding="utf-8")

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])

    def test_provider_coverage_requires_owner_specific_records_to_use_owner_source_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_surface_index.json").write_text("{not-json\n", encoding="utf-8")
            write_owner_specific_provider_records(checkout)
            projection_path = checkout / "kag" / "projections" / "readme.json"
            projection = json.loads(projection_path.read_text(encoding="utf-8"))
            projection["source_refs"][0]["repo"] = "other-owner"
            projection_path.write_text(json.dumps(projection), encoding="utf-8")

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])

    def test_provider_coverage_requires_owner_specific_record_checked_refs_to_be_source_linked(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_surface_index.json").write_text("{not-json\n", encoding="utf-8")
            write_owner_specific_provider_records(checkout)
            projection_path = checkout / "kag" / "projections" / "readme.json"
            projection = json.loads(projection_path.read_text(encoding="utf-8"))
            projection["freshness"]["checked_ref"] = "generated/unlinked.json"
            projection_path.write_text(json.dumps(projection), encoding="utf-8")

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])

    def test_provider_coverage_treats_undecodable_owner_specific_index_as_migration_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_surface_index.json").write_text("{not-json\n", encoding="utf-8")
            (indexes / "source_inventory.json").write_bytes(b"\xff\xfe\x00")

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])

    def test_provider_coverage_rejects_unusable_owner_specific_index_without_canonical_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout = root / "temporary-checkout"
            indexes = checkout / "kag" / "indexes"
            indexes.mkdir(parents=True)
            (checkout / "README.md").write_text("# Connector\n", encoding="utf-8")
            (indexes / "source_inventory.json").write_text("[\"not\", \"a\", \"record\"]\n", encoding="utf-8")

            payload = coverage_generation.build_coverage(
                root,
                owner_roots=[("aoa-demo-connector", checkout)],
            )

        owner = payload["owners"][0]
        self.assertEqual("aoa-demo-connector", owner["repo"])
        self.assertEqual("connector", owner["owner_type"])
        self.assertEqual("migration-needed", owner["index_status"])


if __name__ == "__main__":
    unittest.main()
