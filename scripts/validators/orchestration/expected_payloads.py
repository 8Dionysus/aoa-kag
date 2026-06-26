from __future__ import annotations

from ..generation import *


def build_expected_payloads(
    expected_registry_payload: dict[str, object],
) -> dict[str, dict[str, object]]:
    expected_tos_zarathustra_route_pack_payload = (
        build_tos_zarathustra_route_pack_payload(expected_registry_payload)
    )
    expected_federation_export_registry_payload = build_federation_export_registry_payload()
    return {
        "registry": expected_registry_payload,
        "technique_lift": build_technique_lift_pack_payload(expected_registry_payload),
        "tos_text_chunk_map": build_tos_text_chunk_map_payload(expected_registry_payload),
        "tos_retrieval_axis": build_tos_retrieval_axis_pack_payload(
            expected_registry_payload
        ),
        "tos_zarathustra_route": expected_tos_zarathustra_route_pack_payload,
        "tos_zarathustra_route_retrieval": build_tos_zarathustra_route_retrieval_pack_payload(
            expected_registry_payload,
            route_pack_payload=expected_tos_zarathustra_route_pack_payload,
        ),
        "reasoning_handoff": build_reasoning_handoff_pack_payload(),
        "return_regrounding": build_return_regrounding_pack_payload(
            expected_registry_payload
        ),
        "governance": build_kag_maturity_governance_payload(expected_registry_payload),
        "federation_export_registry": expected_federation_export_registry_payload,
        "federation_spine": build_federation_spine_payload(
            expected_registry_payload,
            federation_export_registry_payload=expected_federation_export_registry_payload,
        ),
        "cross_source_node_projection": build_cross_source_node_projection_payload(
            expected_registry_payload
        ),
        "counterpart_exposure_review": build_counterpart_federation_exposure_review_payload(
            expected_registry_payload
        ),
        "tiny_consumer_bundle": build_tiny_consumer_bundle_payload(
            expected_registry_payload
        ),
    }
