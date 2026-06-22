from __future__ import annotations

import os
import re
from pathlib import Path

from .generation import *

REPO_ROOT = Path(__file__).resolve().parents[2]

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

TREE_OF_SOPHIA_ROOT = repo_root_from_env(
    "TREE_OF_SOPHIA_ROOT", REPO_ROOT.parent / "Tree-of-Sophia"
)

SCHEMA_PATH = REPO_ROOT / "schemas" / "kag-registry.schema.json"

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

EXPECTED_AUTHORITATIVE_SOURCE_REFS = {
    "Tree-of-Sophia/ToS/doctrine/NODE_CONTRACT.md",
    "Tree-of-Sophia/ToS/doctrine/PRACTICE_BRANCH.md",
    "aoa-memo/mechanics/recurrence-support/docs/WITNESS_TRACE_CONTRACT.md",
}

EXPECTED_DERIVED_SURFACE_REFS = {
    "docs/BRIDGE_CONTRACTS.md#retrieval-axis-contract",
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_surface.example.json",
    COUNTERPART_EDGE_CONTRACT_DOC_REF,
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
    COUNTERPART_EDGE_EXAMPLE_REF,
    COUNTERPART_CONSUMER_CONTRACT_DOC_REF,
    COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF,
}

EXPECTED_COUNTERPART_CONSUMER_CONTRACT_REFS = {
    "counterpart_contract_doc": COUNTERPART_EDGE_CONTRACT_DOC_REF,
    "counterpart_contract_schema": COUNTERPART_EDGE_SCHEMA_REF,
    "counterpart_contract_example": COUNTERPART_EDGE_EXAMPLE_REF,
}

EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS = [
    COUNTERPART_CONSUMER_CONTRACT_DOC_REF,
    COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF,
    COUNTERPART_EDGE_CONTRACT_DOC_REF,
    COUNTERPART_EDGE_EXAMPLE_REF,
]

EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF = (
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF
)

EXPECTED_COUNTERPART_CONSUMER_FORBIDDEN_INTERPRETATIONS = [
    "identity_proof",
    "routing_authority",
    "graph_sovereign_activation",
    "silent_federation_exposure",
]

EXPECTED_PROVENANCE_POSTURE = {
    "primary_source_required": True,
    "supporting_sources_allowed": True,
    "source_trace_required": True,
    "derived_summary_posture": "guide_to_source_not_source_replacement",
}

EXPECTED_BOUNDARY_GUARDRAILS = {
    "routing_owner": "aoa-routing",
    "memory_owner": "aoa-memo",
    "canon_owner": "Tree-of-Sophia",
    "direct_canon_authorship": "forbidden",
}

EXPECTED_RETURN_REGROUNDING_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "routing_ownership": "forbidden",
    "memory_truth_ownership": "forbidden",
    "canon_authorship": "forbidden",
    "counterpart_activation": "review_gated",
    "proof_ownership": "forbidden",
}

EXPECTED_KAG_MATURITY_GOVERNANCE_INPUTS = {
    ("maturity_governance_doc", "aoa-kag", KAG_MATURITY_GOVERNANCE_DOC_REF, "governance_doc"),
    ("owner_wait_states_doc", "aoa-kag", KAG_OWNER_WAIT_STATES_DOC_REF, "wait_state_doc"),
    ("proof_expectations_doc", "aoa-kag", KAG_PROOF_EXPECTATIONS_DOC_REF, "proof_expectations_doc"),
    (
        "maturity_hardening_decision",
        "aoa-kag",
        "docs/decisions/AOA-KAG-D-0001-kag-maturity-hardening.md",
        "decision_note",
    ),
    ("kag_registry_manifest", "aoa-kag", "manifests/kag_registry.json", "registry_manifest"),
    (
        "federation_export_registry_manifest",
        "aoa-kag",
        FEDERATION_EXPORT_REGISTRY_MANIFEST_REF,
        "activation_manifest",
    ),
    (
        "return_regrounding_manifest",
        "aoa-kag",
        RETURN_REGROUNDING_MANIFEST_REF,
        "reentry_manifest",
    ),
    (
        "projection_health_receipt_schema",
        "aoa-kag",
        "mechanics/antifragility/parts/projection-health/schemas/projection_health_receipt_v1.json",
        "stress_schema",
    ),
    (
        "regrounding_ticket_schema",
        "aoa-kag",
        "mechanics/antifragility/parts/retrieval-outage-regrounding/schemas/regrounding_ticket_v1.json",
        "recovery_schema",
    ),
}

