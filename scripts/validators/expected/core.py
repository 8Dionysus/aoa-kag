from __future__ import annotations

import os
import re
from pathlib import Path

from ..generation import *

REPO_ROOT = Path(__file__).resolve().parents[3]

KAG_REPO = "aoa-kag"

QUEST_STORE_VALIDATOR_PATH = (
    REPO_ROOT
    / "mechanics"
    / "questbook"
    / "parts"
    / "quest-store"
    / "scripts"
    / "validate_quest_store.py"
)

def repo_root_from_env(env_name: str, default: Path) -> Path:
    override = os.environ.get(env_name)
    if not override:
        return default
    return Path(override).expanduser().resolve()

OS_ABYSS_ROOT = repo_root_from_env("OS_ABYSS_ROOT", REPO_ROOT.parent)

TREE_OF_SOPHIA_ROOT = repo_root_from_env(
    "TREE_OF_SOPHIA_ROOT", REPO_ROOT.parent / "Tree-of-Sophia"
)

SCHEMA_PATH = REPO_ROOT / "schemas" / "kag-registry.schema.json"

LOCAL_KAG_SUBTREE_SCHEMA_PATH = REPO_ROOT / "schemas" / "local-kag-subtree.schema.json"

LOCAL_KAG_SUBTREE_EXAMPLE_PATH = REPO_ROOT / "examples" / "local_kag_subtree.example.json"

LOCAL_KAG_READINESS_MANIFEST_PATH = REPO_ROOT / "manifests" / "local_kag_readiness.json"

PROVIDER_REGISTRY_SCHEMA_PATH = REPO_ROOT / "schemas" / "provider-registry.schema.json"

PROVIDER_REGISTRY_MANIFEST_PATH = REPO_ROOT / "manifests" / "provider_registry.json"

LOCAL_KAG_PROVIDER_MAP_SCHEMA_PATH = REPO_ROOT / "schemas" / "local-kag-provider-map.schema.json"

REPO_LOCAL_KAG_INDEX_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-index.schema.json"

REPO_LOCAL_KAG_REPOSITORY_INDEX_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-repository-index.schema.json"
)

REPO_LOCAL_KAG_FAMILY_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-family-manifest.schema.json"
)

REPO_LOCAL_KAG_QUERY_RESULT_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-query-result.schema.json"
)

KAG_MCP_CAPABILITIES_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "kag-mcp-capabilities.schema.json"
)

KAG_MCP_RESULT_SCHEMA_PATH = REPO_ROOT / "schemas" / "kag-mcp-result.schema.json"

REPO_LOCAL_KAG_FEDERATION_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-federation.schema.json"
)

REPO_LOCAL_KAG_RETRIEVAL_PLAN_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-retrieval-plan.schema.json"
)

REPO_LOCAL_KAG_RETRIEVAL_BUNDLE_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "repo-local-kag-retrieval-bundle.schema.json"
)

DOMAIN_INDEX_CATALOG_SCHEMA_PATH = REPO_ROOT / "schemas" / "domain-index-catalog.schema.json"

REPO_LOCAL_KAG_COVERAGE_SCHEMA_PATH = REPO_ROOT / "schemas" / "repo-local-kag-coverage.schema.json"

REPO_LOCAL_KAG_INDEX_EXAMPLE_PATH = REPO_ROOT / "examples" / "repo_local_kag_index.example.json"

REPO_LOCAL_KAG_QUERY_RESULT_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "repo_local_kag_query_result.example.json"
)

KAG_MCP_CAPABILITIES_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "kag_mcp_capabilities.example.json"
)

KAG_MCP_RESULT_EXAMPLE_PATH = REPO_ROOT / "examples" / "kag_mcp_result.example.json"

REPO_LOCAL_KAG_FEDERATION_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "repo_local_kag_federation.example.json"
)

REPO_LOCAL_KAG_RETRIEVAL_PLAN_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "repo_local_kag_retrieval_plan.example.json"
)

REPO_LOCAL_KAG_RETRIEVAL_BUNDLE_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "repo_local_kag_retrieval_bundle.example.json"
)

DOMAIN_INDEX_CATALOG_EXAMPLE_PATH = REPO_ROOT / "examples" / "domain_index_catalog.example.json"

REPO_LOCAL_KAG_INDEX_PATH = REPO_ROOT / "kag" / "indexes" / "source_surface_index.json"

