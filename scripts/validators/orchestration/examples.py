from __future__ import annotations

from ..example_contracts import *
from ..sibling_readiness import *


def validate_examples(
    expected: dict[str, dict[str, object]],
    generated_surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    validate_bridge_example(generated_surfaces_by_id)
    validate_bridge_envelope_example()
    validate_counterpart_example(generated_surfaces_by_id)
    validate_counterpart_consumer_contract_example(generated_surfaces_by_id)
    validate_tos_text_chunk_map_example(expected["tos_text_chunk_map"])
    validate_tos_retrieval_axis_example(expected["tos_retrieval_axis"])
    validate_tos_zarathustra_route_pack_example(expected["tos_zarathustra_route"])
    validate_tos_zarathustra_route_retrieval_pack_example(
        expected["tos_zarathustra_route_retrieval"]
    )
    validate_reasoning_handoff_example()
    validate_return_regrounding_example(expected["return_regrounding"])
    validate_kag_maturity_governance_example()
    validate_federation_export_registry_example()
    validate_federation_kag_export_example()
    validate_optional_memo_source_owned_export_readiness()
    validate_memo_source_owned_export_consumer_boundary_doc()
    validate_cross_source_node_projection_example(expected["cross_source_node_projection"])
    validate_counterpart_federation_exposure_review_example(
        expected["counterpart_exposure_review"]
    )
    validate_tiny_consumer_bundle_example(expected["tiny_consumer_bundle"])
