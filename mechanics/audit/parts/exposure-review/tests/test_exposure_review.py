from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import kag_generation
import validate_kag
from scripts.validators import example_contracts, manifest_contracts, projection_parity
from scripts.validators.examples import counterpart_examples
from scripts.validators.manifests import counterpart_federation_exposure_review
from scripts.validators.projection import tiny_consumer_bundle


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def registry_surfaces() -> dict[str, dict[str, object]]:
    return validate_kag.validate_registry_payload(
        validate_kag.read_json(validate_kag.REGISTRY_MANIFEST_PATH),
        label="registry manifest",
    )


class ExposureReviewTests(unittest.TestCase):
    def patched_validate_read_json(self, target_module, overrides: dict[Path, object]):
        original = target_module.read_json
        normalized = {Path(path).resolve(): copy.deepcopy(payload) for path, payload in overrides.items()}

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized:
                return copy.deepcopy(normalized[resolved])
            return original(path)

        return patch.object(target_module, "read_json", side_effect=side_effect)

    def patched_generation_read_json(self, overrides: dict[Path, object]):
        original = kag_generation.read_json
        normalized = {Path(path).resolve(): copy.deepcopy(payload) for path, payload in overrides.items()}

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized:
                return copy.deepcopy(normalized[resolved])
            return original(path)

        return patch.object(kag_generation, "read_json", side_effect=side_effect)

    def test_current_exposure_review_contract_validates(self) -> None:
        expected = kag_generation.build_counterpart_federation_exposure_review_payload(
            kag_generation.build_registry_payload()
        )

        validate_kag.validate_counterpart_federation_exposure_review_manifest()
        validate_kag.validate_counterpart_federation_exposure_review_pack(expected)
        validate_kag.validate_counterpart_federation_exposure_review_example(expected)
        self.assertEqual(
            expected,
            load_json(kag_generation.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH),
        )

    def test_counterpart_consumer_contract_stays_planned_and_reviewed(self) -> None:
        surfaces = registry_surfaces()
        payload = load_json(validate_kag.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH)
        assert isinstance(payload, dict)

        broken_status = copy.deepcopy(payload)
        broken_status["surface_status"] = "experimental"
        with self.patched_validate_read_json(
            counterpart_examples,
            {validate_kag.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH: broken_status},
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                example_contracts.validate_counterpart_consumer_contract_example(surfaces)
        self.assertIn("surface_status", str(context.exception))

        broken_ref = copy.deepcopy(payload)
        broken_ref.pop("federation_exposure_review_ref", None)
        with self.patched_validate_read_json(
            counterpart_examples,
            {validate_kag.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH: broken_ref},
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                example_contracts.validate_counterpart_consumer_contract_example(surfaces)
        self.assertIn("federation_exposure_review_ref", str(context.exception))

    def test_exposure_review_rejects_order_drift(self) -> None:
        manifest = load_json(validate_kag.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken = copy.deepcopy(manifest)
        broken["review_bindings"] = list(reversed(broken["review_bindings"]))

        with self.patched_validate_read_json(
            counterpart_federation_exposure_review,
            {validate_kag.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH: broken},
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                manifest_contracts.validate_counterpart_federation_exposure_review_manifest()

        self.assertIn("review_bindings", str(context.exception))

    def test_tiny_bundle_keeps_deferred_counterpart_review_ref(self) -> None:
        expected = kag_generation.build_tiny_consumer_bundle_payload(
            kag_generation.build_registry_payload()
        )
        broken = copy.deepcopy(expected)
        broken["deferred_counterpart"]["federation_exposure_review_ref"] = (
            "generated/wrong_review.min.json"
        )

        with self.patched_validate_read_json(
            tiny_consumer_bundle,
            {validate_kag.TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH: broken},
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                projection_parity.validate_tiny_consumer_bundle_pack(expected)

        self.assertIn("deferred_counterpart", str(context.exception))

    def test_tiny_bundle_order_failures_are_bundle_order_specific(self) -> None:
        manifest = load_json(kag_generation.TINY_CONSUMER_BUNDLE_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken = copy.deepcopy(manifest)
        broken["bundle_order"] = list(reversed(broken["bundle_order"]))

        with self.patched_generation_read_json(
            {kag_generation.TINY_CONSUMER_BUNDLE_MANIFEST_PATH: broken}
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_tiny_consumer_bundle_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("bundle_order", str(context.exception))

    def test_counterpart_consumer_generation_requires_planned_status_and_review_ref(self) -> None:
        registry_manifest = load_json(kag_generation.REGISTRY_MANIFEST_PATH)
        assert isinstance(registry_manifest, dict)
        broken_registry = copy.deepcopy(registry_manifest)
        for surface in broken_registry["surfaces"]:
            if surface["id"] == "AOA-K-0008":
                surface["status"] = "experimental"
                break

        with self.patched_generation_read_json(
            {kag_generation.REGISTRY_MANIFEST_PATH: broken_registry}
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                registry_payload = kag_generation.build_registry_payload()
                kag_generation.build_tiny_consumer_bundle_payload(registry_payload)

        self.assertIn("AOA-K-0008", str(context.exception))
        self.assertIn("planned", str(context.exception))

        contract_example = load_json(kag_generation.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH)
        assert isinstance(contract_example, dict)
        broken_contract = copy.deepcopy(contract_example)
        broken_contract.pop("federation_exposure_review_ref", None)

        with self.patched_generation_read_json(
            {kag_generation.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH: broken_contract}
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.load_counterpart_consumer_contract_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("federation_exposure_review_ref", str(context.exception))

    def test_exposure_builder_rejects_counterpart_refs_in_federation_spine(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        broken_spine = kag_generation.build_federation_spine_payload(registry_payload)
        broken_spine = copy.deepcopy(broken_spine)
        broken_spine["source_inputs"].append(
            {
                "name": "bad_counterpart_ref",
                "repo": "aoa-kag",
                "role": "counterpart_contract",
                "ref": "mechanics/boundary-bridge/parts/counterpart-edge/docs/counterpart-edge-contracts.md",
            }
        )

        with patch.object(
            kag_generation,
            "build_federation_spine_payload",
            return_value=broken_spine,
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_counterpart_federation_exposure_review_payload(
                    registry_payload
                )

        self.assertIn("federation spine", str(context.exception))
        self.assertIn("counterpart refs", str(context.exception))


if __name__ == "__main__":
    unittest.main()