EXPECTED_KAG_MATURITY_GOVERNANCE_INPUT_ORDER = [
    "maturity_governance_doc",
    "owner_wait_states_doc",
    "proof_expectations_doc",
    "maturity_hardening_decision",
    "kag_registry_manifest",
    "federation_export_registry_manifest",
    "return_regrounding_manifest",
    "projection_health_receipt_schema",
    "regrounding_ticket_schema",
]

EXPECTED_KAG_MATURITY_GOVERNANCE_TIER_ORDER = [
    "planned_contract_only",
    "experimental_derived",
    "consumer_stable",
]

EXPECTED_KAG_MATURITY_GOVERNANCE_TIER_STATUS_MAP = {
    "planned_contract_only": (["planned"], False),
    "experimental_derived": (["experimental"], True),
    "consumer_stable": (["active"], True),
}

EXPECTED_KAG_MATURITY_GOVERNANCE_OWNER_WAIT_REPO_ORDER = [
    "aoa-techniques",
    TOS_REPO,
    "aoa-memo",
    "aoa-evals",
    "aoa-playbooks",
    "aoa-agents",
    "aoa-skills",
    "aoa-routing",
    "aoa-stats",
]

EXPECTED_KAG_MATURITY_GOVERNANCE_MODE_ORDER = [
    "source_export_reentry",
    "bridge_axis_reentry",
    "projection_boundary_reentry",
    "handoff_guardrail_reentry",
    "owner_boundary_reentry",
]

EXPECTED_KAG_MATURITY_GOVERNANCE_OUTPUT_PATHS = {
    "full": KAG_MATURITY_GOVERNANCE_OUTPUT_REF,
    "min": KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_REF,
}

EXPECTED_KAG_MATURITY_GOVERNANCE_HEALTH_STATES = [
    "healthy",
    "degraded",
    "quarantined",
]

EXPECTED_KAG_MATURITY_GOVERNANCE_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "routing_ownership": "forbidden",
    "memory_truth_ownership": "forbidden",
    "proof_ownership": "forbidden",
    "new_surface_growth": "paused_by_owner_need",
    "quarantine_shortcuts": "forbidden",
}

EXPECTED_RETURN_REGROUNDING_INPUTS = {
    ("boundaries_doc", "aoa-kag", "docs/BOUNDARIES.md", "boundary_doc"),
    ("bridge_contract_doc", "aoa-kag", "docs/BRIDGE_CONTRACTS.md", "bridge_doc"),
    ("reasoning_handoff_doc", "aoa-kag", "mechanics/checkpoint/parts/reasoning-handoff/docs/reasoning-handoff.md", "handoff_doc"),
    (
        "source_owned_export_dependencies_manifest",
        "aoa-kag",
        SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_REF,
        "dependency_manifest",
    ),
    (
        "federation_spine_pack",
        "aoa-kag",
        FEDERATION_SPINE_MIN_OUTPUT_REF,
        "derived_pack",
    ),
    (
        "retrieval_axis_pack",
        "aoa-kag",
        TOS_RETRIEVAL_AXIS_MIN_OUTPUT_REF,
        "derived_pack",
    ),
    (
        "cross_source_projection_pack",
        "aoa-kag",
        CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF,
        "derived_pack",
    ),
    (
        "reasoning_handoff_pack",
        "aoa-kag",
        "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json",
        "derived_pack",
    ),
    (
        "aoa_techniques_kag_export",
        "aoa-techniques",
        "generated/kag_export.min.json",
        "source_owned_export",
    ),
    (
        "tos_kag_export",
        "Tree-of-Sophia",
        "ToS/derived-exports/kag_export.min.json",
        "source_owned_export",
    ),
    (
        "tos_node_contract",
        "Tree-of-Sophia",
        "ToS/doctrine/NODE_CONTRACT.md",
        "source_contract",
    ),
    (
        "tos_source_node",
        "Tree-of-Sophia",
        "ToS/public-compatibility/source_node.example.json",
        "authority_surface",
    ),
    (
        "memo_checkpoint_contract",
        "aoa-memo",
        "mechanics/checkpoint/parts/checkpoint-to-memory-mapping/examples/checkpoint_to_memory_contract.example.json",
        "owner_contract",
    ),
    (
        "memo_memory_readiness_boundary",
        "aoa-memo",
        "mechanics/readiness-boundary/docs/MEMORY_READINESS_BOUNDARY.md",
        "owner_contract",
    ),
}