REPO_LOCAL_KAG_FAMILY_MANIFEST_PATH = (
    REPO_ROOT / "kag" / "indexes" / "index_family.manifest.json"
)

REPO_LOCAL_KAG_COVERAGE_PATH = REPO_ROOT / "generated" / "repo_local_kag_coverage.json"

REPO_LOCAL_KAG_COVERAGE_MIN_PATH = REPO_ROOT / "generated" / "repo_local_kag_coverage.min.json"

BRIDGE_SCHEMA_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "schemas" / "bridge-retrieval-surface.schema.json"
)

BRIDGE_EXAMPLE_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "examples" / "tos_retrieval_axis_surface.example.json"
)

BRIDGE_ENVELOPE_SCHEMA_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "schemas" / "bridge-envelope.schema.json"
)

BRIDGE_ENVELOPE_EXAMPLE_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "examples" / "aoa_tos_bridge_envelope.example.json"
)

COUNTERPART_SCHEMA_PATH = COUNTERPART_EDGE_PART_ROOT / "schemas" / "counterpart-edge-surface.schema.json"

COUNTERPART_EXAMPLE_PATH = COUNTERPART_EDGE_PART_ROOT / "examples" / "counterpart_edge_view.example.json"

COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_SCHEMA_PATH = (
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_PART_ROOT
    / "schemas"
    / "counterpart-federation-exposure-review-manifest.schema.json"
)

COUNTERPART_FEDERATION_EXPOSURE_REVIEW_SCHEMA_PATH = (
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_PART_ROOT
    / "schemas"
    / "counterpart-federation-exposure-review.schema.json"
)

COUNTERPART_FEDERATION_EXPOSURE_REVIEW_EXAMPLE_PATH = (
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_PART_ROOT
    / "examples"
    / "counterpart_federation_exposure_review.example.json"
)

COUNTERPART_CONSUMER_CONTRACT_SCHEMA_PATH = (
    COUNTERPART_EDGE_PART_ROOT / "schemas" / "counterpart-consumer-contract.schema.json"
)

COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH = (
    COUNTERPART_EDGE_PART_ROOT / "examples" / "counterpart_consumer_contract.example.json"
)

REASONING_HANDOFF_SCHEMA_PATH = (
    REASONING_HANDOFF_PART_ROOT / "schemas" / "reasoning-handoff-guardrail.schema.json"
)

REASONING_HANDOFF_EXAMPLE_PATH = (
    REASONING_HANDOFF_PART_ROOT / "examples" / "reasoning_handoff_guardrail.example.json"
)

TECHNIQUE_LIFT_MANIFEST_SCHEMA_PATH = (
    TECHNIQUE_LIFT_PART_ROOT / "schemas" / "technique-lift-pack-manifest.schema.json"
)

TECHNIQUE_LIFT_PACK_SCHEMA_PATH = (
    TECHNIQUE_LIFT_PART_ROOT / "schemas" / "technique-lift-pack.schema.json"
)

TOS_TEXT_CHUNK_MAP_MANIFEST_SCHEMA_PATH = (
    TOS_TEXT_CHUNK_MAP_PART_ROOT / "schemas" / "tos-text-chunk-map-manifest.schema.json"
)

TOS_TEXT_CHUNK_MAP_SCHEMA_PATH = (
    TOS_TEXT_CHUNK_MAP_PART_ROOT / "schemas" / "tos-text-chunk-map.schema.json"
)

TOS_TEXT_CHUNK_MAP_EXAMPLE_PATH = (
    TOS_TEXT_CHUNK_MAP_PART_ROOT / "examples" / "tos_text_chunk_map.example.json"
)

TOS_RETRIEVAL_AXIS_MANIFEST_SCHEMA_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "schemas" / "tos-retrieval-axis-pack-manifest.schema.json"
)

TOS_RETRIEVAL_AXIS_SCHEMA_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "schemas" / "tos-retrieval-axis-pack.schema.json"
)

TOS_RETRIEVAL_AXIS_EXAMPLE_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT / "examples" / "tos_retrieval_axis_pack.example.json"
)

TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_SCHEMA_PATH = (
    TOS_ROUTE_LIFT_PART_ROOT / "schemas" / "tos-zarathustra-route-pack-manifest.schema.json"
)

TOS_ZARATHUSTRA_ROUTE_PACK_SCHEMA_PATH = (
    TOS_ROUTE_LIFT_PART_ROOT / "schemas" / "tos-zarathustra-route-pack.schema.json"
)

