from __future__ import annotations

from .core import *

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