EXPECTED_RETURN_REGROUNDING_INPUT_ORDER = [
    "boundaries_doc",
    "bridge_contract_doc",
    "reasoning_handoff_doc",
    "source_owned_export_dependencies_manifest",
    "federation_spine_pack",
    "retrieval_axis_pack",
    "cross_source_projection_pack",
    "reasoning_handoff_pack",
    "aoa_techniques_kag_export",
    "tos_kag_export",
    "tos_node_contract",
    "tos_source_node",
    "memo_checkpoint_contract",
    "memo_memory_readiness_boundary",
]

EXPECTED_RETURN_REGROUNDING_BINDINGS = {
    (
        "source_export_reentry",
        "federation_spine_pack",
        (
            "source_owned_export_dependencies_manifest",
            "aoa_techniques_kag_export",
            "tos_kag_export",
        ),
        ("aoa-techniques-kag-export", "tree-of-sophia-kag-export"),
    ),
    (
        "bridge_axis_reentry",
        "retrieval_axis_pack",
        ("bridge_contract_doc", "tos_node_contract", "tos_source_node"),
        (),
    ),
    (
        "projection_boundary_reentry",
        "cross_source_projection_pack",
        ("federation_spine_pack", "retrieval_axis_pack", "bridge_contract_doc"),
        ("aoa-techniques-kag-export", "tree-of-sophia-kag-export"),
    ),
    (
        "handoff_guardrail_reentry",
        "reasoning_handoff_pack",
        (
            "reasoning_handoff_doc",
            "boundaries_doc",
            "memo_checkpoint_contract",
            "memo_memory_readiness_boundary",
        ),
        (),
    ),
    (
        "owner_boundary_reentry",
        "reasoning_handoff_doc",
        (
            "bridge_contract_doc",
            "boundaries_doc",
            "memo_checkpoint_contract",
            "memo_memory_readiness_boundary",
            "tos_node_contract",
        ),
        (),
    ),
}

EXPECTED_RETURN_REGROUNDING_MODE_ORDER = [
    "source_export_reentry",
    "bridge_axis_reentry",
    "projection_boundary_reentry",
    "handoff_guardrail_reentry",
    "owner_boundary_reentry",
]

EXPECTED_RETURN_MUST_INCLUDE = {"source_refs", "axis_summary", "provenance_note"}

EXPECTED_RETURN_MAY_INCLUDE = {
    "lineage_refs",
    "conflict_refs",
    "practice_refs",
    "counterpart_refs",
}

EXPECTED_TECHNIQUE_LIFT_INPUTS = {
    ("technique_section_manifest", "generated/technique_section_manifest.min.json", "section_manifest"),
    ("technique_catalog", "generated/technique_catalog.json", "metadata_spine"),
    ("technique_evidence_note_manifest", "generated/technique_evidence_note_manifest.min.json", "provenance_handles"),
}

EXPECTED_TECHNIQUE_LIFT_BINDINGS = {
    (
        "AOA-K-0001",
        "technique-section-lift",
        "section_manifest",
        "section_lift",
        "technique_section_manifest",
    ),
    (
        "AOA-K-0002",
        "metadata-spine-projection",
        "metadata_spine",
        "metadata_spine",
        "technique_catalog",
    ),
    (
        "AOA-K-0003",
        "bounded-relation-view",
        "relation_view",
        "relation_view",
        "technique_catalog",
    ),
    (
        "AOA-K-0004",
        "provenance-note-view",
        "provenance_view",
        "provenance_view",
        "technique_evidence_note_manifest",
    ),
}

EXPECTED_TECHNIQUE_LIFT_OUTPUT_PATHS = {
    "full": TECHNIQUE_LIFT_OUTPUT_REF,
    "min": TECHNIQUE_LIFT_MIN_OUTPUT_REF,
}

EXPECTED_TECHNIQUE_LIFT_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "graph_sovereignty": "forbidden",
}

EXPECTED_TOS_TEXT_CHUNK_MAP_INPUTS = {
    ("tos_source_node", TOS_TINY_ENTRY_AUTHORITY_PATH, "authority_surface"),
    ("tos_tiny_entry_route_doc", TOS_TINY_ENTRY_DOCTRINE_PATH, "route_surface"),
    ("tos_zarathustra_capsule", TOS_TINY_ENTRY_CAPSULE_PATH, "capsule_surface"),
}

EXPECTED_TOS_TEXT_CHUNK_MAP_BINDINGS = {
    (
        "AOA-K-0005",
        "tos-text-chunk-map",
        "chunk_map",
        "chunks",
        "tos_source_node",
    ),
}

EXPECTED_TOS_TEXT_CHUNK_MAP_OUTPUT_PATHS = {
    "full": TOS_TEXT_CHUNK_MAP_OUTPUT_REF,
    "min": TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_REF,
}

EXPECTED_TOS_TEXT_CHUNK_MAP_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "counterpart_projection": "forbidden",
    "federation_export_activation": "forbidden",
}

