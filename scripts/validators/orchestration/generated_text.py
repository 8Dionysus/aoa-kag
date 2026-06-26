from __future__ import annotations

from ..common import *
from ..generation import *
from ..projection_parity import *


def validate_generated_text_outputs(expected: dict[str, dict[str, object]]) -> None:
    pairs = (
        (REGISTRY_OUTPUT_PATH, expected["registry"], True, "generated registry"),
        (REGISTRY_MIN_OUTPUT_PATH, expected["registry"], False, "generated compact registry"),
        (TECHNIQUE_LIFT_OUTPUT_PATH, expected["technique_lift"], True, "generated technique lift pack"),
        (TECHNIQUE_LIFT_MIN_OUTPUT_PATH, expected["technique_lift"], False, "generated compact technique lift pack"),
        (TOS_TEXT_CHUNK_MAP_OUTPUT_PATH, expected["tos_text_chunk_map"], True, "generated ToS text chunk map"),
        (TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH, expected["tos_text_chunk_map"], False, "generated compact ToS text chunk map"),
        (TOS_RETRIEVAL_AXIS_OUTPUT_PATH, expected["tos_retrieval_axis"], True, "generated ToS retrieval axis pack"),
        (TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH, expected["tos_retrieval_axis"], False, "generated compact ToS retrieval axis pack"),
        (TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH, expected["tos_zarathustra_route"], True, "generated ToS Zarathustra route pack"),
        (TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH, expected["tos_zarathustra_route"], False, "generated compact ToS Zarathustra route pack"),
        (TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATH, expected["tos_zarathustra_route_retrieval"], True, "generated ToS Zarathustra route retrieval pack"),
        (TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH, expected["tos_zarathustra_route_retrieval"], False, "generated compact ToS Zarathustra route retrieval pack"),
        (REASONING_HANDOFF_OUTPUT_PATH, expected["reasoning_handoff"], True, "generated reasoning handoff pack"),
        (REASONING_HANDOFF_MIN_OUTPUT_PATH, expected["reasoning_handoff"], False, "generated compact reasoning handoff pack"),
        (FEDERATION_EXPORT_REGISTRY_OUTPUT_PATH, expected["federation_export_registry"], True, "generated federation export registry"),
        (FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH, expected["federation_export_registry"], False, "generated compact federation export registry"),
        (RETURN_REGROUNDING_OUTPUT_PATH, expected["return_regrounding"], True, "generated return regrounding pack"),
        (RETURN_REGROUNDING_MIN_OUTPUT_PATH, expected["return_regrounding"], False, "generated compact return regrounding pack"),
        (KAG_MATURITY_GOVERNANCE_OUTPUT_PATH, expected["governance"], True, "generated KAG maturity governance pack"),
        (KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH, expected["governance"], False, "generated compact KAG maturity governance pack"),
        (FEDERATION_SPINE_OUTPUT_PATH, expected["federation_spine"], True, "generated federation spine"),
        (FEDERATION_SPINE_MIN_OUTPUT_PATH, expected["federation_spine"], False, "generated compact federation spine"),
        (CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH, expected["cross_source_node_projection"], True, "generated cross-source node projection pack"),
        (CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH, expected["cross_source_node_projection"], False, "generated compact cross-source node projection pack"),
        (COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH, expected["counterpart_exposure_review"], True, "generated counterpart federation exposure review"),
        (COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH, expected["counterpart_exposure_review"], False, "generated compact counterpart federation exposure review"),
        (TINY_CONSUMER_BUNDLE_OUTPUT_PATH, expected["tiny_consumer_bundle"], True, "generated tiny consumer bundle"),
        (TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH, expected["tiny_consumer_bundle"], False, "generated compact tiny consumer bundle"),
    )
    for path, payload, pretty, label in pairs:
        validate_generated_text(path, encode_json(payload, pretty=pretty), label=label)
