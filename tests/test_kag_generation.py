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

    def test_tos_zarathustra_route_pack_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_tos_zarathustra_route_pack_payload,
            kag_generation.TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH,
            kag_generation.TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_tos_zarathustra_route_retrieval_pack_builder_matches_generated_outputs(
        self,
    ) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_tos_zarathustra_route_retrieval_pack_payload,
            kag_generation.TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATH,
            kag_generation.TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH,
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

    def test_federation_export_registry_builder_matches_generated_outputs(self) -> None:
        self.assert_builder_matches_generated(
            kag_generation.build_federation_export_registry_payload,
            kag_generation.FEDERATION_EXPORT_REGISTRY_OUTPUT_PATH,
            kag_generation.FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH,
        )

    def test_tos_zarathustra_route_pack_builder_keeps_family_order(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        payload = kag_generation.build_tos_zarathustra_route_pack_payload(registry_payload)

        self.assertEqual(
            [node["node_type"] for node in payload["nodes"]],
            [
                node_type
                for node_type in kag_generation.TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER
                for _ in range(kag_generation.TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS[node_type])
            ],
        )
        authority_refs = [node["authority_ref"] for node in payload["nodes"]]
        self.assertEqual(len(authority_refs), len(set(authority_refs)))

        node_ids = {node["node_id"] for node in payload["nodes"]}
        for edge in payload["edges"]:
            self.assertIn(edge["from_id"], node_ids)
            self.assertIn(edge["to_id"], node_ids)

    def test_tos_zarathustra_route_retrieval_handles_match_route_pack(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        route_pack_payload = kag_generation.build_tos_zarathustra_route_pack_payload(
            registry_payload
        )
        retrieval_payload = (
            kag_generation.build_tos_zarathustra_route_retrieval_pack_payload(
                registry_payload
            )
        )
        route = retrieval_payload["routes"][0]

        seen_node_ids: set[str] = set()
        for node_type in kag_generation.TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER:
            expected_handles = [
                {
                    "node_id": node["node_id"],
                    "authority_ref": node["authority_ref"],
                }
                for node in route_pack_payload["nodes"]
                if node["node_type"] == node_type
            ]
            self.assertEqual(route[f"{node_type}_handles"], expected_handles)
            seen_node_ids.update(handle["node_id"] for handle in expected_handles)

        self.assertEqual(
            seen_node_ids,
            {node["node_id"] for node in route_pack_payload["nodes"]},
        )

    def test_tos_zarathustra_route_retrieval_pack_keeps_adjunct_budget_and_subordinate_posture(
        self,
    ) -> None:
        registry_payload = kag_generation.build_registry_payload()
        payload = kag_generation.build_tos_zarathustra_route_retrieval_pack_payload(
            registry_payload
        )

        self.assertEqual(
            payload["adjunct_budget"],
            {
                "max_adjunct_surfaces": 1,
                "max_route_families": 1,
                "numbered_tiny_path_inclusion": "forbidden",
                "default_activation": "opt_in_only",
            },
        )
        self.assertEqual(
            payload["subordinate_posture"],
            {
                "adjunct_role": "standalone_handles_only",
                "entry_order": "source_owned_tiny_entry_before_adjunct",
                "source_first_reentry_ref": "Tree-of-Sophia/examples/tos_tiny_entry_route.example.json",
                "routing_ownership": "forbidden",
                "canon_authorship": "forbidden",
            },
        )

    def test_federation_spine_builder_emits_tos_adjunct_only(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        payload = kag_generation.build_federation_spine_payload(registry_payload)
        repos_by_name = {repo["repo"]: repo for repo in payload["repos"]}

        self.assertEqual(repos_by_name["aoa-techniques"]["adjunct_surfaces"], [])
        self.assertEqual(
            repos_by_name["Tree-of-Sophia"]["adjunct_surfaces"],
            [
                {
                    "surface_id": "AOA-K-0011",
                    "surface_name": "tos-zarathustra-route-retrieval-surface",
                    "surface_ref": "generated/tos_zarathustra_route_retrieval_pack.min.json",
                    "match_key": "retrieval_id",
                    "target_value": kag_generation.TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID,
                    "route_id": kag_generation.TOS_ZARATHUSTRA_ROUTE_ID,
                    "adjunct_budget": {
                        "max_adjunct_surfaces": 1,
                        "max_route_families": 1,
                        "numbered_tiny_path_inclusion": "forbidden",
                        "default_activation": "opt_in_only",
                    },
                    "subordinate_posture": {
                        "adjunct_role": "standalone_handles_only",
                        "entry_order": "source_owned_tiny_entry_before_adjunct",
                        "source_first_reentry_ref": "Tree-of-Sophia/examples/tos_tiny_entry_route.example.json",
                        "routing_ownership": "forbidden",
                        "canon_authorship": "forbidden",
                    },
                }
            ],
        )

    def test_federation_export_registry_builder_keeps_memo_registry_only(self) -> None:
        payload = kag_generation.build_federation_export_registry_payload()
        exports_by_owner = {export["owner_repo"]: export for export in payload["exports"]}

        self.assertEqual(payload["export_count"], 3)
        self.assertEqual(
            exports_by_owner["aoa-memo"]["activation"],
            {
                "registry_visible": True,
                "spine_visible": False,
                "routing_visible": False,
            },
        )
        self.assertEqual(exports_by_owner["aoa-memo"]["consumed_by"], [])
        self.assertEqual(
            exports_by_owner["aoa-memo"]["source_inputs"],
            [
                {
                    "repo": "aoa-memo",
                    "source_class": "memo_object",
                    "role": "primary",
                },
                {
                    "repo": "Tree-of-Sophia",
                    "source_class": "tos_text",
                    "role": "supporting",
                },
            ],
        )

    def test_federation_export_registry_builder_rejects_non_kag_view_routing_binding(self) -> None:
        manifest = load_json(kag_generation.FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["exports"][0]["routing_binding"]["kind"] = "other_view"

        with self.patched_read_json(
            {
                kag_generation.FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_federation_export_registry_payload()

        self.assertIn("routing_binding.kind", str(context.exception))
        self.assertIn("kag_view", str(context.exception))

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

    def test_return_regrounding_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_return_regrounding_pack_payload,
            kag_generation.RETURN_REGROUNDING_OUTPUT_PATH,
            kag_generation.RETURN_REGROUNDING_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_kag_maturity_governance_builder_matches_generated_outputs(self) -> None:
        registry_payload = kag_generation.build_registry_payload()
        self.assert_builder_matches_generated(
            kag_generation.build_kag_maturity_governance_payload,
            kag_generation.KAG_MATURITY_GOVERNANCE_OUTPUT_PATH,
            kag_generation.KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH,
            registry_payload=registry_payload,
        )

    def test_return_regrounding_keeps_memo_memory_readiness_boundary_owner_owned(self) -> None:
        payload = kag_generation.build_return_regrounding_pack_payload(
            kag_generation.build_registry_payload()
        )
        inputs_by_name = {source["name"]: source for source in payload["source_inputs"]}
        modes_by_id = {mode["mode_id"]: mode for mode in payload["modes"]}

        self.assertEqual(
            inputs_by_name["memo_memory_readiness_boundary"],
            {
                "name": "memo_memory_readiness_boundary",
                "repo": "aoa-memo",
                "role": "owner_contract",
                "ref": "aoa-memo/docs/MEMORY_READINESS_BOUNDARY.md",
            },
        )
        self.assertIn(
            "aoa-memo/docs/MEMORY_READINESS_BOUNDARY.md",
            modes_by_id["handoff_guardrail_reentry"]["stronger_refs"],
        )
        self.assertIn(
            "aoa-memo/docs/MEMORY_READINESS_BOUNDARY.md",
            modes_by_id["owner_boundary_reentry"]["stronger_refs"],
        )
        self.assertNotIn(
            "aoa-memo/docs/MEMORY_READINESS_BOUNDARY.md",
            modes_by_id["source_export_reentry"]["stronger_refs"],
        )
        self.assertEqual(payload["bounded_output_contract"]["memory_truth_ownership"], "forbidden")

    def test_kag_maturity_governance_builder_keeps_stop_rule_and_recovery_modes_stable(self) -> None:
        payload = kag_generation.build_kag_maturity_governance_payload(
            kag_generation.build_registry_payload()
        )
        surfaces_by_id = {
            surface["surface_id"]: surface for surface in payload["surfaces"]
        }

        self.assertEqual(
            [tier["tier"] for tier in payload["stability_tiers"]],
            [
                "planned_contract_only",
                "experimental_derived",
                "consumer_stable",
            ],
        )
        self.assertEqual(
            payload["projection_recovery"]["mode_refs"],
            [
                "source_export_reentry",
                "bridge_axis_reentry",
                "projection_boundary_reentry",
                "handoff_guardrail_reentry",
                "owner_boundary_reentry",
            ],
        )
        self.assertEqual(
            payload["stop_rule"]["blocked_surface_ids"],
            ["AOA-K-0008"],
        )
        self.assertEqual(
            surfaces_by_id["AOA-K-0008"]["stability_tier"],
            "planned_contract_only",
        )
        self.assertEqual(
            surfaces_by_id["AOA-K-0009"]["stability_tier"],
            "experimental_derived",
        )
        self.assertEqual(
            surfaces_by_id["AOA-K-0001"]["stability_tier"],
            "consumer_stable",
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

    def test_dependency_failure_names_dependency_id_and_registry_surface(self) -> None:
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
        self.assertIn("federation_export_registry", str(context.exception))

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

    def test_kag_maturity_governance_requires_tier_status_alignment(self) -> None:
        manifest = load_json(kag_generation.KAG_MATURITY_GOVERNANCE_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["surface_governance"][0]["stability_tier"] = "planned_contract_only"

        with self.patched_read_json(
            {
                kag_generation.KAG_MATURITY_GOVERNANCE_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_kag_maturity_governance_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("does not match tier", str(context.exception))

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

    def test_return_regrounding_builder_rejects_mode_order_drift(self) -> None:
        manifest = load_json(kag_generation.RETURN_REGROUNDING_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["mode_bindings"] = list(reversed(broken_manifest["mode_bindings"]))

        with self.patched_read_json(
            {
                kag_generation.RETURN_REGROUNDING_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_return_regrounding_pack_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("stable mode order", str(context.exception))

    def test_return_regrounding_builder_rejects_unknown_dependency_ref(self) -> None:
        manifest = load_json(kag_generation.RETURN_REGROUNDING_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["mode_bindings"][0]["dependency_refs"] = ["wrong-dependency"]

        with self.patched_read_json(
            {
                kag_generation.RETURN_REGROUNDING_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_return_regrounding_pack_payload(
                    kag_generation.build_registry_payload()
                )

        self.assertIn("unknown dependency", str(context.exception))


if __name__ == "__main__":
    unittest.main()