EXPECTED_TOS_RETRIEVAL_AXIS_INPUTS = {
    ("tos_text_chunk_map", "aoa-kag", TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_REF, "chunk_map"),
    ("bridge_contract_doc", "aoa-kag", "docs/BRIDGE_CONTRACTS.md", "bridge_doctrine"),
    (
        "bridge_surface_example",
        "aoa-kag",
        "mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_surface.example.json",
        "bridge_surface",
    ),
    (
        "bridge_envelope_example",
        "aoa-kag",
        "mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/aoa_tos_bridge_envelope.example.json",
        "bridge_envelope",
    ),
    ("memo_chunk_face", "aoa-memo", "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_chunk_face.bridge.example.json", "memo_chunk_face"),
    ("memo_graph_face", "aoa-memo", "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_graph_face.bridge.example.json", "memo_graph_face"),
    ("tos_node_contract", TOS_REPO, "ToS/doctrine/NODE_CONTRACT.md", "tos_contract"),
    ("tos_practice_branch", TOS_REPO, "ToS/doctrine/PRACTICE_BRANCH.md", "tos_contract"),
    ("tos_authority_surface", TOS_REPO, "ToS/public-compatibility/source_node.example.json", "authority_surface"),
    ("tos_lineage_hop", TOS_REPO, "ToS/public-compatibility/concept_node.example.json", "lineage_surface"),
}

EXPECTED_TOS_RETRIEVAL_AXIS_BINDINGS = {
    (
        "AOA-K-0007",
        "tos-retrieval-axis-surface",
        "retrieval_surface",
        "axes",
        "tos_text_chunk_map",
    ),
}

EXPECTED_TOS_RETRIEVAL_AXIS_OUTPUT_PATHS = {
    "full": TOS_RETRIEVAL_AXIS_OUTPUT_REF,
    "min": TOS_RETRIEVAL_AXIS_MIN_OUTPUT_REF,
}

EXPECTED_TOS_RETRIEVAL_AXIS_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "scoring_or_ranking": "forbidden",
    "routing_ownership": "forbidden",
    "graph_normalization": "forbidden",
}

EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_INPUTS = {
    ("tos_route_source_node", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_SOURCE_NODE_PATH, "authority_surface"),
    ("tos_becoming_concept", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_BECOMING_CONCEPT_PATH, "concept_surface"),
    ("tos_overcoming_concept", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_OVERCOMING_CONCEPT_PATH, "concept_surface"),
    ("tos_route_lineage_node", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_LINEAGE_NODE_PATH, "lineage_surface"),
    ("tos_route_principle_family_root", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_PRINCIPLE_ROOT, "family_root"),
    ("tos_route_event_family_root", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_EVENT_ROOT, "family_root"),
    ("tos_route_state_family_root", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_STATE_ROOT, "family_root"),
    ("tos_route_support_family_root", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_SUPPORT_ROOT, "family_root"),
    ("tos_route_analogy_family_root", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_ANALOGY_ROOT, "family_root"),
    ("tos_route_synthesis_family_root", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_SYNTHESIS_ROOT, "family_root"),
    ("tos_route_relation_pack", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH, "relation_pack"),
    ("tos_zarathustra_capsule", TOS_REPO, TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH, "capsule_surface"),
}

EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_BINDINGS = {
    (
        "AOA-K-0010",
        "tos-zarathustra-route-pack",
        "node_projection",
        "nodes",
        "tos_route_source_node",
    ),
}

EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATHS = {
    "full": TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_REF,
    "min": TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_REF,
}

EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "intake_consumption": "forbidden",
    "routing_ownership": "forbidden",
    "consumer_projection": "deferred",
}

EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_INPUTS = {
    (
        "tos_zarathustra_route_pack",
        "aoa-kag",
        TOS_ZARATHUSTRA_ROUTE_PACK_INPUT_REF,
        "route_pack",
    ),
}

EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_BINDINGS = {
    (
        "AOA-K-0011",
        "tos-zarathustra-route-retrieval-surface",
        "retrieval_surface",
        "routes",
        "tos_zarathustra_route_pack",
    ),
}

EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATHS = {
    "full": TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_REF,
    "min": TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_REF,
}

EXPECTED_TOS_STANDALONE_ADJUNCT_BUDGET = {
    "max_adjunct_surfaces": 1,
    "max_route_families": 1,
    "numbered_tiny_path_inclusion": "forbidden",
    "default_activation": "opt_in_only",
}

