from __future__ import annotations

from .common import *
from .example_contracts import *
from .local_contracts import *
from .manifest_contracts import *
from .projection_parity import *
from .schema_surfaces import *
from .sibling_readiness import *
from .source_refs import *

def main() -> int:
    missing_cross_repo_roots: list[str] = []
    try:
        validate_nested_agents_docs()
        validate_mechanics_skeleton_surface()
        validate_questbook_surface()
        validate_schema_surface()
        validate_bridge_schema_surface()
        validate_bridge_envelope_schema_surface()
        validate_counterpart_schema_surface()
        validate_counterpart_federation_exposure_review_manifest_schema_surface()
        validate_counterpart_federation_exposure_review_schema_surface()
        validate_counterpart_consumer_contract_schema_surface()
        validate_reasoning_handoff_schema_surface()
        validate_projection_health_receipt_schema_surface()
        validate_regrounding_ticket_schema_surface()
        validate_technique_lift_manifest_schema_surface()
        validate_technique_lift_pack_schema_surface()
        validate_tos_text_chunk_map_manifest_schema_surface()
        validate_tos_text_chunk_map_schema_surface()
        validate_tos_retrieval_axis_manifest_schema_surface()
        validate_tos_retrieval_axis_schema_surface()
        validate_tos_zarathustra_route_pack_manifest_schema_surface()
        validate_tos_zarathustra_route_pack_schema_surface()
        validate_tos_zarathustra_route_retrieval_pack_manifest_schema_surface()
        validate_tos_zarathustra_route_retrieval_pack_schema_surface()
        validate_reasoning_handoff_pack_manifest_schema_surface()
        validate_reasoning_handoff_pack_schema_surface()
        validate_return_regrounding_manifest_schema_surface()
        validate_return_regrounding_schema_surface()
        validate_kag_maturity_governance_manifest_schema_surface()
        validate_kag_maturity_governance_schema_surface()
        validate_source_owned_export_dependencies_schema_surface()
        validate_federation_export_registry_manifest_schema_surface()
        validate_federation_export_registry_schema_surface()
        validate_federation_kag_export_schema_surface()
        validate_federation_spine_manifest_schema_surface()
        validate_federation_spine_schema_surface()
        validate_cross_source_node_projection_manifest_schema_surface()
        validate_cross_source_node_projection_schema_surface()
        validate_tiny_consumer_bundle_manifest_schema_surface()
        validate_tiny_consumer_bundle_schema_surface()
        validate_antifragility_stress_surfaces()

        registry_manifest_payload = read_json(REGISTRY_MANIFEST_PATH)
        registry_manifest_surfaces = validate_registry_payload(
            registry_manifest_payload,
            label="registry manifest",
        )
        missing_cross_repo_roots = missing_full_cross_repo_roots()
        if missing_cross_repo_roots:
            print(
                "[warn] skipped cross-repo manifest/generated validation because "
                "source roots are unavailable: " + ", ".join(missing_cross_repo_roots),
                file=sys.stderr,
            )
            print("[ok] validated local KAG surfaces; full cross-repo validation was skipped")
            return 0
        validate_technique_lift_manifest(registry_manifest_surfaces)
        validate_tos_text_chunk_map_manifest(registry_manifest_surfaces)
        validate_tos_retrieval_axis_manifest(registry_manifest_surfaces)
        validate_tos_zarathustra_route_pack_manifest(registry_manifest_surfaces)
        validate_tos_zarathustra_route_retrieval_pack_manifest(
            registry_manifest_surfaces
        )
        validate_reasoning_handoff_manifest()
        validate_return_regrounding_manifest()
        validate_kag_maturity_governance_manifest(registry_manifest_surfaces)
        source_owned_export_dependencies = (
            validate_source_owned_export_dependency_manifest(
                registry_manifest_surfaces
            )
        )
        federation_export_registry_entries = validate_federation_export_registry_manifest(
            source_owned_export_dependencies
        )
        validate_federation_spine_manifest(
            registry_manifest_surfaces,
            source_owned_export_dependencies,
            federation_export_registry_entries,
        )
        validate_cross_source_node_projection_manifest(
            registry_manifest_surfaces,
            source_owned_export_dependencies,
        )
        validate_tiny_consumer_bundle_manifest(registry_manifest_surfaces)
        validate_counterpart_federation_exposure_review_manifest()

        expected_registry_payload = build_registry_payload()
        expected_technique_lift_pack_payload = build_technique_lift_pack_payload(
            expected_registry_payload
        )
        expected_tos_text_chunk_map_payload = build_tos_text_chunk_map_payload(
            expected_registry_payload
        )
        expected_tos_retrieval_axis_payload = build_tos_retrieval_axis_pack_payload(
            expected_registry_payload
        )
        expected_tos_zarathustra_route_pack_payload = (
            build_tos_zarathustra_route_pack_payload(expected_registry_payload)
        )
        expected_tos_zarathustra_route_retrieval_pack_payload = (
            build_tos_zarathustra_route_retrieval_pack_payload(
                expected_registry_payload,
                route_pack_payload=expected_tos_zarathustra_route_pack_payload,
            )
        )
        expected_reasoning_handoff_pack_payload = build_reasoning_handoff_pack_payload()
        expected_return_regrounding_pack_payload = build_return_regrounding_pack_payload(
            expected_registry_payload
        )
        expected_kag_maturity_governance_payload = build_kag_maturity_governance_payload(
            expected_registry_payload
        )
        expected_federation_export_registry_payload = (
            build_federation_export_registry_payload()
        )
        expected_federation_spine_payload = build_federation_spine_payload(
            expected_registry_payload,
            federation_export_registry_payload=expected_federation_export_registry_payload,
        )
        expected_cross_source_node_projection_payload = (
            build_cross_source_node_projection_payload(expected_registry_payload)
        )
        expected_counterpart_federation_exposure_review_payload = (
            build_counterpart_federation_exposure_review_payload(expected_registry_payload)
        )
        expected_tiny_consumer_bundle_payload = build_tiny_consumer_bundle_payload(
            expected_registry_payload
        )

        validate_generated_text(
            REGISTRY_OUTPUT_PATH,
            encode_json(expected_registry_payload, pretty=True),
            label="generated registry",
        )
        validate_generated_text(
            REGISTRY_MIN_OUTPUT_PATH,
            encode_json(expected_registry_payload, pretty=False),
            label="generated compact registry",
        )
        validate_generated_text(
            TECHNIQUE_LIFT_OUTPUT_PATH,
            encode_json(expected_technique_lift_pack_payload, pretty=True),
            label="generated technique lift pack",
        )
        validate_generated_text(
            TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
            encode_json(expected_technique_lift_pack_payload, pretty=False),
            label="generated compact technique lift pack",
        )
        validate_generated_text(
            TOS_TEXT_CHUNK_MAP_OUTPUT_PATH,
            encode_json(expected_tos_text_chunk_map_payload, pretty=True),
            label="generated ToS text chunk map",
        )
        validate_generated_text(
            TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
            encode_json(expected_tos_text_chunk_map_payload, pretty=False),
            label="generated compact ToS text chunk map",
        )
        validate_generated_text(
            TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
            encode_json(expected_tos_retrieval_axis_payload, pretty=True),
            label="generated ToS retrieval axis pack",
        )
        validate_generated_text(
            TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
            encode_json(expected_tos_retrieval_axis_payload, pretty=False),
            label="generated compact ToS retrieval axis pack",
        )
        validate_generated_text(
            TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH,
            encode_json(expected_tos_zarathustra_route_pack_payload, pretty=True),
            label="generated ToS Zarathustra route pack",
        )
        validate_generated_text(
            TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH,
            encode_json(expected_tos_zarathustra_route_pack_payload, pretty=False),
            label="generated compact ToS Zarathustra route pack",
        )
        validate_generated_text(
            TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATH,
            encode_json(expected_tos_zarathustra_route_retrieval_pack_payload, pretty=True),
            label="generated ToS Zarathustra route retrieval pack",
        )
        validate_generated_text(
            TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH,
            encode_json(expected_tos_zarathustra_route_retrieval_pack_payload, pretty=False),
            label="generated compact ToS Zarathustra route retrieval pack",
        )
        validate_generated_text(
            REASONING_HANDOFF_OUTPUT_PATH,
            encode_json(expected_reasoning_handoff_pack_payload, pretty=True),
            label="generated reasoning handoff pack",
        )
        validate_generated_text(
            REASONING_HANDOFF_MIN_OUTPUT_PATH,
            encode_json(expected_reasoning_handoff_pack_payload, pretty=False),
            label="generated compact reasoning handoff pack",
        )
        validate_generated_text(
            FEDERATION_EXPORT_REGISTRY_OUTPUT_PATH,
            encode_json(expected_federation_export_registry_payload, pretty=True),
            label="generated federation export registry",
        )
        validate_generated_text(
            FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH,
            encode_json(expected_federation_export_registry_payload, pretty=False),
            label="generated compact federation export registry",
        )
        validate_generated_text(
            RETURN_REGROUNDING_OUTPUT_PATH,
            encode_json(expected_return_regrounding_pack_payload, pretty=True),
            label="generated return regrounding pack",
        )
        validate_generated_text(
            RETURN_REGROUNDING_MIN_OUTPUT_PATH,
            encode_json(expected_return_regrounding_pack_payload, pretty=False),
            label="generated compact return regrounding pack",
        )
        validate_generated_text(
            KAG_MATURITY_GOVERNANCE_OUTPUT_PATH,
            encode_json(expected_kag_maturity_governance_payload, pretty=True),
            label="generated KAG maturity governance pack",
        )
        validate_generated_text(
            KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH,
            encode_json(expected_kag_maturity_governance_payload, pretty=False),
            label="generated compact KAG maturity governance pack",
        )
        validate_generated_text(
            FEDERATION_SPINE_OUTPUT_PATH,
            encode_json(expected_federation_spine_payload, pretty=True),
            label="generated federation spine",
        )
        validate_generated_text(
            FEDERATION_SPINE_MIN_OUTPUT_PATH,
            encode_json(expected_federation_spine_payload, pretty=False),
            label="generated compact federation spine",
        )
        validate_generated_text(
            CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
            encode_json(expected_cross_source_node_projection_payload, pretty=True),
            label="generated cross-source node projection pack",
        )
        validate_generated_text(
            CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
            encode_json(expected_cross_source_node_projection_payload, pretty=False),
            label="generated compact cross-source node projection pack",
        )
        validate_generated_text(
            COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
            encode_json(expected_counterpart_federation_exposure_review_payload, pretty=True),
            label="generated counterpart federation exposure review",
        )
        validate_generated_text(
            COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
            encode_json(expected_counterpart_federation_exposure_review_payload, pretty=False),
            label="generated compact counterpart federation exposure review",
        )
        validate_generated_text(
            TINY_CONSUMER_BUNDLE_OUTPUT_PATH,
            encode_json(expected_tiny_consumer_bundle_payload, pretty=True),
            label="generated tiny consumer bundle",
        )
        validate_generated_text(
            TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
            encode_json(expected_tiny_consumer_bundle_payload, pretty=False),
            label="generated compact tiny consumer bundle",
        )

        generated_registry_payload = read_json(REGISTRY_MIN_OUTPUT_PATH)
        generated_surfaces_by_id = validate_registry_payload(
            generated_registry_payload,
            label="generated registry",
        )
        validate_technique_lift_pack(
            read_json(TECHNIQUE_LIFT_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
        )
        validate_tos_text_chunk_map_pack(
            read_json(TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
            expected_tos_text_chunk_map_payload,
        )
        validate_tos_retrieval_axis_pack(
            read_json(TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
            expected_tos_retrieval_axis_payload,
        )
        live_tos_zarathustra_route_pack_payload = read_json(
            TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH
        )
        validate_tos_zarathustra_route_pack(
            live_tos_zarathustra_route_pack_payload,
            generated_surfaces_by_id,
            expected_tos_zarathustra_route_pack_payload,
        )
        validate_tos_zarathustra_route_retrieval_pack(
            read_json(TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
            expected_tos_zarathustra_route_retrieval_pack_payload,
            live_tos_zarathustra_route_pack_payload,
        )
        validate_reasoning_handoff_pack(
            read_json(REASONING_HANDOFF_MIN_OUTPUT_PATH),
        )
        validate_federation_export_registry_pack(
            read_json(FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH),
            expected_federation_export_registry_payload,
        )
        validate_return_regrounding_pack(
            read_json(RETURN_REGROUNDING_MIN_OUTPUT_PATH),
            expected_return_regrounding_pack_payload,
        )
        validate_kag_maturity_governance_pack(
            read_json(KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH),
            expected_kag_maturity_governance_payload,
            generated_surfaces_by_id,
        )
        validate_federation_spine_pack(
            read_json(FEDERATION_SPINE_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
            expected_federation_spine_payload,
        )
        validate_cross_source_node_projection_pack(
            read_json(CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
            expected_cross_source_node_projection_payload,
        )
        validate_counterpart_federation_exposure_review_pack(
            expected_counterpart_federation_exposure_review_payload
        )
        validate_tiny_consumer_bundle_pack(expected_tiny_consumer_bundle_payload)
        validate_bridge_example(generated_surfaces_by_id)
        validate_bridge_envelope_example()
        validate_counterpart_example(generated_surfaces_by_id)
        validate_counterpart_consumer_contract_example(generated_surfaces_by_id)
        validate_tos_text_chunk_map_example(expected_tos_text_chunk_map_payload)
        validate_tos_retrieval_axis_example(expected_tos_retrieval_axis_payload)
        validate_tos_zarathustra_route_pack_example(
            expected_tos_zarathustra_route_pack_payload
        )
        validate_tos_zarathustra_route_retrieval_pack_example(
            expected_tos_zarathustra_route_retrieval_pack_payload
        )
        validate_reasoning_handoff_example()
        validate_return_regrounding_example(expected_return_regrounding_pack_payload)
        validate_kag_maturity_governance_example()
        validate_federation_export_registry_example()
        validate_federation_kag_export_example()
        validate_optional_memo_source_owned_export_readiness()
        validate_memo_source_owned_export_consumer_boundary_doc()
        validate_cross_source_node_projection_example(
            expected_cross_source_node_projection_payload
        )
        validate_counterpart_federation_exposure_review_example(
            expected_counterpart_federation_exposure_review_payload
        )
        validate_tiny_consumer_bundle_example(expected_tiny_consumer_bundle_payload)
    except ValidationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print("[ok] validated nested AGENTS docs")
    print("[ok] validated mechanics skeleton")
    print("[ok] validated questbook quest-store surfaces")
    print("[ok] validated KAG registry schema surface")
    print("[ok] validated bridge retrieval surface schema")
    print("[ok] validated bridge envelope schema")
    print("[ok] validated counterpart edge surface schema")
    print("[ok] validated counterpart federation exposure review manifest schema")
    print("[ok] validated counterpart federation exposure review schema")
    print("[ok] validated counterpart consumer contract schema")
    print("[ok] validated reasoning handoff guardrail schema")
    print("[ok] validated projection health receipt schema")
    print("[ok] validated regrounding ticket schema")
    print("[ok] validated technique lift manifest schema")
    print("[ok] validated technique lift pack schema")
    print("[ok] validated ToS text chunk map manifest schema")
    print("[ok] validated ToS text chunk map schema")
    print("[ok] validated ToS retrieval axis manifest schema")
    print("[ok] validated ToS retrieval axis pack schema")
    print("[ok] validated ToS Zarathustra route pack manifest schema")
    print("[ok] validated ToS Zarathustra route pack schema")
    print("[ok] validated ToS Zarathustra route retrieval pack manifest schema")
    print("[ok] validated ToS Zarathustra route retrieval pack schema")
    print("[ok] validated reasoning handoff pack manifest schema")
    print("[ok] validated reasoning handoff pack schema")
    print("[ok] validated return regrounding pack manifest schema")
    print("[ok] validated return regrounding pack schema")
    print("[ok] validated KAG maturity governance manifest schema")
    print("[ok] validated KAG maturity governance pack schema")
    print("[ok] validated source-owned export dependency manifest schema")
    print("[ok] validated federation export registry manifest schema")
    print("[ok] validated federation export registry schema")
    print("[ok] validated federation KAG export schema")
    print("[ok] validated federation spine manifest schema")
    print("[ok] validated federation spine schema")
    print("[ok] validated cross-source node projection manifest schema")
    print("[ok] validated cross-source node projection schema")
    print("[ok] validated tiny consumer bundle manifest schema")
    print("[ok] validated tiny consumer bundle schema")
    print("[ok] validated manifests/kag_registry.json")
    print(f"[ok] validated {TECHNIQUE_LIFT_MANIFEST_REF}")
    print(f"[ok] validated {TOS_TEXT_CHUNK_MAP_MANIFEST_REF}")
    print(f"[ok] validated {TOS_RETRIEVAL_AXIS_MANIFEST_REF}")
    print(f"[ok] validated {TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_REF}")
    print(f"[ok] validated {TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_REF}")
    print(f"[ok] validated {REASONING_HANDOFF_MANIFEST_REF}")
    print(f"[ok] validated {RETURN_REGROUNDING_MANIFEST_REF}")
    print(f"[ok] validated {KAG_MATURITY_GOVERNANCE_MANIFEST_REF}")
    print(f"[ok] validated {SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_REF}")
    print(f"[ok] validated {FEDERATION_EXPORT_REGISTRY_MANIFEST_REF}")
    print(f"[ok] validated {FEDERATION_SPINE_MANIFEST_REF}")
    print(f"[ok] validated {CROSS_SOURCE_NODE_PROJECTION_MANIFEST_REF}")
    print(f"[ok] validated {COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_REF}")
    print("[ok] validated mechanics/boundary-bridge/parts/tiny-consumer-bundle/manifests/tiny_consumer_bundle.json")
    print("[ok] validated generated registry outputs are up to date")
    print("[ok] validated generated technique lift pack outputs are up to date")
    print("[ok] validated generated ToS text chunk map outputs are up to date")
    print("[ok] validated generated ToS retrieval axis pack outputs are up to date")
    print("[ok] validated generated ToS Zarathustra route pack outputs are up to date")
    print("[ok] validated generated ToS Zarathustra route retrieval pack outputs are up to date")
    print("[ok] validated generated reasoning handoff pack outputs are up to date")
    print("[ok] validated generated federation export registry outputs are up to date")
    print("[ok] validated generated return regrounding pack outputs are up to date")
    print("[ok] validated generated KAG maturity governance pack outputs are up to date")
    print("[ok] validated generated federation spine outputs are up to date")
    print("[ok] validated generated cross-source node projection outputs are up to date")
    print("[ok] validated generated counterpart federation exposure review outputs are up to date")
    print("[ok] validated generated tiny consumer bundle outputs are up to date")
    print("[ok] validated generated technique lift pack structure")
    print("[ok] validated generated ToS text chunk map structure")
    print("[ok] validated generated ToS retrieval axis pack structure")
    print("[ok] validated generated ToS Zarathustra route pack structure")
    print("[ok] validated generated ToS Zarathustra route retrieval pack structure")
    print("[ok] validated generated reasoning handoff pack structure")
    print("[ok] validated generated federation export registry structure")
    print("[ok] validated generated return regrounding pack structure")
    print("[ok] validated generated KAG maturity governance pack structure")
    print("[ok] validated generated federation spine structure")
    print("[ok] validated generated cross-source node projection structure")
    print("[ok] validated generated counterpart federation exposure review structure")
    print("[ok] validated generated tiny consumer bundle structure")
    print("[ok] validated antifragility projection-health adjunct surfaces")
    print("[ok] validated bridge retrieval example")
    print("[ok] validated bridge envelope example")
    print("[ok] validated counterpart edge example")
    print("[ok] validated counterpart consumer contract example")
    print("[ok] validated ToS text chunk map example")
    print("[ok] validated ToS retrieval axis example")
    print("[ok] validated ToS Zarathustra route pack example")
    print("[ok] validated ToS Zarathustra route retrieval pack example")
    print("[ok] validated reasoning handoff guardrail example")
    print("[ok] validated return regrounding example")
    print("[ok] validated KAG maturity governance example")
    print("[ok] validated federation export registry example")
    print("[ok] validated federation KAG export example")
    if AOA_MEMO_ROOT.exists():
        print("[ok] validated optional aoa-memo source-owned export readiness")
    print("[ok] validated memo source-owned export consumer boundary doc")
    print("[ok] validated cross-source node projection example")
    print("[ok] validated counterpart federation exposure review example")
    print("[ok] validated tiny consumer bundle example")
    return 0
