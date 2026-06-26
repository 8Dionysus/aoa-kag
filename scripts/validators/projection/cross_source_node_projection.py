from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_cross_source_node_projection_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("cross-source node projection pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "projection_count",
        "projections",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"cross-source node projection pack is missing required key '{key}'")

    if payload["pack_type"] != "cross_source_node_projection":
        fail("cross-source node projection pack pack_type must equal 'cross_source_node_projection'")
    if payload["bounded_output_contract"] != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_CONTRACT:
        fail("cross-source node projection pack bounded_output_contract must match the current source-first guardrail")
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("cross-source node projection pack source_inputs must match the manifest-driven donor set")
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail("cross-source node projection pack surface_bindings must match the current bounded projection binding")
    forbidden_counterpart_refs = set(EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS) | {
        EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF,
        "AOA-K-0008",
    }
    if any(value in forbidden_counterpart_refs for value in iter_string_values(payload)):
        fail(
            "cross-source node projection pack must not expose counterpart refs or "
            "AOA-K-0008 activation hints in the current review-closed posture"
        )

    surface_0006 = surfaces_by_id.get("AOA-K-0006")
    if surface_0006 is None or surface_0006.get("status") != "experimental":
        fail("cross-source node projection pack requires AOA-K-0006 to remain experimental in the generated registry")

    projections = payload["projections"]
    if not isinstance(projections, list) or len(projections) != 1:
        fail("cross-source node projection pack must contain exactly one projection in the current pilot")
    if payload["projection_count"] != 1:
        fail("cross-source node projection pack projection_count must equal 1 in the current pilot")
    projection = projections[0]
    if not isinstance(projection, dict):
        fail("cross-source node projection pack projection must be an object")
    for input_key in ("primary_input",):
        input_payload = projection.get(input_key)
        if not isinstance(input_payload, dict):
            fail(f"cross-source node projection pack {input_key} must be an object")
        resolve_known_ref(input_payload["export_ref"], label=f"cross-source node projection pack {input_key}.export_ref")
    supporting_inputs = projection.get("supporting_inputs")
    if not isinstance(supporting_inputs, list) or len(supporting_inputs) != 1:
        fail("cross-source node projection pack supporting_inputs must contain exactly one supporting export in the current pilot")
    resolve_known_ref(
        supporting_inputs[0]["export_ref"],
        label="cross-source node projection pack supporting_inputs[0].export_ref",
    )
    resolve_known_ref(
        projection["retrieval_axis_ref"],
        label="cross-source node projection pack retrieval_axis_ref",
    )
    resolve_known_ref(
        projection["federation_spine_ref"],
        label="cross-source node projection pack federation_spine_ref",
    )
    if payload != expected_payload:
        fail("cross-source node projection pack must match the committed manifest-driven projection payload")
