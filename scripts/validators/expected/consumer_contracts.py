from __future__ import annotations

from .core import *
from .registry_contracts import *

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
