from __future__ import annotations

import copy
import hashlib
import json
import shutil
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
    effective_event_history_ref,
    effective_history_ref,
    local_default_history_ref,
    main,
    payload_digest,
)
from scripts.generate_repo_local_kag_coverage import source_index_matches_owner
from scripts.generation.provider_map import _is_repo_local_meta_index_payload
from scripts.repo_local.projections import build_repo_retrieval_documents
from scripts.repo_local.query import RepoKagQuery
from scripts.repo_local import portable_family as portable_family_module
from scripts.repo_local.portable_family import (
    BUDGET_RECEIPT_SCHEMA_PATH,
    HARD_MAX_SHARD_BYTES,
    MANIFEST_RELATIVE_PATH,
    PortableFamilyError,
    build_budget_receipt,
    build_portable_family,
    capture_budget_producer_execution_inputs,
    load_portable_family,
    validate_changed_generated_budget,
    write_budget_receipt,
    write_portable_output,
)
from scripts.validators.common import ValidationError
from scripts.validators.repo_local_kag_index import (
    load_repo_local_kag_repository_index_family_with_manifest,
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
FAMILY_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-family-manifest.schema.json"
)
BUDGET_RECEIPT_SCHEMA_FILE = REPO_ROOT / BUDGET_RECEIPT_SCHEMA_PATH


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


