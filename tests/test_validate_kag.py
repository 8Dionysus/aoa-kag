from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import validate_kag


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class ValidateKagTestCase(unittest.TestCase):
    def patched_read_json(self, overrides: dict[Path, object]):
        original = validate_kag.read_json
        normalized_overrides = {
            Path(path).resolve(): copy.deepcopy(payload)
            for path, payload in overrides.items()
        }

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized_overrides:
                return copy.deepcopy(normalized_overrides[resolved])
            return original(path)

        return patch.object(validate_kag, "read_json", side_effect=side_effect)

    def registry_manifest_surfaces(self) -> dict[str, dict[str, object]]:
        registry_manifest_payload = validate_kag.read_json(validate_kag.REGISTRY_MANIFEST_PATH)
        return validate_kag.validate_registry_payload(
            registry_manifest_payload,
            label="registry manifest",
        )

    def memo_kag_export_payload(self) -> dict[str, object]:
        return {
            "owner_repo": "aoa-memo",
            "kind": "bridge",
            "object_id": validate_kag.EXPECTED_MEMO_KAG_EXPORT_ENTRY_SURFACE["match_value"],
            "primary_question": "How should aoa-memo publish a bridge-bearing memory object for KAG use without turning memo into graph truth?",
            "summary_50": "Source-owned tiny export for a provenance-visible memo bridge.",
            "summary_200": "Source-owned tiny export capsule for the current reviewed memo bridge candidate so aoa-kag can consume one explicit bridge-bearing memory object by source-owned entry surface rather than by inferred graph meaning.",
            "source_inputs": copy.deepcopy(validate_kag.EXPECTED_MEMO_KAG_EXPORT_SOURCE_INPUTS),
            "entry_surface": copy.deepcopy(validate_kag.EXPECTED_MEMO_KAG_EXPORT_ENTRY_SURFACE),
            "section_handles": copy.deepcopy(validate_kag.EXPECTED_MEMO_KAG_EXPORT_SECTION_HANDLES),
            "direct_relations": copy.deepcopy(validate_kag.EXPECTED_MEMO_KAG_EXPORT_DIRECT_RELATIONS),
            "provenance_note": "Guide to source, not source replacement, built from the memo-owned bridge object plus explicit Tree-of-Sophia support refs.",
            "non_identity_boundary": "Source-owned memo export for KAG readiness; derived consumers must not treat this bridge capsule as normalized graph truth, routing authority, or replacement for Tree-of-Sophia-authored meaning.",
        }

    def test_projection_pairings_validator_failures_are_pairing_specific(self) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        dependencies = validate_kag.validate_source_owned_export_dependency_manifest(
            registry_surfaces
        )
        base_manifest = load_json(validate_kag.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH)
        assert isinstance(base_manifest, dict)

        missing_pairings = copy.deepcopy(base_manifest)
        missing_pairings.pop("projection_pairings", None)
        duplicate_pairings = copy.deepcopy(base_manifest)
        duplicate_pairings["projection_pairings"].append(
            copy.deepcopy(duplicate_pairings["projection_pairings"][0])
        )

        for label, manifest_override in (
            ("missing", missing_pairings),
            ("duplicate", duplicate_pairings),
        ):
            with self.subTest(case=label):
                with self.patched_read_json(
                    {
                        validate_kag.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH: manifest_override,
                    }
                ):
                    with self.assertRaises(validate_kag.ValidationError) as context:
                        validate_kag.validate_cross_source_node_projection_manifest(
                            registry_surfaces,
                            dependencies,
                        )
                self.assertIn("projection_pairings", str(context.exception))

    def test_counterpart_consumer_contract_validator_rejects_non_planned_status(self) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        example_payload = load_json(validate_kag.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH)
        assert isinstance(example_payload, dict)
        broken_payload = copy.deepcopy(example_payload)
        broken_payload["surface_status"] = "experimental"

        with self.patched_read_json(
            {
                validate_kag.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_counterpart_consumer_contract_example(
                    registry_surfaces
                )

        self.assertIn("surface_status", str(context.exception))

    def test_counterpart_consumer_contract_validator_rejects_missing_review_ref(self) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        example_payload = load_json(validate_kag.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH)
        assert isinstance(example_payload, dict)
        broken_payload = copy.deepcopy(example_payload)
        broken_payload.pop("federation_exposure_review_ref", None)

        with self.patched_read_json(
            {
                validate_kag.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_counterpart_consumer_contract_example(
                    registry_surfaces
                )

        self.assertIn("federation_exposure_review_ref", str(context.exception))

    def test_reasoning_handoff_validator_requires_counterpart_contract_refs(self) -> None:
        example_payload = load_json(validate_kag.REASONING_HANDOFF_EXAMPLE_PATH)
        assert isinstance(example_payload, dict)
        broken_payload = copy.deepcopy(example_payload)
        broken_payload["derived_surface_refs"] = [
            ref
            for ref in broken_payload["derived_surface_refs"]
            if ref != "docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md"
        ]

        with self.patched_read_json(
            {
                validate_kag.REASONING_HANDOFF_EXAMPLE_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_reasoning_handoff_example()

        self.assertIn("derived_surface_refs", str(context.exception))

    def test_counterpart_federation_exposure_review_manifest_rejects_order_drift(self) -> None:
        manifest_payload = load_json(
            validate_kag.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH
        )
        assert isinstance(manifest_payload, dict)
        broken_manifest = copy.deepcopy(manifest_payload)
        broken_manifest["review_bindings"] = list(reversed(broken_manifest["review_bindings"]))

        with self.patched_read_json(
            {
                validate_kag.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_counterpart_federation_exposure_review_manifest()

        self.assertIn("review_bindings", str(context.exception))

    def test_tiny_consumer_bundle_manifest_rejects_bundle_order_drift(self) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        manifest_payload = load_json(validate_kag.TINY_CONSUMER_BUNDLE_MANIFEST_PATH)
        assert isinstance(manifest_payload, dict)
        broken_manifest = copy.deepcopy(manifest_payload)
        broken_manifest["bundle_order"] = list(reversed(broken_manifest["bundle_order"]))

        with self.patched_read_json(
            {
                validate_kag.TINY_CONSUMER_BUNDLE_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_tiny_consumer_bundle_manifest(registry_surfaces)

        self.assertIn("bundle_order", str(context.exception))

    def test_tiny_consumer_bundle_pack_rejects_review_ref_drift(self) -> None:
        expected_payload = validate_kag.build_tiny_consumer_bundle_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["deferred_counterpart"]["federation_exposure_review_ref"] = (
            "generated/wrong_review.min.json"
        )

        with self.patched_read_json(
            {
                validate_kag.TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_tiny_consumer_bundle_pack(expected_payload)

        self.assertIn("deferred_counterpart", str(context.exception))

    def test_tiny_consumer_bundle_pack_rejects_deferred_counterpart_drift(self) -> None:
        expected_payload = validate_kag.build_tiny_consumer_bundle_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["deferred_counterpart"]["posture"] = "activated"

        with self.patched_read_json(
            {
                validate_kag.TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_tiny_consumer_bundle_pack(expected_payload)

        self.assertIn("deferred_counterpart", str(context.exception))

    def test_federation_spine_pack_rejects_counterpart_ref_exposure(self) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        expected_payload = validate_kag.build_federation_spine_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["repos"][0]["entry_surface_ref"] = "docs/COUNTERPART_EDGE_CONTRACTS.md"

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_federation_spine_pack(
                broken_payload,
                registry_surfaces,
                expected_payload,
            )

        self.assertIn("counterpart refs", str(context.exception))

    def test_cross_source_projection_pack_rejects_counterpart_ref_exposure(self) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        expected_payload = validate_kag.build_cross_source_node_projection_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["projections"][0]["retrieval_axis_ref"] = "docs/COUNTERPART_EDGE_CONTRACTS.md"

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_cross_source_node_projection_pack(
                broken_payload,
                registry_surfaces,
                expected_payload,
            )

        self.assertIn("counterpart refs", str(context.exception))

    def test_bridge_envelope_example_rejects_non_tos_tos_refs(self) -> None:
        example_payload = load_json(validate_kag.BRIDGE_ENVELOPE_EXAMPLE_PATH)
        assert isinstance(example_payload, dict)
        broken_payload = copy.deepcopy(example_payload)
        broken_payload["tos_refs"][0] = "aoa-memo/examples/bridge.kag-lift.example.json"

        with self.patched_read_json(
            {
                validate_kag.BRIDGE_ENVELOPE_EXAMPLE_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_bridge_envelope_example()

        self.assertIn("tos_refs[0]", str(context.exception))

    def test_bridge_envelope_example_rejects_non_memo_memory_refs(self) -> None:
        example_payload = load_json(validate_kag.BRIDGE_ENVELOPE_EXAMPLE_PATH)
        assert isinstance(example_payload, dict)
        broken_payload = copy.deepcopy(example_payload)
        broken_payload["memory_refs"][0] = "Tree-of-Sophia/docs/NODE_CONTRACT.md"

        with self.patched_read_json(
            {
                validate_kag.BRIDGE_ENVELOPE_EXAMPLE_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_bridge_envelope_example()

        self.assertIn("memory_refs[0]", str(context.exception))

    def test_reasoning_handoff_example_allows_missing_external_dependency_roots(self) -> None:
        missing_tos_root = REPO_ROOT / ".tmp" / "missing-Tree-of-Sophia"
        missing_memo_root = REPO_ROOT / ".tmp" / "missing-aoa-memo"

        with (
            patch.object(validate_kag, "TREE_OF_SOPHIA_ROOT", missing_tos_root),
            patch.object(validate_kag, "AOA_MEMO_ROOT", missing_memo_root),
        ):
            validate_kag.validate_reasoning_handoff_example()

    def test_return_regrounding_pack_rejects_drifted_bounded_output_contract(self) -> None:
        expected_payload = validate_kag.build_return_regrounding_pack_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["bounded_output_contract"]["proof_ownership"] = "allowed"

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_return_regrounding_pack(
                broken_payload,
                expected_payload,
            )

        self.assertIn("bounded_output_contract", str(context.exception))

    def test_return_regrounding_pack_rejects_local_kag_stronger_ref(self) -> None:
        expected_payload = validate_kag.build_return_regrounding_pack_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["modes"][2]["stronger_refs"][0] = "generated/federation_spine.min.json"

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_return_regrounding_pack(
                broken_payload,
                expected_payload,
            )

        self.assertIn("stronger_refs", str(context.exception))

    def test_return_regrounding_pack_rejects_counterpart_review_as_stronger_ref(self) -> None:
        expected_payload = validate_kag.build_return_regrounding_pack_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["modes"][2]["stronger_refs"][0] = (
            "docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md"
        )

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_return_regrounding_pack(
                broken_payload,
                expected_payload,
            )

        self.assertIn("counterpart", str(context.exception))

    def test_return_regrounding_pack_rejects_wrong_owner_repo_in_handoff_mode(self) -> None:
        expected_payload = validate_kag.build_return_regrounding_pack_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["modes"][3]["stronger_refs"][0] = "aoa-routing/README.md"

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_return_regrounding_pack(
                broken_payload,
                expected_payload,
            )

        self.assertIn("stronger_refs", str(context.exception))

    def test_return_regrounding_pack_rejects_duplicate_mode(self) -> None:
        expected_payload = validate_kag.build_return_regrounding_pack_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["modes"][4]["mode_id"] = "handoff_guardrail_reentry"

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_return_regrounding_pack(
                broken_payload,
                expected_payload,
            )

        self.assertIn("duplicated", str(context.exception))

    def test_optional_memo_export_readiness_allows_missing_root(self) -> None:
        missing_root = REPO_ROOT / ".tmp" / "missing-aoa-memo-export"

        with patch.object(validate_kag, "AOA_MEMO_ROOT", missing_root):
            validate_kag.validate_optional_memo_source_owned_export_readiness()

    def test_optional_memo_export_readiness_rejects_wrong_entry_surface(self) -> None:
        payload = self.memo_kag_export_payload()
        payload["entry_surface"]["path"] = "generated/memory_object_sections.full.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            memo_root = Path(tmpdir)
            generated = memo_root / "generated"
            generated.mkdir()
            (generated / "kag_export.min.json").write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch.object(validate_kag, "AOA_MEMO_ROOT", memo_root):
                with self.assertRaises(validate_kag.ValidationError) as context:
                    validate_kag.validate_optional_memo_source_owned_export_readiness()

        self.assertIn("entry_surface", str(context.exception))

    def test_optional_memo_export_readiness_rejects_missing_tos_supporting_input(self) -> None:
        payload = self.memo_kag_export_payload()
        payload["source_inputs"] = [payload["source_inputs"][0]]

        with tempfile.TemporaryDirectory() as tmpdir:
            memo_root = Path(tmpdir)
            generated = memo_root / "generated"
            generated.mkdir()
            (generated / "kag_export.min.json").write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch.object(validate_kag, "AOA_MEMO_ROOT", memo_root):
                with self.assertRaises(validate_kag.ValidationError) as context:
                    validate_kag.validate_optional_memo_source_owned_export_readiness()

        self.assertIn("source_inputs", str(context.exception))


if __name__ == "__main__":
    unittest.main()