TOS_ZARATHUSTRA_ROUTE_PACK_EXAMPLE_PATH = (
    TOS_ROUTE_LIFT_PART_ROOT / "examples" / "tos_zarathustra_route_pack.example.json"
)

TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_SCHEMA_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT
    / "schemas"
    / "tos-zarathustra-route-retrieval-pack-manifest.schema.json"
)

TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_SCHEMA_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT
    / "schemas"
    / "tos-zarathustra-route-retrieval-pack.schema.json"
)

TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_EXAMPLE_PATH = (
    TOS_RETRIEVAL_AXIS_PART_ROOT
    / "examples"
    / "tos_zarathustra_route_retrieval_pack.example.json"
)

TOS_TEXT_CHUNK_MAP_EXAMPLE_SEGMENT_ID = "seg.1.1.1.10"

REASONING_HANDOFF_PACK_MANIFEST_SCHEMA_PATH = (
    REASONING_HANDOFF_PART_ROOT
    / "schemas"
    / "reasoning-handoff-pack-manifest.schema.json"
)

REASONING_HANDOFF_PACK_SCHEMA_PATH = (
    REASONING_HANDOFF_PART_ROOT / "schemas" / "reasoning-handoff-pack.schema.json"
)

RETURN_REGROUNDING_MANIFEST_SCHEMA_PATH = (
    RETURN_REGROUNDING_PART_ROOT
    / "schemas"
    / "return-regrounding-pack-manifest.schema.json"
)

RETURN_REGROUNDING_SCHEMA_PATH = (
    RETURN_REGROUNDING_PART_ROOT / "schemas" / "return-regrounding-pack.schema.json"
)

KAG_MATURITY_GOVERNANCE_MANIFEST_SCHEMA_PATH = (
    SURFACE_GROWTH_STOP_RULE_PART_ROOT
    / "schemas"
    / "kag-maturity-governance-manifest.schema.json"
)

KAG_MATURITY_GOVERNANCE_SCHEMA_PATH = (
    SURFACE_GROWTH_STOP_RULE_PART_ROOT
    / "schemas"
    / "kag-maturity-governance.schema.json"
)

SOURCE_OWNED_EXPORT_DEPENDENCIES_SCHEMA_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT
    / "schemas"
    / "source-owned-export-dependencies.schema.json"
)

SOURCE_OWNED_EXPORT_DEPENDENCIES_DOC_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT / "docs" / "source-owned-export-dependencies.md"
)

FEDERATION_EXPORT_REGISTRY_MANIFEST_SCHEMA_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT
    / "schemas"
    / "federation-export-registry-manifest.schema.json"
)

FEDERATION_EXPORT_REGISTRY_SCHEMA_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT / "schemas" / "federation-export-registry.schema.json"
)

FEDERATION_EXPORT_REGISTRY_EXAMPLE_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT / "examples" / "federation_export_registry.example.json"
)

FEDERATION_KAG_EXPORT_SCHEMA_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT / "schemas" / "federation-kag-export.schema.json"
)

FEDERATION_KAG_EXPORT_EXAMPLE_PATH = (
    SOURCE_OWNED_EXPORT_PART_ROOT / "examples" / "federation_kag_export.example.json"
)

FEDERATION_SPINE_MANIFEST_SCHEMA_PATH = (
    FEDERATION_SPINE_PART_ROOT / "schemas" / "federation-spine-manifest.schema.json"
)

FEDERATION_SPINE_SCHEMA_PATH = (
    FEDERATION_SPINE_PART_ROOT / "schemas" / "federation-spine.schema.json"
)

CROSS_SOURCE_NODE_PROJECTION_MANIFEST_SCHEMA_PATH = (
    CROSS_SOURCE_NODE_PROJECTION_PART_ROOT
    / "schemas"
    / "cross-source-node-projection-manifest.schema.json"
)

CROSS_SOURCE_NODE_PROJECTION_SCHEMA_PATH = (
    CROSS_SOURCE_NODE_PROJECTION_PART_ROOT
    / "schemas"
    / "cross-source-node-projection.schema.json"
)

CROSS_SOURCE_NODE_PROJECTION_EXAMPLE_PATH = (
    CROSS_SOURCE_NODE_PROJECTION_PART_ROOT
    / "examples"
    / "cross_source_node_projection.example.json"
)

