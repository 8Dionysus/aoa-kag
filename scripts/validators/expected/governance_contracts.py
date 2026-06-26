from __future__ import annotations

from .core import *

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