EXPECTED_TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE = {
    "adjunct_role": "standalone_handles_only",
    "entry_order": "source_owned_tiny_entry_before_adjunct",
    "source_first_reentry_ref": repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH),
    "routing_ownership": "forbidden",
    "canon_authorship": "forbidden",
}

EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "scoring_or_ranking": "forbidden",
    "routing_ownership": "forbidden",
    "graph_normalization": "forbidden",
    "consumer_projection": "bounded_handles_only",
}

ALLOWED_CONTRACT_STRENGTH = {
    "schema_backed",
    "doc_backed",
    "playbook_declared",
}

EXPECTED_REASONING_HANDOFF_SOURCE_ROOT_ENVS = {
    "aoa-playbooks": "AOA_PLAYBOOKS_ROOT",
    "aoa-evals": "AOA_EVALS_ROOT",
    "aoa-memo": "AOA_MEMO_ROOT",
    "aoa-agents": "AOA_AGENTS_ROOT",
}

EXPECTED_REASONING_HANDOFF_INPUTS = {
    (
        "reasoning_handoff_doc",
        "aoa-kag",
        REASONING_HANDOFF_GUARDRAIL_REF,
        "kag_guardrail_doc",
    ),
    (
        "reasoning_handoff_schema",
        "aoa-kag",
        REASONING_HANDOFF_GUARDRAIL_SCHEMA_REF,
        "kag_guardrail_schema",
    ),
    ("counterpart_consumer_contract_doc", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_DOC_REF, "kag_guardrail_doc"),
    ("counterpart_consumer_contract_schema", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_SCHEMA_REF, "kag_guardrail_schema"),
    ("counterpart_consumer_contract_example", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF, "kag_guardrail_example"),
    (
        "counterpart_federation_exposure_review_doc",
        "aoa-kag",
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
        "kag_guardrail_doc",
    ),
    ("artifact_to_verdict_hook_schema", "aoa-evals", "mechanics/audit/parts/artifact-verdict-hooks/schemas/artifact-to-verdict-hook.schema.json", "eval_hook_schema"),
    ("aoa_p_0008_playbook", "aoa-playbooks", "playbooks/operations/orchestration/long-horizon-model-tier-orchestra/PLAYBOOK.md", "playbook_doc"),
    ("aoa_p_0008_hook", "aoa-evals", "mechanics/audit/parts/artifact-verdict-hooks/examples/artifact_to_verdict_hook.long-horizon-model-tier-orchestra.example.json", "eval_hook_fixture"),
    ("aoa_p_0009_playbook", "aoa-playbooks", "playbooks/continuity/session-growth/restartable-inquiry-loop/PLAYBOOK.md", "playbook_doc"),
    ("aoa_p_0009_hook", "aoa-evals", "mechanics/checkpoint/parts/restartable-inquiry/examples/artifact_to_verdict_hook.restartable-inquiry-loop.example.json", "eval_hook_fixture"),
    ("checkpoint_to_memory_contract", "aoa-memo", "mechanics/checkpoint/parts/checkpoint-to-memory-mapping/examples/checkpoint_to_memory_contract.example.json", "memo_contract_fixture"),
    ("inquiry_checkpoint_schema", "aoa-memo", "mechanics/checkpoint/parts/checkpoint-carry-contract/schemas/inquiry_checkpoint.schema.json", "memo_schema"),
    ("witness_trace_contract", "aoa-memo", "mechanics/recurrence-support/docs/WITNESS_TRACE_CONTRACT.md", "memo_doc"),
    ("witness_trace_schema", "aoa-memo", "mechanics/recurrence-support/parts/witness-trace-contract/schemas/witness-trace.schema.json", "memo_schema"),
}

EXPECTED_REASONING_HANDOFF_BINDINGS = {
    ("AOA-P-0008", "aoa_p_0008_playbook", "aoa_p_0008_hook", ("checkpoint_to_memory_contract",), None, ("witness_trace_contract", "witness_trace_schema")),
    ("AOA-P-0009", "aoa_p_0009_playbook", "aoa_p_0009_hook", ("checkpoint_to_memory_contract",), "inquiry_checkpoint_schema", ()),
}

EXPECTED_REASONING_HANDOFF_OUTPUT_PATHS = {
    "full": REASONING_HANDOFF_OUTPUT_REF,
    "min": REASONING_HANDOFF_MIN_OUTPUT_REF,
}

EXPECTED_REASONING_HANDOFF_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "routing_ownership": "forbidden",
    "memory_truth_ownership": "forbidden",
    "canon_authorship": "forbidden",
    "verdict_ownership": "forbidden",
}

EXPECTED_REASONING_HANDOFF_SCENARIOS = {"AOA-P-0008", "AOA-P-0009"}

