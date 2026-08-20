from __future__ import annotations

from .common import *

def validate_top_level_schema(path: Path, label: str) -> None:
    schema = read_json(path)
    if not isinstance(schema, dict):
        fail(f"{label} schema file must contain a JSON object")
    required_top_level = {"$schema", "$id", "title", "type", "properties", "required"}
    missing = sorted(required_top_level - set(schema))
    if missing:
        fail(f"{label} schema is missing required top-level keys: {', '.join(missing)}")

def validate_schema_surface() -> None:
    validate_top_level_schema(SCHEMA_PATH, "registry")
    validate_top_level_schema(LOCAL_KAG_PROVIDER_MAP_SCHEMA_PATH, "local KAG provider map")
    validate_top_level_schema(REPO_LOCAL_KAG_INDEX_SCHEMA_PATH, "repo-local KAG index")
    validate_top_level_schema(
        REPO_LOCAL_KAG_REPOSITORY_INDEX_SCHEMA_PATH,
        "repo-local KAG repository index",
    )
    validate_top_level_schema(REPO_LOCAL_KAG_QUERY_RESULT_SCHEMA_PATH, "repo-local KAG query result")
    validate_top_level_schema(
        REPO_LOCAL_KAG_QUERY_UNAVAILABLE_SCHEMA_PATH,
        "repo-local KAG unavailable query result",
    )
    validate_top_level_schema(KAG_MCP_CAPABILITIES_SCHEMA_PATH, "KAG MCP capabilities")
    validate_top_level_schema(KAG_MCP_RESULT_SCHEMA_PATH, "KAG MCP result")
    validate_top_level_schema(REPO_LOCAL_KAG_FEDERATION_SCHEMA_PATH, "repo-local KAG federation")
    validate_top_level_schema(
        REPO_LOCAL_KAG_RETRIEVAL_PLAN_SCHEMA_PATH,
        "repo-local KAG retrieval plan",
    )
    validate_top_level_schema(
        REPO_LOCAL_KAG_RETRIEVAL_BUNDLE_SCHEMA_PATH,
        "repo-local KAG retrieval bundle",
    )
    validate_top_level_schema(DOMAIN_INDEX_CATALOG_SCHEMA_PATH, "domain index catalog")
    validate_top_level_schema(REPO_LOCAL_KAG_COVERAGE_SCHEMA_PATH, "repo-local KAG coverage")
    for path, label in (
        (REPO_LOCAL_KAG_CORPUS_MANIFEST_SCHEMA_PATH, "repo-local KAG corpus manifest"),
        (REPO_LOCAL_KAG_DISTRIBUTION_MANIFEST_SCHEMA_PATH, "repo-local KAG distribution manifest"),
        (REPO_LOCAL_KAG_HOT_PROFILE_SCHEMA_PATH, "repo-local KAG hot profile"),
        (KAG_ARTIFACT_LOCATOR_SCHEMA_PATH, "KAG artifact locator"),
        (KAG_PACK_SCHEMA_PATH, "KAG transport pack"),
        (KAG_PACK_INDEX_SCHEMA_PATH, "KAG pack index"),
        (KAG_OWNER_FAMILY_RELEASE_SCHEMA_PATH, "KAG owner-family release"),
        (KAG_OS_COMPOSITION_SCHEMA_PATH, "KAG OS composition"),
        (KAG_OWNER_CHANGE_RECEIPT_SCHEMA_PATH, "KAG owner change receipt"),
        (KAG_RECEIPT_GOVERNANCE_SCHEMA_PATH, "KAG receipt governance"),
        (KAG_RECEIPT_GOVERNANCE_REPORT_SCHEMA_PATH, "KAG receipt governance report"),
        (KAG_TIERED_METRICS_SCHEMA_PATH, "KAG tiered metrics"),
        (
            KAG_TIERED_ROLLOUT_EVIDENCE_SCHEMA_PATH,
            "KAG tiered rollout evidence",
        ),
        (KAG_PORTABLE_FAMILY_BUNDLE_SCHEMA_PATH, "KAG portable family bundle"),
        (
            KAG_TIERED_BASELINE_EVIDENCE_SCHEMA_PATH,
            "KAG tiered baseline evidence",
        ),
        (KAG_COVERAGE_BUILD_PACKET_SCHEMA_PATH, "KAG coverage build packet"),
    ):
        validate_top_level_schema(path, label)

