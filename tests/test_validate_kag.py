from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import validate_kag
from scripts.validators import example_contracts, local_contracts, local_kag_subtree
from scripts.validators.examples import bridge_examples


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

    def test_local_kag_readiness_rejects_missing_source_ready_provider(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        for entry in broken_payload["repos"]:
            if entry["repo"] == "aoa-skills":
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

    def test_local_kag_readiness_keeps_contract_when_host_roots_are_unavailable(self) -> None:
        payload = load_json(validate_kag.LOCAL_KAG_READINESS_MANIFEST_PATH)
        assert isinstance(payload, dict)

        with patch.object(Path, "is_dir", return_value=False):
            with patch.object(local_kag_subtree, "STRICT_OS_SURFACE_ROOTS", False):
                local_kag_subtree._validate_os_surfaces(payload)


if __name__ == "__main__":
    unittest.main()