TINY_CONSUMER_BUNDLE_MANIFEST_SCHEMA_PATH = (
    TINY_CONSUMER_BUNDLE_PART_ROOT
    / "schemas"
    / "tiny-consumer-bundle-manifest.schema.json"
)

TINY_CONSUMER_BUNDLE_SCHEMA_PATH = (
    TINY_CONSUMER_BUNDLE_PART_ROOT / "schemas" / "tiny-consumer-bundle.schema.json"
)

TINY_CONSUMER_BUNDLE_EXAMPLE_PATH = (
    TINY_CONSUMER_BUNDLE_PART_ROOT / "examples" / "tiny_consumer_bundle.example.json"
)

RETURN_REGROUNDING_EXAMPLE_PATH = (
    RETURN_REGROUNDING_PART_ROOT / "examples" / "return_regrounding_pack.example.json"
)

KAG_MATURITY_GOVERNANCE_EXAMPLE_PATH = (
    SURFACE_GROWTH_STOP_RULE_PART_ROOT
    / "examples"
    / "kag_maturity_governance.example.json"
)

ANTIFRAGILITY_PARTS_ROOT = REPO_ROOT / "mechanics" / "antifragility" / "parts"

PROJECTION_HEALTH_PART_ROOT = ANTIFRAGILITY_PARTS_ROOT / "projection-health"

PROJECTION_QUARANTINE_PART_ROOT = ANTIFRAGILITY_PARTS_ROOT / "projection-quarantine"

RETRIEVAL_OUTAGE_REGROUNDING_PART_ROOT = (
    ANTIFRAGILITY_PARTS_ROOT / "retrieval-outage-regrounding"
)

KAG_STRESS_REGROUNDING_DOC_PATH = (
    PROJECTION_HEALTH_PART_ROOT / "docs" / "stress-regrounding.md"
)

KAG_PROJECTION_QUARANTINE_DOC_PATH = (
    PROJECTION_QUARANTINE_PART_ROOT / "docs" / "projection-quarantine.md"
)

PROJECTION_HEALTH_RECEIPT_SCHEMA_PATH = (
    PROJECTION_HEALTH_PART_ROOT / "schemas" / "projection_health_receipt_v1.json"
)

REGROUNDING_TICKET_SCHEMA_PATH = (
    RETRIEVAL_OUTAGE_REGROUNDING_PART_ROOT / "schemas" / "regrounding_ticket_v1.json"
)

PROJECTION_HEALTH_RECEIPT_EXAMPLE_PATH = (
    PROJECTION_HEALTH_PART_ROOT / "examples" / "projection_health_receipt.example.json"
)

REGROUNDING_TICKET_EXAMPLE_PATH = (
    RETRIEVAL_OUTAGE_REGROUNDING_PART_ROOT
    / "examples"
    / "regrounding_ticket.example.json"
)

PROJECTION_HEALTH_RECEIPT_EXAMPLE_PATHS = tuple(
    sorted((PROJECTION_HEALTH_PART_ROOT / "examples").glob("projection_health_receipt*.example.json"))
)

REGROUNDING_TICKET_EXAMPLE_PATHS = tuple(
    sorted((RETRIEVAL_OUTAGE_REGROUNDING_PART_ROOT / "examples").glob("regrounding_ticket*.example.json"))
)

ALLOWED_STATUS = {"active", "planned", "experimental", "deprecated"}

ALLOWED_SOURCE_CLASS = {
    "technique_bundle",
    "skill_bundle",
    "eval_bundle",
    "playbook_bundle",
    "memo_object",
    "tos_text",
    "review_surface",
}

ALLOWED_DERIVED_KIND = {
    "section_manifest",
    "metadata_spine",
    "relation_view",
    "provenance_view",
    "chunk_map",
    "node_projection",
    "edge_projection",
    "retrieval_surface",
}

ALLOWED_PROVENANCE = {
    "strict_source_linked",
    "bounded_source_linked",
    "derived_with_handles",
}

ALLOWED_FRAMEWORK = {
    "neutral",
    "hipporag_ready",
    "llamaindex_ready",
    "multi_consumer_ready",
}

ALLOWED_SOURCE_INPUT_ROLE = {"primary", "supporting"}

ALLOWED_COUNTERPART_MODE = {"analogy", "support", "tension", "calibration"}

ALLOWED_QUERY_MODES = {"local_search", "global_search", "drift_search"}
