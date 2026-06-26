from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_counterpart_federation_exposure_review_pack(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH)
    if not isinstance(payload, dict):
        fail("counterpart federation exposure review pack must be a JSON object")

    for key in (
        "review_version",
        "review_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_id",
        "surface_status",
        "review_status",
        "reviewed_surface_count",
        "reviewed_surfaces",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(
                "counterpart federation exposure review pack is missing required key "
                f"'{key}'"
            )

    if payload["review_version"] != 1:
        fail("counterpart federation exposure review pack review_version must equal 1")
    if payload["review_type"] != "counterpart_federation_exposure_review":
        fail(
            "counterpart federation exposure review pack review_type must equal "
            "'counterpart_federation_exposure_review'"
        )
    if payload["source_manifest_ref"] != COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_REF:
        fail(
            "counterpart federation exposure review pack source_manifest_ref must point "
            f"to {COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_REF}"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail(
            "counterpart federation exposure review pack source_inputs must match the "
            "manifest-driven donor set"
        )
    if payload["surface_id"] != "AOA-K-0008":
        fail("counterpart federation exposure review pack surface_id must equal 'AOA-K-0008'")
    if payload["surface_status"] != "planned":
        fail("counterpart federation exposure review pack surface_status must equal 'planned'")
    if payload["review_status"] != "passed_for_planned_posture":
        fail(
            "counterpart federation exposure review pack review_status must equal "
            "'passed_for_planned_posture'"
        )
    if payload["bounded_output_contract"] != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_CONTRACT:
        fail(
            "counterpart federation exposure review pack bounded_output_contract must "
            "match the current review guardrail"
        )

    reviewed_surfaces = payload["reviewed_surfaces"]
    if not isinstance(reviewed_surfaces, list) or not reviewed_surfaces:
        fail("counterpart federation exposure review pack reviewed_surfaces must be a non-empty list")
    if payload["reviewed_surface_count"] != len(reviewed_surfaces):
        fail(
            "counterpart federation exposure review pack reviewed_surface_count must "
            "equal the number of reviewed_surfaces"
        )

    observed_order: list[str] = []
    for index, reviewed_surface in enumerate(reviewed_surfaces):
        location = f"counterpart federation exposure review pack reviewed_surfaces[{index}]"
        if not isinstance(reviewed_surface, dict):
            fail(f"{location} must be an object")
        for key in ("surface_name", "surface_ref", "exposure_posture", "review_note"):
            if key not in reviewed_surface:
                fail(f"{location} is missing required key '{key}'")
        surface_name = reviewed_surface["surface_name"]
        surface_ref = reviewed_surface["surface_ref"]
        exposure_posture = reviewed_surface["exposure_posture"]
        observed_order.append(surface_name)
        resolve_known_ref(surface_ref, label=f"{location}.surface_ref")
        expected_posture = EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_POSTURES.get(surface_name)
        if exposure_posture != expected_posture:
            fail(
                f"{location}.exposure_posture must match the current reviewed posture "
                f"for '{surface_name}'"
            )
        if surface_name in {"reasoning_handoff_pack", "tiny_consumer_bundle"}:
            if reviewed_surface.get("allowed_counterpart_refs") != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.allowed_counterpart_refs must match the current "
                    "contract-only counterpart refs"
                )
        elif surface_name in {"federation_spine", "cross_source_node_projection"}:
            if reviewed_surface.get("forbidden_refs") != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.forbidden_refs must match the current forbidden "
                    "counterpart exposure set"
                )

    if observed_order != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER:
        fail(
            "counterpart federation exposure review pack reviewed_surfaces must keep "
            "the current reviewed surface order"
        )
    if payload != expected_payload:
        fail(
            "counterpart federation exposure review pack must match the committed "
            "manifest-driven review payload"
        )