EXPECTED_REASONING_HANDOFF_KAG_GUARDRAIL_REFS = [
    REASONING_HANDOFF_GUARDRAIL_REF,
    REASONING_HANDOFF_GUARDRAIL_SCHEMA_REF,
    COUNTERPART_CONSUMER_CONTRACT_DOC_REF,
    COUNTERPART_CONSUMER_CONTRACT_SCHEMA_REF,
    COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF,
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
]

EXPECTED_FEDERATION_SPINE_SOURCE_INPUTS = {
    ("kag_registry_manifest", "aoa-kag", "manifests/kag_registry.json", "registry_manifest"),
    (
        "federation_export_registry_manifest",
        "aoa-kag",
        FEDERATION_EXPORT_REGISTRY_MANIFEST_REF,
        "activation_manifest",
    ),
    ("aoa_techniques_kag_export", "aoa-techniques", "generated/kag_export.min.json", "source_owned_export"),
    ("tos_kag_export", TOS_REPO, "ToS/derived-exports/kag_export.min.json", "source_owned_export"),
}

EXPECTED_FEDERATION_SPINE_SOURCE_INPUT_ORDER = [
    "kag_registry_manifest",
    "federation_export_registry_manifest",
    "aoa_techniques_kag_export",
    "tos_kag_export",
]

EXPECTED_FEDERATION_EXPORT_REGISTRY_OUTPUT_PATHS = {
    "full": FEDERATION_EXPORT_REGISTRY_OUTPUT_REF,
    "min": FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_REF,
}

EXPECTED_FEDERATION_SPINE_BINDINGS = {
    (
        "AOA-K-0009",
        "aoa-techniques",
        "source_owned_export_tiny",
        "aoa_techniques_kag_export",
    ),
    (
        "AOA-K-0009",
        TOS_REPO,
        "source_owned_export_tiny",
        "tos_kag_export",
    )
}

EXPECTED_FEDERATION_SPINE_REPO_ORDER = ["aoa-techniques", TOS_REPO]

EXPECTED_FEDERATION_SPINE_OUTPUT_PATHS = {
    "full": FEDERATION_SPINE_OUTPUT_REF,
    "min": FEDERATION_SPINE_MIN_OUTPUT_REF,
}

EXPECTED_FEDERATION_SPINE_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "routing_ownership": "forbidden",
    "canon_authorship": "forbidden",
    "full_federation_claim": "forbidden",
}

EXPECTED_FEDERATION_SPINE_REPOS = {"aoa-techniques", TOS_REPO}

EXPECTED_MEMO_KAG_EXPORT_PATH = "mechanics/consumer-handoff/parts/kag-source-export/generated/kag_export.min.json"

EXPECTED_MEMO_KAG_EXPORT_REQUIRED_FIELDS = {
    "owner_repo",
    "kind",
    "object_id",
    "primary_question",
    "summary_50",
    "summary_200",
    "source_inputs",
    "entry_surface",
    "section_handles",
    "direct_relations",
    "provenance_note",
    "non_identity_boundary",
}

EXPECTED_MEMO_KAG_EXPORT_SOURCE_INPUTS = [
    {"repo": "aoa-memo", "source_class": "memo_object", "role": "primary"},
    {"repo": TOS_REPO, "source_class": "tos_text", "role": "supporting"},
]

EXPECTED_MEMO_KAG_EXPORT_ENTRY_SURFACE = {
    "repo": "aoa-memo",
    "path": "generated/memory-objects/memory_object_capsules.json",
    "match_key": "id",
    "match_value": "memo.bridge.2026-03-23.tos-lineage-kag-candidate",
}

EXPECTED_MEMO_KAG_EXPORT_SECTION_HANDLES = [
    "identity-and-recall",
    "provenance-and-evidence",
    "trust-and-lifecycle",
    "bridges-and-access",
]

EXPECTED_MEMO_KAG_EXPORT_DIRECT_RELATIONS = [
    {
        "relation_type": "source_memory_object",
        "target_ref": "memo/objects/bridges/2026/tos-lineage-kag-candidate/object.json",
    },
    {
        "relation_type": "supported_by_claim",
        "target_ref": "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/claim.tos-bridge-ready.example.json",
    },
    {
        "relation_type": "drafted_by_episode",
        "target_ref": "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/episode.tos-interpretation.example.json",
    },
    {
        "relation_type": "points_to_tos_fragment",
        "target_ref": "repo:Tree-of-Sophia/mechanics/distillation/parts/source-compost/docs/CONTEXT_COMPOST.md#memory-bridge-fragment",
    },
    {
        "relation_type": "provenance_thread",
        "target_ref": "mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/provenance_thread.kag-lift.example.json",
    },
]

