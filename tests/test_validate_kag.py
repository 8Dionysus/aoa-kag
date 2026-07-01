from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import validate_kag
from scripts.validators import example_contracts, local_contracts, local_kag_subtree
from scripts.validators.examples import bridge_examples
from scripts.validators.orchestration import runner
from scripts.validators.orchestration import static_surfaces as static_surface_runner


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class ValidateKagTestCase(unittest.TestCase):
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
        self.assertEqual("source_preparation", course["provider_status"])
        self.assertEqual(
            "/srv/AbyssOS/connectors/aoa-course-connector",
            course["root"],
        )
        self.assertIn("BOUNDARIES.md", course["candidate_source_surfaces"])
        self.assertIn(
            "connector/SOURCE_POLICY.md",
            course["candidate_source_surfaces"],
        )
        self.assertIn(
            "connector/STORAGE_POLICY.md",
            course["candidate_source_surfaces"],
        )

    def test_local_kag_readiness_rejects_source_preparation_provider_home_paths(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        for entry in broken_payload["os_surfaces"]:
            if entry["surface_id"] == "connectors/aoa-course-connector":
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

    def test_provider_home_skips_repo_local_source_surface_index_record(self) -> None:
        original = local_kag_subtree.read_json

        def read_json_without_repo_local_source_index(path: Path) -> object:
            if Path(path).name == local_kag_subtree.REPO_LOCAL_SOURCE_INDEX_NAME:
                raise AssertionError("provider-home validation must not read repo-local source index")
            return original(path)

        with patch.object(local_kag_subtree, "read_json", side_effect=read_json_without_repo_local_source_index):
            local_kag_subtree._validate_provider_home("aoa-kag", REPO_ROOT)

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
        ):
            with redirect_stderr(stderr):
                self.assertEqual(0, runner.main())

        expected = [
            "static-surfaces",
            "registry-context",
            "manifest-contracts",
            "expected-payloads",
            "generated-text",
            "generated-structures",
            "examples",
            "success-status",
        ]
        self.assertEqual(expected, calls)
        self.assertEqual(
            "".join(f"[validate-kag] {phase}\n" for phase in expected),
            stderr.getvalue(),
        )

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

    def test_local_kag_progress_wrapper_enables_progress_mode(self) -> None:
        with patch.object(local_kag_subtree, "validate_local_kag_subtree_contract") as validate:
            local_kag_subtree.validate_local_kag_subtree_contract_with_progress()

        validate.assert_called_once_with(progress=True)


if __name__ == "__main__":
    unittest.main()
