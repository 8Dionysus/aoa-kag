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

    def test_aoa_k_0011_stays_inspectable_but_separate_from_tiny_entry_bundle(self) -> None:
        registry = load_json(GENERATED_ROOT / "kag_registry.min.json")
        tiny_bundle = load_json(GENERATED_ROOT / "tiny_consumer_bundle.min.json")
        retrieval_pack = load_json(GENERATED_ROOT / "tos_zarathustra_route_retrieval_pack.min.json")
        federation_spine = load_json(GENERATED_ROOT / "federation_spine.min.json")

        registry_entry = next(item for item in registry["surfaces"] if item["id"] == "AOA-K-0011")
        self.assertEqual(registry_entry["status"], "experimental")
        self.assertEqual(registry_entry["derived_kind"], "retrieval_surface")

        tiny_bundle_refs = {item["ref"] for item in tiny_bundle["bundle_items"]}
        self.assertNotIn("generated/tos_zarathustra_route_retrieval_pack.min.json", tiny_bundle_refs)
        self.assertNotIn(
            "tos_zarathustra_route_retrieval_pack",
            {item["name"] for item in tiny_bundle["bundle_items"]},
        )

        self.assertEqual(retrieval_pack["surface_id"], "AOA-K-0011")
        self.assertEqual(
            [binding["surface_id"] for binding in retrieval_pack["surface_bindings"]],
            ["AOA-K-0011"],
        )
        self.assertTrue(
            all(route["retrieval_id"].startswith("AOA-K-0011::") for route in retrieval_pack["routes"])
        )
        self.assertEqual(
            retrieval_pack["bounded_output_contract"]["consumer_projection"],
            "bounded_handles_only",
        )
        self.assertEqual(
            retrieval_pack["adjunct_budget"],
            {
                "max_adjunct_surfaces": 1,
                "max_route_families": 1,
                "numbered_tiny_path_inclusion": "forbidden",
                "default_activation": "opt_in_only",
            },
        )
        self.assertEqual(
            retrieval_pack["subordinate_posture"],
            {
                "adjunct_role": "standalone_handles_only",
                "entry_order": "source_owned_tiny_entry_before_adjunct",
                "source_first_reentry_ref": "Tree-of-Sophia/examples/tos_tiny_entry_route.example.json",
                "routing_ownership": "forbidden",
                "canon_authorship": "forbidden",
            },
        )

        tos_repo = next(repo for repo in federation_spine["repos"] if repo["repo"] == "Tree-of-Sophia")
        adjunct_surfaces = tos_repo["adjunct_surfaces"]
        self.assertEqual(len(adjunct_surfaces), 1)
        self.assertEqual(adjunct_surfaces[0]["surface_id"], "AOA-K-0011")
        self.assertEqual(
            adjunct_surfaces[0]["surface_ref"],
            "generated/tos_zarathustra_route_retrieval_pack.min.json",
        )
        self.assertEqual(
            adjunct_surfaces[0]["adjunct_budget"]["numbered_tiny_path_inclusion"],
            "forbidden",
        )
        self.assertEqual(
            adjunct_surfaces[0]["subordinate_posture"]["source_first_reentry_ref"],
            "Tree-of-Sophia/examples/tos_tiny_entry_route.example.json",
        )

    def test_readme_surfaces_source_first_route_and_honest_validation_paths(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("- role, model, and source-first posture:", readme)
        self.assertIn("- docs map:", readme)
        self.assertLess(
            readme.index("- role, model, and source-first posture:"),
            readme.index("- docs map:"),
        )

        for command in (
            "python scripts/validate_kag.py",
            "python scripts/validate_nested_agents.py",
            "python -m unittest discover -s tests -p 'test_*.py'",
            "python scripts/release_check.py",
            "python scripts/generate_kag.py",
            "git status -sb",
        ):
            self.assertIn(command, readme)

    def test_agents_and_contributing_distinguish_current_validation_from_release_prep(self) -> None:
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        contributing = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

        for text in (agents, contributing):
            for command in (
                "python scripts/validate_kag.py",
                "python scripts/validate_nested_agents.py",
                "python -m unittest discover -s tests -p 'test_*.py'",
                "python scripts/release_check.py",
                "git status -sb",
            ):
                self.assertIn(command, text)

    def test_consumer_guide_verification_posture_mentions_read_only_and_release_prep(self) -> None:
        guide = (REPO_ROOT / "docs" / "CONSUMER_GUIDE.md").read_text(encoding="utf-8")

        for command in (
            "python scripts/validate_kag.py",
            "python scripts/validate_nested_agents.py",
            "python -m unittest discover -s tests -p 'test_*.py'",
            "python scripts/release_check.py",
            "git status -sb",
        ):
            self.assertIn(command, guide)


if __name__ == "__main__":
    unittest.main()
