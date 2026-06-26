from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_kag_maturity_governance_pack(
    payload: object,
    expected_payload: dict[str, object],
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    if not isinstance(payload, dict):
        fail("KAG maturity governance pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "stability_tier_count",
        "stability_tiers",
        "surface_count",
        "surfaces",
        "owner_wait_state_count",
        "owner_wait_states",
        "stop_rule",
        "projection_recovery",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"KAG maturity governance pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("KAG maturity governance pack pack_version must equal 1")
    if payload["pack_type"] != "kag_maturity_governance":
        fail("KAG maturity governance pack pack_type must equal 'kag_maturity_governance'")
    if payload["source_manifest_ref"] != KAG_MATURITY_GOVERNANCE_MANIFEST_REF:
        fail(
            "KAG maturity governance pack source_manifest_ref must point to "
            f"{KAG_MATURITY_GOVERNANCE_MANIFEST_REF}"
        )
    if payload["bounded_output_contract"] != EXPECTED_KAG_MATURITY_GOVERNANCE_CONTRACT:
        fail("KAG maturity governance pack bounded_output_contract must match the current source-first stop-rule contract")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("KAG maturity governance pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    source_input_order: list[str] = []
    for index, source_input in enumerate(source_inputs):
        location = f"KAG maturity governance pack source_inputs[{index}]"
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
    if actual_source_inputs != EXPECTED_KAG_MATURITY_GOVERNANCE_INPUTS:
        fail("KAG maturity governance pack source_inputs must match the manifest-driven donor set")
    if source_input_order != EXPECTED_KAG_MATURITY_GOVERNANCE_INPUT_ORDER:
        fail("KAG maturity governance pack source_inputs must keep the current donor order")

    stability_tiers = payload["stability_tiers"]
    if not isinstance(stability_tiers, list) or not stability_tiers:
        fail("KAG maturity governance pack stability_tiers must be a non-empty list")
    if payload["stability_tier_count"] != len(stability_tiers):
        fail("KAG maturity governance pack stability_tier_count must equal the number of tiers")
    tier_order: list[str] = []
    tier_status_map: dict[str, list[str]] = {}
    for index, tier in enumerate(stability_tiers):
        location = f"KAG maturity governance pack stability_tiers[{index}]"
        if not isinstance(tier, dict):
            fail(f"{location} must be an object")
        for key in (
            "tier",
            "registry_statuses",
            "consumer_posture",
            "expansion_posture",
            "live_payload_allowed",
        ):
            if key not in tier:
                fail(f"{location} is missing required key '{key}'")
        tier_name = tier["tier"]
        registry_statuses = validate_unique_string_list(
            tier["registry_statuses"],
            label=f"{location}.registry_statuses",
        )
        tier_order.append(tier_name)
        expected_statuses, expected_live_payload_allowed = (
            EXPECTED_KAG_MATURITY_GOVERNANCE_TIER_STATUS_MAP.get(tier_name, (None, None))
        )
        if expected_statuses is None:
            fail(f"{location}.tier '{tier_name}' is not supported")
        if registry_statuses != expected_statuses:
            fail(f"{location}.registry_statuses must match the current tier-to-status mapping")
        if tier["live_payload_allowed"] != expected_live_payload_allowed:
            fail(f"{location}.live_payload_allowed must match the current tier contract")
        tier_status_map[tier_name] = registry_statuses
    if tier_order != EXPECTED_KAG_MATURITY_GOVERNANCE_TIER_ORDER:
        fail("KAG maturity governance pack stability_tiers must keep the current stable order")

    surfaces = payload["surfaces"]
    if not isinstance(surfaces, list) or not surfaces:
        fail("KAG maturity governance pack surfaces must be a non-empty list")
    if payload["surface_count"] != len(surfaces):
        fail("KAG maturity governance pack surface_count must equal the number of surfaces")
    seen_surface_ids: set[str] = set()
    for index, surface in enumerate(surfaces):
        location = f"KAG maturity governance pack surfaces[{index}]"
        if not isinstance(surface, dict):
            fail(f"{location} must be an object")
        required_keys = {
            "surface_id",
            "surface_name",
            "registry_status",
            "source_repos",
            "derived_kind",
            "stability_tier",
            "consumer_posture",
            "proof_expectation_refs",
            "regrounding_mode_refs",
            "quarantine_policy",
            "stop_rule",
        }
        if not required_keys.issubset(surface):
            missing = sorted(required_keys - set(surface))
            fail(f"{location} is missing required keys: {', '.join(missing)}")
        surface_id = surface["surface_id"]
        if not isinstance(surface_id, str) or not surface_id:
            fail(f"{location}.surface_id must be a non-empty string")
        if surface_id in seen_surface_ids:
            fail(f"{location}.surface_id '{surface_id}' is duplicated")
        seen_surface_ids.add(surface_id)
        registry_surface = surfaces_by_id.get(surface_id)
        if registry_surface is None:
            fail(f"{location}.surface_id references unknown registry surface '{surface_id}'")
        if surface["surface_name"] != registry_surface["name"]:
            fail(f"{location}.surface_name must match the generated registry")
        if surface["registry_status"] != registry_surface["status"]:
            fail(f"{location}.registry_status must match the generated registry")
        if surface["derived_kind"] != registry_surface["derived_kind"]:
            fail(f"{location}.derived_kind must match the generated registry")
        source_repos = validate_unique_string_list(
            surface["source_repos"],
            label=f"{location}.source_repos",
        )
        if source_repos != registry_surface["source_repos"]:
            fail(f"{location}.source_repos must match the generated registry")
        stability_tier = surface["stability_tier"]
        if stability_tier not in tier_status_map:
            fail(f"{location}.stability_tier '{stability_tier}' is not supported")
        if registry_surface["status"] not in tier_status_map[stability_tier]:
            fail(f"{location}.stability_tier must match the registry status")
        if not isinstance(surface["consumer_posture"], str) or len(surface["consumer_posture"]) < 3:
            fail(f"{location}.consumer_posture must be a string of length >= 3")
        if not isinstance(surface["quarantine_policy"], str) or len(surface["quarantine_policy"]) < 3:
            fail(f"{location}.quarantine_policy must be a string of length >= 3")
        if not isinstance(surface["stop_rule"], str) or len(surface["stop_rule"]) < 3:
            fail(f"{location}.stop_rule must be a string of length >= 3")
        proof_gap_note = surface.get("proof_gap_note")
        if proof_gap_note is not None and (not isinstance(proof_gap_note, str) or len(proof_gap_note) < 10):
            fail(f"{location}.proof_gap_note must be a string of length >= 10 when present")

        proof_expectation_refs = validate_unique_string_list(
            surface["proof_expectation_refs"],
            label=f"{location}.proof_expectation_refs",
        )
        regrounding_mode_refs = validate_unique_string_list(
            surface["regrounding_mode_refs"],
            label=f"{location}.regrounding_mode_refs",
        )
        for proof_ref in proof_expectation_refs:
            resolve_aoa_evals_ref(
                proof_ref,
                label=f"{location}.proof_expectation_refs",
            )
        for mode_ref in regrounding_mode_refs:
            if mode_ref not in EXPECTED_KAG_MATURITY_GOVERNANCE_MODE_ORDER:
                fail(f"{location}.regrounding_mode_refs contains unsupported mode '{mode_ref}'")
    validate_exact_set(
        seen_surface_ids,
        set(surfaces_by_id),
        label="KAG maturity governance pack surface coverage",
    )

    owner_wait_states = payload["owner_wait_states"]
    if not isinstance(owner_wait_states, list) or not owner_wait_states:
        fail("KAG maturity governance pack owner_wait_states must be a non-empty list")
    if payload["owner_wait_state_count"] != len(owner_wait_states):
        fail("KAG maturity governance pack owner_wait_state_count must equal the number of owner wait states")
    owner_repo_order: list[str] = []
    for index, wait_state in enumerate(owner_wait_states):
        location = f"KAG maturity governance pack owner_wait_states[{index}]"
        if not isinstance(wait_state, dict):
            fail(f"{location} must be an object")
        owner_repo = wait_state.get("owner_repo")
        if not isinstance(owner_repo, str) or not owner_repo:
            fail(f"{location}.owner_repo must be a non-empty string")
        owner_repo_order.append(owner_repo)
        if not isinstance(wait_state.get("current_kag_posture"), str) or len(wait_state["current_kag_posture"]) < 10:
            fail(f"{location}.current_kag_posture must be a string of length >= 10")
        if not isinstance(wait_state.get("forbidden_inference"), str) or len(wait_state["forbidden_inference"]) < 10:
            fail(f"{location}.forbidden_inference must be a string of length >= 10")
        validate_unique_string_list(
            wait_state.get("waits_for"),
            label=f"{location}.waits_for",
        )
    if owner_repo_order != EXPECTED_KAG_MATURITY_GOVERNANCE_OWNER_WAIT_REPO_ORDER:
        fail("KAG maturity governance pack owner_wait_states must keep the current owner wait-state order")

    stop_rule = payload["stop_rule"]
    if not isinstance(stop_rule, dict):
        fail("KAG maturity governance pack stop_rule must be an object")
    blocked_surface_ids = validate_unique_string_list(
        stop_rule.get("blocked_surface_ids"),
        label="KAG maturity governance pack stop_rule.blocked_surface_ids",
    )
    validate_exact_set(
        blocked_surface_ids,
        {"AOA-K-0008"},
        label="KAG maturity governance pack stop_rule.blocked_surface_ids",
    )
    validate_unique_string_list(
        stop_rule.get("resume_when"),
        label="KAG maturity governance pack stop_rule.resume_when",
    )
    if not isinstance(stop_rule.get("new_surface_growth"), str) or len(stop_rule["new_surface_growth"]) < 3:
        fail("KAG maturity governance pack stop_rule.new_surface_growth must be a string of length >= 3")
    if not isinstance(stop_rule.get("current_program"), str) or len(stop_rule["current_program"]) < 3:
        fail("KAG maturity governance pack stop_rule.current_program must be a string of length >= 3")
    if not isinstance(stop_rule.get("pause_threshold"), str) or len(stop_rule["pause_threshold"]) < 10:
        fail("KAG maturity governance pack stop_rule.pause_threshold must be a string of length >= 10")

    projection_recovery = payload["projection_recovery"]
    if not isinstance(projection_recovery, dict):
        fail("KAG maturity governance pack projection_recovery must be an object")
    for field_name in (
        "stress_receipt_schema_ref",
        "regrounding_ticket_schema_ref",
        "stress_doc_ref",
        "quarantine_doc_ref",
        "regrounding_pack_ref",
    ):
        ref = projection_recovery.get(field_name)
        if not isinstance(ref, str) or not ref:
            fail(f"KAG maturity governance pack projection_recovery.{field_name} must be a non-empty string")
        resolve_known_ref(
            ref,
            label=f"KAG maturity governance pack projection_recovery.{field_name}",
        )
    health_states = validate_unique_string_list(
        projection_recovery.get("health_states"),
        label="KAG maturity governance pack projection_recovery.health_states",
    )
    if health_states != EXPECTED_KAG_MATURITY_GOVERNANCE_HEALTH_STATES:
        fail("KAG maturity governance pack projection_recovery.health_states must keep the current health-state order")
    mode_refs = validate_unique_string_list(
        projection_recovery.get("mode_refs"),
        label="KAG maturity governance pack projection_recovery.mode_refs",
    )
    if mode_refs != EXPECTED_KAG_MATURITY_GOVERNANCE_MODE_ORDER:
        fail("KAG maturity governance pack projection_recovery.mode_refs must keep the current regrounding mode order")
    validate_unique_string_list(
        projection_recovery.get("quarantine_triggers"),
        label="KAG maturity governance pack projection_recovery.quarantine_triggers",
    )
    validate_unique_string_list(
        projection_recovery.get("quarantine_exit_requirements"),
        label="KAG maturity governance pack projection_recovery.quarantine_exit_requirements",
    )

    if payload != expected_payload:
        fail("KAG maturity governance pack must match the committed manifest-driven governance payload")
