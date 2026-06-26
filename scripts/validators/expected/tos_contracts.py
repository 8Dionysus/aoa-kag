from __future__ import annotations

from .core import *

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
