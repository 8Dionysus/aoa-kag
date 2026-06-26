from __future__ import annotations

from .core import *
from .registry_contracts import *

EXPECTED_RETURN_REGROUNDING_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "routing_ownership": "forbidden",
    "memory_truth_ownership": "forbidden",
    "canon_authorship": "forbidden",
    "counterpart_activation": "review_gated",
    "proof_ownership": "forbidden",
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
