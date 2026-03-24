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

import kag_generation


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class KagGenerationTestCase(unittest.TestCase):
    def patched_read_json(self, overrides: dict[Path, object]):
        original = kag_generation.read_json
        normalized_overrides = {
            Path(path).resolve(): copy.deepcopy(payload)
            for path, payload in overrides.items()
        }

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized_overrides:
                return copy.deepcopy(normalized_overrides[resolved])
            return original(path)

        return patch.object(kag_generation, "read_json", side_effect=side_effect)

    def assert_builder_matches_generated(
        self,
        builder,
        full_output_path: Path,
        min_output_path: Path,
        *,
        registry_payload: dict[str, object] | None = None,
    ) -> None:
        payload = builder() if registry_payload is None else builder(registry_payload)
        expected_payload = load_json(full_output_path)
        self.assertEqual(payload, expected_payload)
        self.assertEqual(
            kag_generation.encode_json(payload, pretty=True),
            full_output_path.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            kag_generation.encode_json(payload, pretty=False),
            min_output_path.read_text(encoding="utf-8"),
        )

    def test_ordered_unique_preserves_first_seen_order(self) -> None:
        self.assertEqual(
            kag_generation.ordered_unique(["alpha", "beta", "alpha", "gamma", "beta"]),
            ["alpha", "beta", "gamma"],
        )

    def test_ensure_repo_relative_path_rejects_absolute_path(self) -> None:
        with self.assertRaises(kag_generation.GenerationError):
            kag_generation.ensure_repo_relative_path(
                "D:/aoa-kag/generated/kag_registry.json",
                label="absolute_path",
            )

    def test_tos_text_chunk_map_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_tos_text_chunk_map_payload,
            kag_generation.TOS_TEXT_CHUNK_MAP_OUTPUT_PATH,
            kag_generation.TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_tos_retrieval_axis_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_tos_retrieval_axis_pack_payload,
            kag_generation.TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
            kag_generation.TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_federation_spine_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_federation_spine_payload,
            kag_generation.FEDERATION_SPINE_OUTPUT_PATH,
            kag_generation.FEDERATION_SPINE_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_cross_source_projection_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_cross_source_node_projection_payload,
            kag_generation.CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
            kag_generation.CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_counterpart_federation_exposure_review_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_counterpart_federation_exposure_review_payload,
            kag_generation.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
            kag_generation.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_tiny_consumer_bundle_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_tiny_consumer_bundle_payload,
            kag_generation.TINY_CONSUMER_BUNDLE_OUTPUT_PATH,
            kag_generation.TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_counterpart_federation_exposure_review_builder_keeps_stable_review_order(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        payload = kag_generation.build_counterpart_federation_exposure_review_payload(
            registry_payload
        )
        self.assertEqual(
            [review["surface_name"] for review in payload["reviewed_surfaces"]],
            [
                "reasoning_handoff_pack",
                "tiny_consumer_bundle",
                "federation_spine",
                "cross_source_node_projection",
                "counterpart_consumer_contract_doc",
                "counterpart_consumer_contract_example",
                "counterpart_edge_contract_doc",
                "counterpart_edge_contract_example",
            ],
        )

    def test_tiny_consumer_bundle_builder_keeps_stable_bundle_order(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        payload = kag_generation.build_tiny_consumer_bundle_payload(registry_payload)
        bundle_items = payload["bundle_items"]
        self.assertEqual(
            [bundle_item["name"] for bundle_item in bundle_items],
            [
                "tos_text_chunk_map",
                "tos_retrieval_axis_pack",
                "federation_spine",
                "cross_source_node_projection",
                "consumer_guide",
                "counterpart_consumer_contract_doc",
                "counterpart_consumer_contract_example",
            ],
        )

    def test_dependency_failure_names_dependency_id_and_consumer_surface(self) -> None:
        broken_export = load_json(
            kag_generation.AOA_TECHNIQUES_ROOT / "generated" / "kag_export.min.json"
        )
        assert isinstance(broken_export, dict)
        broken_export["owner_repo"] = "wrong-owner"

        with self.patched_read_json(
            {
                kag_generation.AOA_TECHNIQUES_ROOT / "generated" / "kag_export.min.json": broken_export,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_federation_spine_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("aoa-techniques-kag-export", str(context.exception))
        self.assertIn("AOA-K-0009", str(context.exception))

    def test_projection_pairings_generator_failures_are_pairing_specific(self) -> None:
        base_manifest = load_json(kag_generation.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH)
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
                        kag_generation.CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH: manifest_override,
                    }
                ):
                    with self.assertRaises(kag_generation.GenerationError) as context:
                        kag_generation.build_cross_source_node_projection_payload(
                            kag_generation.build_registry_payload()
                        )
                self.assertIn("projection_pairings", str(context.exception))

    def test_counterpart_consumer_contract_requires_aoa_k_0008_to_remain_planned(self) -> None:
        registry_manifest = load_json(kag_generation.REGISTRY_MANIFEST_PATH)
        assert isinstance(registry_manifest, dict)
        surfaces = registry_manifest["surfaces"]
        assert isinstance(surfaces, list)
        broken_registry_manifest = copy.deepcopy(registry_manifest)
        for surface in broken_registry_manifest["surfaces"]:
            if surface["id"] == "AOA-K-0008":
                surface["status"] = "experimental"
                break

        with self.patched_read_json(
            {
                kag_generation.REGISTRY_MANIFEST_PATH: broken_registry_manifest,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                registry_payload = kag_generation.build_registry_payload()
                kag_generation.build_tiny_consumer_bundle_payload(registry_payload)

        self.assertIn("AOA-K-0008", str(context.exception))
        self.assertIn("planned", str(context.exception))

    def test_counterpart_consumer_contract_requires_review_ref(self) -> None:
        contract_example = load_json(
            kag_generation.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH
        )
        assert isinstance(contract_example, dict)
        broken_contract_example = copy.deepcopy(contract_example)
        broken_contract_example.pop("federation_exposure_review_ref", None)

        with self.patched_read_json(
            {
                kag_generation.COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH: broken_contract_example,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.load_counterpart_consumer_contract_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("federation_exposure_review_ref", str(context.exception))

    def test_reasoning_handoff_builder_requires_counterpart_contract_refs(self) -> None:
        manifest = load_json(kag_generation.REASONING_HANDOFF_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["source_inputs"] = [
            source_input
            for source_input in broken_manifest["source_inputs"]
            if source_input["name"] != "counterpart_federation_exposure_review_doc"
        ]

        with self.patched_read_json(
            {
                kag_generation.REASONING_HANDOFF_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_reasoning_handoff_pack_payload()

        self.assertIn("KAG guardrail refs", str(context.exception))

    def test_counterpart_federation_exposure_review_rejects_counterpart_refs_in_federation_spine(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        broken_federation_spine = kag_generation.build_federation_spine_payload(
            registry_payload
        )
        broken_federation_spine = copy.deepcopy(broken_federation_spine)
        broken_federation_spine["source_inputs"].append(
            {
                "name": "bad_counterpart_ref",
                "repo": "aoa-kag",
                "role": "counterpart_contract",
                "ref": "docs/COUNTERPART_EDGE_CONTRACTS.md",
            }
        )

        with patch.object(
            kag_generation,
            "build_federation_spine_payload",
            return_value=broken_federation_spine,
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_counterpart_federation_exposure_review_payload(
                    registry_payload
                )

        self.assertIn("federation spine", str(context.exception))
        self.assertIn("counterpart refs", str(context.exception))

    def test_tiny_consumer_bundle_order_failures_are_bundle_order_specific(self) -> None:
        manifest = load_json(kag_generation.TINY_CONSUMER_BUNDLE_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["bundle_order"] = list(reversed(broken_manifest["bundle_order"]))

        with self.patched_read_json(
            {
                kag_generation.TINY_CONSUMER_BUNDLE_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_tiny_consumer_bundle_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("bundle_order", str(context.exception))


if __name__ == "__main__":
    unittest.main()