def write_capability_graph_fixture(root: Path) -> None:
    (root / "kag" / "manifest.json").write_text(
        json.dumps({"repo": "demo"}),
        encoding="utf-8",
    )
    family_path = root / "capabilities" / "families" / "session-memory.yaml"
    family_path.parent.mkdir(parents=True)
    family_path.write_text(
        "schema_version: aoa-capability-family-v1\n"
        "family: session-memory\n"
        "nodes:\n"
        "  - id: memory\n"
        "    kind: capability\n"
        "    title: Session memory\n"
        "    contract_level: navigation\n"
        "    primary_parent: null\n"
        "    owner:\n"
        "      authority: authored\n"
        "      repo: demo\n"
        "      surface: capabilities/families/session-memory.yaml\n"
        "    lifecycle:\n"
        "      state: active\n"
        "  - id: skill.query\n"
        "    kind: skill\n"
        "    title: Query memory\n"
        "    contract_level: executable\n"
        "    primary_parent: memory\n"
        "    owner:\n"
        "      authority: authored\n"
        "      repo: demo\n"
        "      surface: capabilities/families/session-memory.yaml\n"
        "    lifecycle:\n"
        "      state: active\n"
        "  - id: adapter.audit\n"
        "    kind: adapter\n"
        "    title: Audit adapter\n"
        "    contract_level: executable\n"
        "    primary_parent: memory\n"
        "    owner:\n"
        "      authority: authored\n"
        "      repo: demo\n"
        "      surface: capabilities/families/session-memory.yaml\n"
        "    lifecycle:\n"
        "      state: active\n"
        "relations:\n"
        "  - kind: hands-off-to\n"
        "    source: skill.query\n"
        "    target: adapter.audit\n"
        "    condition: Query evidence is ready for audit.\n",
        encoding="utf-8",
    )
    (root / "capabilities" / "port.manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "aoa_capability_home_port_v1",
                "contract_ref": "aoa-skills:schemas/capability-home-port.schema.json",
                "owner_repo": "demo",
                "owner_ref": "capabilities/AGENTS.md",
                "admission_ref": "docs/decisions/demo.md",
                "source": {
                    "family_root": "capabilities/families",
                    "root_id": "memory",
                },
                "federation": {
                    "parent_owner": "aoa-skills",
                    "parent_node": "sessions",
                    "relation": "specializes",
                },
                "skill_home_ref": "skills/port.manifest.json",
                "eval_port_ref": "evals/PORT.yaml",
                "projection": {
                    "authority": False,
                    "graph_json": "generated/capability_graph.json",
                    "graph_markdown": "generated/capability_graph.md",
                    "router_markdown": "skills/demo/references/capability-router.md",
                    "generated_by": "aoa-skills:scripts/build_capability_home_projection.py",
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (root / "scripts" / "build_capability_projection.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    graph_path = root / "generated" / "capability_graph.json"
    graph_path.parent.mkdir()
    graph_path.write_text(
        json.dumps(
            {
                "schema_version": "aoa-capability-graph-v1",
                "authority": False,
                "source": {
                    "root": "capabilities/families",
                    "family_files": [
                        {
                            "path": "capabilities/families/session-memory.yaml",
                            "sha256": hashlib.sha256(family_path.read_bytes()).hexdigest(),
                        }
                    ],
                    "referenced_files": [],
                    "content_hash": "b" * 64,
                },
                "roots": ["memory"],
                "nodes": [
                    {
                        "id": "memory",
                        "kind": "capability",
                        "title": "Session memory",
                        "contract_level": "navigation",
                        "primary_parent": None,
                        "source_family": "session-memory",
                        "source_path": "capabilities/families/session-memory.yaml",
                        "owner": {
                            "authority": "authored",
                            "repo": "demo",
                            "surface": "capabilities/families/session-memory.yaml",
                        },
                        "lifecycle": {"state": "active"},
                    },
                    {
                        "id": "skill.query",
                        "kind": "skill",
                        "title": "Query memory",
                        "contract_level": "executable",
                        "primary_parent": "memory",
                        "source_family": "session-memory",
                        "source_path": "capabilities/families/session-memory.yaml",
                        "owner": {
                            "authority": "authored",
                            "repo": "demo",
                            "surface": "capabilities/families/session-memory.yaml",
                        },
                        "lifecycle": {"state": "active"},
                    },
                    {
                        "id": "adapter.audit",
                        "kind": "adapter",
                        "title": "Audit adapter",
                        "contract_level": "executable",
                        "primary_parent": "memory",
                        "source_family": "session-memory",
                        "source_path": "capabilities/families/session-memory.yaml",
                        "owner": {
                            "authority": "authored",
                            "repo": "demo",
                            "surface": "capabilities/families/session-memory.yaml",
                        },
                        "lifecycle": {"state": "active"},
                    },
                ],
                "relations": [
                    {
                        "kind": "primary-parent",
                        "source": "skill.query",
                        "target": "memory",
                        "source_path": "capabilities/families/session-memory.yaml",
                    },
                    {
                        "kind": "hands-off-to",
                        "source": "skill.query",
                        "target": "adapter.audit",
                        "condition": "Query evidence is ready for audit.",
                        "source_path": "capabilities/families/session-memory.yaml",
                    },
                    {
                        "kind": "primary-parent",
                        "source": "adapter.audit",
                        "target": "memory",
                        "source_path": "capabilities/families/session-memory.yaml",
                    },
                ],
                "retrieval_documents": [
                    {
                        "id": "skill.query",
                        "kind": "skill",
                        "visibility": "internal",
                        "title": "Query memory",
                        "description": "Retrieve session evidence.",
                        "search_text": "query memory evidence",
                        "positive_text": "find session evidence",
                        "negative_text": "",
                        "negative_phrases": [],
                        "routing_tokens": ["query"],
                        "positive_tokens": ["evidence"],
                        "negative_tokens": [],
                        "tokens": ["query", "evidence"],
                    }
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (root / "generated" / "capability_graph.md").write_text(
        "# Capability graph\n",
        encoding="utf-8",
    )
    (root / "skills" / "demo" / "references").mkdir(parents=True)
    (root / "skills" / "demo" / "references" / "capability-router.md").write_text(
        "# Capability router\n",
        encoding="utf-8",
    )


class RepoLocalKagRepositoryIndexTests(unittest.TestCase):
    def test_portable_family_round_trips_exact_v2_compatibility_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            manifest, shards = build_portable_family(source_index, family)
            write_portable_output(root, manifest, shards)

            rebuilt_source, rebuilt_family, rebuilt_manifest = (
                load_portable_family(root)
            )

        Draft202012Validator(load_json(FAMILY_MANIFEST_SCHEMA_PATH)).validate(
            manifest
        )
        self.assertEqual(source_index, rebuilt_source)
        self.assertEqual(family, rebuilt_family)
        self.assertEqual(manifest, rebuilt_manifest)
        self.assertTrue(shards)
        self.assertTrue(
            all(len(content) <= HARD_MAX_SHARD_BYTES for content in shards.values())
        )
        self.assertEqual(
            MANIFEST_RELATIVE_PATH.as_posix(),
            "kag/indexes/index_family.manifest.json",
        )

    def test_portable_family_preserves_ranges_and_localizes_small_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            first_source = build_index(root)
            first_family = build_repository_indexes(
                first_source,
                repo_root=root,
            )
            first_manifest, first_shards = build_portable_family(
                first_source,
                first_family,
            )
            write_portable_output(root, first_manifest, first_shards)

            (root / "docs" / "guides" / "small.md").write_text(
                "# Small\n",
                encoding="utf-8",
            )
            second_source = build_index(root)
            second_family = build_repository_indexes(
                second_source,
                repo_root=root,
            )
            second_manifest, second_shards = build_portable_family(
                second_source,
                second_family,
                previous_manifest=first_manifest,
            )

        first_ranges = first_manifest["partitioning"]["ranges"]
        second_ranges = second_manifest["partitioning"]["ranges"]
        for kind, ranges in first_ranges.items():
            self.assertTrue(
                all(
                    any(
                        candidate == prefix
                        or candidate.startswith(prefix)
                        for candidate in second_ranges[kind]
                    )
                    for prefix in ranges
                )
            )
        changed = {
            path
            for path in set(first_shards) | set(second_shards)
            if first_shards.get(path) != second_shards.get(path)
        }
        self.assertLess(len(changed), len(second_shards))
        self.assertLess(
            sum(
                max(
                    len(first_shards.get(path, b"")),
                    len(second_shards.get(path, b"")),
                )
                for path in changed
            ),
            second_manifest["budgets"]["changed_generated_bytes_max"],
        )

    def test_portable_family_cannot_raise_standing_budget_with_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
            subprocess.run(
                ("git", "config", "user.name", "KAG Test"),
                cwd=root,
                check=True,
            )
            subprocess.run(
                ("git", "config", "user.email", "kag@example.test"),
                cwd=root,
                check=True,
            )
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-qm", "source"),
                cwd=root,
                check=True,
            )
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            manifest, shards = build_portable_family(source_index, family)
            write_portable_output(root, manifest, shards)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-qm", "portable base"),
                cwd=root,
                check=True,
            )

            raised = json.loads(json.dumps(manifest))
            raised["budgets"]["tracked_bytes_max"] += 1024 * 1024
            raised_manifest, raised_shards = build_portable_family(
                source_index,
                family,
                previous_manifest=raised,
            )
            write_portable_output(root, raised_manifest, raised_shards)

            with self.assertRaisesRegex(
                PortableFamilyError,
                "cannot be raised",
            ):
                validate_changed_generated_budget(
                    root,
                    base_ref="HEAD",
                    manifest=raised_manifest,
                )

    def test_portable_family_budget_admission_can_only_be_deferred_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            manifest, shards = build_portable_family(
                source_index,
                family,
                previous_manifest={"budgets": {"tracked_bytes_max": 1}},
            )
            write_portable_output(root, manifest, shards)

            with self.assertRaisesRegex(
                PortableFamilyError,
                "without a matching digest-bound receipt",
            ):
                load_portable_family(root)

            loaded_source, loaded_family, loaded_manifest = load_portable_family(
                root,
                require_budget_receipt=False,
            )

        self.assertEqual(source_index, loaded_source)
        self.assertEqual(family, loaded_family)
        self.assertEqual(manifest, loaded_manifest)

    def _prepare_budget_fixture(self) -> tuple[Path, dict[str, object], tempfile.TemporaryDirectory]:
        tmpdir = tempfile.TemporaryDirectory()
        root = Path(tmpdir.name)
        write_fixture(root)
        subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
        subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
        subprocess.run(
            ("git", "config", "user.email", "kag@example.test"),
            cwd=root,
            check=True,
        )
        subprocess.run(("git", "add", "."), cwd=root, check=True)
        subprocess.run(("git", "commit", "-qm", "source"), cwd=root, check=True)
        source_index = build_index(root)
        family = build_repository_indexes(source_index, repo_root=root)
        base_manifest, base_shards = build_portable_family(source_index, family)
        write_portable_output(root, base_manifest, base_shards)
        subprocess.run(("git", "add", "."), cwd=root, check=True)
        subprocess.run(
            ("git", "commit", "-qm", "portable base"),
            cwd=root,
            check=True,
        )
        manifest, shards = build_portable_family(
            source_index,
            family,
            previous_manifest={"budgets": {"tracked_bytes_max": 1}},
        )
        write_portable_output(root, manifest, shards)
        execution_inputs = capture_budget_producer_execution_inputs(
            root,
            base_ref="HEAD",
            history_ref="HEAD",
            event_history_ref="HEAD",
        )
        receipt_path, receipt = build_budget_receipt(
            root,
            base_ref="HEAD",
            manifest=manifest,
            reason="identity-bound adversarial test",
            producer_execution_inputs=execution_inputs,
        )
        write_budget_receipt(root, receipt_path, receipt)
        Draft202012Validator(load_json(BUDGET_RECEIPT_SCHEMA_FILE)).validate(receipt)
        return root, manifest, tmpdir

    def test_foreign_budget_receipt_can_keep_its_pinned_producer_identity(self) -> None:
        root, manifest, tmpdir = self._prepare_budget_fixture()
        try:
            with mock.patch.object(
                portable_family_module,
                "_budget_producer_identity",
                side_effect=PortableFamilyError("newer executing producer"),
            ):
                with self.assertRaisesRegex(
                    PortableFamilyError,
                    "newer executing producer",
                ):
                    load_portable_family(root)
                loaded_source, loaded_family, loaded_manifest = load_portable_family(
                    root,
                    require_current_producer_identity=False,
                )

            self.assertEqual(manifest, loaded_manifest)
            self.assertEqual(
                build_index(root),
                loaded_source,
            )
            self.assertEqual(
                build_repository_indexes(loaded_source, repo_root=root),
                loaded_family,
            )
        finally:
            tmpdir.cleanup()

    def test_repository_family_loader_forwards_foreign_receipt_mode(self) -> None:
        root, manifest, tmpdir = self._prepare_budget_fixture()
        try:
            with mock.patch.object(
                portable_family_module,
                "_budget_producer_identity",
                side_effect=PortableFamilyError("newer executing producer"),
            ):
                with self.assertRaisesRegex(
                    ValidationError,
                    "newer executing producer",
                ):
                    load_repo_local_kag_repository_index_family_with_manifest(
                        root,
                    )
                source, family, loaded_manifest = (
                    load_repo_local_kag_repository_index_family_with_manifest(
                        root,
                        require_current_producer_identity=False,
                    )
                )

            self.assertEqual(manifest, loaded_manifest)
            self.assertEqual(build_index(root), source)
            self.assertEqual(build_repository_indexes(source, repo_root=root), family)
        finally:
            tmpdir.cleanup()

    def test_budget_receipt_rejects_candidate_base_family_and_producer_replay(self) -> None:
        schema = load_json(BUDGET_RECEIPT_SCHEMA_FILE)
        Draft202012Validator.check_schema(schema)

        def prepare() -> tuple[Path, dict[str, object], Path]:
            tmpdir = tempfile.TemporaryDirectory()
            root = Path(tmpdir.name)
            write_fixture(root)
            subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
            subprocess.run(
                ("git", "config", "user.name", "KAG Test"),
                cwd=root,
                check=True,
            )
            subprocess.run(
                ("git", "config", "user.email", "kag@example.test"),
                cwd=root,
                check=True,
            )
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-qm", "source"),
                cwd=root,
                check=True,
            )
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            base_manifest, base_shards = build_portable_family(source_index, family)
            write_portable_output(root, base_manifest, base_shards)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-qm", "portable base"),
                cwd=root,
                check=True,
            )
            manifest, shards = build_portable_family(
                source_index,
                family,
                previous_manifest={"budgets": {"tracked_bytes_max": 1}},
            )
            write_portable_output(root, manifest, shards)
            execution_inputs = capture_budget_producer_execution_inputs(
                root,
                base_ref="HEAD",
                history_ref="HEAD",
                event_history_ref="HEAD",
            )
            receipt_path, receipt = build_budget_receipt(
                root,
                base_ref="HEAD",
                manifest=manifest,
                reason="identity-bound adversarial test",
                producer_execution_inputs=execution_inputs,
            )
            write_budget_receipt(root, receipt_path, receipt)
            Draft202012Validator(schema).validate(receipt)
            for candidate in root.rglob("*"):
                if candidate.is_file() and ".git" not in candidate.relative_to(root).parts:
                    candidate.chmod(0o600)
            return root, manifest, tmpdir

        root, manifest, tmpdir = prepare()
        try:
            accepted = validate_changed_generated_budget(
                root,
                base_ref="HEAD",
                manifest=manifest,
            )
            self.assertTrue(accepted[2])
            (root / "README.md").write_text("candidate replay\n", encoding="utf-8")
            with self.assertRaisesRegex(
                PortableFamilyError,
                "source epoch",
            ):
                validate_changed_generated_budget(root, base_ref="HEAD", manifest=manifest)
        finally:
            tmpdir.cleanup()

        for label in ("base", "family", "producer"):
            root, manifest, tmpdir = prepare()
            try:
                receipt_path = root / "kag" / "receipts" / "index_family_budget"
                receipt_file = next(receipt_path.glob("*.json"))
                receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
                if label == "base":
                    receipt["base_ref"] = "0" * 40
                elif label == "family":
                    receipt["head_family_digest"] = "f" * 64
                else:
                    tampered = dict(receipt["producer_identity"])
                    tampered["source_digest"] = "f" * 64
                    receipt["producer_identity"] = tampered
                receipt_file.write_text(
                    json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                with self.subTest(replay=label):
                    with self.assertRaises(PortableFamilyError):
                        validate_changed_generated_budget(
                            root,
                            base_ref="HEAD",
                            manifest=manifest,
                        )
            finally:
                tmpdir.cleanup()

        root, manifest, tmpdir = prepare()
        try:
            original_producer_identity = portable_family_module._budget_producer_identity
            with mock.patch.object(
                portable_family_module,
                "_budget_producer_identity",
                side_effect=lambda execution_inputs=None: {
                    **original_producer_identity(execution_inputs),
                    "source_digest": "e" * 64,
                },
            ):
                with self.assertRaisesRegex(
                    PortableFamilyError,
                    "producer identity does not match",
                ):
                    validate_changed_generated_budget(
                        root,
                        base_ref="HEAD",
                        manifest=manifest,
                    )
        finally:
            tmpdir.cleanup()

    def test_budget_producer_manifest_rejects_an_omitted_import(self) -> None:
        original_loader = portable_family_module._budget_load_producer_manifest

        def omit_identity(root: Path) -> tuple[dict[str, object], bytes]:
            manifest, raw = original_loader(root)
            changed = copy.deepcopy(manifest)
            changed["python_import_closure"] = [
                path
                for path in changed["python_import_closure"]
                if path != "scripts/repo_local/identity.py"
            ]
            return changed, raw

        with mock.patch.object(
            portable_family_module,
            "_budget_load_producer_manifest",
            side_effect=omit_identity,
        ):
            with self.assertRaisesRegex(
                PortableFamilyError,
                "import closure differs",
            ):
                portable_family_module._budget_producer_identity()

    def test_budget_producer_rejects_unresolved_dynamic_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "scripts").mkdir()
            (root / "scripts" / "entry.py").write_text(
                "import importlib\n"
                "importlib.import_module('scripts.dynamic')\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                PortableFamilyError,
                "unresolved dynamic import",
            ):
                portable_family_module._budget_import_closure(
                    root,
                    [Path("scripts/entry.py")],
                )

    def test_budget_producer_rejects_dynamic_import_aliases_and_nested_forms(
        self,
    ) -> None:
        cases = {
            "from_import_direct": (
                "from importlib import import_module\n"
                "import_module('scripts.dynamic')\n"
            ),
            "from_import_alias": (
                "from importlib import import_module as load\n"
                "load('scripts.dynamic')\n"
            ),
            "getattr_direct": (
                "import importlib\n"
                "getattr(importlib, 'import_module')('scripts.dynamic')\n"
            ),
            "assigned_attribute_alias": (
                "import importlib\n"
                "load = importlib.import_module\n"
                "load('scripts.dynamic')\n"
            ),
            "assigned_getattr_alias": (
                "import importlib\n"
                "load = getattr(importlib, 'import_module')\n"
                "load('scripts.dynamic')\n"
            ),
            "nested_getattr_and_indirect_call": (
                "import importlib as il\n"
                "get = getattr\n"
                "load = get(il, 'import_' + 'module')\n"
                "invoke = load\n"
                "invoke('scripts.dynamic')\n"
            ),
            "builtin_import_alias": (
                "from builtins import __import__ as load\n"
                "load('scripts.dynamic')\n"
            ),
            "globals_import_lookup": (
                "globals()['__import__']('scripts.dynamic')\n"
            ),
            "importlib_getattribute_lookup": (
                "import importlib\n"
                "importlib.__getattribute__('import_module')('scripts.dynamic')\n"
            ),
            "operator_getitem_globals_lookup": (
                "import operator\n"
                "operator.getitem(globals(), '__import__')('scripts.dynamic')\n"
            ),
            "vars_importlib_get_lookup": (
                "import importlib\n"
                "vars(importlib).get('import_module')('scripts.dynamic')\n"
            ),
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    root = Path(tmpdir)
                    (root / "scripts").mkdir()
                    (root / "scripts" / "entry.py").write_text(
                        source,
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(
                        PortableFamilyError,
                        "unresolved dynamic import",
                    ):
                        portable_family_module._budget_import_closure(
                            root,
                            [Path("scripts/entry.py")],
                        )

    def test_budget_import_closure_preserves_static_local_import_resolution(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "scripts").mkdir()
            (root / "scripts" / "static.py").write_text(
                "VALUE = 'static'\n",
                encoding="utf-8",
            )
            (root / "scripts" / "entry.py").write_text(
                "import scripts.static\n"
                "from scripts.static import VALUE\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [Path("scripts/entry.py"), Path("scripts/static.py")],
                portable_family_module._budget_import_closure(
                    root,
                    [Path("scripts/entry.py")],
                ),
            )

    def test_budget_receipt_rejects_legacy_v1_at_the_current_digest_path(self) -> None:
        root, manifest, tmpdir = self._prepare_budget_fixture()
        try:
            receipt_file = root / portable_family_module.receipt_path_for(manifest)
            receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
            legacy = {
                key: value
                for key, value in receipt.items()
                if key
                not in {
                    "head_source_snapshot",
                    "candidate_identity",
                    "producer_identity",
                }
            }
            legacy["schema_version"] = "aoa-repo-local-kag-budget-receipt-v1"
            receipt_file.write_text(
                json.dumps(legacy, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                PortableFamilyError,
                "current identity-bound contract",
            ):
                validate_changed_generated_budget(
                    root,
                    base_ref="HEAD",
                    manifest=manifest,
                )
            loaded_source, loaded_family, loaded_manifest = load_portable_family(
                root,
                require_current_producer_identity=False,
                allow_legacy_external_receipt=True,
            )
            self.assertEqual(manifest, loaded_manifest)
            self.assertEqual(build_index(root), loaded_source)
            self.assertEqual(
                build_repository_indexes(loaded_source, repo_root=root),
                loaded_family,
            )
        finally:
            tmpdir.cleanup()

    def test_budget_receipt_binds_action_and_environment_inputs(self) -> None:
        root, manifest, tmpdir = self._prepare_budget_fixture()
        try:
            changed_action = capture_budget_producer_execution_inputs(
                root,
                base_ref="HEAD",
                history_ref="HEAD",
                event_history_ref="HEAD",
                output=Path("kag/indexes/other_source_surface_index.json"),
            )
            with self.assertRaisesRegex(
                PortableFamilyError,
                "producer identity does not match",
            ):
                validate_changed_generated_budget(
                    root,
                    base_ref="HEAD",
                    manifest=manifest,
                    producer_execution_inputs=changed_action,
                )
            with mock.patch.dict(
                portable_family_module.os.environ,
                {"AOA_KAG_FORCE_COLD_SCHEMA_COMPILATION": "1"},
                clear=False,
            ):
                with self.assertRaisesRegex(
                    PortableFamilyError,
                    "producer identity does not match",
                ):
                    validate_changed_generated_budget(
                        root,
                        base_ref="HEAD",
                        manifest=manifest,
                    )
        finally:
            tmpdir.cleanup()

    def test_budget_producer_runtime_contract_is_checkout_portable(self) -> None:
        first_root, _, first_tmpdir = self._prepare_budget_fixture()
        second_root, _, second_tmpdir = self._prepare_budget_fixture()
        try:
            first = capture_budget_producer_execution_inputs(
                first_root,
                base_ref="HEAD",
                history_ref="HEAD",
                event_history_ref="HEAD",
                jobs=1,
            )
            second = capture_budget_producer_execution_inputs(
                second_root,
                base_ref="HEAD",
                history_ref="HEAD",
                event_history_ref="HEAD",
                jobs=3,
            )
            self.assertEqual(first, second)
            self.assertNotIn("jobs", first["action_inputs"])
            self.assertNotIn("jobs", first["command_targets"])
            rendered = json.dumps(first, sort_keys=True)
            self.assertNotIn(str(first_root), rendered)
            self.assertNotIn(str(second_root), rendered)
            self.assertEqual("declared", next(
                item for item in first["dependencies"]
                if item["name"] == "jsonschema-rs"
            )["state"])
        finally:
            first_tmpdir.cleanup()
            second_tmpdir.cleanup()

    def test_budget_source_epoch_rejects_staged_source_drift(self) -> None:
        root, manifest, tmpdir = self._prepare_budget_fixture()
        try:
            (root / "README.md").write_text("staged source drift\n", encoding="utf-8")
            subprocess.run(("git", "add", "README.md"), cwd=root, check=True)
            with self.assertRaisesRegex(PortableFamilyError, "source epoch"):
                validate_changed_generated_budget(
                    root,
                    base_ref="HEAD",
                    manifest=manifest,
                )
        finally:
            tmpdir.cleanup()

    def test_budget_receipt_rejects_exact_receipt_symlink_and_parent_symlink(self) -> None:
        root, manifest, tmpdir = self._prepare_budget_fixture()
        try:
            receipt_file = root / portable_family_module.receipt_path_for(manifest)
            outside = root.parent / f"{root.name}-outside.json"
            receipt_file.unlink()
            receipt_file.symlink_to(outside)
            with self.assertRaisesRegex(PortableFamilyError, "regular in-root"):
                validate_changed_generated_budget(
                    root,
                    base_ref="HEAD",
                    manifest=manifest,
                )
        finally:
            tmpdir.cleanup()

        root, manifest, tmpdir = self._prepare_budget_fixture()
        try:
            receipt_root = root / portable_family_module.BUDGET_RECEIPT_ROOT_RELATIVE_PATH
            receipt_file = root / portable_family_module.receipt_path_for(manifest)
            outside_root = root / "receipt-root-outside"
            outside_root.mkdir()
            receipt_file.unlink()
            receipt_root.rmdir()
            receipt_root.symlink_to(outside_root, target_is_directory=True)
            with self.assertRaisesRegex(PortableFamilyError, "parent must be"):
                validate_changed_generated_budget(
                    root,
                    base_ref="HEAD",
                    manifest=manifest,
                )
        finally:
            tmpdir.cleanup()

    def test_budget_receipt_pins_parent_descriptor_across_replacement(self) -> None:
        root, manifest, tmpdir = self._prepare_budget_fixture()
        receipt_root = root / portable_family_module.BUDGET_RECEIPT_ROOT_RELATIVE_PATH
        relative = portable_family_module.receipt_path_for(manifest)
        pinned_root = root / "pinned-receipt-parent"
        outside_root = root.parent / f"{root.name}-receipt-outside"
        outside_root.mkdir()
        original_open_parent = portable_family_module._budget_open_receipt_parent

        def replace_parent(
            owner_root: Path,
            receipt_path: Path,
            *,
            allow_missing: bool,
        ) -> tuple[int, str]:
            descriptor, leaf = original_open_parent(
                owner_root,
                receipt_path,
                allow_missing=allow_missing,
            )
            receipt_root.rename(pinned_root)
            receipt_root.symlink_to(outside_root, target_is_directory=True)
            return descriptor, leaf

        try:
            with mock.patch.object(
                portable_family_module,
                "_budget_open_receipt_parent",
                side_effect=replace_parent,
            ):
                observed = portable_family_module._budget_read_receipt(root, manifest)
            self.assertEqual("aoa-repo-local-kag-budget-receipt-v2", observed["schema_version"])
            receipt_root.unlink()
            pinned_root.rename(receipt_root)

            receipt = dict(observed)
            receipt["reason"] = "descriptor-pinned replacement test"
            with mock.patch.object(
                portable_family_module,
                "_budget_open_receipt_parent",
                side_effect=replace_parent,
            ):
                portable_family_module.write_budget_receipt(root, relative, receipt)
            self.assertFalse((outside_root / relative.name).exists())
            receipt_root.unlink()
            pinned_root.rename(receipt_root)
            rewritten = portable_family_module._budget_read_receipt(root, manifest)
            self.assertEqual(receipt["reason"], rewritten["reason"])
        finally:
            if receipt_root.is_symlink():
                receipt_root.unlink()
            if pinned_root.exists():
                pinned_root.rename(receipt_root)
            shutil.rmtree(outside_root, ignore_errors=True)
            tmpdir.cleanup()

    def test_portable_family_paths_do_not_amplify_repository_event_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
            subprocess.run(
                ("git", "config", "user.name", "KAG Test"),
                cwd=root,
                check=True,
            )
            subprocess.run(
                ("git", "config", "user.email", "kag@example.test"),
                cwd=root,
                check=True,
            )
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-qm", "source"),
                cwd=root,
                check=True,
            )
            source_index = build_index(root)
            family = build_repository_indexes(
                source_index,
                repo_root=root,
                history_ref="HEAD",
                event_history_ref="HEAD",
            )
            manifest, shards = build_portable_family(source_index, family)
            write_portable_output(root, manifest, shards)
            for relative in (
                Path("kag/indexes/corpus.manifest.json"),
                Path("kag/indexes/hot_profile.json"),
                Path("kag/indexes/artifact_locators.json"),
                Path("generated/repo_local_kag_preparation_seed.json"),
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")
            subprocess.run(("git", "add", "kag"), cwd=root, check=True)
            subprocess.run(("git", "add", "generated"), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-qm", "generated family controls"),
                cwd=root,
                check=True,
            )

            rebuilt = build_repository_indexes(
                source_index,
                repo_root=root,
                history_ref="HEAD",
                event_history_ref="HEAD",
            )

        self.assertEqual(family["event"], rebuilt["event"])

    def test_environment_history_ref_is_scoped_to_its_owner(self) -> None:
        with mock.patch(
            "scripts.generate_repo_local_kag_index.local_default_history_ref",
            return_value=None,
        ):
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

    def test_environment_event_history_ref_is_scoped_to_its_owner(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                "AOA_REPO_LOCAL_KAG_HISTORY_REPO": "aoa-kag",
                "AOA_REPO_LOCAL_KAG_EVENT_HISTORY_REF": "stable-base",
            },
        ):
            self.assertEqual(
                "stable-base",
                effective_event_history_ref(REPO_ROOT, fallback="stable-head"),
            )
            self.assertEqual(
                "explicit-base",
                effective_event_history_ref(
                    REPO_ROOT,
                    "explicit-base",
                    fallback="stable-head",
                ),
            )

        with mock.patch.dict(
            "os.environ",
            {
                "AOA_REPO_LOCAL_KAG_HISTORY_REPO": "another-owner",
                "AOA_REPO_LOCAL_KAG_EVENT_HISTORY_REF": "foreign-base",
            },
        ):
            self.assertEqual(
                "stable-head",
                effective_event_history_ref(REPO_ROOT, fallback="stable-head"),
            )

    def test_cli_uses_local_default_branch_history_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(
                ("git", "config", "user.email", "kag@example.test"),
                cwd=root,
                check=True,
            )
            write_fixture(root)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "base"), cwd=root, check=True)
            base_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(
                ("git", "update-ref", "refs/remotes/origin/main", base_sha),
                cwd=root,
                check=True,
            )
            subprocess.run(
                (
                    "git",
                    "symbolic-ref",
                    "refs/remotes/origin/HEAD",
                    "refs/remotes/origin/main",
                ),
                cwd=root,
                check=True,
            )
            subprocess.run(("git", "checkout", "-qb", "feature"), cwd=root, check=True)
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\nFeature one.\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "add", "README.md"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "feature one"), cwd=root, check=True)
            usage = root / "docs" / "guides" / "usage.md"
            usage.write_text(
                usage.read_text(encoding="utf-8") + "\nFeature two.\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "add", "docs/guides/usage.md"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "feature two"), cwd=root, check=True)

            self.assertEqual(base_sha, local_default_history_ref(root))
            self.assertEqual(
                0,
                main(
                    [
                        "--repo-root",
                        str(root),
                        "--index-family",
                        "--history-ref",
                        base_sha,
                        "--event-history-ref",
                        base_sha,
                    ]
                ),
            )
            self.assertEqual(
                0,
                main(["--repo-root", str(root), "--index-family", "--check"]),
            )

    def test_local_default_branch_history_uses_first_parent_not_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(
                ("git", "config", "user.email", "kag@example.test"),
                cwd=root,
                check=True,
            )
            (root / "surface.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(("git", "add", "surface.txt"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "base"), cwd=root, check=True)
            base_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            (root / "surface.txt").write_text("head\n", encoding="utf-8")
            subprocess.run(("git", "commit", "-am", "head", "-q"), cwd=root, check=True)
            head_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(
                ("git", "update-ref", "refs/remotes/origin/main", head_sha),
                cwd=root,
                check=True,
            )
            subprocess.run(
                (
                    "git",
                    "symbolic-ref",
                    "refs/remotes/origin/HEAD",
                    "refs/remotes/origin/main",
                ),
                cwd=root,
                check=True,
            )

            self.assertEqual(base_sha, local_default_history_ref(root))
            self.assertNotEqual(head_sha, local_default_history_ref(root))

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

    def test_payload_digest_matches_deepcopy_reference_without_mutating_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            payload = build_index(root)

        original = copy.deepcopy(payload)
        digest_material = copy.deepcopy(payload)
        digest_material["index_identity"]["content_digest"] = "0" * 64
        expected = hashlib.sha256(
            json.dumps(
                digest_material,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

        self.assertEqual(expected, payload_digest(payload))
        self.assertEqual(original, payload)
        self.assertEqual(expected, repo_local_kag_index_digest_without_self(payload))
        self.assertEqual(original, payload)

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

    def test_incremental_source_build_invalidates_for_generator_helper_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.email", "kag@example.test"), cwd=root, check=True)
            write_fixture(root)
            helper = root / "scripts" / "repo_local" / "identity.py"
            helper.parent.mkdir(parents=True)
            helper.write_text("IDENTITY_VERSION = 1\n", encoding="utf-8")
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial"), cwd=root, check=True)
            previous = build_index(root)
            helper.write_text("IDENTITY_VERSION = 2\n", encoding="utf-8")
            subprocess.run(("git", "add", helper.relative_to(root).as_posix()), cwd=root, check=True)

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
        self.assertEqual(len(full["records"]), build_record_spy.call_count)

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

    def test_capability_graph_projects_typed_edges_and_authored_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            fixture_graph = root / "tests" / "fixtures" / "capability_graph.json"
            fixture_graph.parent.mkdir(parents=True)
            fixture_graph.write_text(
                (root / "generated" / "capability_graph.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)
            documents = build_repo_retrieval_documents(root, source, family)
            query = RepoKagQuery(source, family, repo_root=root)

        records_by_path = {
            record["identity"]["path"]: record for record in source["records"]
        }
        graph_record = records_by_path["generated/capability_graph.json"]
        self.assertEqual("generated_projection", graph_record["surface_state"])
        self.assertEqual(
            [
                {
                    "repo": source["repo"]["name"],
                    "path": "capabilities/families/session-memory.yaml",
                    "role": "primary",
                    "authority": "authored_source",
                }
            ],
            graph_record["provenance"]["source_refs"],
        )
        self.assertEqual(
            "aoa-skills:scripts/build_capability_home_projection.py",
            graph_record["provenance"]["generated_by"],
        )
        self.assertEqual(
            {
                "repo": source["repo"]["name"],
                "surface": "capabilities/families/session-memory.yaml",
                "route_kind": "source_owner",
            },
            graph_record["owner_return_route"],
        )

        capability_entities = {
            entry["semantic_key"]: entry
            for entry in family["entity"]["entries"]
            if str(entry["semantic_key"]).startswith("capability:")
        }
        self.assertEqual(
            {"capability:memory", "capability:skill.query", "capability:adapter.audit"},
            set(capability_entities),
        )
        self.assertEqual(
            {"capability", "skill", "adapter"},
            {entry["entity_kind"] for entry in capability_entities.values()},
        )
        self.assertEqual(
            "Query memory",
            capability_entities["capability:skill.query"]["label"],
        )

        graph_source_id = graph_record["identity"]["id"]
        fixture_source_id = records_by_path[
            "tests/fixtures/capability_graph.json"
        ]["identity"]["id"]
        graph_anchors = {
            entry["locator"]["pointer"]: entry
            for entry in family["anchor"]["entries"]
            if entry["source_record_id"] == graph_source_id
            and entry["parser_ref"] == "aoa-capability-graph@1"
        }
        self.assertEqual(
            {
                "/nodes/0",
                "/nodes/1",
                "/nodes/2",
                "/relations/0",
                "/relations/1",
                "/relations/2",
            },
            set(graph_anchors),
        )
        self.assertFalse(
            any(
                entry["source_record_id"] == graph_source_id
                and entry["locator"]["pointer"] == "/retrieval_documents"
                for entry in family["anchor"]["entries"]
            )
        )
        self.assertFalse(
            any(
                document["path"] == "generated/capability_graph.json"
                and "Retrieve session evidence." in document["text"]
                for document in documents
            )
        )
        self.assertFalse(
            any(
                entry["source_record_id"] == fixture_source_id
                and entry["parser_ref"] == "aoa-capability-graph@1"
                for entry in family["anchor"]["entries"]
            )
        )
        typed_relations = [
            relation
            for relation in family["relation"]["entries"]
            if relation["relation_kind"] in {"primary-parent", "hands-off-to"}
        ]
        self.assertEqual(3, len(typed_relations))
        handoff = next(
            relation
            for relation in typed_relations
            if relation["relation_kind"] == "hands-off-to"
        )
        self.assertEqual(
            capability_entities["capability:skill.query"]["id"],
            handoff["from_id"],
        )
        self.assertEqual(
            capability_entities["capability:adapter.audit"]["id"],
            handoff["to_id"],
        )
        self.assertEqual(
            [graph_anchors["/relations/1"]["id"]],
            handoff["evidence_anchor_ids"],
        )
        self.assertEqual("declared", handoff["evidence_class"])
        self.assertEqual("declared", handoff["provenance_ref"])
        self.assertEqual("declared", handoff["trust_ref"])

        graph_artifact = next(
            entry
            for entry in family["artifact"]["entries"]
            if entry["path"] == "generated/capability_graph.json"
        )
        family_artifact = next(
            entry
            for entry in family["artifact"]["entries"]
            if entry["path"] == "capabilities/families/session-memory.yaml"
        )
        self.assertTrue(
            any(
                relation["relation_kind"] == "derives_from"
                and relation["from_id"] == graph_artifact["id"]
                and relation["to_id"] == family_artifact["id"]
                for relation in family["relation"]["entries"]
            )
        )

        traversed = query.traverse(
            [capability_entities["capability:skill.query"]["id"]],
            relation_kinds={"hands-off-to"},
            max_hops=1,
        )
        audit = next(
            hit
            for hit in traversed
            if hit["id"] == capability_entities["capability:adapter.audit"]["id"]
        )
        self.assertEqual([handoff["id"]], audit["evidence"]["relation_ids"])
        relation_document = next(
            document
            for document in documents
            if document["node_id"] == graph_anchors["/relations/1"]["id"]
        )
        self.assertIn("Query evidence is ready for audit.", relation_document["text"])
        self.assertEqual(
            "capabilities/families/session-memory.yaml",
            relation_document["provenance"]["source_refs"][0]["path"],
        )
        self.assertEqual(
            "capabilities/families/session-memory.yaml",
            relation_document["provenance"]["source_path"],
        )
        session_memory_source_id = records_by_path[
            "capabilities/families/session-memory.yaml"
        ]["identity"]["id"]
        authored_anchors = {
            entry["locator"]["pointer"]: entry
            for entry in family["anchor"]["entries"]
            if entry["source_record_id"] == session_memory_source_id
            and entry["parser_ref"] == "aoa-yaml-path@1"
        }
        authored_handoff_anchor = authored_anchors["/relations/0/kind"]
        self.assertEqual(
            authored_handoff_anchor["locator"],
            relation_document["locator"],
        )
        self.assertEqual(
            [authored_handoff_anchor["id"]],
            relation_document["anchor_ids"],
        )
        primary_parent_document = next(
            document
            for document in documents
            if document["node_id"] == graph_anchors["/relations/0"]["id"]
        )
        authored_primary_parent_anchor = authored_anchors[
            "/nodes/1/primary_parent"
        ]
        self.assertEqual(
            authored_primary_parent_anchor["locator"],
            primary_parent_document["locator"],
        )

    def test_capability_graph_preserves_relation_source_path_for_multi_family_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            supporting_path = root / "capabilities" / "families" / "supporting.yaml"
            supporting_path.write_text(
                "schema_version: aoa-capability-family-v1\n"
                "family: supporting\n"
                "nodes:\n"
                "  - id: adapter.audit\n"
                "    kind: adapter\n"
                "    title: Audit adapter\n"
                "    contract_level: executable\n"
                "    primary_parent: memory\n"
                "    owner:\n"
                "      authority: authored\n"
                "      repo: demo\n"
                "      surface: capabilities/families/supporting.yaml\n"
                "    lifecycle:\n"
                "      state: active\n"
                "relations:\n"
                "  - kind: hands-off-to\n"
                "    source: skill.query\n"
                "    target: adapter.audit\n"
                "    condition: Query evidence is ready for audit.\n",
                encoding="utf-8",
            )
            (root / "capabilities" / "families" / "session-memory.yaml").write_text(
                "schema_version: aoa-capability-family-v1\n"
                "family: session-memory\n"
                "nodes:\n"
                "  - id: memory\n"
                "    kind: capability\n"
                "    title: Session memory\n"
                "    contract_level: navigation\n"
                "    primary_parent: null\n"
                "    owner:\n"
                "      authority: authored\n"
                "      repo: demo\n"
                "      surface: capabilities/families/session-memory.yaml\n"
                "    lifecycle:\n"
                "      state: active\n"
                "  - id: skill.query\n"
                "    kind: skill\n"
                "    title: Query memory\n"
                "    contract_level: executable\n"
                "    primary_parent: memory\n"
                "    owner:\n"
                "      authority: authored\n"
                "      repo: demo\n"
                "      surface: capabilities/families/session-memory.yaml\n"
                "    lifecycle:\n"
                "      state: active\n"
                "relations: []\n",
                encoding="utf-8",
            )
            graph_path = root / "generated" / "capability_graph.json"
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            graph_payload["source"]["family_files"].append(
                {
                    "path": "capabilities/families/supporting.yaml",
                    "sha256": hashlib.sha256(supporting_path.read_bytes()).hexdigest(),
                }
            )
            graph_payload["source"]["family_files"][0]["sha256"] = hashlib.sha256(
                (root / "capabilities" / "families" / "session-memory.yaml").read_bytes()
            ).hexdigest()
            graph_payload["nodes"][2]["source_path"] = (
                "capabilities/families/supporting.yaml"
            )
            graph_payload["nodes"][2]["source_family"] = "supporting"
            graph_payload["nodes"][2]["owner"]["surface"] = (
                "capabilities/families/supporting.yaml"
            )
            graph_payload["relations"][1]["source_path"] = (
                "capabilities/families/supporting.yaml"
            )
            graph_payload["relations"][2]["source_path"] = (
                "capabilities/families/supporting.yaml"
            )
            graph_path.write_text(
                json.dumps(graph_payload, sort_keys=True),
                encoding="utf-8",
            )
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)
            documents = build_repo_retrieval_documents(root, source, family)
            query = RepoKagQuery(source, family, repo_root=root)

        graph_record = next(
            record
            for record in source["records"]
            if record["identity"]["path"] == "generated/capability_graph.json"
        )
        self.assertEqual(
            [
                "capabilities/families/session-memory.yaml",
                "capabilities/families/supporting.yaml",
            ],
            [
                source_ref["path"]
                for source_ref in graph_record["provenance"]["source_refs"]
            ],
        )
        capability_entities = {
            entry["semantic_key"]: entry
            for entry in family["entity"]["entries"]
            if entry["semantic_key"].startswith("capability:")
        }
        graph_node = next(
            anchor
            for anchor in family["anchor"]["entries"]
            if anchor["source_record_id"] == graph_record["identity"]["id"]
            and anchor["locator"]["pointer"] == "/nodes/2"
        )
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            graph_node["source_path"],
        )
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            capability_entities["capability:adapter.audit"]["source_path"],
        )
        graph_anchor = next(
            anchor
            for anchor in family["anchor"]["entries"]
            if anchor["source_record_id"] == graph_record["identity"]["id"]
            and anchor["locator"]["pointer"] == "/relations/1"
        )
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            graph_anchor["outbound_refs"][0]["source_path"],
        )
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            graph_anchor["source_path"],
        )
        handoff = next(
            relation
            for relation in family["relation"]["entries"]
            if relation["relation_kind"] == "hands-off-to"
        )
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            handoff["source_path"],
        )
        relation_document = next(
            document
            for document in documents
            if document["node_id"] == graph_anchor["id"]
        )
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            relation_document["provenance"]["source_refs"][0]["path"],
        )
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            relation_document["provenance"]["source_path"],
        )
        supporting_record = next(
            record
            for record in source["records"]
            if record["identity"]["path"]
            == "capabilities/families/supporting.yaml"
        )
        expected_supporting_provenance = copy.deepcopy(
            supporting_record["provenance"]
        )
        expected_supporting_provenance["source_path"] = (
            "capabilities/families/supporting.yaml"
        )
        self.assertEqual(
            expected_supporting_provenance,
            relation_document["provenance"],
        )
        self.assertEqual(
            supporting_record["owner_return_route"],
            relation_document["owner_return_route"],
        )
        supporting_source_id = supporting_record["identity"]["id"]
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            relation_document["path"],
        )
        self.assertEqual(
            [supporting_source_id],
            relation_document["source_record_ids"],
        )
        self.assertEqual(
            [supporting_record["identity"]["version_id"]],
            relation_document["source_version_ids"],
        )
        supporting_authored_anchors = {
            entry["locator"]["pointer"]: entry
            for entry in family["anchor"]["entries"]
            if entry["source_record_id"] == supporting_source_id
            and entry["parser_ref"] == "aoa-yaml-path@1"
        }
        supporting_handoff_anchor = supporting_authored_anchors[
            "/relations/0/kind"
        ]
        self.assertEqual(
            supporting_handoff_anchor["locator"],
            relation_document["locator"],
        )
        self.assertEqual(
            [supporting_handoff_anchor["id"]],
            relation_document["anchor_ids"],
        )
        supporting_entity_handle = query.projection_handle(
            capability_entities["capability:adapter.audit"]["id"]
        )
        self.assertIsNotNone(supporting_entity_handle)
        self.assertEqual(
            [supporting_source_id],
            supporting_entity_handle["source_record_ids"],
        )
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            supporting_entity_handle["path"],
        )
        self.assertEqual(
            supporting_record["owner_return_route"],
            supporting_entity_handle["owner_return_route"],
        )
        relation_handle = query.projection_handle(handoff["id"])
        self.assertIsNotNone(relation_handle)
        self.assertEqual(
            [supporting_source_id],
            relation_handle["source_record_ids"],
        )
        self.assertEqual(
            [supporting_handoff_anchor["id"]],
            relation_handle["anchor_ids"],
        )
        relation_hit = query.read(handoff["id"], access_scopes={"public"})
        self.assertIsNotNone(relation_hit)
        self.assertEqual(
            [supporting_handoff_anchor["id"]],
            relation_hit["anchor_ids"],
        )
        self.assertEqual(
            [supporting_handoff_anchor["id"]],
            relation_hit["evidence"]["anchor_ids"],
        )
        self.assertEqual(
            supporting_record["owner_return_route"],
            relation_handle["owner_return_route"],
        )
        node_document = next(
            document
            for document in documents
            if document["node_id"] == graph_node["id"]
        )
        self.assertEqual(
            "capabilities/families/supporting.yaml",
            node_document["provenance"]["source_path"],
        )
        supporting_node_anchor = supporting_authored_anchors["/nodes/0/id"]
        self.assertEqual(
            [supporting_node_anchor["id"]],
            supporting_entity_handle["anchor_ids"],
        )
        entity_hit = query.read(
            capability_entities["capability:adapter.audit"]["id"],
            access_scopes={"public"},
        )
        self.assertIsNotNone(entity_hit)
        self.assertEqual(
            [supporting_node_anchor["id"]],
            entity_hit["anchor_ids"],
        )
        self.assertEqual(
            [supporting_node_anchor["id"]],
            entity_hit["evidence"]["anchor_ids"],
        )
        self.assertEqual(
            supporting_node_anchor["locator"],
            node_document["locator"],
        )
        self.assertEqual(
            [supporting_node_anchor["id"]],
            node_document["anchor_ids"],
        )

    def test_capability_query_keeps_graph_fallback_without_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)
            query = RepoKagQuery(source, family)

        graph_record = next(
            record
            for record in source["records"]
            if record["identity"]["path"] == "generated/capability_graph.json"
        )
        graph_anchor = next(
            anchor
            for anchor in family["anchor"]["entries"]
            if anchor["source_record_id"] == graph_record["identity"]["id"]
            and anchor["locator"]["pointer"] == "/nodes/2"
        )
        entity = next(
            entry
            for entry in family["entity"]["entries"]
            if entry["semantic_key"] == "capability:adapter.audit"
        )
        handle = query.projection_handle(entity["id"])
        self.assertIsNotNone(handle)
        self.assertEqual([graph_record["identity"]["id"]], handle["source_record_ids"])
        self.assertEqual([graph_anchor["id"]], handle["anchor_ids"])
        hit = query.read(entity["id"], access_scopes={"public"})
        self.assertIsNotNone(hit)
        self.assertEqual([graph_record["identity"]["id"]], hit["source_record_ids"])
        self.assertEqual([graph_anchor["id"]], hit["anchor_ids"])
        self.assertEqual([graph_anchor["id"]], hit["evidence"]["anchor_ids"])

    def test_capability_graph_rebinds_repeated_relation_to_matching_authored_locator(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            family_path = root / "capabilities" / "families" / "session-memory.yaml"
            family_path.write_text(
                family_path.read_text(encoding="utf-8")
                + "  - kind: hands-off-to\n"
                + "    source: skill.query\n"
                + "    target: adapter.audit\n"
                + "    condition: Second evidence handoff.\n",
                encoding="utf-8",
            )
            graph_path = root / "generated" / "capability_graph.json"
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            graph_payload["source"]["family_files"][0]["sha256"] = hashlib.sha256(
                family_path.read_bytes()
            ).hexdigest()
            graph_payload["relations"].append(
                {
                    "kind": "hands-off-to",
                    "source": "skill.query",
                    "target": "adapter.audit",
                    "condition": "Second evidence handoff.",
                    "source_path": "capabilities/families/session-memory.yaml",
                }
            )
            graph_path.write_text(
                json.dumps(graph_payload, sort_keys=True),
                encoding="utf-8",
            )
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)
            documents = build_repo_retrieval_documents(root, source, family)

        graph_anchors = {
            entry["locator"]["pointer"]: entry
            for entry in family["anchor"]["entries"]
            if entry["parser_ref"] == "aoa-capability-graph@1"
            and entry["locator"]["pointer"].startswith("/relations/")
        }
        authored_anchors = {
            entry["locator"]["pointer"]: entry
            for entry in family["anchor"]["entries"]
            if entry["parser_ref"] == "aoa-yaml-path@1"
            and entry["source_record_id"]
            == next(
                record["identity"]["id"]
                for record in source["records"]
                if record["identity"]["path"]
                == "capabilities/families/session-memory.yaml"
            )
        }
        second_document = next(
            document
            for document in documents
            if document["node_id"] == graph_anchors["/relations/3"]["id"]
        )
        self.assertEqual(
            authored_anchors["/relations/0/kind"]["locator"],
            next(
                document
                for document in documents
                if document["node_id"] == graph_anchors["/relations/1"]["id"]
            )["locator"],
        )
        self.assertEqual(
            authored_anchors["/relations/1/kind"]["locator"],
            second_document["locator"],
        )
        self.assertEqual(
            [authored_anchors["/relations/1/kind"]["id"]],
            second_document["anchor_ids"],
        )

    def test_capability_graph_rejects_stale_authored_family_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            graph_path = root / "generated" / "capability_graph.json"
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            graph_payload["source"]["family_files"][0]["sha256"] = "0" * 64
            graph_path.write_text(
                json.dumps(graph_payload, sort_keys=True),
                encoding="utf-8",
            )
            source = build_index(root)
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                build_repository_indexes(source, repo_root=root)

    def test_capability_graph_rejects_malformed_projection_shape(self) -> None:
        malformed_fields = ("source", "nodes", "relations")
        for field in malformed_fields:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                write_fixture(root)
                write_capability_graph_fixture(root)
                graph_path = root / "generated" / "capability_graph.json"
                graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
                if field == "source":
                    del graph_payload[field]
                else:
                    graph_payload[field] = {}
                graph_path.write_text(
                    json.dumps(graph_payload, sort_keys=True),
                    encoding="utf-8",
                )
                source = build_index(root)
                with self.assertRaisesRegex(ValueError, rf"{field} must be"):
                    build_repository_indexes(source, repo_root=root)

    def test_capability_graph_rejects_unrecognized_selected_graph(self) -> None:
        variants = ("invalid-json", "schema-version", "authority")
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                write_fixture(root)
                write_capability_graph_fixture(root)
                graph_path = root / "generated" / "capability_graph.json"
                if variant == "invalid-json":
                    graph_path.write_text("{", encoding="utf-8")
                else:
                    graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
                    if variant == "schema-version":
                        graph_payload["schema_version"] = "aoa-capability-graph-v2"
                    else:
                        graph_payload["authority"] = True
                    graph_path.write_text(
                        json.dumps(graph_payload, sort_keys=True),
                        encoding="utf-8",
                    )
                source = build_index(root)
                with self.assertRaisesRegex(
                    ValueError,
                    "manifest-selected capability graph",
                ):
                    build_repository_indexes(source, repo_root=root)

    def test_capability_graph_rejects_missing_projection_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            graph_path = root / "generated" / "capability_graph.json"
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            del graph_payload["nodes"][0]["kind"]
            graph_path.write_text(
                json.dumps(graph_payload, sort_keys=True),
                encoding="utf-8",
            )
            source = build_index(root)
            with self.assertRaisesRegex(ValueError, r"nodes\[0\]\.kind is required"):
                build_repository_indexes(source, repo_root=root)

    def test_capability_graph_rejects_duplicate_primary_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            graph_path = root / "generated" / "capability_graph.json"
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            graph_payload["relations"].append(
                copy.deepcopy(graph_payload["relations"][0])
            )
            graph_path.write_text(
                json.dumps(graph_payload, sort_keys=True),
                encoding="utf-8",
            )
            source = build_index(root)
            with self.assertRaisesRegex(
                ValueError,
                "duplicate primary-parent relation",
            ):
                build_repository_indexes(source, repo_root=root)

    def test_capability_graph_rejects_unauthored_semantic_fields(self) -> None:
        variants = ("node", "relation")
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                write_fixture(root)
                write_capability_graph_fixture(root)
                graph_path = root / "generated" / "capability_graph.json"
                graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
                if variant == "node":
                    graph_payload["nodes"][0]["derived_label"] = "forged"
                else:
                    graph_payload["relations"][0]["derived_condition"] = "forged"
                graph_path.write_text(
                    json.dumps(graph_payload, sort_keys=True),
                    encoding="utf-8",
                )
                source = build_index(root)
                with self.assertRaisesRegex(ValueError, "unauthored fields"):
                    build_repository_indexes(source, repo_root=root)

    def test_capability_graph_matches_exact_authored_relation_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            family_path = root / "capabilities" / "families" / "session-memory.yaml"
            family_path.write_text(
                family_path.read_text(encoding="utf-8")
                + "\n"
                + "  - kind: references\n"
                + "    source: memory\n"
                + "    target: skill.query\n",
                encoding="utf-8",
            )
            graph_path = root / "generated" / "capability_graph.json"
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            graph_payload["source"]["family_files"][0]["sha256"] = hashlib.sha256(
                family_path.read_bytes()
            ).hexdigest()
            graph_payload["relations"].append(
                {
                    "kind": "references",
                    "source": "memory",
                    "target": "skill.query",
                    "condition": "forged",
                    "source_path": "capabilities/families/session-memory.yaml",
                }
            )
            graph_path.write_text(
                json.dumps(graph_payload, sort_keys=True),
                encoding="utf-8",
            )
            source = build_index(root)
            with self.assertRaisesRegex(ValueError, "does not match an authored relation"):
                build_repository_indexes(source, repo_root=root)

    def test_capability_graph_accepts_typed_owner_projection_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            graph_path = root / "generated" / "capability_graph.json"
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            graph_payload["nodes"][1].update(
                {
                    "owner_contract": {
                        "authority": "forged-owner",
                        "marker": "owner-metadata-must-not-be-retrieved",
                    },
                    "owner_contract_ref": {
                        "path": "skills/demo/references/nonexistent.yaml",
                        "sha256": "0" * 64,
                    },
                    "package": "forged-package-metadata",
                }
            )
            graph_payload["search_payload"] = {
                "marker": "unvalidated-top-level-metadata-must-not-be-retrieved"
            }
            graph_payload["$defs"] = {
                "Injected": {
                    "marker": "unvalidated-schema-definition-must-not-be-retrieved"
                }
            }
            graph_payload["nodes"][1]["kind"] = "skill"
            graph_path.write_text(
                json.dumps(graph_payload, sort_keys=True),
                encoding="utf-8",
            )
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)
            documents = build_repo_retrieval_documents(root, source, family)

        graph_anchor = next(
            entry
            for entry in family["anchor"]["entries"]
            if entry["parser_ref"] == "aoa-capability-graph@1"
            and entry["locator"]["pointer"] == "/nodes/1"
        )
        graph_document = next(
            document for document in documents if document["node_id"] == graph_anchor["id"]
        )
        graph_source_id = next(
            record["identity"]["id"]
            for record in source["records"]
            if record["identity"]["path"] == "generated/capability_graph.json"
        )
        self.assertTrue(
            any(
                entry["semantic_key"] == "capability:skill.query"
                for entry in family["entity"]["entries"]
            )
        )
        self.assertNotIn("owner-metadata-must-not-be-retrieved", graph_document["text"])
        self.assertNotIn("nonexistent.yaml", graph_document["text"])
        self.assertFalse(
            any(
                entry["source_record_id"] == graph_source_id
                and entry["locator"]["pointer"]
                in {"/nodes", "/search_payload", "/$defs/Injected"}
                for entry in family["anchor"]["entries"]
            )
        )
        self.assertFalse(
            any(
                "unvalidated-top-level-metadata-must-not-be-retrieved" in document["text"]
                or "unvalidated-schema-definition-must-not-be-retrieved" in document["text"]
                for document in documents
            )
        )

    def test_capability_source_path_override_requires_graph_anchor_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)

            graph_record = next(
                record
                for record in source["records"]
                if record["identity"]["path"] == "generated/capability_graph.json"
            )
            graph_source_id = graph_record["identity"]["id"]
            graph_anchor = next(
                entry
                for entry in family["anchor"]["entries"]
                if entry["parser_ref"] == "aoa-capability-graph@1"
                and entry["locator"]["pointer"] == "/nodes/1"
            )
            authored_path = graph_anchor["source_path"]
            capability_entity = next(
                entry
                for entry in family["entity"]["entries"]
                if entry["semantic_key"] == "capability:skill.query"
            )
            handoff = next(
                entry
                for entry in family["relation"]["entries"]
                if entry["relation_kind"] == "hands-off-to"
            )
            readme_source_id = next(
                record["identity"]["id"]
                for record in source["records"]
                if record["identity"]["path"] == "README.md"
            )
            forged_anchor = copy.deepcopy(graph_anchor)
            forged_anchor["id"] = f"{graph_anchor['id']}:forged-owner"
            forged_anchor["source_record_id"] = readme_source_id
            forged_anchor["source_path"] = authored_path
            family["anchor"]["entries"].append(forged_anchor)
            graph_anchor["source_path"] = "README.md"
            capability_entity["source_path"] = "README.md"
            capability_entity["anchor_ids"] = [forged_anchor["id"]]
            handoff["source_path"] = "README.md"

            query = RepoKagQuery(source, family, repo_root=root)
            entity_handle = query.projection_handle(capability_entity["id"])
            relation_handle = query.projection_handle(handoff["id"])
            documents = build_repo_retrieval_documents(root, source, family)
            graph_document = next(
                document for document in documents if document["node_id"] == graph_anchor["id"]
            )

        self.assertEqual([graph_source_id], entity_handle["source_record_ids"])
        self.assertEqual([graph_source_id], relation_handle["source_record_ids"])
        self.assertNotIn("README.md", graph_document["provenance"].get("source_path", ""))
        self.assertTrue(
            all(
                source_ref["path"] != "README.md"
                for source_ref in graph_document["provenance"]["source_refs"]
            )
        )

    def test_capability_graph_rejects_phantom_nodes_and_relations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            graph_path = root / "generated" / "capability_graph.json"
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            phantom = copy.deepcopy(graph_payload["nodes"][0])
            phantom["id"] = "phantom.capability"
            graph_payload["nodes"].append(phantom)
            graph_payload["relations"][1]["target"] = "phantom.capability"
            graph_path.write_text(
                json.dumps(graph_payload, sort_keys=True),
                encoding="utf-8",
            )
            source = build_index(root)
            with self.assertRaisesRegex(ValueError, "graph node IDs do not match authored"):
                build_repository_indexes(source, repo_root=root)

    def test_capability_graph_rejects_authored_source_path_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            graph_path = root / "generated" / "capability_graph.json"
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            graph_payload["nodes"][1]["source_path"] = "capabilities/families/missing.yaml"
            graph_path.write_text(
                json.dumps(graph_payload, sort_keys=True),
                encoding="utf-8",
            )
            source = build_index(root)
            with self.assertRaisesRegex(ValueError, "source_path"):
                build_repository_indexes(source, repo_root=root)

    def test_capability_projection_upgrade_invalidates_legacy_incremental_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            current_source = build_index(root)
            current_family = build_repository_indexes(
                current_source,
                repo_root=root,
            )
            legacy_source = json.loads(json.dumps(current_source))
            legacy_graph = next(
                record
                for record in legacy_source["records"]
                if record["identity"]["path"] == "generated/capability_graph.json"
            )
            legacy_graph["provenance"]["source_refs"] = [
                {
                    "repo": current_source["repo"]["name"],
                    "path": "generated/capability_graph.json",
                    "role": "primary",
                    "authority": "derived_readmodel",
                }
            ]
            legacy_graph["provenance"]["generated_by"] = ""
            legacy_graph["owner_return_route"]["surface"] = (
                "generated/capability_graph.json"
            )
            with mock.patch(
                "scripts.generate_repo_local_kag_index.build_record",
                wraps=__import__(
                    "scripts.generate_repo_local_kag_index",
                    fromlist=["build_record"],
                ).build_record,
            ) as build_record_spy:
                incremental_source = build_index_incremental(
                    root,
                    legacy_source,
                )

            legacy_family = json.loads(json.dumps(current_family))
            legacy_family["anchor"]["entries"] = [
                anchor
                for anchor in legacy_family["anchor"]["entries"]
                if anchor["parser_ref"] != "aoa-capability-graph@1"
            ]
            with mock.patch(
                "scripts.generate_repo_local_kag_index.extract_structure",
                wraps=__import__(
                    "scripts.generate_repo_local_kag_index",
                    fromlist=["extract_structure"],
                ).extract_structure,
            ) as extract_spy:
                incremental_family = build_repository_indexes_incremental(
                    current_source,
                    legacy_family,
                    repo_root=root,
                )
            full_family = build_repository_indexes(
                current_source,
                repo_root=root,
            )

        self.assertEqual(current_source, incremental_source)
        self.assertEqual(3, build_record_spy.call_count)
        self.assertEqual(full_family, incremental_family)
        self.assertEqual(1, extract_spy.call_count)

    def test_incremental_capability_graph_reselect_invalidates_previous_graph_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            write_capability_graph_fixture(root)
            previous_source = build_index(root)
            previous_family = build_repository_indexes(
                previous_source,
                repo_root=root,
            )

            old_graph_path = root / "generated" / "capability_graph.json"
            new_graph_path = root / "generated" / "capability_graph-v2.json"
            new_graph_path.write_text(
                old_graph_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            manifest_path = root / "capabilities" / "port.manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["projection"]["graph_json"] = "generated/capability_graph-v2.json"
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True),
                encoding="utf-8",
            )
            current_source = build_index(root)
            incremental_family = build_repository_indexes_incremental(
                current_source,
                previous_family,
                repo_root=root,
            )
            full_family = build_repository_indexes(
                current_source,
                repo_root=root,
            )

        self.assertEqual(full_family, incremental_family)
        old_graph_id = next(
            record["identity"]["id"]
            for record in current_source["records"]
            if record["identity"]["path"] == "generated/capability_graph.json"
        )
        new_graph_id = next(
            record["identity"]["id"]
            for record in current_source["records"]
            if record["identity"]["path"] == "generated/capability_graph-v2.json"
        )
        self.assertFalse(
            any(
                anchor["source_record_id"] == old_graph_id
                and anchor["parser_ref"] == "aoa-capability-graph@1"
                for anchor in incremental_family["anchor"]["entries"]
            )
        )
        self.assertTrue(
            any(
                anchor["source_record_id"] == new_graph_id
                and anchor["parser_ref"] == "aoa-capability-graph@1"
                for anchor in incremental_family["anchor"]["entries"]
            )
        )

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

    def test_source_heading_refs_share_the_canonical_markdown_parser(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            (root / "README.md").write_text(
                "# Visible\n\n```bash\n# shell comment\n```\n\n## Visible child\n",
                encoding="utf-8",
            )
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)

        record = next(
            entry for entry in source["records"] if entry["identity"]["path"] == "README.md"
        )
        source_id = record["identity"]["id"]
        advertised = {
            heading["anchor"] for heading in record["refs"]["heading_refs"]
        }
        indexed = {
            anchor["locator"]["fragment"]
            for anchor in family["anchor"]["entries"]
            if anchor["source_record_id"] == source_id
            and anchor["anchor_kind"] == "markdown_heading"
        }
        self.assertEqual({"visible", "visible-child"}, advertised)
        self.assertEqual(advertised, indexed)

    def test_attribute_calls_do_not_resolve_to_unrelated_methods(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            (root / "src" / "demo.py").write_text(
                "def render() -> str:\n"
                "    helper()\n"
                "    return '\\n'.join(['ok'])\n\n"
                "def helper() -> None:\n"
                "    pass\n",
                encoding="utf-8",
            )
            (root / "src" / "other.py").write_text(
                "class FakeThread:\n"
                "    def join(self) -> None:\n"
                "        pass\n",
                encoding="utf-8",
            )
            source = build_index(root)
            family = build_repository_indexes(source, repo_root=root)

        entities = {entry["semantic_key"]: entry for entry in family["entity"]["entries"]}
        calls = [
            relation
            for relation in family["relation"]["entries"]
            if relation["relation_kind"] == "calls"
        ]
        self.assertTrue(
            any(
                relation["from_id"] == entities["python:function:render"]["id"]
                and relation["to_id"] == entities["python:function:helper"]["id"]
                for relation in calls
            )
        )
        self.assertFalse(
            any(
                relation["from_id"] == entities["python:function:render"]["id"]
                and relation["to_id"] == entities["python:method:FakeThread.join"]["id"]
                for relation in calls
            )
        )

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
        artifact_ids = {entry["id"] for entry in family["artifact"]["entries"]}
        self.assertIn(rename["object_id"], lifecycle["object_ids"])
        self.assertNotIn(delete["object_id"], lifecycle["object_ids"])
        self.assertTrue(
            all(
                set(event["object_ids"]).issubset(artifact_ids)
                for event in family["event"]["entries"]
            )
        )
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

    def test_event_history_preserves_lineage_when_a_path_is_reused(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(
                ("git", "config", "user.email", "kag@example.test"),
                cwd=root,
                check=True,
            )
            reused = root / "reused.txt"
            reused.write_text("first\n", encoding="utf-8")
            subprocess.run(("git", "add", "reused.txt"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "initial generation"), cwd=root, check=True)
            reused.unlink()
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "delete generation"), cwd=root, check=True)
            reused.write_text("second\n", encoding="utf-8")
            subprocess.run(("git", "add", "reused.txt"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "second generation"), cwd=root, check=True)

            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)

        current_id = next(
            record["identity"]["id"]
            for record in source_index["records"]
            if record["identity"]["path"] == "reused.txt"
        )
        initial = next(
            event for event in family["event"]["entries"] if event["label"] == "initial generation"
        )
        deleted = next(
            event for event in family["event"]["entries"] if event["label"] == "delete generation"
        )
        snapshot = next(
            event
            for event in family["event"]["entries"]
            if event["event_kind"] == "repository_snapshot_change_set"
        )
        initial_id = initial["changes"][0]["object_id"]
        self.assertNotEqual(initial_id, current_id)
        self.assertEqual(initial_id, deleted["changes"][0]["object_id"])
        self.assertEqual(current_id, snapshot["changes"][0]["object_id"])
        self.assertEqual([], initial["object_ids"])
        self.assertEqual([], deleted["object_ids"])
        self.assertEqual([current_id], snapshot["object_ids"])

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
                    "AOA_REPO_LOCAL_KAG_EVENT_HISTORY_REF": feature_sha,
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

    def test_event_index_matches_after_multi_commit_feature_is_squashed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.email", "kag@example.test"), cwd=root, check=True)
            write_fixture(root)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "base"), cwd=root, check=True)
            base_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(("git", "checkout", "-qb", "feature"), cwd=root, check=True)
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\nFeature one.\n",
                encoding="utf-8",
            )
            reused = root / "reused.txt"
            reused.write_text("generation one\n", encoding="utf-8")
            subprocess.run(("git", "add", "README.md", "reused.txt"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "feature one"), cwd=root, check=True)
            reused.unlink()
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "remove reused path"), cwd=root, check=True)
            readme.write_text(
                readme.read_text(encoding="utf-8") + "Feature two.\n",
                encoding="utf-8",
            )
            reused.write_text("generation two\n", encoding="utf-8")
            subprocess.run(("git", "add", "README.md", "reused.txt"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "feature two"), cwd=root, check=True)
            feature_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            feature_source = build_index(root, history_ref=base_sha)
            feature_family = build_repository_indexes(
                feature_source,
                repo_root=root,
                history_ref=base_sha,
                event_history_ref=base_sha,
            )

            subprocess.run(("git", "checkout", "-q", "main"), cwd=root, check=True)
            subprocess.run(("git", "merge", "--squash", "feature"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "squashed feature"), cwd=root, check=True)
            squash_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            squash_source = build_index(root, history_ref=squash_sha)
            squash_family = build_repository_indexes(
                squash_source,
                repo_root=root,
                history_ref=squash_sha,
            )

        self.assertEqual(feature_source, squash_source)
        self.assertEqual(feature_family, squash_family)
        feature_artifact_ids = {
            entry["id"] for entry in feature_family["artifact"]["entries"]
        }
        snapshot = next(
            event
            for event in feature_family["event"]["entries"]
            if event["event_kind"] == "repository_snapshot_change_set"
        )
        self.assertTrue(set(snapshot["object_ids"]).issubset(feature_artifact_ids))

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
        self.assertTrue(
            _is_repo_local_meta_index_payload(
                {"schema_version": "aoa-repo-local-kag-family-manifest-v3"}
            )
        )
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

    def test_family_validation_rejects_dangling_event_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
        family["event"]["entries"][0]["object_ids"] = [
            "aoa:missing:artifact:missing:0000"
        ]
        family["event"]["index_identity"]["content_digest"] = (
            repo_local_kag_index_digest_without_self(family["event"])
        )

        with self.assertRaisesRegex(ValidationError, "event object ids"):
            validate_repo_local_kag_repository_index_family(
                family,
                source_payload=source_index,
                label="repository family",
            )

    def test_family_validation_rejects_heading_ref_without_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
        family["anchor"]["entries"] = [
            entry
            for entry in family["anchor"]["entries"]
            if entry["anchor_kind"] != "markdown_heading"
        ]
        family["anchor"]["summary"]["entry_count"] = len(
            family["anchor"]["entries"]
        )
        family["anchor"]["index_identity"]["content_digest"] = (
            repo_local_kag_index_digest_without_self(family["anchor"])
        )

        with self.assertRaisesRegex(ValidationError, "source heading refs"):
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

    def test_query_exact_indexes_event_evidence_and_dashboard_readiness_path(self) -> None:
        immutable_ref = "f46f146cc79a26fa81ad0f400b9c5774df293e57"
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            dashboard_map = root / "generated" / "local_kag_provider_map.json"
            dashboard_map.parent.mkdir(parents=True, exist_ok=True)
            dashboard_map.write_text(
                '{"repo":"aoa-dashboard","provider_status":"source_preparation"}\n',
                encoding="utf-8",
            )
            source_index = build_index(root)
            family = build_repository_indexes(source_index, repo_root=root)
            event = family["event"]["entries"][0]
            event["evidence_refs"] = [{"kind": "git_commit", "ref": immutable_ref}]
            query = RepoKagQuery(source_index, family)

        event_hits = query.exact(immutable_ref, node_classes={"event"})
        self.assertEqual(1, len(event_hits))
        self.assertEqual(
            [{"kind": "git_commit", "ref": immutable_ref}],
            event_hits[0]["record"]["evidence_refs"],
        )
        handle = query.projection_handle(event["id"])
        self.assertIsNotNone(handle)
        self.assertEqual(
            [{"kind": "git_commit", "ref": immutable_ref}],
            handle["evidence_refs"],
        )

        dashboard_hits = query.exact("generated/local_kag_provider_map.json")
        dashboard_hit = next(
            hit for hit in dashboard_hits if hit["node_class"] == "artifact"
        )
        self.assertEqual(
            "generated/local_kag_provider_map.json",
            dashboard_hit["path"],
        )
        self.assertEqual([], query.exact("helper python_function"))

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
