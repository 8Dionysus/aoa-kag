from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_kag_maturity_governance_example() -> None:
    schema = read_json(KAG_MATURITY_GOVERNANCE_SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("KAG maturity governance schema must be a JSON object")
    Draft202012Validator.check_schema(schema)

    payload = read_json(KAG_MATURITY_GOVERNANCE_EXAMPLE_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        first = errors[0]
        error_path = format_schema_path(list(first.absolute_path))
        if error_path:
            fail(
                f"{display_path(KAG_MATURITY_GOVERNANCE_EXAMPLE_PATH)} schema violation at "
                f"'{error_path}': {first.message}"
            )
        fail(
            f"{display_path(KAG_MATURITY_GOVERNANCE_EXAMPLE_PATH)} schema violation: "
            f"{first.message}"
        )

    if not isinstance(payload, dict):
        fail("KAG maturity governance example must be a JSON object")
    if payload.get("pack_type") != "kag_maturity_governance":
        fail("KAG maturity governance example pack_type must equal 'kag_maturity_governance'")
    if payload.get("source_manifest_ref") != KAG_MATURITY_GOVERNANCE_MANIFEST_REF:
        fail(
            "KAG maturity governance example source_manifest_ref must point to "
            f"{KAG_MATURITY_GOVERNANCE_MANIFEST_REF}"
        )
    if payload.get("stability_tier_count") != len(payload.get("stability_tiers", [])):
        fail("KAG maturity governance example stability_tier_count must equal the number of tiers")
    if payload.get("surface_count") != len(payload.get("surfaces", [])):
        fail("KAG maturity governance example surface_count must equal the number of surfaces")
    if payload.get("owner_wait_state_count") != len(payload.get("owner_wait_states", [])):
        fail("KAG maturity governance example owner_wait_state_count must equal the number of owner wait states")

    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        fail("KAG maturity governance example surfaces must be a non-empty list")
    example_surface = surfaces[0]
    if not isinstance(example_surface, dict):
        fail("KAG maturity governance example first surface must be an object")
    if example_surface.get("surface_id") != "AOA-K-0008":
        fail("KAG maturity governance example must center the planned-only AOA-K-0008 posture")
    if example_surface.get("stability_tier") != "planned_contract_only":
        fail("KAG maturity governance example first surface must stay planned_contract_only")
    for proof_ref in validate_unique_string_list(
        example_surface.get("proof_expectation_refs"),
        label="KAG maturity governance example proof_expectation_refs",
    ):
        resolve_aoa_evals_ref(proof_ref, label="KAG maturity governance example proof_expectation_refs")
    for field_name in (
        "stress_receipt_schema_ref",
        "regrounding_ticket_schema_ref",
        "stress_doc_ref",
        "quarantine_doc_ref",
        "regrounding_pack_ref",
    ):
        projection_recovery = payload.get("projection_recovery")
        if not isinstance(projection_recovery, dict):
            fail("KAG maturity governance example projection_recovery must be an object")
        ref = projection_recovery.get(field_name)
        if not isinstance(ref, str) or not ref:
            fail(f"KAG maturity governance example projection_recovery.{field_name} must be a non-empty string")
        resolve_known_ref(
            ref,
            label=f"KAG maturity governance example projection_recovery.{field_name}",
        )
