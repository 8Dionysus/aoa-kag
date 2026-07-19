from __future__ import annotations

import ast
import copy
import importlib
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

import kag_generation
import generate_kag
from generation import provider_map
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
        self.assertIn("from .generation import *", text)
        self.assertIn("from generation import *", text)

    def test_kag_generation_facade_supports_package_import(self) -> None:
        module = importlib.import_module("scripts.kag_generation")

        self.assertIs(module.GenerationError, kag_generation.GenerationError)

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

    def test_generate_kag_check_mode_does_not_write_outputs(self) -> None:
        with patch.object(generate_kag, "check_generated_outputs", return_value=[]) as check:
            with patch.object(generate_kag, "write_generated_outputs") as write:
                self.assertEqual(0, generate_kag.main(["--check"]))

        check.assert_called_once_with()
        write.assert_not_called()

    def test_generate_kag_check_mode_reports_drift(self) -> None:
        drifted_path = REPO_ROOT / "generated" / "kag_registry.json"
        with patch.object(
            generate_kag,
            "check_generated_outputs",
            return_value=[drifted_path],
        ):
            with patch.object(generate_kag, "write_generated_outputs") as write:
                self.assertEqual(1, generate_kag.main(["--check"]))

        write.assert_not_called()

    def test_generate_kag_default_mode_writes_outputs(self) -> None:
        written_path = REPO_ROOT / "generated" / "kag_registry.json"
        with patch.object(
            generate_kag,
            "write_generated_outputs",
            return_value=[written_path],
        ) as write:
            with patch.object(generate_kag, "check_generated_outputs") as check:
                self.assertEqual(0, generate_kag.main([]))

        write.assert_called_once_with()
        check.assert_not_called()

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

    def test_local_kag_provider_map_rebuilds_common_profile_from_live_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            coverage_by_repo = {
                "aoa-demo": {
                    "index_status": "missing",
                    "index_files": [],
                    "coverage": {"documents": 1},
                }
            }
            fallback_provider = {
                "repo_local_index": {
                    "common_surface_profile": {
                        "source": "source_surface_index",
                        "counts": {"artifact_kind": {"document": 99}},
                        "quality": {"unknown_count": 99},
                    }
                }
            }
            roots = dict(kag_generation.KNOWN_REPO_ROOTS)
            roots["aoa-demo"] = root

            with self.patch_generation_attribute("KNOWN_REPO_ROOTS", roots):
                packet = provider_map._provider_repo_local_index_packet(
                    "aoa-demo",
                    coverage_by_repo,
                    fallback_provider,
                )

        profile = packet["common_surface_profile"]
        assert isinstance(profile, dict)
        self.assertEqual("source_tree_scan", profile["source"])
        self.assertEqual(1, profile["counts"]["artifact_kind"]["document"])
        self.assertEqual(0, profile["quality"]["unknown_count"])

    def test_local_kag_provider_map_rejects_present_provider_missing_kag_home(self) -> None:
        expected_payload = load_json(kag_generation.LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH)
        assert isinstance(expected_payload, dict)
        provider = next(
            item
            for item in expected_payload["providers"]
            if item["repo"] != "aoa-kag"
        )
        repo = provider["repo"]

        with tempfile.TemporaryDirectory() as tmpdir:
            present_root = Path(tmpdir) / repo
            present_root.mkdir()
            roots = dict(kag_generation.KNOWN_REPO_ROOTS)
            roots[repo] = present_root

            with self.patch_generation_attribute("KNOWN_REPO_ROOTS", roots):
                with self.assertRaises(kag_generation.GenerationError) as context:
                    kag_generation.build_local_kag_provider_map_payload()

        self.assertIn("kag/manifest.json", str(context.exception))

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
        templates = {
            item["uri_template"]: item for item in handoff["resource_templates"]
        }

        self.assertEqual(
            handoff["service_route"],
            "abyss-stack/mcp/services/aoa-kag-mcp",
        )
        self.assertEqual(
            handoff["resource_uri_scheme"],
            "aoa-kag://{resource_class}/{identifier}",
        )
        self.assertEqual(
            set(templates),
            {
                "aoa-kag://capabilities",
                "aoa-kag://owners/{repo}/manifest",
                "aoa-kag://records/{qualified_id}",
                "aoa-kag://documents/{document_id}",
                "aoa-kag://anchors/{anchor_id}",
                "aoa-kag://sources/{repo}/{document_id}",
                "aoa-kag://evidence/{trace_id}",
                "aoa-kag://schemas/{name}",
                "aoa-kag://projections/{digest}",
            },
        )
        self.assertTrue(handoff["root_boundaries"])
        self.assertEqual(
            handoff["tools"],
            [
                "kag_discover",
                "kag_search",
                "kag_read",
                "kag_traverse",
                "kag_explain",
            ],
        )
        self.assertEqual(handoff["prompts"], [])
        self.assertEqual(
            set(handoff["package_surfaces"]),
            {
                "AGENTS.md",
                "DESIGN.md",
                "README.md",
                "pyproject.toml",
                "src/aoa_kag_mcp/",
                "tests/",
                "scripts/validate_kag_mcp.py",
            },
        )
        self.assertEqual(
            handoff["runtime_state_route"],
            "abyss-stack/mechanics/federation-seams/parts/kag-seam",
        )
        self.assertEqual(
            templates["aoa-kag://owners/{repo}/manifest"]["source"],
            "{repo}/kag/manifest.json",
        )
        self.assertEqual(
            templates["aoa-kag://records/{qualified_id}"]["source"],
            "{repo}/kag/indexes/index_family.manifest.json",
        )
        self.assertEqual(
            templates["aoa-kag://anchors/{anchor_id}"]["source"],
            "{repo}/kag/indexes/index_family.manifest.json",
        )
        self.assertEqual(
            templates["aoa-kag://documents/{document_id}"]["source"],
            "abyss-stack/Knowledge/kag/repo-self/exact/repo-self.sqlite3",
        )
        self.assertEqual(
            templates["aoa-kag://schemas/{name}"]["source"],
            "aoa-kag/schemas/{name}.schema.json",
        )
        self.assertEqual(
            templates["aoa-kag://projections/{digest}"]["source"],
            "abyss-stack/Knowledge/kag/repo-self/current.json",
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
                self.assertEqual(
                    provider["repo_local_index"]["common_surface_profile"],
                    payload["provider_common_surface_profiles"][repo],
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
        self.assertEqual(
            "aoa-owner:abyss-stack",
            coverage_by_repo["abyss-stack"]["root"],
        )
        self.assertEqual(
            "aoa-owner:abyss-machine",
            coverage_by_repo["abyss-machine"]["root"],
        )
        self.assertEqual("aoa-os:canonical-providers", coverage["root"])
        self.assertNotIn("/home/", json.dumps(payload))
        self.assertNotIn("/srv/", json.dumps(payload))

        for provider in payload["providers"]:
            repo = provider["repo"]
            with self.subTest(repo=repo):
                coverage_row = coverage_by_repo[repo]
                index_packet = provider["repo_local_index"]
                self.assertEqual(coverage_row["index_status"], index_packet["status"])
                self.assertEqual(coverage_row["index_files"], index_packet["index_files"])
                self.assertEqual(
                    coverage_row["repository_index_family"],
                    index_packet["repository_index_family"],
                )
                self.assertEqual(
                    (
                        coverage_row["repository_index_family"].get("source", "")
                        if coverage_row["index_status"] == "passed"
                        else ""
                    ),
                    index_packet["source_index_ref"],
                )
                self.assertEqual(
                    coverage_row["domain_index_catalog_ref"],
                    index_packet["domain_index_catalog_ref"],
                )
                self.assertEqual(coverage_row["coverage"], index_packet["coverage"])
                self.assertEqual(
                    coverage_row["common_surface_profile"],
                    index_packet["common_surface_profile"],
                )
                self.assertEqual(
                    "generated/repo_local_kag_coverage.min.json",
                    index_packet["coverage_report_ref"],
                )
                self.assertEqual(repo, index_packet["coverage_owner_key"])
                common_profile = index_packet["common_surface_profile"]
                self.assertIn(
                    common_profile["source"],
                    {"source_surface_index", "source_tree_scan"},
                )
                self.assertIn("artifact_kind", common_profile["counts"])
                self.assertIn("primary_kind", common_profile["counts"])
                self.assertIn("has_kag_home", common_profile["quality"])
                self.assertIsInstance(common_profile["quality"]["has_kag_home"], bool)

        providers = {provider["repo"]: provider for provider in payload["providers"]}
        self.assertEqual(
            "passed",
            providers["aoa-kag"]["repo_local_index"]["status"],
        )
        self.assertIn(
            "kag/indexes/session_memory_source_inventory.json",
            providers["aoa-session-memory"]["repo_local_index"]["index_files"],
        )
        self.assertEqual(
            "kag/indexes/domain_index_catalog.json",
            providers["aoa-session-memory"]["repo_local_index"]["domain_index_catalog_ref"],
        )
        self.assertEqual(
            {
                "source": "kag/indexes/source_surface_index.json",
                "entity": "kag/indexes/repo_entity_index.json",
                "artifact": "kag/indexes/repo_artifact_index.json",
                "anchor": "kag/indexes/repo_anchor_index.json",
                "event": "kag/indexes/repo_event_index.json",
                "assertion": "kag/indexes/repo_assertion_index.json",
                "relation": "kag/indexes/repo_relation_index.json",
            },
            providers["aoa-session-memory"]["repo_local_index"]["repository_index_family"],
        )
        connector_statuses = {
            repo: provider["repo_local_index"]["status"]
            for repo, provider in providers.items()
            if repo.endswith("-connector")
        }
        self.assertTrue(connector_statuses)
        self.assertLessEqual(
            set(connector_statuses.values()),
            {"passed", "migration-needed", "owner-specific"},
        )
        for repo, provider in providers.items():
            if not repo.endswith("-connector"):
                continue
            index_packet = provider["repo_local_index"]
            if index_packet["status"] == "passed":
                self.assertEqual(
                    "kag/indexes/source_surface_index.json",
                    index_packet["source_index_ref"],
                )
            else:
                self.assertEqual("", index_packet["source_index_ref"])

    def test_provider_records_ignore_corrupt_repo_local_source_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "aoa-demo-connector"
            for group in provider_map.PROVIDER_RECORD_DIRECTORIES:
                directory = root / "kag" / group
                directory.mkdir(parents=True)
                (directory / "demo.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "aoa-local-kag-record-v1",
                            "record_class": group,
                        }
                    ),
                    encoding="utf-8",
                )
            (root / "kag" / "indexes" / "source_surface_index.json").write_text(
                "{not-json\n",
                encoding="utf-8",
            )

            with self.patch_generation_attribute(
                "KNOWN_REPO_ROOTS",
                {"aoa-demo-connector": root},
            ):
                records = provider_map._provider_record_payloads("aoa-demo-connector", None)
                counts = provider_map._provider_record_counts("aoa-demo-connector", None)

        self.assertIsNotNone(records)
        assert records is not None
        self.assertEqual(len(provider_map.PROVIDER_RECORD_DIRECTORIES), len(records))
        self.assertEqual(
            {group: 1 for group in provider_map.PROVIDER_RECORD_DIRECTORIES},
            counts,
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