def validate_bridge_schema_surface() -> None:
    validate_top_level_schema(BRIDGE_SCHEMA_PATH, "bridge")

def validate_bridge_envelope_schema_surface() -> None:
    validate_top_level_schema(BRIDGE_ENVELOPE_SCHEMA_PATH, "bridge envelope")

def validate_counterpart_schema_surface() -> None:
    validate_top_level_schema(COUNTERPART_SCHEMA_PATH, "counterpart")

def validate_counterpart_federation_exposure_review_manifest_schema_surface() -> None:
    validate_top_level_schema(
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_SCHEMA_PATH,
        "counterpart federation exposure review manifest",
    )

def validate_counterpart_federation_exposure_review_schema_surface() -> None:
    validate_top_level_schema(
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_SCHEMA_PATH,
        "counterpart federation exposure review",
    )

def validate_counterpart_consumer_contract_schema_surface() -> None:
    validate_top_level_schema(
        COUNTERPART_CONSUMER_CONTRACT_SCHEMA_PATH,
        "counterpart consumer contract",
    )

def validate_reasoning_handoff_schema_surface() -> None:
    validate_top_level_schema(REASONING_HANDOFF_SCHEMA_PATH, "reasoning handoff")

def validate_projection_health_receipt_schema_surface() -> None:
    validate_top_level_schema(
        PROJECTION_HEALTH_RECEIPT_SCHEMA_PATH,
        "projection health receipt",
    )

def validate_regrounding_ticket_schema_surface() -> None:
    validate_top_level_schema(
        REGROUNDING_TICKET_SCHEMA_PATH,
        "regrounding ticket",
    )

def validate_technique_lift_manifest_schema_surface() -> None:
    validate_top_level_schema(TECHNIQUE_LIFT_MANIFEST_SCHEMA_PATH, "technique lift manifest")

def validate_technique_lift_pack_schema_surface() -> None:
    validate_top_level_schema(TECHNIQUE_LIFT_PACK_SCHEMA_PATH, "technique lift pack")

def validate_tos_text_chunk_map_manifest_schema_surface() -> None:
    validate_top_level_schema(
        TOS_TEXT_CHUNK_MAP_MANIFEST_SCHEMA_PATH,
        "ToS text chunk map manifest",
    )

def validate_tos_text_chunk_map_schema_surface() -> None:
    validate_top_level_schema(TOS_TEXT_CHUNK_MAP_SCHEMA_PATH, "ToS text chunk map")

def validate_tos_retrieval_axis_manifest_schema_surface() -> None:
    validate_top_level_schema(
        TOS_RETRIEVAL_AXIS_MANIFEST_SCHEMA_PATH,
        "ToS retrieval axis manifest",
    )

def validate_tos_retrieval_axis_schema_surface() -> None:
    validate_top_level_schema(TOS_RETRIEVAL_AXIS_SCHEMA_PATH, "ToS retrieval axis pack")

def validate_tos_zarathustra_route_pack_manifest_schema_surface() -> None:
    validate_top_level_schema(
        TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_SCHEMA_PATH,
        "ToS Zarathustra route pack manifest",
    )

def validate_tos_zarathustra_route_pack_schema_surface() -> None:
    validate_top_level_schema(
        TOS_ZARATHUSTRA_ROUTE_PACK_SCHEMA_PATH,
        "ToS Zarathustra route pack",
    )

