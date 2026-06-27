from __future__ import annotations

from .common import write_json
from .context import *
from .consumer import build_counterpart_federation_exposure_review_payload, build_tiny_consumer_bundle_payload
from .federation import build_cross_source_node_projection_payload, build_federation_export_registry_payload, build_federation_spine_payload
from .governance import build_kag_maturity_governance_payload
from .handoff import build_reasoning_handoff_pack_payload
from .provider_map import build_local_kag_provider_map_payload
from .registry import build_registry_payload
from .regrounding import build_return_regrounding_pack_payload
from .technique import build_technique_lift_pack_payload
from .tos import build_tos_retrieval_axis_pack_payload, build_tos_text_chunk_map_payload, build_tos_zarathustra_route_pack_payload, build_tos_zarathustra_route_retrieval_pack_payload


GENERATED_OUTPUT_PATHS = [
    REGISTRY_OUTPUT_PATH,
    REGISTRY_MIN_OUTPUT_PATH,
    LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH,
    LOCAL_KAG_PROVIDER_MAP_MIN_OUTPUT_PATH,
    TECHNIQUE_LIFT_OUTPUT_PATH,
    TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
    TOS_TEXT_CHUNK_MAP_OUTPUT_PATH,
    TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
    TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
    TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
    TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH,
    TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH,
    TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATH,
    TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH,
    REASONING_HANDOFF_OUTPUT_PATH,
    REASONING_HANDOFF_MIN_OUTPUT_PATH,
    FEDERATION_EXPORT_REGISTRY_OUTPUT_PATH,
    FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH,
    FEDERATION_SPINE_OUTPUT_PATH,
    FEDERATION_SPINE_MIN_OUTPUT_PATH,
    CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
    CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
    RETURN_REGROUNDING_OUTPUT_PATH,
    RETURN_REGROUNDING_MIN_OUTPUT_PATH,
    KAG_MATURITY_GOVERNANCE_OUTPUT_PATH,
    KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH,
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
    COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
    TINY_CONSUMER_BUNDLE_OUTPUT_PATH,
    TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
]

def write_generated_outputs() -> list[Path]:
    registry_payload = build_registry_payload()
    local_kag_provider_map_payload = build_local_kag_provider_map_payload()
    technique_lift_pack_payload = build_technique_lift_pack_payload(registry_payload)
    tos_text_chunk_map_payload = build_tos_text_chunk_map_payload(registry_payload)
    tos_retrieval_axis_pack_payload = build_tos_retrieval_axis_pack_payload(
        registry_payload
    )
    tos_zarathustra_route_pack_payload = build_tos_zarathustra_route_pack_payload(
        registry_payload
    )
    tos_zarathustra_route_retrieval_pack_payload = (
        build_tos_zarathustra_route_retrieval_pack_payload(
            registry_payload,
            route_pack_payload=tos_zarathustra_route_pack_payload,
        )
    )
    reasoning_handoff_pack_payload = build_reasoning_handoff_pack_payload()
    federation_export_registry_payload = build_federation_export_registry_payload()
    federation_spine_payload = build_federation_spine_payload(
        registry_payload,
        federation_export_registry_payload=federation_export_registry_payload,
    )
    cross_source_node_projection_payload = build_cross_source_node_projection_payload(
        registry_payload
    )
    return_regrounding_pack_payload = build_return_regrounding_pack_payload(
        registry_payload
    )
    kag_maturity_governance_payload = build_kag_maturity_governance_payload(
        registry_payload
    )
    counterpart_federation_exposure_review_payload = (
        build_counterpart_federation_exposure_review_payload(registry_payload)
    )
    tiny_consumer_bundle_payload = build_tiny_consumer_bundle_payload(registry_payload)

    write_json(REGISTRY_OUTPUT_PATH, registry_payload, pretty=True)
    write_json(REGISTRY_MIN_OUTPUT_PATH, registry_payload, pretty=False)
    write_json(
        LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH,
        local_kag_provider_map_payload,
        pretty=True,
    )
    write_json(
        LOCAL_KAG_PROVIDER_MAP_MIN_OUTPUT_PATH,
        local_kag_provider_map_payload,
        pretty=False,
    )
    write_json(TECHNIQUE_LIFT_OUTPUT_PATH, technique_lift_pack_payload, pretty=True)
    write_json(TECHNIQUE_LIFT_MIN_OUTPUT_PATH, technique_lift_pack_payload, pretty=False)
    write_json(TOS_TEXT_CHUNK_MAP_OUTPUT_PATH, tos_text_chunk_map_payload, pretty=True)
    write_json(
        TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
        tos_text_chunk_map_payload,
        pretty=False,
    )
    write_json(
        TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
        tos_retrieval_axis_pack_payload,
        pretty=True,
    )
    write_json(
        TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
        tos_retrieval_axis_pack_payload,
        pretty=False,
    )
    write_json(
        TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH,
        tos_zarathustra_route_pack_payload,
        pretty=True,
    )
    write_json(
        TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH,
        tos_zarathustra_route_pack_payload,
        pretty=False,
    )
    write_json(
        TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATH,
        tos_zarathustra_route_retrieval_pack_payload,
        pretty=True,
    )
    write_json(
        TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH,
        tos_zarathustra_route_retrieval_pack_payload,
        pretty=False,
    )
    write_json(REASONING_HANDOFF_OUTPUT_PATH, reasoning_handoff_pack_payload, pretty=True)
    write_json(
        REASONING_HANDOFF_MIN_OUTPUT_PATH,
        reasoning_handoff_pack_payload,
        pretty=False,
    )
    write_json(
        FEDERATION_EXPORT_REGISTRY_OUTPUT_PATH,
        federation_export_registry_payload,
        pretty=True,
    )
    write_json(
        FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH,
        federation_export_registry_payload,
        pretty=False,
    )
    write_json(FEDERATION_SPINE_OUTPUT_PATH, federation_spine_payload, pretty=True)
    write_json(
        FEDERATION_SPINE_MIN_OUTPUT_PATH,
        federation_spine_payload,
        pretty=False,
    )
    write_json(
        CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
        cross_source_node_projection_payload,
        pretty=True,
    )
    write_json(
        CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
        cross_source_node_projection_payload,
        pretty=False,
    )
    write_json(
        RETURN_REGROUNDING_OUTPUT_PATH,
        return_regrounding_pack_payload,
        pretty=True,
    )
    write_json(
        RETURN_REGROUNDING_MIN_OUTPUT_PATH,
        return_regrounding_pack_payload,
        pretty=False,
    )
    write_json(
        KAG_MATURITY_GOVERNANCE_OUTPUT_PATH,
        kag_maturity_governance_payload,
        pretty=True,
    )
    write_json(
        KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH,
        kag_maturity_governance_payload,
        pretty=False,
    )
    write_json(
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
        counterpart_federation_exposure_review_payload,
        pretty=True,
    )
    write_json(
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
        counterpart_federation_exposure_review_payload,
        pretty=False,
    )
    write_json(TINY_CONSUMER_BUNDLE_OUTPUT_PATH, tiny_consumer_bundle_payload, pretty=True)
    write_json(
        TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
        tiny_consumer_bundle_payload,
        pretty=False,
    )

    return list(GENERATED_OUTPUT_PATHS)
