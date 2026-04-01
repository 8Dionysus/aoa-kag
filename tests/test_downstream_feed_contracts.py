from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import kag_generation


GENERATED_ROOT = REPO_ROOT / "generated"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class KagDownstreamFeedContractsTests(unittest.TestCase):
    def assert_builder_matches_generated(
        self,
        builder,
        full_output_path: Path,
        min_output_path: Path,
        *,
        registry_payload: dict[str, object] | None = None,
    ) -> None:
        payload = builder() if registry_payload is None else builder(registry_payload)
        self.assertEqual(payload, load_json(full_output_path))
        self.assertEqual(
            kag_generation.encode_json(payload, pretty=False),
            min_output_path.read_text(encoding="utf-8"),
        )

    def test_registry_surface_keeps_exact_consumer_contract(self) -> None:
        registry = kag_generation.build_registry_payload()
        current = load_json(GENERATED_ROOT / "kag_registry.min.json")

        self.assertEqual(current, registry)
        self.assertEqual(set(current.keys()), {"version", "layer", "surfaces"})
        self.assertEqual(current["version"], 1)
        self.assertEqual(current["layer"], "aoa-kag")
        self.assertEqual([item["id"] for item in current["surfaces"]], [f"AOA-K-000{i}" for i in range(1, 10)] + ["AOA-K-0010", "AOA-K-0011"])

    def test_generated_consumer_packs_match_builders(self) -> None:
        registry = kag_generation.build_registry_payload()

        self.assert_builder_matches_generated(
            kag_generation.build_technique_lift_pack_payload,
            kag_generation.TECHNIQUE_LIFT_OUTPUT_PATH,
            kag_generation.TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
            registry_payload=registry,
        )
        self.assert_builder_matches_generated(
            kag_generation.build_tos_text_chunk_map_payload,
            kag_generation.TOS_TEXT_CHUNK_MAP_OUTPUT_PATH,
            kag_generation.TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
            registry_payload=registry,
        )
        self.assert_builder_matches_generated(
            kag_generation.build_tos_retrieval_axis_pack_payload,
            kag_generation.TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
            kag_generation.TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
            registry_payload=registry,
        )
        self.assert_builder_matches_generated(
            kag_generation.build_tos_zarathustra_route_retrieval_pack_payload,
            kag_generation.TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATH,
            kag_generation.TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH,
            registry_payload=registry,
        )
        self.assert_builder_matches_generated(
            kag_generation.build_reasoning_handoff_pack_payload,
            kag_generation.REASONING_HANDOFF_OUTPUT_PATH,
            kag_generation.REASONING_HANDOFF_MIN_OUTPUT_PATH,
        )
        self.assert_builder_matches_generated(
            kag_generation.build_federation_spine_payload,
            kag_generation.FEDERATION_SPINE_OUTPUT_PATH,
            kag_generation.FEDERATION_SPINE_MIN_OUTPUT_PATH,
            registry_payload=registry,
        )
        self.assert_builder_matches_generated(
            kag_generation.build_cross_source_node_projection_payload,
            kag_generation.CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
            kag_generation.CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
            registry_payload=registry,
        )
        self.assert_builder_matches_generated(
            kag_generation.build_return_regrounding_pack_payload,
            kag_generation.RETURN_REGROUNDING_OUTPUT_PATH,
            kag_generation.RETURN_REGROUNDING_MIN_OUTPUT_PATH,
            registry_payload=registry,
        )
        self.assert_builder_matches_generated(
            kag_generation.build_counterpart_federation_exposure_review_payload,
            kag_generation.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
            kag_generation.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
            registry_payload=registry,
        )
        self.assert_builder_matches_generated(
            kag_generation.build_tiny_consumer_bundle_payload,
            kag_generation.TINY_CONSUMER_BUNDLE_OUTPUT_PATH,
            kag_generation.TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
            registry_payload=registry,
        )

    def test_bounded_output_contracts_remain_narrow(self) -> None:
        expectations = {
            "federation_spine.min.json": {
                "source_trace_required": True,
                "source_replacement": "forbidden",
                "routing_ownership": "forbidden",
                "canon_authorship": "forbidden",
                "full_federation_claim": "forbidden",
            },
            "reasoning_handoff_pack.min.json": {
                "source_trace_required": True,
                "source_replacement": "forbidden",
                "routing_ownership": "forbidden",
                "memory_truth_ownership": "forbidden",
                "verdict_ownership": "forbidden",
            },
            "return_regrounding_pack.min.json": {
                "source_trace_required": True,
                "source_replacement": "forbidden",
                "routing_ownership": "forbidden",
                "memory_truth_ownership": "forbidden",
                "counterpart_activation": "review_gated",
                "proof_ownership": "forbidden",
            },
            "tos_retrieval_axis_pack.min.json": {
                "source_trace_required": True,
                "source_replacement": "forbidden",
                "scoring_or_ranking": "forbidden",
                "routing_ownership": "forbidden",
                "graph_normalization": "forbidden",
            },
            "tos_text_chunk_map.min.json": {
                "source_trace_required": True,
                "source_replacement": "forbidden",
                "counterpart_projection": "forbidden",
                "federation_export_activation": "forbidden",
            },
            "cross_source_node_projection.min.json": {
                "source_trace_required": True,
                "source_replacement": "forbidden",
                "counterpart_activation": "forbidden",
                "graph_expansion": "forbidden",
                "routing_ownership": "forbidden",
            },
            "counterpart_federation_exposure_review.min.json": {
                "silent_federation_exposure": "forbidden",
                "generated_counterpart_payload_inference": "forbidden",
                "routing_ownership": "forbidden",
                "source_replacement": "forbidden",
            },
            "tos_zarathustra_route_retrieval_pack.min.json": {
                "source_trace_required": True,
                "source_replacement": "forbidden",
                "scoring_or_ranking": "forbidden",
                "routing_ownership": "forbidden",
                "graph_normalization": "forbidden",
                "consumer_projection": "bounded_handles_only",
            },
        }

        for name, contract_expectations in expectations.items():
            payload = load_json(GENERATED_ROOT / name)
            contract = payload["bounded_output_contract"]
            for key, value in contract_expectations.items():
                self.assertEqual(contract[key], value, msg=f"{name}:{key}")

    def test_consumer_bundle_and_spine_keep_expected_counts(self) -> None:
        federation_spine = load_json(GENERATED_ROOT / "federation_spine.min.json")
        tiny_bundle = load_json(GENERATED_ROOT / "tiny_consumer_bundle.min.json")
        retrieval_pack = load_json(GENERATED_ROOT / "tos_zarathustra_route_retrieval_pack.min.json")

        self.assertEqual(federation_spine["repo_count"], 2)
        self.assertEqual(
            [repo["repo"] for repo in federation_spine["repos"]],
            ["aoa-techniques", "Tree-of-Sophia"],
        )
        self.assertEqual(tiny_bundle["bundle_item_count"], len(tiny_bundle["bundle_items"]))
        self.assertEqual(retrieval_pack["route_count"], len(retrieval_pack["routes"]))
        self.assertEqual(retrieval_pack["surface_id"], "AOA-K-0011")


if __name__ == "__main__":
    unittest.main()
