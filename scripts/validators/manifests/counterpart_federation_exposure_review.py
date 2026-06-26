from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_counterpart_federation_exposure_review_manifest() -> None:
    payload = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("counterpart federation exposure review manifest must be a JSON object")

    for key in (
        "manifest_version",
        "review_type",
        "source_inputs",
        "review_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(
                "counterpart federation exposure review manifest is missing required "
                f"key '{key}'"
            )

    if payload["manifest_version"] != 1:
        fail("counterpart federation exposure review manifest manifest_version must equal 1")
    if payload["review_type"] != "counterpart_federation_exposure_review":
        fail(
            "counterpart federation exposure review manifest review_type must equal "
            "'counterpart_federation_exposure_review'"
        )

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("counterpart federation exposure review manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    source_input_order: list[str] = []
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"counterpart federation exposure review manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(f"{location} must keep name, repo, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        source_input_order.append(name)
        actual_source_inputs.add((name, repo, path, role))
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_INPUTS:
        fail(
            "counterpart federation exposure review manifest source_inputs must match "
            "the current reviewed donor set"
        )
    if source_input_order != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER:
        fail(
            "counterpart federation exposure review manifest source_inputs must keep "
            "the current reviewed surface order"
        )

    review_bindings = payload["review_bindings"]
    if not isinstance(review_bindings, list) or not review_bindings:
        fail("counterpart federation exposure review manifest review_bindings must be a non-empty list")
    actual_review_order: list[str] = []
    seen_review_names: set[str] = set()
    for index, binding in enumerate(review_bindings):
        location = f"counterpart federation exposure review manifest review_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_name = binding.get("surface_name")
        surface_input = binding.get("surface_input")
        exposure_posture = binding.get("exposure_posture")
        review_note = binding.get("review_note")
        if not all(
            isinstance(value, str) and value
            for value in (surface_name, surface_input, exposure_posture, review_note)
        ):
            fail(
                f"{location} must keep surface_name, surface_input, exposure_posture, "
                "and review_note"
            )
        if surface_name in seen_review_names:
            fail(f"{location} duplicates review binding '{surface_name}'")
        seen_review_names.add(surface_name)
        actual_review_order.append(surface_name)
        if surface_name != surface_input:
            fail(f"{location}.surface_name must match surface_input in the current review scope")
        if exposure_posture != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_POSTURES.get(surface_name):
            fail(
                f"{location}.exposure_posture must match the current reviewed posture "
                f"for '{surface_name}'"
            )

        allowed_counterpart_refs = binding.get("allowed_counterpart_refs")
        forbidden_refs = binding.get("forbidden_refs")
        if surface_name in {"reasoning_handoff_pack", "tiny_consumer_bundle"}:
            if allowed_counterpart_refs != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.allowed_counterpart_refs must match the current "
                    "contract-only counterpart refs"
                )
            for ref_index, ref in enumerate(allowed_counterpart_refs):
                resolve_known_ref(
                    ref,
                    label=f"{location}.allowed_counterpart_refs[{ref_index}]",
                )
            if forbidden_refs is not None:
                fail(f"{location}.forbidden_refs must stay absent when counterpart refs are allowed")
        elif surface_name in {"federation_spine", "cross_source_node_projection"}:
            if forbidden_refs != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.forbidden_refs must match the current forbidden "
                    "counterpart exposure set"
                )
            for ref_index, ref in enumerate(forbidden_refs):
                resolve_known_ref(
                    ref,
                    label=f"{location}.forbidden_refs[{ref_index}]",
                )
            if allowed_counterpart_refs is not None:
                fail(
                    f"{location}.allowed_counterpart_refs must stay absent for "
                    "non-exposing surfaces"
                )
        else:
            if allowed_counterpart_refs is not None or forbidden_refs is not None:
                fail(
                    f"{location} must not declare allowed_counterpart_refs or "
                    "forbidden_refs for contract/example review surfaces"
                )

    if actual_review_order != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER:
        fail(
            "counterpart federation exposure review manifest review_bindings must keep "
            "the current reviewed surface order"
        )
    if payload["output_paths"] != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATHS:
        fail(
            "counterpart federation exposure review manifest output_paths must match "
            "the committed generated output paths"
        )
    if payload["bounded_output_contract"] != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_CONTRACT:
        fail(
            "counterpart federation exposure review manifest bounded_output_contract "
            "must match the current review guardrail"
        )
