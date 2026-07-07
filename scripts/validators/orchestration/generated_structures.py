from __future__ import annotations

from ..common import *
from ..projection_parity import *


def validate_generated_structures(
    expected: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    generated_registry_payload = read_json(REGISTRY_MIN_OUTPUT_PATH)
    generated_surfaces_by_id = validate_registry_payload(
        generated_registry_payload,
        label="generated registry",
    )
    provider_map_payload = validate_local_kag_provider_map_payload(
        read_json(LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH),
        label="generated local KAG provider map",
    )
    min_provider_map_payload = validate_local_kag_provider_map_payload(
        read_json(LOCAL_KAG_PROVIDER_MAP_MIN_OUTPUT_PATH),
        label="generated min local KAG provider map",
    )
    if min_provider_map_payload != provider_map_payload:
        fail("generated min local KAG provider map must match full provider map")
    validate_technique_lift_pack(
        read_json(TECHNIQUE_LIFT_MIN_OUTPUT_PATH),
        generated_surfaces_by_id,
    )
    validate_tos_text_chunk_map_pack(
        read_json(TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH),
        generated_surfaces_by_id,
        expected["tos_text_chunk_map"],
    )
    validate_tos_retrieval_axis_pack(
        read_json(TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH),
        generated_surfaces_by_id,
        expected["tos_retrieval_axis"],
    )
    live_tos_zarathustra_route_pack_payload = read_json(
        TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH
    )
    validate_tos_zarathustra_route_pack(
        live_tos_zarathustra_route_pack_payload,
        generated_surfaces_by_id,
        expected["tos_zarathustra_route"],
    )
    validate_tos_zarathustra_route_retrieval_pack(
        read_json(TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH),
        generated_surfaces_by_id,
        expected["tos_zarathustra_route_retrieval"],
        live_tos_zarathustra_route_pack_payload,
    )
    validate_reasoning_handoff_pack(read_json(REASONING_HANDOFF_MIN_OUTPUT_PATH))
    validate_federation_export_registry_pack(
        read_json(FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH),
        expected["federation_export_registry"],
    )
    validate_return_regrounding_pack(
        read_json(RETURN_REGROUNDING_MIN_OUTPUT_PATH),
        expected["return_regrounding"],
    )
    validate_kag_maturity_governance_pack(
        read_json(KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH),
        expected["governance"],
        generated_surfaces_by_id,
    )
    validate_federation_spine_pack(
        read_json(FEDERATION_SPINE_MIN_OUTPUT_PATH),
        generated_surfaces_by_id,
        expected["federation_spine"],
    )
    validate_cross_source_node_projection_pack(
        read_json(CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH),
        generated_surfaces_by_id,
        expected["cross_source_node_projection"],
    )
    validate_counterpart_federation_exposure_review_pack(
        expected["counterpart_exposure_review"]
    )
    validate_tiny_consumer_bundle_pack(expected["tiny_consumer_bundle"])
    return generated_surfaces_by_id