REQUIRED_MEMO_SOURCE_OWNED_EXPORT_CONSUMER_BOUNDARY_SNIPPETS = (
    "Reviewed memo donor consumer boundary",
    "`aoa-kag` is a read-only memory consumer",
    "reviewed `aoa-memo` object ids, provenance,",
    "lifecycle, and generated read models",
    "`source_kind: reviewed_corpus`",
    "`memo.bridge.2026-03-23.tos-lineage-kag-candidate`",
    "`aoa_memo_brief`, `aoa_memo_search`, and `aoa_memo_pending_exports`",
    "`aoa_memo_landing_plan`",
    "access-plane or dry-run evidence only",
    "do not authorize `aoa-kag` to",
    "write local memo candidates, reviewed-intake exports, or durable memory",
    "Session evidence remains `.aoa` or source-owner evidence",
    "must not treat the donor as normalized",
    "graph truth, routing authority, proof, or memory ownership",
)

EXPECTED_FEDERATION_SPINE_ADJUNCTS_BY_REPO = {
    "aoa-techniques": [],
    TOS_REPO: [
        {
            "surface_id": "AOA-K-0011",
            "surface_name": "tos-zarathustra-route-retrieval-surface",
            "surface_ref": TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_REF,
            "match_key": "retrieval_id",
            "target_value": TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID,
            "route_id": TOS_ZARATHUSTRA_ROUTE_ID,
            "adjunct_budget": EXPECTED_TOS_STANDALONE_ADJUNCT_BUDGET,
            "subordinate_posture": EXPECTED_TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE,
        }
    ],
}

EXPECTED_CROSS_SOURCE_NODE_PROJECTION_INPUTS = {
    ("aoa_techniques_kag_export", "aoa-techniques", "generated/kag_export.min.json", "primary_export"),
    ("tos_kag_export", TOS_REPO, "ToS/derived-exports/kag_export.min.json", "supporting_export"),
    ("tos_retrieval_axis_pack", "aoa-kag", TOS_RETRIEVAL_AXIS_MIN_OUTPUT_REF, "retrieval_axis"),
    ("federation_spine", "aoa-kag", FEDERATION_SPINE_MIN_OUTPUT_REF, "federation_spine"),
}

EXPECTED_CROSS_SOURCE_NODE_PROJECTION_BINDINGS = {
    (
        "AOA-K-0006",
        "cross-source-node-projection",
        "node_projection",
        "projections",
        "aoa_techniques_kag_export",
    ),
}

EXPECTED_CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATHS = {
    "full": CROSS_SOURCE_NODE_PROJECTION_OUTPUT_REF,
    "min": CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF,
}

EXPECTED_CROSS_SOURCE_NODE_PROJECTION_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "counterpart_activation": "forbidden",
    "graph_expansion": "forbidden",
    "routing_ownership": "forbidden",
}

EXPECTED_TINY_CONSUMER_BUNDLE_INPUTS = {
    ("tos_text_chunk_map", "aoa-kag", TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_REF, "generated_surface"),
    ("tos_retrieval_axis_pack", "aoa-kag", TOS_RETRIEVAL_AXIS_MIN_OUTPUT_REF, "generated_surface"),
    ("federation_spine", "aoa-kag", FEDERATION_SPINE_MIN_OUTPUT_REF, "generated_surface"),
    ("cross_source_node_projection", "aoa-kag", CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF, "generated_surface"),
    ("consumer_guide", "aoa-kag", "docs/CONSUMER_GUIDE.md", "consumer_doc"),
    ("counterpart_consumer_contract_doc", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_DOC_REF, "counterpart_contract"),
    ("counterpart_consumer_contract_example", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF, "counterpart_contract"),
}

EXPECTED_TINY_CONSUMER_BUNDLE_ORDER = [
    "tos_text_chunk_map",
    "tos_retrieval_axis_pack",
    "federation_spine",
    "cross_source_node_projection",
    "consumer_guide",
    "counterpart_consumer_contract_doc",
    "counterpart_consumer_contract_example",
]

EXPECTED_TINY_CONSUMER_BUNDLE_OUTPUT_PATHS = {
    "full": TINY_CONSUMER_BUNDLE_OUTPUT_REF,
    "min": TINY_CONSUMER_BUNDLE_MIN_OUTPUT_REF,
}

