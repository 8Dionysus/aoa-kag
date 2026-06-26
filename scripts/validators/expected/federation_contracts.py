from __future__ import annotations

from .core import *
from .registry_contracts import *
from .tos_contracts import *

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