def validate_tos_zarathustra_route_retrieval_pack_manifest_schema_surface() -> None:
    validate_top_level_schema(
        TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_SCHEMA_PATH,
        "ToS Zarathustra route retrieval pack manifest",
    )

def validate_tos_zarathustra_route_retrieval_pack_schema_surface() -> None:
    validate_top_level_schema(
        TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_SCHEMA_PATH,
        "ToS Zarathustra route retrieval pack",
    )

def validate_reasoning_handoff_pack_manifest_schema_surface() -> None:
    validate_top_level_schema(
        REASONING_HANDOFF_PACK_MANIFEST_SCHEMA_PATH,
        "reasoning handoff pack manifest",
    )

def validate_reasoning_handoff_pack_schema_surface() -> None:
    validate_top_level_schema(
        REASONING_HANDOFF_PACK_SCHEMA_PATH,
        "reasoning handoff pack",
    )

def validate_return_regrounding_manifest_schema_surface() -> None:
    validate_top_level_schema(
        RETURN_REGROUNDING_MANIFEST_SCHEMA_PATH,
        "return regrounding pack manifest",
    )

def validate_return_regrounding_schema_surface() -> None:
    validate_top_level_schema(
        RETURN_REGROUNDING_SCHEMA_PATH,
        "return regrounding pack",
    )

def validate_kag_maturity_governance_manifest_schema_surface() -> None:
    validate_top_level_schema(
        KAG_MATURITY_GOVERNANCE_MANIFEST_SCHEMA_PATH,
        "KAG maturity governance manifest",
    )

def validate_kag_maturity_governance_schema_surface() -> None:
    validate_top_level_schema(
        KAG_MATURITY_GOVERNANCE_SCHEMA_PATH,
        "KAG maturity governance pack",
    )

def validate_source_owned_export_dependencies_schema_surface() -> None:
    validate_top_level_schema(
        SOURCE_OWNED_EXPORT_DEPENDENCIES_SCHEMA_PATH,
        "source-owned export dependency manifest",
    )

def validate_federation_export_registry_manifest_schema_surface() -> None:
    validate_top_level_schema(
        FEDERATION_EXPORT_REGISTRY_MANIFEST_SCHEMA_PATH,
        "federation export registry manifest",
    )

def validate_federation_export_registry_schema_surface() -> None:
    validate_top_level_schema(
        FEDERATION_EXPORT_REGISTRY_SCHEMA_PATH,
        "federation export registry",
    )

def validate_federation_kag_export_schema_surface() -> None:
    validate_top_level_schema(
        FEDERATION_KAG_EXPORT_SCHEMA_PATH,
        "federation KAG export",
    )

def validate_federation_spine_manifest_schema_surface() -> None:
    validate_top_level_schema(
        FEDERATION_SPINE_MANIFEST_SCHEMA_PATH,
        "federation spine manifest",
    )

def validate_federation_spine_schema_surface() -> None:
    validate_top_level_schema(
        FEDERATION_SPINE_SCHEMA_PATH,
        "federation spine",
    )

def validate_cross_source_node_projection_manifest_schema_surface() -> None:
    validate_top_level_schema(
        CROSS_SOURCE_NODE_PROJECTION_MANIFEST_SCHEMA_PATH,
        "cross-source node projection manifest",
    )

def validate_cross_source_node_projection_schema_surface() -> None:
    validate_top_level_schema(
        CROSS_SOURCE_NODE_PROJECTION_SCHEMA_PATH,
        "cross-source node projection",
    )

def validate_tiny_consumer_bundle_manifest_schema_surface() -> None:
    validate_top_level_schema(
        TINY_CONSUMER_BUNDLE_MANIFEST_SCHEMA_PATH,
        "tiny consumer bundle manifest",
    )

def validate_tiny_consumer_bundle_schema_surface() -> None:
    validate_top_level_schema(TINY_CONSUMER_BUNDLE_SCHEMA_PATH, "tiny consumer bundle")
