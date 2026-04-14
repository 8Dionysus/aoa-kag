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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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

    def test_source_owned_export_dependency_manifest_accepts_memo_cross_repo_supporting(
        self,
    ) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        dependencies = validate_kag.validate_source_owned_export_dependency_manifest(
            registry_surfaces
        )

        self.assertIn(
            ("aoa-memo", validate_kag.EXPECTED_MEMO_KAG_EXPORT_PATH),
            dependencies,
        )
        self.assertEqual(
            dependencies[("aoa-memo", validate_kag.EXPECTED_MEMO_KAG_EXPORT_PATH)][
                "consumed_by"
            ],
            [],
        )

    def test_source_owned_export_dependency_manifest_rejects_zero_primary_for_memo_export(
        self,
    ) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        broken_payload = self.memo_kag_export_payload()
        broken_payload["source_inputs"] = [
            {
                "repo": "aoa-memo",
                "source_class": "memo_object",
                "role": "supporting",
            },
            {
                "repo": "Tree-of-Sophia",
                "source_class": "tos_text",
                "role": "supporting",
            },
        ]

        with self.patched_read_json(
            {
                validate_kag.AOA_MEMO_ROOT / validate_kag.EXPECTED_MEMO_KAG_EXPORT_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_source_owned_export_dependency_manifest(
                    registry_surfaces
                )

        self.assertIn("exactly one primary", str(context.exception))

    def test_source_owned_export_dependency_manifest_rejects_multiple_primary_for_memo_export(
        self,
    ) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        broken_payload = self.memo_kag_export_payload()
        broken_payload["source_inputs"] = [
            {
                "repo": "aoa-memo",
                "source_class": "memo_object",
                "role": "primary",
            },
            {
                "repo": "aoa-memo",
                "source_class": "memo_object",
                "role": "primary",
            },
        ]

        with self.patched_read_json(
            {
                validate_kag.AOA_MEMO_ROOT / validate_kag.EXPECTED_MEMO_KAG_EXPORT_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_source_owned_export_dependency_manifest(
                    registry_surfaces
                )

        self.assertIn("exactly one primary", str(context.exception))

    def test_source_owned_export_dependency_manifest_rejects_wrong_primary_repo_for_memo_export(
        self,
    ) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        broken_payload = self.memo_kag_export_payload()
        broken_payload["source_inputs"] = [
            {
                "repo": "aoa-memo",
                "source_class": "memo_object",
                "role": "supporting",
            },
            {
                "repo": "Tree-of-Sophia",
                "source_class": "tos_text",
                "role": "primary",
            },
        ]

        with self.patched_read_json(
            {
                validate_kag.AOA_MEMO_ROOT / validate_kag.EXPECTED_MEMO_KAG_EXPORT_PATH: broken_payload,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_source_owned_export_dependency_manifest(
                    registry_surfaces
                )

        self.assertIn(".repo must equal 'aoa-memo'", str(context.exception))

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

    def test_tos_zarathustra_route_retrieval_pack_rejects_source_first_reentry_drift(
        self,
    ) -> None:
        registry_payload = validate_kag.build_registry_payload()
        registry_surfaces = self.registry_manifest_surfaces()
        route_pack_payload = validate_kag.build_tos_zarathustra_route_pack_payload(
            registry_payload
        )
        expected_payload = validate_kag.build_tos_zarathustra_route_retrieval_pack_payload(
            registry_payload
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["subordinate_posture"]["source_first_reentry_ref"] = (
            "generated/tos_zarathustra_route_retrieval_pack.min.json"
        )

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_tos_zarathustra_route_retrieval_pack(
                broken_payload,
                registry_surfaces,
                expected_payload,
                route_pack_payload,
            )

        self.assertIn("subordinate_posture", str(context.exception))

    def test_federation_spine_pack_rejects_adjunct_budget_drift(self) -> None:
        registry_payload = validate_kag.build_registry_payload()
        registry_surfaces = self.registry_manifest_surfaces()
        expected_payload = validate_kag.build_federation_spine_payload(
            registry_payload
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["repos"][1]["adjunct_surfaces"][0]["adjunct_budget"][
            "numbered_tiny_path_inclusion"
        ] = "included"

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_federation_spine_pack(
                broken_payload,
                registry_surfaces,
                expected_payload,
            )

        self.assertIn("adjunct_surfaces", str(context.exception))

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

    def test_kag_maturity_governance_manifest_rejects_owner_wait_state_order_drift(self) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        manifest_payload = load_json(validate_kag.KAG_MATURITY_GOVERNANCE_MANIFEST_PATH)
        assert isinstance(manifest_payload, dict)
        broken_manifest = copy.deepcopy(manifest_payload)
        broken_manifest["owner_wait_states"] = list(
            reversed(broken_manifest["owner_wait_states"])
        )

        with self.patched_read_json(
            {
                validate_kag.KAG_MATURITY_GOVERNANCE_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(validate_kag.ValidationError) as context:
                validate_kag.validate_kag_maturity_governance_manifest(
                    registry_surfaces
                )

        self.assertIn("owner_wait_states", str(context.exception))

    def test_kag_maturity_governance_pack_rejects_unblocked_growth(self) -> None:
        registry_surfaces = self.registry_manifest_surfaces()
        expected_payload = validate_kag.build_kag_maturity_governance_payload(
            validate_kag.build_registry_payload()
        )
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["stop_rule"]["blocked_surface_ids"] = []

        with self.assertRaises(validate_kag.ValidationError) as context:
            validate_kag.validate_kag_maturity_governance_pack(
                broken_payload,
                expected_payload,
                registry_surfaces,
            )

        self.assertIn("blocked_surface_ids", str(context.exception))

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

    def test_optional_memo_export_readiness_rejects_missing_direct_relation_target(self) -> None:
        payload = self.memo_kag_export_payload()

        with tempfile.TemporaryDirectory() as tmpdir:
            memo_root = Path(tmpdir)
            generated = memo_root / "generated"
            generated.mkdir()
            (generated / "kag_export.min.json").write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )
            (generated / "memory_object_capsules.json").write_text(
                json.dumps({"capsules": []}, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch.object(validate_kag, "AOA_MEMO_ROOT", memo_root):
                with self.assertRaises(validate_kag.ValidationError) as context:
                    validate_kag.validate_optional_memo_source_owned_export_readiness()

        self.assertIn("direct_relations[0]", str(context.exception))

    def test_optional_memo_export_readiness_rejects_missing_provenance_thread_relation(self) -> None:
        payload = self.memo_kag_export_payload()
        payload["direct_relations"] = [
            relation
            for relation in payload["direct_relations"]
            if relation["relation_type"] != "provenance_thread"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            memo_root = Path(tmpdir)
            generated = memo_root / "generated"
            generated.mkdir()
            (generated / "kag_export.min.json").write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )
            (generated / "memory_object_capsules.json").write_text(
                json.dumps({"memory_objects": []}, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch.object(validate_kag, "AOA_MEMO_ROOT", memo_root):
                with self.assertRaises(validate_kag.ValidationError) as context:
                    validate_kag.validate_optional_memo_source_owned_export_readiness()

        self.assertIn("direct_relations", str(context.exception))


class ValidateQuestbookSurfaceTests(unittest.TestCase):
    def write_valid_surface(self, repo_root: Path) -> None:
        write_text(
            repo_root / "QUESTBOOK.md",
            (REPO_ROOT / "QUESTBOOK.md").read_text(encoding="utf-8"),
        )
        write_text(
            repo_root / "docs" / "QUESTBOOK_KAG_INTEGRATION.md",
            (REPO_ROOT / "docs" / "QUESTBOOK_KAG_INTEGRATION.md").read_text(
                encoding="utf-8"
            ),
        )
        write_text(
            repo_root / "schemas" / "quest.schema.json",
            (REPO_ROOT / "schemas" / "quest.schema.json").read_text(encoding="utf-8"),
        )
        write_text(
            repo_root / "schemas" / "quest_dispatch.schema.json",
            (REPO_ROOT / "schemas" / "quest_dispatch.schema.json").read_text(
                encoding="utf-8"
            ),
        )
        for quest_id in validate_kag.QUEST_IDS:
            write_text(
                repo_root / "quests" / f"{quest_id}.yaml",
                (REPO_ROOT / "quests" / f"{quest_id}.yaml").read_text(encoding="utf-8"),
            )
        write_text(
            repo_root / "examples" / "quest_catalog.min.example.json",
            (REPO_ROOT / "examples" / "quest_catalog.min.example.json").read_text(
                encoding="utf-8"
            ),
        )
        write_text(
            repo_root / "examples" / "quest_dispatch.min.example.json",
            (REPO_ROOT / "examples" / "quest_dispatch.min.example.json").read_text(
                encoding="utf-8"
            ),
        )

    def test_valid_questbook_surface_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)

            with patch.object(validate_kag, "REPO_ROOT", repo_root):
                validate_kag.validate_questbook_surface()

    def test_missing_quest_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            (repo_root / "quests" / "AOA-KAG-Q-0003.yaml").unlink()

            with patch.object(validate_kag, "REPO_ROOT", repo_root):
                with self.assertRaises(validate_kag.ValidationError) as context:
                    validate_kag.validate_questbook_surface()

        self.assertIn("AOA-KAG-Q-0003.yaml", str(context.exception))

    def test_wrong_repo_value_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            write_text(
                repo_root / "quests" / "AOA-KAG-Q-0002.yaml",
                (repo_root / "quests" / "AOA-KAG-Q-0002.yaml")
                .read_text(encoding="utf-8")
                .replace("repo: aoa-kag", "repo: aoa-evals"),
            )

            with patch.object(validate_kag, "REPO_ROOT", repo_root):
                with self.assertRaises(validate_kag.ValidationError) as context:
                    validate_kag.validate_questbook_surface()

        self.assertIn("repo must equal 'aoa-kag'", str(context.exception))

    def test_source_boundary_phrase_missing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            write_text(
                repo_root / "docs" / "QUESTBOOK_KAG_INTEGRATION.md",
                (repo_root / "docs" / "QUESTBOOK_KAG_INTEGRATION.md")
                .read_text(encoding="utf-8")
                .replace("source repos remain the owners of meaning", "source repos stay nearby"),
            )

            with patch.object(validate_kag, "REPO_ROOT", repo_root):
                with self.assertRaises(validate_kag.ValidationError) as context:
                    validate_kag.validate_questbook_surface()

        self.assertIn("source repos remain the owners of meaning", str(context.exception))

    def test_dispatch_example_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            write_text(
                repo_root / "examples" / "quest_dispatch.min.example.json",
                (repo_root / "examples" / "quest_dispatch.min.example.json")
                .read_text(encoding="utf-8")
                .replace(
                    '"source_path": "quests/AOA-KAG-Q-0004.yaml"',
                    '"source_path": "quests/AOA-KAG-Q-9999.yaml"',
                ),
            )

            with patch.object(validate_kag, "REPO_ROOT", repo_root):
                with self.assertRaises(validate_kag.ValidationError) as context:
                    validate_kag.validate_questbook_surface()

        self.assertIn("AOA-KAG-Q-0004", str(context.exception))


if __name__ == "__main__":
    unittest.main()
