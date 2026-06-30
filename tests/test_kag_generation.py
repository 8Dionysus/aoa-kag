from __future__ import annotations

import ast
import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import kag_generation
from tests.support.generation_patch import patched_generation_attribute, patched_generation_read_json


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class KagGenerationTestCase(unittest.TestCase):
    def patched_read_json(self, overrides: dict[Path, object]):
        return patched_generation_read_json(overrides)

    def patch_generation_attribute(self, name: str, value: object):
        return patched_generation_attribute(name, value)

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

    def test_kag_generation_facade_stays_thin(self) -> None:
        text = (SCRIPTS_ROOT / "kag_generation.py").read_text(encoding="utf-8")
        tree = ast.parse(text)
        definitions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }

        self.assertLessEqual(len(text.splitlines()), 8)
        self.assertEqual(set(), definitions)
        self.assertIn("from generation import *", text)

    def test_generated_output_paths_cover_all_writer_outputs(self) -> None:
        self.assertEqual(
            [
                kag_generation.REGISTRY_OUTPUT_PATH,
                kag_generation.REGISTRY_MIN_OUTPUT_PATH,
                kag_generation.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH,
                kag_generation.LOCAL_KAG_PROVIDER_MAP_MIN_OUTPUT_PATH,
                kag_generation.TECHNIQUE_LIFT_OUTPUT_PATH,
                kag_generation.TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
                kag_generation.TOS_TEXT_CHUNK_MAP_OUTPUT_PATH,
                kag_generation.TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
                kag_generation.TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
                kag_generation.TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
                kag_generation.TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH,
                kag_generation.TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH,
                kag_generation.TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATH,
                kag_generation.TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH,
                kag_generation.REASONING_HANDOFF_OUTPUT_PATH,
                kag_generation.REASONING_HANDOFF_MIN_OUTPUT_PATH,
                kag_generation.FEDERATION_EXPORT_REGISTRY_OUTPUT_PATH,
                kag_generation.FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH,
                kag_generation.FEDERATION_SPINE_OUTPUT_PATH,
                kag_generation.FEDERATION_SPINE_MIN_OUTPUT_PATH,
                kag_generation.CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
                kag_generation.CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
                kag_generation.RETURN_REGROUNDING_OUTPUT_PATH,
                kag_generation.RETURN_REGROUNDING_MIN_OUTPUT_PATH,
                kag_generation.KAG_MATURITY_GOVERNANCE_OUTPUT_PATH,
                kag_generation.KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH,
                kag_generation.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
                kag_generation.COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
                kag_generation.TINY_CONSUMER_BUNDLE_OUTPUT_PATH,
                kag_generation.TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
            ],
            kag_generation.GENERATED_OUTPUT_PATHS,
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

    def test_eval_catalog_rejects_absolute_paths(self) -> None:
        with self.patched_read_json(
            {
                kag_generation.EVAL_CATALOG_PATH: {
                    "evals": [
                        {
                            "name": "aoa-long-horizon-depth",
                            "eval_path": "/tmp/outside/EVAL.md",
                        }
                    ]
                }
            }
        ):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.load_eval_paths_by_name()

        self.assertIn("repo-relative", str(context.exception))

    def test_registry_payload_carries_artifact_identity(self) -> None:
        payload = kag_generation.build_registry_payload()

        self.assertEqual(
            kag_generation.KAG_REGISTRY_ARTIFACT_IDENTITY,
            payload["artifact_identity"],
        )

    def test_registry_payload_rejects_artifact_identity_drift(self) -> None:
        payload = load_json(kag_generation.REGISTRY_MANIFEST_PATH)
        assert isinstance(payload, dict)
        broken_payload = copy.deepcopy(payload)
        artifact_identity = copy.deepcopy(broken_payload["artifact_identity"])
        assert isinstance(artifact_identity, dict)
        artifact_identity["abi_epoch"] = "wrong_epoch"
        broken_payload["artifact_identity"] = artifact_identity

        with self.patched_read_json({kag_generation.REGISTRY_MANIFEST_PATH: broken_payload}):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_registry_payload()

        self.assertIn("artifact_identity", str(context.exception))

    def test_local_kag_provider_map_builder_matches_generated_outputs(self) -> None:
        self.assert_builder_matches_generated(
            kag_generation.build_local_kag_provider_map_payload,
            kag_generation.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH,
            kag_generation.LOCAL_KAG_PROVIDER_MAP_MIN_OUTPUT_PATH,
        )

    def test_local_kag_provider_map_falls_back_to_committed_provider_packets(self) -> None:
        expected_payload = load_json(kag_generation.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(expected_payload, dict)
        missing_roots = dict(kag_generation.KNOWN_REPO_ROOTS)
        for provider in expected_payload["providers"]:
            if provider["repo"] == "aoa-kag":
                continue
            missing_roots[provider["repo"]] = REPO_ROOT / ".missing-deps" / provider["repo"]

        with self.patched_read_json({}), self.patch_generation_attribute(
            "KNOWN_REPO_ROOTS", missing_roots
        ):
            self.assertEqual(
                kag_generation.build_local_kag_provider_map_payload(),
                expected_payload,
            )

    def test_local_kag_provider_map_rejects_receipt_without_checked_ref(self) -> None:
        receipt_path = kag_generation.REPO_ROOT / "kag" / "receipts" / "validation_receipt.json"
        broken_receipt = load_json(receipt_path)
        assert isinstance(broken_receipt, dict)
        freshness = broken_receipt["freshness"]
        assert isinstance(freshness, dict)
        freshness.pop("checked_ref")

        with self.patched_read_json({receipt_path: broken_receipt}):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_local_kag_provider_map_payload()

        self.assertIn("freshness.checked_ref", str(context.exception))

    def test_local_kag_provider_map_rejects_missing_checked_ref_target(self) -> None:
        receipt_path = kag_generation.REPO_ROOT / "kag" / "receipts" / "validation_receipt.json"
        broken_receipt = load_json(receipt_path)
        assert isinstance(broken_receipt, dict)
        freshness = broken_receipt["freshness"]
        assert isinstance(freshness, dict)
        freshness["checked_ref"] = "tests/missing_validate_kag.py"

        with self.patched_read_json({receipt_path: broken_receipt}):
            with self.assertRaises(kag_generation.GenerationError) as context:
                kag_generation.build_local_kag_provider_map_payload()

        self.assertIn("freshness.checked_ref target is missing", str(context.exception))

    def test_local_kag_provider_map_carries_mcp_handoff_planes(self) -> None:
        payload = kag_generation.build_local_kag_provider_map_payload()
        handoff = payload["mcp_handoff"]
        records_template = next(
            item
            for item in handoff["resource_templates"]
            if item["uri_template"] == "aoa-kag://providers/{repo}/records/{record_class}"
        )
        generation_template = next(
            item
            for item in handoff["resource_templates"]
            if item["uri_template"] == "aoa-kag://providers/{repo}/generation"
        )
        source_index_template = next(
            item
            for item in handoff["resource_templates"]
            if item["uri_template"] == "aoa-kag://providers/{repo}/source-index"
        )
        repo_local_index_template = next(
            item
            for item in handoff["resource_templates"]
            if item["uri_template"] == "aoa-kag://providers/{repo}/repo-local-index"
        )

        self.assertEqual(
            handoff["service_route"],
            "abyss-stack/mcp/services/aoa-kag-mcp",
        )
        self.assertEqual(
            {item["uri_template"] for item in handoff["resource_templates"]},
            {
                "aoa-kag://providers/{repo}/manifest",
                "aoa-kag://providers/{repo}/records/{record_class}",
                "aoa-kag://providers/{repo}/generation",
                "aoa-kag://providers/{repo}/source-index",
                "aoa-kag://providers/{repo}/repo-local-index",
                "aoa-kag://registry/provider-map",
                "aoa-kag://coverage/repo-local-source-indexes",
                "aoa-kag://readiness/os-surfaces",
            },
        )
        self.assertTrue(handoff["root_boundaries"])
        self.assertIn("generation_route_lookup", handoff["tools"])
        self.assertIn("source_index_lookup", handoff["tools"])
        self.assertIn("repo_local_coverage_status", handoff["tools"])
        self.assertIn("validation_status", handoff["tools"])
        self.assertIn("bounded_provider_query", handoff["prompts"])
        self.assertIn("repo_source_surface_brief", handoff["prompts"])
        self.assertEqual(
            generation_template["source"],
            "aoa-kag/generated/local_kag_provider_map.min.json"
            "#/provider_generation_profiles/{repo}",
        )
        self.assertEqual(
            repo_local_index_template["source"],
            "aoa-kag/generated/local_kag_provider_map.min.json"
            "#/provider_repo_local_indexes/{repo}",
        )
        self.assertEqual(
            source_index_template["source"],
            "aoa-kag/generated/local_kag_provider_map.min.json"
            "#/provider_repo_local_indexes/{repo}/source_index_ref",
        )
        self.assertEqual(
            source_index_template["fallback_source"],
            "aoa-kag/generated/local_kag_provider_map.min.json"
            "#/provider_repo_local_indexes/{repo}/index_files",
        )
        self.assertNotEqual(
            source_index_template["source"],
            "{repo}/kag/indexes/source_surface_index.json",
        )
        self.assertEqual(records_template["source"], "{repo}/kag/{record_class_directory}/")
        self.assertEqual(
            records_template["record_class_directory_map"],
            {
                "node": "nodes",
                "edge": "edges",
                "index": "indexes",
                "projection": "projections",
                "receipt": "receipts",
            },
        )

    def test_local_kag_provider_map_carries_generation_readiness(self) -> None:
        payload = kag_generation.build_local_kag_provider_map_payload()

        readiness = payload["generation_readiness"]
        self.assertEqual(
            {"authored_control", "generated_from_source"},
            set(readiness["provider_generation_record_counts"]),
        )
        self.assertIn("Tree-of-Sophia", readiness["generated_record_repos"])
        self.assertIn("aoa-techniques", readiness["source_owned_export_repos"])
        self.assertEqual(
            {"provider_ready", "runtime_consumer", "source_preparation"},
            set(readiness["os_surface_status_counts"]),
        )

        for provider in payload["providers"]:
            with self.subTest(repo=provider["repo"]):
                repo = provider["repo"]
                profile = provider["generation_profile"]
                self.assertEqual(profile, payload["provider_generation_profiles"][repo])
                self.assertEqual(
                    provider["repo_local_index"],
                    payload["provider_repo_local_indexes"][repo],
                )
                self.assertTrue(profile["source_home_surfaces"])
                self.assertTrue(profile["candidate_source_surfaces"])
                self.assertTrue(profile["graph_entities"])
                self.assertTrue(profile["builder_routes"])
                self.assertEqual(
                    sum(profile["record_authoring_counts"].values()),
                    sum(profile["record_class_counts"].values()),
                )
                self.assertIn("runtime_consumers", profile)

    def test_local_kag_provider_map_carries_status_and_freshness_handles(self) -> None:
        payload = kag_generation.build_local_kag_provider_map_payload()

        self.assertEqual([], payload["remaining_routes"])
        for provider in payload["providers"]:
            with self.subTest(repo=provider["repo"]):
                self.assertEqual("provider_ready", provider["provider_status"])
                self.assertEqual(
                    {"nodes", "edges", "indexes", "projections", "receipts"},
                    set(provider["record_counts"]),
                )
                self.assertIn("repo_local_index", provider)
                self.assertTrue(provider["freshness_handles"])
                for handle in provider["freshness_handles"]:
                    self.assertIn("receipt_ref", handle)
                    self.assertIn("checked_ref", handle)
                    self.assertIn("state", handle)
                    self.assertIn("validator", handle)
                    self.assertIn("owner_return_route", handle)

    def test_local_kag_provider_map_carries_repo_local_index_status(self) -> None:
        payload = kag_generation.build_local_kag_provider_map_payload()
        coverage = load_json(kag_generation.REPO_LOCAL_KAG_COVERAGE_OUTPUT_PATH)
        assert isinstance(coverage, dict)
        coverage_by_repo = {
            owner["repo"]: owner
            for owner in coverage["owners"]
        }

        for provider in payload["providers"]:
            repo = provider["repo"]
            with self.subTest(repo=repo):
                coverage_row = coverage_by_repo[repo]
                index_packet = provider["repo_local_index"]
                self.assertEqual(coverage_row["index_status"], index_packet["status"])
                self.assertEqual(coverage_row["index_files"], index_packet["index_files"])
                self.assertEqual(coverage_row["coverage"], index_packet["coverage"])
                self.assertEqual(
                    "generated/repo_local_kag_coverage.min.json",
                    index_packet["coverage_report_ref"],
                )
                self.assertEqual(repo, index_packet["coverage_owner_key"])

        providers = {provider["repo"]: provider for provider in payload["providers"]}
        self.assertEqual(
            "passed",
            providers["aoa-kag"]["repo_local_index"]["status"],
        )
        self.assertEqual(
            "migration-needed",
            providers["aoa-session-memory"]["repo_local_index"]["status"],
        )
        connector_statuses = {
            repo: provider["repo_local_index"]["status"]
            for repo, provider in providers.items()
            if repo.endswith("-connector")
        }
        self.assertTrue(connector_statuses)
        self.assertEqual(
            {"passed"},
            set(connector_statuses.values()),
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


if __name__ == "__main__":
    unittest.main()
