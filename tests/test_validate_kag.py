from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import nullcontext, redirect_stderr
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import validate_kag
from scripts.validators import example_contracts, local_contracts, local_kag_subtree, repo_local_kag_index
from scripts.validators.examples import bridge_examples
from scripts.validators.orchestration import runner
from scripts.validators.orchestration import static_surfaces as static_surface_runner
from scripts.validators.projection import registry as registry_projection


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class ValidateKagTestCase(unittest.TestCase):
    def test_provider_audit_workers_fail_closed_outside_bounded_choices(self) -> None:
        for value in ("", "0", "4", "many"):
            with self.subTest(value=value), patch.dict(
                local_kag_subtree.os.environ,
                {local_kag_subtree.PROVIDER_AUDIT_WORKERS_ENV: value},
            ):
                with self.assertRaisesRegex(
                    local_kag_subtree.ValidationError,
                    "must be 1, 2, or 3",
                ):
                    local_kag_subtree._provider_audit_workers()

    def test_parallel_provider_audit_keeps_canonical_parent_fan_in(self) -> None:
        owner_root = REPO_ROOT.resolve()
        result = {
            "ok": True,
            "owner": "aoa-kag",
            "owner_root": owner_root.as_posix(),
            "family_content_digest": "a" * 64,
            "owner_payload": {"repo": "aoa-kag"},
            "owner_timing": {"owner": "aoa-kag"},
            "nested_timings": [],
            "provider_timing": {
                "event": "validation-timing",
                "timing_schema_version": "aoa-kag-validation-timing-v1",
                "component_type": "provider-home",
                "component_id": "aoa-kag",
                "duration_ms": 1,
                "cpu_user_ms": 1,
                "cpu_system_ms": 0,
                "process_peak_rss_kib": 1,
                "status": "passed",
            },
            "error": "",
        }

        class FakeExecutor:
            def __init__(self, *, max_workers: int, mp_context: object) -> None:
                self.max_workers = max_workers
                self.mp_context = mp_context

            def __enter__(self):
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def map(self, _function, tasks, *, chunksize: int):
                self.assert_equal(chunksize, 1)
                self.assert_equal(list(tasks)[0][0], "aoa-kag")
                return [copy.deepcopy(result)]

            @staticmethod
            def assert_equal(left: object, right: object) -> None:
                if left != right:
                    raise AssertionError(f"{left!r} != {right!r}")

        readiness = {
            "repos": [{"repo": "aoa-kag", "provider_status": "provider_ready"}]
        }
        with patch.dict(
            local_kag_subtree.os.environ,
            {local_kag_subtree.PROVIDER_AUDIT_WORKERS_ENV: "2"},
        ), patch.object(
            local_kag_subtree,
            "PROVIDER_REPO_ROOTS",
            {"aoa-kag": owner_root},
        ), patch.object(
            local_kag_subtree.multiprocessing,
            "get_all_start_methods",
            return_value=["fork"],
        ), patch.object(
            local_kag_subtree.multiprocessing,
            "get_context",
            return_value=object(),
        ), patch.object(
            local_kag_subtree,
            "ProcessPoolExecutor",
            FakeExecutor,
        ), patch.object(
            local_kag_subtree,
            "_publish_process_validation_timing",
        ) as publish, patch(
            "scripts.generate_repo_local_kag_coverage.prebuild_provider_coverage_owner_result"
        ) as prebuild:
            local_kag_subtree._validate_provider_ready_surfaces(readiness)

        publish.assert_called_once_with(result["provider_timing"])
        prebuild.assert_called_once_with(
            "aoa-kag",
            owner_root,
            family_content_digest="a" * 64,
            owner_payload={"repo": "aoa-kag"},
            owner_timing={"owner": "aoa-kag"},
        )

    def test_local_kag_schema_def_validator_is_reused_by_schema_identity(self) -> None:
        payload = load_json(REPO_ROOT / "kag" / "manifest.json")
        local_kag_subtree._cached_local_kag_schema_def_validator.cache_clear()
        with patch.dict(
            local_kag_subtree.os.environ,
            {local_kag_subtree.FORCE_COLD_SCHEMA_COMPILATION_ENV: "0"},
        ), patch.object(
            local_kag_subtree,
            "_build_local_kag_schema_def_validator",
            wraps=local_kag_subtree._build_local_kag_schema_def_validator,
        ) as build_validator:
            for _ in range(2):
                local_kag_subtree._validate_payload_against_schema_def(
                    payload,
                    def_name="localManifest",
                    label="local manifest",
                )

        build_validator.assert_called_once()

    def test_local_kag_schema_def_validator_has_forced_cold_path(self) -> None:
        payload = load_json(REPO_ROOT / "kag" / "manifest.json")
        with patch.dict(
            local_kag_subtree.os.environ,
            {local_kag_subtree.FORCE_COLD_SCHEMA_COMPILATION_ENV: "1"},
        ), patch.object(
            local_kag_subtree,
            "_build_local_kag_schema_def_validator",
            wraps=local_kag_subtree._build_local_kag_schema_def_validator,
        ) as build_validator:
            for _ in range(2):
                local_kag_subtree._validate_payload_against_schema_def(
                    payload,
                    def_name="localManifest",
                    label="local manifest",
                )

        self.assertEqual(2, build_validator.call_count)

    def test_local_kag_schema_def_validator_preserves_non_object_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_path = Path(temp_dir) / "local-kag-subtree.schema.json"
            schema_path.write_text("[]\n", encoding="utf-8")
            with patch.object(
                local_kag_subtree,
                "LOCAL_KAG_SUBTREE_SCHEMA_PATH",
                schema_path,
            ):
                with self.assertRaisesRegex(
                    local_kag_subtree.ValidationError,
                    "local KAG subtree schema must be a JSON object",
                ):
                    local_kag_subtree._validate_payload_against_schema_def(
                        {},
                        def_name="localManifest",
                        label="local manifest",
                    )

    def test_local_kag_schemas_share_runtime_source_vocabulary(self) -> None:
        subtree_schema = load_json(validate_kag.LOCAL_KAG_SUBTREE_SCHEMA_PATH)
        provider_map_schema = load_json(validate_kag.LOCAL_KAG_PROVIDER_MAP_SCHEMA_PATH)
        self.assertIn(
            "runtime_source",
            subtree_schema["$defs"]["sourceRef"]["properties"]["source_class"]["enum"],
        )
        self.assertIn(
            "runtime_source",
            provider_map_schema["$defs"]["sourceClass"]["enum"],
        )

    def patched_read_json(self, target_module, overrides: dict[Path, object]):
        original = target_module.read_json
        normalized_overrides: dict[Path, object] = {}
        for path, payload in overrides.items():
            resolved = Path(path).resolve()
            normalized_overrides[resolved] = copy.deepcopy(payload)
            for repo, root in (
                ("aoa-memo", target_module.AOA_MEMO_ROOT),
                ("aoa-evals", target_module.AOA_EVALS_ROOT),
            ):
                try:
                    relative_path = resolved.relative_to(root.resolve()).as_posix()
                except ValueError:
                    continue
                for alias in target_module.COMPATIBILITY_REF_ALIASES.get(repo, {}).get(
                    relative_path,
                    (),
                ):
                    normalized_overrides[(root / alias).resolve()] = copy.deepcopy(payload)

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized_overrides:
                return copy.deepcopy(normalized_overrides[resolved])
            return original(path)

        return patch.object(target_module, "read_json", side_effect=side_effect)

    def registry_manifest_surfaces(self) -> dict[str, dict[str, object]]:
        registry_manifest_payload = validate_kag.read_json(validate_kag.REGISTRY_MANIFEST_PATH)
        return validate_kag.validate_registry_payload(
            registry_manifest_payload,
            label="registry manifest",
        )

    def test_registry_payload_rejects_artifact_identity_drift(self) -> None:
        payload = load_json(validate_kag.REGISTRY_MANIFEST_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        artifact_identity = copy.deepcopy(broken_payload["artifact_identity"])
        assert isinstance(artifact_identity, dict)
        artifact_identity["artifact_class"] = "wrong_registry_bundle"
        broken_payload["artifact_identity"] = artifact_identity

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_registry_payload(
                broken_payload,
                label="registry manifest",
            )

        self.assertIn("artifact_identity", str(context.exception))

    def test_validate_antifragility_stress_surfaces_rejects_empty_example_glob(self) -> None:
        with patch.object(local_contracts, "PROJECTION_HEALTH_RECEIPT_EXAMPLE_PATHS", ()):
            with self.assertRaises(validate_kag.ValidationError) as context:
                local_contracts.validate_antifragility_stress_surfaces()

        self.assertIn("projection_health_receipt*.example.json", str(context.exception))

    def test_bridge_envelope_example_rejects_non_tos_tos_refs(self) -> None:
        example_payload = load_json(validate_kag.BRIDGE_ENVELOPE_EXAMPLE_PATH)
        assert isinstance(example_payload, dict)
        broken_payload = copy.deepcopy(example_payload)
        broken_payload["tos_refs"][0] = (
            "aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/bridge.kag-lift.example.json"
        )

        with self.patched_read_json(
            bridge_examples,
            {
                validate_kag.BRIDGE_ENVELOPE_EXAMPLE_PATH: broken_payload,
            },
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                example_contracts.validate_bridge_envelope_example()

        self.assertIn("tos_refs[0]", str(context.exception))

    def test_bridge_envelope_example_rejects_non_memo_memory_refs(self) -> None:
        example_payload = load_json(validate_kag.BRIDGE_ENVELOPE_EXAMPLE_PATH)
        assert isinstance(example_payload, dict)
        broken_payload = copy.deepcopy(example_payload)
        broken_payload["memory_refs"][0] = "Tree-of-Sophia/ToS/doctrine/NODE_CONTRACT.md"

        with self.patched_read_json(
            bridge_examples,
            {
                validate_kag.BRIDGE_ENVELOPE_EXAMPLE_PATH: broken_payload,
            },
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                example_contracts.validate_bridge_envelope_example()

        self.assertIn("memory_refs[0]", str(context.exception))

    def test_local_kag_example_rejects_edge_without_local_node_target(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_SUBTREE_EXAMPLE_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        edge = broken_payload["records"]["edges"][0]
        edge["to_id"] = "node:missing"

        with self.patched_read_json(
            local_kag_subtree,
            {
                validate_kag.LOCAL_KAG_SUBTREE_EXAMPLE_PATH: broken_payload,
            },
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                local_kag_subtree.validate_local_kag_subtree_contract()

        self.assertIn("to_id", str(context.exception))

    def test_local_kag_schema_requires_freshness_checked_ref(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_SUBTREE_EXAMPLE_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        receipt = broken_payload["records"]["receipts"][0]
        freshness = receipt["freshness"]
        assert isinstance(freshness, dict)
        freshness.pop("checked_ref")

        with self.patched_read_json(
            local_kag_subtree,
            {
                validate_kag.LOCAL_KAG_SUBTREE_EXAMPLE_PATH: broken_payload,
            },
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                local_kag_subtree.validate_local_kag_subtree_contract()

        self.assertIn("checked_ref", str(context.exception))

    def test_local_kag_rejects_strict_checked_ref_outside_source_refs(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_SUBTREE_EXAMPLE_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        receipt = broken_payload["records"]["receipts"][0]
        freshness = receipt["freshness"]
        assert isinstance(freshness, dict)
        checked_ref = freshness["checked_ref"]
        receipt["source_refs"] = [
            source_ref
            for source_ref in receipt["source_refs"]
            if source_ref.get("path") != checked_ref
        ]

        with self.patched_read_json(
            local_kag_subtree,
            {
                validate_kag.LOCAL_KAG_SUBTREE_EXAMPLE_PATH: broken_payload,
            },
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                local_kag_subtree.validate_local_kag_subtree_contract()

        self.assertIn("freshness.checked_ref must be listed in source_refs", str(context.exception))

    def test_local_kag_allows_strict_checked_ref_via_builder_surface(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_SUBTREE_EXAMPLE_PATH)
        assert isinstance(payload, dict)
        receipt = copy.deepcopy(payload["records"]["receipts"][0])
        builder = receipt["builder"]
        freshness = receipt["freshness"]
        assert isinstance(builder, dict)
        assert isinstance(freshness, dict)
        freshness["checked_ref"] = builder["surface"]
        receipt["source_refs"] = [
            source_ref
            for source_ref in receipt["source_refs"]
            if source_ref.get("path") != freshness["checked_ref"]
        ]

        local_kag_subtree._validate_checked_ref_is_source_linked(
            receipt,
            label="local KAG subtree example",
        )

    def test_local_kag_allows_strict_checked_ref_via_local_control_ref(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_SUBTREE_EXAMPLE_PATH)
        assert isinstance(payload, dict)
        receipt = copy.deepcopy(payload["records"]["receipts"][0])
        freshness = receipt["freshness"]
        assert isinstance(freshness, dict)
        freshness["checked_ref"] = "kag/manifest.json"
        receipt["source_refs"] = [
            source_ref
            for source_ref in receipt["source_refs"]
            if source_ref.get("path") != freshness["checked_ref"]
        ]

        local_kag_subtree._validate_checked_ref_is_source_linked(
            receipt,
            label="local KAG subtree example",
        )

    def test_local_kag_readiness_rejects_missing_direct_repo(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        broken_payload["repos"] = [
            entry for entry in broken_payload["repos"] if entry["repo"] != "aoa-stats"
        ]

        with self.patched_read_json(
            local_kag_subtree,
            {
                validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH: broken_payload,
            },
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                local_kag_subtree.validate_local_kag_subtree_contract()

        self.assertIn("every direct OS Abyss repo", str(context.exception))

    def test_local_kag_readiness_rejects_missing_os_surface(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        broken_payload["os_surfaces"] = [
            entry for entry in broken_payload["os_surfaces"] if entry["surface_id"] != ".aoa"
        ]

        with self.patched_read_json(
            local_kag_subtree,
            {
                validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH: broken_payload,
            },
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                local_kag_subtree.validate_local_kag_subtree_contract()

        self.assertIn("every OS surface class", str(context.exception))

    def test_local_kag_readiness_tracks_course_connector_surface(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        surfaces = {
            entry["surface_id"]: entry
            for entry in payload["os_surfaces"]
        }
        course = surfaces["connectors/aoa-course-connector"]

        self.assertEqual("connector_repo", course["surface_class"])
        self.assertEqual("provider_ready", course["provider_status"])
        self.assertEqual(
            "/srv/AbyssOS/connectors/aoa-course-connector",
            course["root"],
        )
        self.assertIn("kag/", course["source_home_surfaces"])
        self.assertIn("kag/manifest.json", course["candidate_source_surfaces"])
        self.assertIn("BOUNDARIES.md", course["candidate_source_surfaces"])
        self.assertIn(
            "connector/SOURCE_POLICY.md",
            course["candidate_source_surfaces"],
        )
        self.assertIn(
            "connector/STORAGE_POLICY.md",
            course["candidate_source_surfaces"],
        )

    def test_local_kag_readiness_keeps_agents_companion_only_boundary(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        surfaces = {
            entry["surface_id"]: entry
            for entry in payload["os_surfaces"]
        }
        agents = surfaces[".agents"]

        self.assertEqual(["AGENTS.md"], agents["source_home_surfaces"])
        self.assertEqual(["AGENTS.md"], agents["candidate_source_surfaces"])
        self.assertEqual([], agents["source_owned_exports"])
        self.assertNotIn(
            "Codex plugin discovery",
            agents["runtime_consumers"],
        )
        self.assertIn("no shared plugin marketplace", agents["surface_role"])

    def test_local_kag_readiness_rejects_source_preparation_provider_home_paths(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        for entry in broken_payload["os_surfaces"]:
            if entry["surface_id"] == ".agents":
                entry["candidate_source_surfaces"].append("kag/manifest.json")
                break

        with self.patched_read_json(
            local_kag_subtree,
            {
                validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH: broken_payload,
            },
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                local_kag_subtree.validate_local_kag_subtree_contract()

        self.assertIn("provider-home paths", str(context.exception))

    def test_local_kag_readiness_rejects_untracked_live_connector_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            connectors_root = Path(tmpdir) / "connectors"
            (connectors_root / "aoa-demo-connector" / ".git").mkdir(parents=True)

            with patch.object(local_kag_subtree, "STRICT_OS_SURFACE_ROOTS", True):
                with patch.dict(
                    local_kag_subtree.EXPECTED_OS_SURFACE_ROOTS,
                    {"connectors": connectors_root},
                ):
                    with self.assertRaises(validate_kag.ValidationError) as context:
                        local_kag_subtree._validate_live_connector_surfaces(
                            {"connectors"}
                        )

        self.assertIn("live connector repos", str(context.exception))

    def test_local_kag_readiness_rejects_untracked_live_os_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            os_root = Path(tmpdir)
            (os_root / "aoa-demo" / ".git").mkdir(parents=True)

            with patch.object(local_kag_subtree, "OS_ABYSS_ROOT", os_root):
                with patch.object(local_kag_subtree, "STRICT_OS_SURFACE_ROOTS", True):
                    with self.assertRaises(validate_kag.ValidationError) as context:
                        local_kag_subtree._validate_live_canonical_os_owner_surfaces(
                            {"aoa-kag"},
                            set(),
                        )

        self.assertIn("live canonical OS repo roots", str(context.exception))

    def test_local_kag_readiness_allows_source_preparation_live_connector_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            os_root = Path(tmpdir)
            (os_root / "connectors" / "aoa-demo-connector" / ".git").mkdir(parents=True)

            with patch.object(local_kag_subtree, "OS_ABYSS_ROOT", os_root):
                with patch.object(local_kag_subtree, "STRICT_OS_SURFACE_ROOTS", True):
                    local_kag_subtree._validate_live_canonical_os_owner_surfaces(
                        {"aoa-kag"},
                        {"connectors/aoa-demo-connector"},
                    )

    def test_local_kag_readiness_ignores_worktree_repo_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            os_root = Path(tmpdir)
            (os_root / ".worktrees" / "aoa-demo" / ".git").mkdir(parents=True)

            with patch.object(local_kag_subtree, "OS_ABYSS_ROOT", os_root):
                with patch.object(local_kag_subtree, "STRICT_OS_SURFACE_ROOTS", True):
                    local_kag_subtree._validate_live_canonical_os_owner_surfaces(
                        set(),
                        set(),
                    )

    def test_local_kag_readiness_ignores_linked_worktree_git_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            os_root = Path(tmpdir)
            repo_root = os_root / "aoa-demo"
            repo_root.mkdir()
            (repo_root / ".git").write_text(
                "gitdir: ../.worktrees/aoa-demo/.git\n",
                encoding="utf-8",
            )

            with patch.object(local_kag_subtree, "OS_ABYSS_ROOT", os_root):
                with patch.object(local_kag_subtree, "STRICT_OS_SURFACE_ROOTS", True):
                    local_kag_subtree._validate_live_canonical_os_owner_surfaces(
                        set(),
                        set(),
                    )

    def test_local_kag_readiness_rejects_missing_source_ready_provider(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        for entry in broken_payload["repos"]:
            if entry["repo"] == "8Dionysus":
                entry["provider_status"] = "candidate"
                break

        with self.patched_read_json(
            local_kag_subtree,
            {
                validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH: broken_payload,
            },
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                local_kag_subtree.validate_local_kag_subtree_contract()

        self.assertIn("source-ready provider repo", str(context.exception))

    def test_local_kag_readiness_keeps_unadmitted_owners_in_source_preparation(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        for repo in ("ATM10-Agent", "aoa-models"):
            with self.subTest(repo=repo):
                row = next(entry for entry in payload["repos"] if entry["repo"] == repo)
                self.assertEqual("source_preparation", row["provider_status"])
                self.assertEqual([], row["source_owned_exports"])
                self.assertEqual([], row["first_record_classes"])

    def test_local_kag_readiness_rejects_unadmitted_owner_promotion(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        for repo in ("ATM10-Agent", "aoa-models"):
            candidate = copy.deepcopy(broken_payload)
            next(entry for entry in candidate["repos"] if entry["repo"] == repo)[
                "provider_status"
            ] = "provider_ready"
            with self.subTest(repo=repo), self.patched_read_json(
                local_kag_subtree,
                {validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH: candidate},
            ):
                with self.assertRaises(validate_kag.ValidationError) as context:
                    local_kag_subtree.validate_local_kag_subtree_local_contract()
                self.assertIn("must remain source_preparation", str(context.exception))

    def test_local_kag_provider_map_schema_rejects_invalid_repo_index_status(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        broken_payload["providers"][0]["repo_local_index"]["status"] = "ready"

        with self.assertRaises(validate_kag.ValidationError) as context:
            registry_projection.validate_local_kag_provider_map_payload(
                broken_payload,
                label="generated local KAG provider map",
            )

        self.assertIn("repo_local_index", str(context.exception))

    def test_local_kag_provider_map_accepts_v1_without_common_profiles(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(payload, dict)
        compatible_payload = copy.deepcopy(payload)
        compatible_payload.pop("provider_common_surface_profiles", None)
        for provider in compatible_payload["providers"]:
            repo = provider["repo"]
            provider["repo_local_index"].pop("common_surface_profile", None)
            compatible_payload["provider_repo_local_indexes"][repo].pop(
                "common_surface_profile",
                None,
            )
        handoff = compatible_payload["mcp_handoff"]
        handoff["resource_templates"] = [
            template
            for template in handoff["resource_templates"]
            if template["uri_template"] != "aoa-kag://providers/{repo}/common-surface-profile"
        ]

        registry_projection.validate_local_kag_provider_map_payload(
            compatible_payload,
            label="compatible local KAG provider map",
        )

    def test_local_kag_provider_map_rejects_retired_mcp_resource_template(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        broken_payload["mcp_handoff"]["resource_templates"].append(
            {
                "uri_template": "aoa-kag://providers/{repo}/common-surface-profile",
                "source": (
                    "aoa-kag/generated/local_kag_provider_map.min.json"
                    "#/provider_common_surface_profiles/{repo}"
                ),
            }
        )

        with self.assertRaises(validate_kag.ValidationError) as context:
            registry_projection.validate_local_kag_provider_map_payload(
                broken_payload,
                label="generated local KAG provider map",
            )

        self.assertIn(
            "unknown MCP resource templates",
            str(context.exception),
        )

    def test_local_kag_provider_map_rejects_empty_common_profiles(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        broken_payload["provider_common_surface_profiles"] = {}

        with self.assertRaises(validate_kag.ValidationError) as context:
            registry_projection.validate_local_kag_provider_map_payload(
                broken_payload,
                label="generated local KAG provider map",
            )

        self.assertIn(
            "provider_common_surface_profiles must cover provider repos exactly",
            str(context.exception),
        )

    def test_repo_local_kag_coverage_accepts_v1_without_common_profiles(self) -> None:
        payload = load_json(repo_local_kag_index.REPO_LOCAL_KAG_COVERAGE_PATH)
        assert isinstance(payload, dict)
        compatible_payload = copy.deepcopy(payload)
        for owner in compatible_payload["owners"]:
            owner.pop("common_surface_profile", None)

        repo_local_kag_index.validate_repo_local_kag_coverage_payload(
            compatible_payload,
            label="compatible repo-local KAG coverage",
        )

    def test_repo_local_kag_coverage_rejects_partial_portable_rollout(self) -> None:
        payload = load_json(repo_local_kag_index.REPO_LOCAL_KAG_COVERAGE_PATH)
        assert isinstance(payload, dict)
        partial_payload = copy.deepcopy(payload)
        partial_payload["coverage_summary"]["aggregate_budget_state"] = "partial"

        with self.assertRaises(validate_kag.ValidationError) as context:
            repo_local_kag_index.validate_repo_local_kag_coverage_payload(
                partial_payload,
                label="partial repo-local KAG coverage",
            )

        self.assertIn(
            "portable aggregate budget summary is invalid",
            str(context.exception),
        )

    def test_repo_local_kag_coverage_drift_reports_first_difference(self) -> None:
        payload = load_json(repo_local_kag_index.REPO_LOCAL_KAG_COVERAGE_PATH)
        assert isinstance(payload, dict)
        expected = copy.deepcopy(payload)
        expected["owners"][0]["coverage"]["documents"] += 1

        with patch.object(
            repo_local_kag_index,
            "build_provider_coverage",
            return_value=expected,
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                repo_local_kag_index.validate_repo_local_kag_coverage_generated_payload()

        self.assertIn(
            "$.owners[0].coverage.documents",
            str(context.exception),
        )
        self.assertIn("actual=", str(context.exception))
        self.assertIn("expected=", str(context.exception))

    def test_local_kag_provider_map_rejects_missing_mcp_resource_template(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        handoff = broken_payload["mcp_handoff"]
        handoff["resource_templates"] = [
            template
            for template in handoff["resource_templates"]
            if template["uri_template"] != "aoa-kag://records/{qualified_id}"
        ]

        with self.assertRaises(validate_kag.ValidationError) as context:
            registry_projection.validate_local_kag_provider_map_payload(
                broken_payload,
                label="generated local KAG provider map",
            )

        self.assertIn("missing required MCP resource templates", str(context.exception))

    def test_local_kag_provider_map_rejects_mcp_package_surface_drift(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        handoff = broken_payload["mcp_handoff"]
        handoff["package_surfaces"] = [
            surface
            for surface in handoff["package_surfaces"]
            if surface != "src/aoa_kag_mcp/"
        ]

        with self.assertRaises(validate_kag.ValidationError) as context:
            registry_projection.validate_local_kag_provider_map_payload(
                broken_payload,
                label="generated local KAG provider map",
            )

        self.assertIn("package_surfaces", str(context.exception))

    def test_local_kag_provider_map_rejects_mcp_runtime_route_drift(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        broken_payload["mcp_handoff"]["runtime_state_route"] = "aoa-kag runtime"

        with self.assertRaises(validate_kag.ValidationError) as context:
            registry_projection.validate_local_kag_provider_map_payload(
                broken_payload,
                label="generated local KAG provider map",
            )

        self.assertIn("runtime_state_route", str(context.exception))

    def test_local_kag_provider_map_rejects_repo_local_index_mismatch(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        repo = broken_payload["providers"][0]["repo"]
        broken_payload["provider_repo_local_indexes"][repo]["coverage_owner_key"] = "other"

        with self.assertRaises(validate_kag.ValidationError) as context:
            registry_projection.validate_local_kag_provider_map_payload(
                broken_payload,
                label="generated local KAG provider map",
            )

        self.assertIn("repo_local_index must match provider_repo_local_indexes", str(context.exception))

    def test_local_kag_provider_roots_cover_source_ready_providers(self) -> None:
        self.assertEqual(
            local_kag_subtree.EXPECTED_PROVIDER_READY_REPOS,
            set(local_kag_subtree.PROVIDER_REPO_ROOTS),
        )
        for repo in local_kag_subtree.EXPECTED_PROVIDER_READY_REPOS:
            with self.subTest(repo=repo):
                self.assertEqual(
                    local_kag_subtree.KNOWN_REPO_ROOTS[repo],
                    local_kag_subtree.PROVIDER_REPO_ROOTS[repo],
                )

    def test_provider_home_validates_portable_repository_family(self) -> None:
        original = local_kag_subtree.read_json
        source_reads = 0
        manifest_reads = 0

        def read_json_with_source_count(path: Path) -> object:
            nonlocal manifest_reads, source_reads
            if Path(path).name == local_kag_subtree.REPO_LOCAL_SOURCE_INDEX_NAME:
                source_reads += 1
            if Path(path).name == local_kag_subtree.REPO_LOCAL_FAMILY_MANIFEST_NAME:
                manifest_reads += 1
            return original(path)

        with patch.object(local_kag_subtree, "read_json", side_effect=read_json_with_source_count):
            local_kag_subtree._validate_provider_home("aoa-kag", REPO_ROOT)
        self.assertEqual(0, source_reads)
        self.assertEqual(1, manifest_reads)

    def test_provider_home_keeps_portable_only_family_as_effective_index(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "portable-provider"
            kag_root = repo_root / "kag"
            kag_root.mkdir(parents=True)
            for filename in ("AGENTS.md", "README.md"):
                (kag_root / filename).write_text("# fixture\n", encoding="utf-8")
            (kag_root / "manifest.json").write_text(
                json.dumps(
                    {
                        "repo": "portable-provider",
                        "record_classes": sorted(
                            local_kag_subtree.REQUIRED_RECORD_CLASSES
                        ),
                    }
                ),
                encoding="utf-8",
            )
            for group_name in local_kag_subtree.PROVIDER_RECORD_DIRS:
                directory = kag_root / group_name
                directory.mkdir()
                if group_name == "indexes":
                    (directory / "index_family.manifest.json").write_text(
                        json.dumps(
                            {
                                "schema_version": (
                                    "aoa-repo-local-kag-family-manifest-v3"
                                ),
                                "family_identity": {
                                    "content_digest": "0" * 64,
                                },
                                "source_index_header": {
                                    "index_identity": {
                                        "local_id": (
                                            "index:repo-local:source-surfaces"
                                        ),
                                    },
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                else:
                    (directory / "fixture.json").write_text(
                        "{}\n",
                        encoding="utf-8",
                    )

            with patch.object(
                local_kag_subtree,
                "_validate_payload_against_schema_def",
            ), patch.object(
                local_kag_subtree,
                "_validate_source_refs_exist",
            ), patch.object(
                local_kag_subtree,
                "_validate_checked_ref_is_source_linked",
            ), patch.object(
                repo_local_kag_index,
                "repo_local_kag_validate_payload",
            ), patch.object(
                repo_local_kag_index,
                "load_repo_local_kag_repository_index_family_with_manifest",
                return_value=(
                    {},
                    {},
                    {"family_identity": {"content_digest": "0" * 64}},
                ),
            ), patch.object(
                local_kag_subtree,
                "_validate_record_links",
            ) as validate_links:
                local_kag_subtree._validate_provider_home(
                    "portable-provider",
                    repo_root,
                )

        packet = validate_links.call_args.args[0]
        indexes = packet["records"]["indexes"]
        self.assertEqual(1, len(indexes))
        self.assertEqual(
            "portable_family_manifest",
            indexes[0]["effective_index_surface"],
        )

    def test_record_links_accept_portable_family_effective_index(self) -> None:
        local_kag_subtree._validate_record_links(
            {
                "records": {
                    "nodes": [
                        {
                            "local_id": "node:fixture",
                            "record_class": "node",
                        }
                    ],
                    "edges": [
                        {
                            "local_id": "edge:fixture",
                            "record_class": "edge",
                            "from_id": "node:fixture",
                            "to_id": "node:fixture",
                            "edge_trace": ["fixture"],
                        }
                    ],
                    "indexes": [
                        {
                            "schema_version": (
                                "aoa-repo-local-kag-family-manifest-v3"
                            ),
                            "local_id": "index:repo-local:source-surfaces",
                            "record_class": "index",
                            "effective_index_surface": (
                                "portable_family_manifest"
                            ),
                            "portable_family_content_digest": "0" * 64,
                        }
                    ],
                    "projections": [
                        {
                            "local_id": "projection:fixture",
                            "record_class": "projection",
                            "source_record_ids": ["node:fixture"],
                        }
                    ],
                    "receipts": [
                        {
                            "local_id": "receipt:fixture",
                            "record_class": "receipt",
                            "fallback_route": "owner-review",
                        }
                    ],
                }
            }
        )

    def test_local_kag_readiness_keeps_contract_when_host_roots_are_unavailable(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)

        with patch.object(Path, "is_dir", return_value=False):
            with patch.object(local_kag_subtree, "STRICT_OS_SURFACE_ROOTS", False):
                local_kag_subtree._validate_os_surfaces(payload)

    def test_validate_kag_main_reports_phase_progress_to_stderr(self) -> None:
        calls: list[str] = []

        def mark(name: str, return_value: object = None):
            def side_effect(*_args: object, **_kwargs: object) -> object:
                calls.append(name)
                return copy.deepcopy(return_value)

            return side_effect

        stderr = io.StringIO()
        with patch.object(
            runner,
            "validate_static_surfaces",
            side_effect=mark("static-surfaces"),
        ), patch.object(
            runner,
            "validate_local_kag_provider_homes_contract_with_progress",
            side_effect=mark("os-wide-provider-homes"),
        ), patch.object(
            runner,
            "validate_repo_local_kag_os_wide_contract_with_progress",
            side_effect=mark("os-wide-provider-coverage"),
        ), patch.object(
            runner,
            "load_registry_context",
            side_effect=mark("registry-context", ({}, {}, [])),
        ), patch.object(
            runner,
            "validate_manifest_contracts",
            side_effect=mark("manifest-contracts"),
        ), patch.object(
            runner,
            "build_expected_payloads",
            side_effect=mark("expected-payloads", {"expected": {}}),
        ), patch.object(
            runner,
            "validate_generated_text_outputs",
            side_effect=mark("generated-text"),
        ), patch.object(
            runner,
            "validate_generated_structures",
            side_effect=mark("generated-structures", {"surface": {}}),
        ), patch.object(
            runner,
            "validate_examples",
            side_effect=mark("examples"),
        ), patch.object(
            runner,
            "print_success_status",
            side_effect=mark("success-status"),
        ), patch.object(
            runner,
            "print_os_wide_success_status",
            side_effect=mark("os-wide-success-status"),
        ), patch.object(
            runner,
            "provider_coverage_prebuild_scope",
            return_value=nullcontext(),
        ) as coverage_prebuild_scope:
            with redirect_stderr(stderr):
                self.assertEqual(0, runner.main(["--scope", "full"]))

        expected = [
            "static-surfaces",
            "os-wide-provider-homes",
            "os-wide-provider-coverage",
            "registry-context",
            "manifest-contracts",
            "expected-payloads",
            "generated-text",
            "generated-structures",
            "examples",
            "success-status",
            "os-wide-success-status",
        ]
        self.assertEqual(expected, calls)
        coverage_prebuild_scope.assert_called_once_with()
        self.assertEqual(
            "".join(
                f"[validate-kag] {phase}\n"
                for phase in (
                    "static-surfaces",
                    "os-wide-provider-homes",
                    "os-wide-provider-coverage",
                    "registry-context",
                    "manifest-contracts",
                    "expected-payloads",
                    "generated-text",
                    "generated-structures",
                    "examples",
                    "success-status",
                )
            ),
            stderr.getvalue(),
        )

    def test_validate_kag_scopes_keep_local_and_os_wide_execution_explicit(self) -> None:
        self.assertEqual("full", runner.parse_args([]).scope)

        with patch.object(runner, "validate_static_surfaces") as local_validate, patch.object(
            runner,
            "validate_local_kag_provider_homes_contract_with_progress",
        ) as provider_homes_validate, patch.object(
            runner,
            "validate_repo_local_kag_os_wide_contract_with_progress",
        ) as os_wide_validate, patch.object(
            runner,
            "load_registry_context",
            return_value=({}, {}, ["missing-provider-root"]),
        ), patch.object(
            runner,
            "print_success_status",
        ), patch.object(
            runner,
            "provider_coverage_prebuild_scope",
            return_value=nullcontext(),
        ) as coverage_prebuild_scope, redirect_stderr(io.StringIO()):
            self.assertEqual(0, runner.main(["--scope", "local"]))

        local_validate.assert_called_once_with()
        provider_homes_validate.assert_not_called()
        os_wide_validate.assert_not_called()
        coverage_prebuild_scope.assert_not_called()

        with patch.object(runner, "validate_static_surfaces") as local_validate, patch.object(
            runner,
            "validate_local_kag_provider_homes_contract_with_progress",
        ) as provider_homes_validate, patch.object(
            runner,
            "validate_repo_local_kag_os_wide_contract_with_progress",
        ) as os_wide_validate, patch.object(
            runner,
            "load_registry_context",
        ) as load_registry, patch.object(
            runner,
            "print_os_wide_success_status",
        ) as print_os_wide_status, patch.object(
            runner,
            "provider_coverage_prebuild_scope",
            return_value=nullcontext(),
        ) as coverage_prebuild_scope, redirect_stderr(io.StringIO()):
            self.assertEqual(0, runner.main(["--scope", "os-wide"]))

        local_validate.assert_not_called()
        load_registry.assert_not_called()
        provider_homes_validate.assert_called_once_with()
        os_wide_validate.assert_called_once_with()
        print_os_wide_status.assert_called_once_with()
        coverage_prebuild_scope.assert_called_once_with()

    def test_static_surfaces_reports_subphase_progress_to_stderr(self) -> None:
        calls: list[str] = []

        def check(name: str):
            def side_effect() -> None:
                calls.append(name)

            return side_effect

        phases = (
            ("local-route-surfaces", (check("nested-agents"), check("mechanics"))),
            ("core-kag-contracts", (check("provider-registry"),)),
        )
        stderr = io.StringIO()
        with patch.object(static_surface_runner, "STATIC_SURFACE_PHASES", phases):
            with redirect_stderr(stderr):
                static_surface_runner.validate_static_surfaces()

        self.assertEqual(
            ["nested-agents", "mechanics", "provider-registry"],
            calls,
        )
        self.assertEqual(
            (
                "[validate-kag:static] local-route-surfaces\n"
                "[validate-kag:static] core-kag-contracts\n"
            ),
            stderr.getvalue(),
        )

    def test_static_surfaces_keep_provider_homes_out_of_local_scope(self) -> None:
        checks = dict(static_surface_runner.STATIC_SURFACE_PHASES)[
            "core-local-kag-subtree"
        ]

        self.assertIn(
            local_kag_subtree.validate_local_kag_subtree_local_contract_with_progress,
            checks,
        )
        self.assertNotIn(
            local_kag_subtree.validate_local_kag_subtree_contract_with_progress,
            checks,
        )
        self.assertNotIn(
            local_kag_subtree.validate_local_kag_provider_homes_contract_with_progress,
            checks,
        )

    def test_local_kag_progress_wrapper_enables_progress_mode(self) -> None:
        with patch.object(local_kag_subtree, "validate_local_kag_subtree_contract") as validate:
            local_kag_subtree.validate_local_kag_subtree_contract_with_progress()

        validate.assert_called_once_with(progress=True)

    def test_local_kag_scope_wrappers_enable_progress_mode(self) -> None:
        with patch.object(
            local_kag_subtree,
            "validate_local_kag_subtree_local_contract",
        ) as validate_local:
            local_kag_subtree.validate_local_kag_subtree_local_contract_with_progress()
        validate_local.assert_called_once_with(progress=True)

        with patch.object(
            local_kag_subtree,
            "validate_local_kag_provider_homes_contract",
        ) as validate_provider_homes:
            local_kag_subtree.validate_local_kag_provider_homes_contract_with_progress()
        validate_provider_homes.assert_called_once_with(progress=True)

    def test_local_kag_compatibility_contract_keeps_both_scopes(self) -> None:
        readiness = {"repos": []}
        with patch.object(
            local_kag_subtree,
            "_validate_local_kag_subtree_local_contract",
            return_value=readiness,
        ) as validate_local, patch.object(
            local_kag_subtree,
            "_validate_provider_ready_surfaces",
        ) as validate_provider_homes:
            local_kag_subtree.validate_local_kag_subtree_contract(progress=True)

        validate_local.assert_called_once_with(progress=True)
        validate_provider_homes.assert_called_once_with(readiness, progress=True)

    def test_repo_local_index_progress_wrapper_enables_progress_mode(self) -> None:
        with patch.object(repo_local_kag_index, "validate_repo_local_kag_index_contract") as validate:
            repo_local_kag_index.validate_repo_local_kag_index_contract_with_progress()

        validate.assert_called_once_with(progress=True)

    def test_repo_local_index_scope_wrappers_enable_progress_mode(self) -> None:
        with patch.object(
            repo_local_kag_index,
            "validate_repo_local_kag_local_contract",
        ) as validate_local:
            repo_local_kag_index.validate_repo_local_kag_local_contract_with_progress()
        validate_local.assert_called_once_with(progress=True)

        with patch.object(
            repo_local_kag_index,
            "validate_repo_local_kag_os_wide_contract",
        ) as validate_os_wide:
            repo_local_kag_index.validate_repo_local_kag_os_wide_contract_with_progress()
        validate_os_wide.assert_called_once_with(progress=True)

    def test_repo_local_index_compatibility_contract_keeps_both_scopes(self) -> None:
        with patch.object(
            repo_local_kag_index,
            "validate_repo_local_kag_local_contract",
        ) as validate_local, patch.object(
            repo_local_kag_index,
            "validate_repo_local_kag_os_wide_contract",
        ) as validate_os_wide:
            repo_local_kag_index.validate_repo_local_kag_index_contract(progress=True)

        validate_local.assert_called_once_with(progress=True)
        validate_os_wide.assert_called_once_with(progress=True)


if __name__ == "__main__":
    unittest.main()
