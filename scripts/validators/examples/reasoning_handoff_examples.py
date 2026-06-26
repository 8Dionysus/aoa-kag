from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_reasoning_handoff_example() -> None:
    payload = read_json(REASONING_HANDOFF_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("reasoning handoff example must be a JSON object")

    for key in (
        "surface_type",
        "handoff_id",
        "supported_query_modes",
        "authoritative_source_refs",
        "derived_surface_refs",
        "provenance_posture",
        "return_contract",
        "boundary_guardrails",
    ):
        if key not in payload:
            fail(f"reasoning handoff example is missing required key '{key}'")

    if payload["surface_type"] != "reasoning_handoff_guardrail":
        fail("reasoning handoff example surface_type must equal 'reasoning_handoff_guardrail'")

    handoff_id = payload["handoff_id"]
    if not isinstance(handoff_id, str) or len(handoff_id) < 3:
        fail("reasoning handoff example handoff_id must be a string of length >= 3")

    query_modes = validate_unique_string_list(
        payload["supported_query_modes"],
        label="reasoning handoff example supported_query_modes",
    )
    validate_exact_set(
        query_modes,
        ALLOWED_QUERY_MODES,
        label="reasoning handoff example supported_query_modes",
    )

    authoritative_source_refs = validate_unique_string_list(
        payload["authoritative_source_refs"],
        label="reasoning handoff example authoritative_source_refs",
    )
    validate_exact_set(
        authoritative_source_refs,
        EXPECTED_AUTHORITATIVE_SOURCE_REFS,
        label="reasoning handoff example authoritative_source_refs",
    )
    for ref in authoritative_source_refs:
        resolve_authoritative_ref(ref, label="reasoning handoff example authoritative_source_refs")

    derived_surface_refs = validate_unique_string_list(
        payload["derived_surface_refs"],
        label="reasoning handoff example derived_surface_refs",
    )
    validate_exact_set(
        derived_surface_refs,
        EXPECTED_DERIVED_SURFACE_REFS,
        label="reasoning handoff example derived_surface_refs",
    )
    for ref in derived_surface_refs:
        resolve_relative_ref(
            REPO_ROOT,
            ref,
            label="reasoning handoff example derived_surface_refs",
        )

    provenance_posture = payload["provenance_posture"]
    if provenance_posture != EXPECTED_PROVENANCE_POSTURE:
        fail("reasoning handoff example provenance_posture must match the bounded guardrail contract")

    return_contract = payload["return_contract"]
    if not isinstance(return_contract, dict):
        fail("reasoning handoff example return_contract must be an object")

    for key in ("must_include", "may_include"):
        if key not in return_contract:
            fail(f"reasoning handoff example return_contract is missing '{key}'")

    must_include = validate_unique_string_list(
        return_contract["must_include"],
        label="reasoning handoff example return_contract.must_include",
    )
    validate_exact_set(
        must_include,
        EXPECTED_RETURN_MUST_INCLUDE,
        label="reasoning handoff example return_contract.must_include",
    )

    may_include = validate_unique_string_list(
        return_contract["may_include"],
        label="reasoning handoff example return_contract.may_include",
    )
    validate_exact_set(
        may_include,
        EXPECTED_RETURN_MAY_INCLUDE,
        label="reasoning handoff example return_contract.may_include",
    )

    if set(must_include) & set(may_include):
        fail("reasoning handoff example return_contract must not overlap must_include and may_include")

    boundary_guardrails = payload["boundary_guardrails"]
    if boundary_guardrails != EXPECTED_BOUNDARY_GUARDRAILS:
        fail("reasoning handoff example boundary_guardrails must match the bounded guardrail contract")
