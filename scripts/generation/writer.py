from __future__ import annotations

from .common import encode_json, write_json
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

GeneratedOutput = tuple[Path, dict[str, object], bool]


def build_generated_outputs() -> list[GeneratedOutput]:
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

    return [
        (REGISTRY_OUTPUT_PATH, registry_payload, True),
        (REGISTRY_MIN_OUTPUT_PATH, registry_payload, False),
        (LOCAL_KAG_PROVIDER_MAP_OUTPUT_PATH, local_kag_provider_map_payload, True),
        (LOCAL_KAG_PROVIDER_MAP_MIN_OUTPUT_PATH, local_kag_provider_map_payload, False),
        (TECHNIQUE_LIFT_OUTPUT_PATH, technique_lift_pack_payload, True),
        (TECHNIQUE_LIFT_MIN_OUTPUT_PATH, technique_lift_pack_payload, False),
        (TOS_TEXT_CHUNK_MAP_OUTPUT_PATH, tos_text_chunk_map_payload, True),
        (TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH, tos_text_chunk_map_payload, False),
        (TOS_RETRIEVAL_AXIS_OUTPUT_PATH, tos_retrieval_axis_pack_payload, True),
        (TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH, tos_retrieval_axis_pack_payload, False),
        (TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH, tos_zarathustra_route_pack_payload, True),
        (TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH, tos_zarathustra_route_pack_payload, False),
        (
            TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATH,
            tos_zarathustra_route_retrieval_pack_payload,
            True,
        ),
        (
            TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MIN_OUTPUT_PATH,
            tos_zarathustra_route_retrieval_pack_payload,
            False,
        ),
        (REASONING_HANDOFF_OUTPUT_PATH, reasoning_handoff_pack_payload, True),
        (REASONING_HANDOFF_MIN_OUTPUT_PATH, reasoning_handoff_pack_payload, False),
        (FEDERATION_EXPORT_REGISTRY_OUTPUT_PATH, federation_export_registry_payload, True),
        (FEDERATION_EXPORT_REGISTRY_MIN_OUTPUT_PATH, federation_export_registry_payload, False),
        (FEDERATION_SPINE_OUTPUT_PATH, federation_spine_payload, True),
        (FEDERATION_SPINE_MIN_OUTPUT_PATH, federation_spine_payload, False),
        (CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH, cross_source_node_projection_payload, True),
        (CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH, cross_source_node_projection_payload, False),
        (RETURN_REGROUNDING_OUTPUT_PATH, return_regrounding_pack_payload, True),
        (RETURN_REGROUNDING_MIN_OUTPUT_PATH, return_regrounding_pack_payload, False),
        (KAG_MATURITY_GOVERNANCE_OUTPUT_PATH, kag_maturity_governance_payload, True),
        (KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_PATH, kag_maturity_governance_payload, False),
        (
            COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
            counterpart_federation_exposure_review_payload,
            True,
        ),
        (
            COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
            counterpart_federation_exposure_review_payload,
            False,
        ),
        (TINY_CONSUMER_BUNDLE_OUTPUT_PATH, tiny_consumer_bundle_payload, True),
        (TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH, tiny_consumer_bundle_payload, False),
    ]


def check_generated_outputs() -> list[Path]:
    drifted_paths: list[Path] = []
    for path, payload, pretty in build_generated_outputs():
        expected = encode_json(payload, pretty=pretty)
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            drifted_paths.append(path)
    return drifted_paths


def write_generated_outputs() -> list[Path]:
    for path, payload, pretty in build_generated_outputs():
        write_json(path, payload, pretty=pretty)

    return list(GENERATED_OUTPUT_PATHS)