EXPECTED_TINY_CONSUMER_BUNDLE_DEFERRED_COUNTERPART = {
    "surface_id": "AOA-K-0008",
    "surface_status": "planned",
    "posture": "planned_contract_only",
    "federation_exposure_review_ref": EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF,
    "allowed_refs": EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS,
    "forbidden_active_payload_refs": [COUNTERPART_EDGE_EXAMPLE_REF],
    "forbidden_interpretations": [
        "active_retrieval_payload",
        "active_projection_payload",
    ],
}

EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_INPUTS = {
    ("reasoning_handoff_pack", "aoa-kag", "mechanics/checkpoint/parts/reasoning-handoff/generated/reasoning_handoff_pack.min.json", "reviewed_surface"),
    ("tiny_consumer_bundle", "aoa-kag", TINY_CONSUMER_BUNDLE_MIN_OUTPUT_REF, "reviewed_surface"),
    ("federation_spine", "aoa-kag", FEDERATION_SPINE_MIN_OUTPUT_REF, "reviewed_surface"),
    ("cross_source_node_projection", "aoa-kag", CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_REF, "reviewed_surface"),
    ("counterpart_consumer_contract_doc", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_DOC_REF, "counterpart_contract"),
    ("counterpart_consumer_contract_example", "aoa-kag", COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF, "counterpart_contract"),
    ("counterpart_edge_contract_doc", "aoa-kag", COUNTERPART_EDGE_CONTRACT_DOC_REF, "counterpart_contract"),
    ("counterpart_edge_contract_example", "aoa-kag", COUNTERPART_EDGE_EXAMPLE_REF, "counterpart_contract"),
}

EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER = [
    "reasoning_handoff_pack",
    "tiny_consumer_bundle",
    "federation_spine",
    "cross_source_node_projection",
    "counterpart_consumer_contract_doc",
    "counterpart_consumer_contract_example",
    "counterpart_edge_contract_doc",
    "counterpart_edge_contract_example",
]

EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATHS = {
    "full": COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_REF,
    "min": COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF,
}

EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_CONTRACT = {
    "silent_federation_exposure": "forbidden",
    "generated_counterpart_payload_inference": "forbidden",
    "routing_ownership": "forbidden",
    "source_replacement": "forbidden",
}

EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_POSTURES = {
    "reasoning_handoff_pack": "contract_only_counterpart_refs",
    "tiny_consumer_bundle": "planned_contract_only",
    "federation_spine": "no_counterpart_exposure",
    "cross_source_node_projection": "counterpart_activation_forbidden",
    "counterpart_consumer_contract_doc": "contract_reference_surface",
    "counterpart_consumer_contract_example": "contract_reference_surface",
    "counterpart_edge_contract_doc": "planned_contract_surface",
    "counterpart_edge_contract_example": "planned_example_surface",
}

EXPECTED_AOA_K_0006_SOURCE_INPUTS = [
    {
        "repo": "aoa-techniques",
        "source_class": "technique_bundle",
        "role": "primary",
    },
    {
        "repo": TOS_REPO,
        "source_class": "tos_text",
        "role": "supporting",
    },
]

EXPECTED_AOA_K_0009_SOURCE_INPUTS = [
    {
        "repo": "aoa-techniques",
        "source_class": "review_surface",
        "role": "primary",
    },
    {
        "repo": TOS_REPO,
        "source_class": "tos_text",
        "role": "supporting",
    },
]

MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

VISIBLE_ROOTS = (
    REPO_ROOT,
    AOA_TECHNIQUES_ROOT,
    AOA_PLAYBOOKS_ROOT,
    AOA_EVALS_ROOT,
    AOA_MEMO_ROOT,
    AOA_AGENTS_ROOT,
    TREE_OF_SOPHIA_ROOT,
)

FULL_CROSS_REPO_ROOTS = {
    "aoa-techniques": AOA_TECHNIQUES_ROOT,
    "aoa-playbooks": AOA_PLAYBOOKS_ROOT,
    "aoa-evals": AOA_EVALS_ROOT,
    "aoa-memo": AOA_MEMO_ROOT,
    "aoa-agents": AOA_AGENTS_ROOT,
    TOS_REPO: TREE_OF_SOPHIA_ROOT,
}

REQUIRED_KAG_STRESS_REGROUNDING_SNIPPETS = (
    "Teach the derived substrate to become more honest under drift.",
    "do not silently regenerate and republish drifted surfaces as if nothing happened",
    "do not let KAG overrule source-owned truth",
    "It is not a new claim about source meaning.",
)

REQUIRED_KAG_PROJECTION_QUARANTINE_SNIPPETS = (
    "Make quarantine a bounded honesty mechanism for derived surfaces that are currently unsafe to expand.",
    "preserve evidence refs",
    "narrow consumer posture",
    "silently disappear without review",
)

