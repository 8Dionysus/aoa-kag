from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_return_regrounding_pack(
    payload: object,
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("return regrounding pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "mode_count",
        "modes",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"return regrounding pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("return regrounding pack pack_version must equal 1")
    if payload["pack_type"] != "return_regrounding_pack":
        fail("return regrounding pack pack_type must equal 'return_regrounding_pack'")
    if payload["source_manifest_ref"] != RETURN_REGROUNDING_MANIFEST_REF:
        fail(
            "return regrounding pack source_manifest_ref must point to "
            f"{RETURN_REGROUNDING_MANIFEST_REF}"
        )
    if payload["bounded_output_contract"] != EXPECTED_RETURN_REGROUNDING_CONTRACT:
        fail("return regrounding pack bounded_output_contract must match the current source-first guardrail")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("return regrounding pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    source_input_order: list[str] = []
    for index, source_input in enumerate(source_inputs):
        location = f"return regrounding pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, repo, role, ref)):
            fail(f"{location} must keep name, repo, role, and ref")
        resolve_known_ref(ref, label=location)
        relative_ref = ref if repo == "aoa-kag" else ref.split("/", 1)[1]
        actual_source_inputs.add((name, repo, relative_ref, role))
        source_input_order.append(name)
    if actual_source_inputs != EXPECTED_RETURN_REGROUNDING_INPUTS:
        fail("return regrounding pack source_inputs must match the manifest-driven donor set")
    if source_input_order != EXPECTED_RETURN_REGROUNDING_INPUT_ORDER:
        fail("return regrounding pack source_inputs must keep the current additive donor order")

    modes = payload["modes"]
    if not isinstance(modes, list) or not modes:
        fail("return regrounding pack modes must be a non-empty list")
    mode_count = payload["mode_count"]
    if not isinstance(mode_count, int) or mode_count != len(modes):
        fail("return regrounding pack mode_count must equal the number of modes")

    seen_modes: set[str] = set()
    mode_order: list[str] = []
    counterpart_forbidden_refs = set(EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS) | {
        EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF,
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
    }

    for index, mode in enumerate(modes):
        location = f"return regrounding pack modes[{index}]"
        if not isinstance(mode, dict):
            fail(f"{location} must be an object")
        for key in (
            "mode_id",
            "used_when",
            "query_mode_hint",
            "trigger_surface_refs",
            "stronger_refs",
            "supporting_surface_refs",
            "preserved_fields",
            "reentry_note",
            "non_identity_boundary",
            "prohibited_promotions",
        ):
            if key not in mode:
                fail(f"{location} is missing required key '{key}'")

        mode_id = mode["mode_id"]
        used_when = mode["used_when"]
        query_mode_hint = mode["query_mode_hint"]
        reentry_note = mode["reentry_note"]
        non_identity_boundary = mode["non_identity_boundary"]
        if not isinstance(mode_id, str) or not mode_id:
            fail(f"{location}.mode_id must be a non-empty string")
        if mode_id in seen_modes:
            fail(f"{location}.mode_id '{mode_id}' is duplicated")
        seen_modes.add(mode_id)
        mode_order.append(mode_id)
        if not isinstance(used_when, str) or len(used_when) < 20:
            fail(f"{location}.used_when must be a string of length >= 20")
        if query_mode_hint not in {"local_search", "global_search", "drift_search", "consumer_read_path"}:
            fail(f"{location}.query_mode_hint '{query_mode_hint}' is not allowed")
        if not isinstance(reentry_note, str) or len(reentry_note) < 20:
            fail(f"{location}.reentry_note must be a string of length >= 20")
        if not isinstance(non_identity_boundary, str) or len(non_identity_boundary) < 20:
            fail(f"{location}.non_identity_boundary must be a string of length >= 20")

        trigger_surface_refs = validate_unique_string_list(
            mode["trigger_surface_refs"],
            label=f"{location}.trigger_surface_refs",
        )
        stronger_refs = validate_unique_string_list(
            mode["stronger_refs"],
            label=f"{location}.stronger_refs",
        )
        supporting_surface_refs = validate_unique_string_list(
            mode["supporting_surface_refs"],
            label=f"{location}.supporting_surface_refs",
        )
        preserved_fields = validate_unique_string_list(
            mode["preserved_fields"],
            label=f"{location}.preserved_fields",
        )
        prohibited_promotions = validate_unique_string_list(
            mode["prohibited_promotions"],
            label=f"{location}.prohibited_promotions",
        )

        for ref in trigger_surface_refs:
            resolve_known_ref(ref, label=f"{location}.trigger_surface_refs")
        for ref in stronger_refs:
            resolve_known_ref(ref, label=f"{location}.stronger_refs")
        for ref in supporting_surface_refs:
            resolve_known_ref(ref, label=f"{location}.supporting_surface_refs")

        if any(ref in counterpart_forbidden_refs for ref in stronger_refs):
            fail(f"{location}.stronger_refs must not promote counterpart review or contract refs into stronger authority")
        if any(ref.startswith(("generated/", "docs/", "examples/", "manifests/", "schemas/")) for ref in stronger_refs):
            fail(f"{location}.stronger_refs must not point to aoa-kag-local surfaces")

        if mode_id == "source_export_reentry":
            validate_exact_set(
                stronger_refs,
                {
                    "aoa-techniques/generated/kag_export.min.json",
                    "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json",
                },
                label=f"{location}.stronger_refs",
            )
            validate_exact_set(
                set(preserved_fields),
                {"provenance_note", "non_identity_boundary", "entry_surface_ref"},
                label=f"{location}.preserved_fields",
            )
        elif mode_id == "bridge_axis_reentry":
            if not all(ref.startswith("Tree-of-Sophia/") for ref in stronger_refs):
                fail(f"{location}.stronger_refs must stay ToS-owned for bridge axis regrounding")
            validate_exact_set(
                set(preserved_fields),
                {
                    "source_refs",
                    "lineage_refs",
                    "conflict_refs",
                    "practice_refs",
                    "axis_summary",
                },
                label=f"{location}.preserved_fields",
            )
        elif mode_id == "projection_boundary_reentry":
            validate_exact_set(
                stronger_refs,
                {
                    "aoa-techniques/generated/kag_export.min.json",
                    "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json",
                },
                label=f"{location}.stronger_refs",
            )
            if COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF not in supporting_surface_refs:
                fail(f"{location}.supporting_surface_refs must keep the counterpart exposure review as a supporting boundary ref")
        elif mode_id == "handoff_guardrail_reentry":
            if not all(
                ref.startswith(("aoa-playbooks/", "aoa-evals/", "aoa-memo/"))
                for ref in stronger_refs
            ):
                fail(f"{location}.stronger_refs must stay playbook/eval/memo-owned for handoff regrounding")
            validate_exact_set(
                set(preserved_fields),
                {
                    "source_refs",
                    "axis_summary",
                    "provenance_note",
                    "boundary_guardrails",
                },
                label=f"{location}.preserved_fields",
            )
        elif mode_id == "owner_boundary_reentry":
            if not all(ref.startswith(("aoa-memo/", "Tree-of-Sophia/")) for ref in stronger_refs):
                fail(f"{location}.stronger_refs must stay memo- or ToS-owned at the owner boundary")
            validate_exact_set(
                set(preserved_fields),
                {"source_refs", "provenance_note", "boundary_guardrails"},
                label=f"{location}.preserved_fields",
            )
        else:
            fail(f"{location}.mode_id '{mode_id}' is not supported")

    if mode_order != EXPECTED_RETURN_REGROUNDING_MODE_ORDER:
        fail("return regrounding pack modes must keep the current stable mode order")

    if payload != expected_payload:
        fail("return regrounding pack must match the committed manifest-driven regrounding payload")
