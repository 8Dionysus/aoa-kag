from __future__ import annotations

from .core import *

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
