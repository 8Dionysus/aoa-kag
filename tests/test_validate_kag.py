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


if __name__ == "__main__":
    unittest.main()
