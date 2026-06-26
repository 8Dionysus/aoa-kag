from __future__ import annotations

from ..common import *
from ..projection_parity import *
from ..source_refs import *

def validate_counterpart_example(surfaces_by_id: dict[str, dict[str, object]]) -> None:
    payload = read_json(COUNTERPART_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("counterpart example must be a JSON object")

    surface_id = payload.get("surface_id")
    if surface_id != "AOA-K-0008":
        fail("counterpart example surface_id must equal 'AOA-K-0008'")
    if surface_id not in surfaces_by_id:
        fail("counterpart example surface_id must exist in the generated registry")

    registry_entry = surfaces_by_id[surface_id]
    if registry_entry["derived_kind"] != "edge_projection":
        fail("AOA-K-0008 must remain an edge_projection")
    if registry_entry["status"] != "planned":
        fail("AOA-K-0008 must remain planned in the registry")
    if registry_entry["source_class"] != "tos_text":
        fail("AOA-K-0008 must keep 'tos_text' as its primary source_class")

    mappings = payload.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        fail("counterpart example 'mappings' must be a non-empty list")

    seen_mapping_ids: set[str] = set()
    seen_modes: set[str] = set()
    source_inputs = registry_entry.get("source_inputs")
    supporting_repos = {
        item["repo"]
        for item in source_inputs
        if isinstance(item, dict) and item.get("role") == "supporting"
    }

    for index, mapping in enumerate(mappings):
        location = f"counterpart example mappings[{index}]"
        if not isinstance(mapping, dict):
            fail(f"{location} must be an object")
        for key in (
            "mapping_id",
            "concept_ref",
            "operational_ref",
            "counterpart_mode",
            "evidence_note",
            "non_identity_note",
        ):
            if key not in mapping:
                fail(f"{location} is missing required key '{key}'")

        mapping_id = mapping["mapping_id"]
        concept_ref = mapping["concept_ref"]
        operational_ref = mapping["operational_ref"]
        counterpart_mode = mapping["counterpart_mode"]
        evidence_note = mapping["evidence_note"]
        non_identity_note = mapping["non_identity_note"]
        supporting_refs = mapping.get("supporting_refs")

        if not isinstance(mapping_id, str) or len(mapping_id) < 1:
            fail(f"{location}.mapping_id must be a non-empty string")
        if mapping_id in seen_mapping_ids:
            fail(f"{location}.mapping_id '{mapping_id}' is duplicated")
        seen_mapping_ids.add(mapping_id)

        if not isinstance(concept_ref, str) or not concept_ref.startswith("Tree-of-Sophia/"):
            fail(f"{location}.concept_ref must point to a Tree-of-Sophia surface")
        if not isinstance(operational_ref, str) or "/" not in operational_ref:
            fail(f"{location}.operational_ref must be a non-empty repo-qualified string")
        operational_repo = operational_ref.split("/", 1)[0]
        if operational_repo not in supporting_repos:
            fail(f"{location}.operational_ref repo '{operational_repo}' must match a supporting source repo")

        if counterpart_mode not in ALLOWED_COUNTERPART_MODE:
            fail(f"{location}.counterpart_mode '{counterpart_mode}' is not allowed")
        seen_modes.add(counterpart_mode)

        if not isinstance(evidence_note, str) or len(evidence_note) < 20:
            fail(f"{location}.evidence_note must be a string of length >= 20")
        if not isinstance(non_identity_note, str) or len(non_identity_note) < 20:
            fail(f"{location}.non_identity_note must be a string of length >= 20")

        if supporting_refs is not None:
            refs = validate_unique_string_list(
                supporting_refs,
                label=f"{location}.supporting_refs",
            )
            for supporting_ref in refs:
                if "/" not in supporting_ref:
                    fail(f"{location}.supporting_refs contains an invalid repo-qualified ref")
                supporting_repo = supporting_ref.split("/", 1)[0]
                if supporting_repo not in supporting_repos:
                    fail(f"{location}.supporting_refs repo '{supporting_repo}' must match a supporting source repo")

    if seen_modes != ALLOWED_COUNTERPART_MODE:
        fail("counterpart example must cover all supported counterpart modes at least once")

def validate_counterpart_consumer_contract_example(
    surfaces_by_id: dict[str, dict[str, object]]
) -> None:
    payload = read_json(COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("counterpart consumer contract example must be a JSON object")

    for key in (
        "contract_type",
        "surface_id",
        "surface_status",
        "consumer_surface_type",
        "allowed_return_field",
        "federation_exposure_review_ref",
        "required_contract_refs",
        "allowed_refs",
        "forbidden_interpretations",
    ):
        if key not in payload:
            fail(f"counterpart consumer contract example is missing required key '{key}'")

    if payload["contract_type"] != "counterpart_consumer_contract":
        fail(
            "counterpart consumer contract example contract_type must equal "
            "'counterpart_consumer_contract'"
        )
    if payload["surface_id"] != "AOA-K-0008":
        fail("counterpart consumer contract example surface_id must equal 'AOA-K-0008'")
    if payload["surface_status"] != "planned":
        fail("counterpart consumer contract example surface_status must equal 'planned'")
    if payload["consumer_surface_type"] != "reasoning_handoff_guardrail":
        fail(
            "counterpart consumer contract example consumer_surface_type must equal "
            "'reasoning_handoff_guardrail'"
        )
    if payload["allowed_return_field"] != "counterpart_refs":
        fail(
            "counterpart consumer contract example allowed_return_field must equal "
            "'counterpart_refs'"
        )
    if (
        payload["federation_exposure_review_ref"]
        != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF
    ):
        fail(
            "counterpart consumer contract example federation_exposure_review_ref must "
            "point to the current review artifact"
        )
    resolve_known_ref(
        payload["federation_exposure_review_ref"],
        label="counterpart consumer contract example federation_exposure_review_ref",
    )

    registry_surface = surfaces_by_id.get("AOA-K-0008")
    if registry_surface is None:
        fail("counterpart consumer contract example requires AOA-K-0008 in the generated registry")
    if registry_surface.get("status") != "planned":
        fail("counterpart consumer contract example requires AOA-K-0008 to remain planned")

    required_contract_refs = payload["required_contract_refs"]
    if not isinstance(required_contract_refs, dict):
        fail("counterpart consumer contract example required_contract_refs must be an object")
    if required_contract_refs != EXPECTED_COUNTERPART_CONSUMER_CONTRACT_REFS:
        fail(
            "counterpart consumer contract example required_contract_refs must match the "
            "current counterpart contract surfaces"
        )
    for key, ref in required_contract_refs.items():
        resolve_known_ref(
            ref,
            label=f"counterpart consumer contract example required_contract_refs.{key}",
        )

    allowed_refs = validate_unique_string_list(
        payload["allowed_refs"],
        label="counterpart consumer contract example allowed_refs",
    )
    if allowed_refs != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
        fail(
            "counterpart consumer contract example allowed_refs must keep the current "
            "contract/example-only posture"
        )
    for index, ref in enumerate(allowed_refs):
        resolve_known_ref(
            ref,
            label=f"counterpart consumer contract example allowed_refs[{index}]",
        )

    forbidden_interpretations = validate_unique_string_list(
        payload["forbidden_interpretations"],
        label="counterpart consumer contract example forbidden_interpretations",
    )
    if forbidden_interpretations != EXPECTED_COUNTERPART_CONSUMER_FORBIDDEN_INTERPRETATIONS:
        fail(
            "counterpart consumer contract example forbidden_interpretations must match "
            "the bounded contract"
        )
