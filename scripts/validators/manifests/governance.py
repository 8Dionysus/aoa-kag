from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_kag_maturity_governance_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    payload = read_json(KAG_MATURITY_GOVERNANCE_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("KAG maturity governance manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_inputs",
        "stability_tiers",
        "surface_governance",
        "owner_wait_states",
        "stop_rule",
        "projection_recovery",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"KAG maturity governance manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("KAG maturity governance manifest manifest_version must equal 1")
    if payload["pack_type"] != "kag_maturity_governance":
        fail("KAG maturity governance manifest pack_type must equal 'kag_maturity_governance'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("KAG maturity governance manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    source_input_order: list[str] = []
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"KAG maturity governance manifest source_inputs[{index}]"
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
    if actual_source_inputs != EXPECTED_KAG_MATURITY_GOVERNANCE_INPUTS:
        fail("KAG maturity governance manifest source_inputs must match the current maturity donor set")
    if source_input_order != EXPECTED_KAG_MATURITY_GOVERNANCE_INPUT_ORDER:
        fail("KAG maturity governance manifest source_inputs must keep the current donor order")

    stability_tiers = payload["stability_tiers"]
    if not isinstance(stability_tiers, list) or not stability_tiers:
        fail("KAG maturity governance manifest stability_tiers must be a non-empty list")
    tier_order: list[str] = []
    tier_status_map: dict[str, list[str]] = {}
    for index, tier in enumerate(stability_tiers):
        location = f"KAG maturity governance manifest stability_tiers[{index}]"
        if not isinstance(tier, dict):
            fail(f"{location} must be an object")
        if set(tier) != {
            "tier",
            "registry_statuses",
            "consumer_posture",
            "expansion_posture",
            "live_payload_allowed",
        }:
            fail(
                f"{location} must keep exactly tier, registry_statuses, consumer_posture, "
                "expansion_posture, and live_payload_allowed"
            )
        tier_name = tier.get("tier")
        registry_statuses = tier.get("registry_statuses")
        consumer_posture = tier.get("consumer_posture")
        expansion_posture = tier.get("expansion_posture")
        live_payload_allowed = tier.get("live_payload_allowed")
        if not isinstance(tier_name, str) or not tier_name:
            fail(f"{location}.tier must be a non-empty string")
        tier_order.append(tier_name)
        normalized_registry_statuses = validate_unique_string_list(
            registry_statuses,
            label=f"{location}.registry_statuses",
        )
        if not isinstance(consumer_posture, str) or len(consumer_posture) < 3:
            fail(f"{location}.consumer_posture must be a string of length >= 3")
        if not isinstance(expansion_posture, str) or len(expansion_posture) < 3:
            fail(f"{location}.expansion_posture must be a string of length >= 3")
        if not isinstance(live_payload_allowed, bool):
            fail(f"{location}.live_payload_allowed must be a boolean")
        expected_statuses, expected_live_payload_allowed = (
            EXPECTED_KAG_MATURITY_GOVERNANCE_TIER_STATUS_MAP.get(tier_name, (None, None))
        )
        if expected_statuses is None:
            fail(f"{location}.tier '{tier_name}' is not supported")
        if normalized_registry_statuses != expected_statuses:
            fail(f"{location}.registry_statuses must match the current tier-to-status mapping")
        if live_payload_allowed != expected_live_payload_allowed:
            fail(f"{location}.live_payload_allowed must match the current tier contract")
        tier_status_map[tier_name] = normalized_registry_statuses
    if tier_order != EXPECTED_KAG_MATURITY_GOVERNANCE_TIER_ORDER:
        fail("KAG maturity governance manifest stability_tiers must keep the current stable order")

    surface_governance = payload["surface_governance"]
    if not isinstance(surface_governance, list) or not surface_governance:
        fail("KAG maturity governance manifest surface_governance must be a non-empty list")
    seen_surface_ids: set[str] = set()
    for index, surface in enumerate(surface_governance):
        location = f"KAG maturity governance manifest surface_governance[{index}]"
        if not isinstance(surface, dict):
            fail(f"{location} must be an object")
        allowed_keys = {
            "surface_id",
            "stability_tier",
            "consumer_posture",
            "proof_expectation_refs",
            "regrounding_mode_refs",
            "quarantine_policy",
            "stop_rule",
            "proof_gap_note",
        }
        if set(surface) - allowed_keys or {
            "surface_id",
            "stability_tier",
            "consumer_posture",
            "proof_expectation_refs",
            "regrounding_mode_refs",
            "quarantine_policy",
            "stop_rule",
        } - set(surface):
            fail(
                f"{location} must keep required maturity fields and may only add proof_gap_note"
            )

        surface_id = surface.get("surface_id")
        stability_tier = surface.get("stability_tier")
        consumer_posture = surface.get("consumer_posture")
        quarantine_policy = surface.get("quarantine_policy")
        stop_rule = surface.get("stop_rule")
        proof_gap_note = surface.get("proof_gap_note")
        if not isinstance(surface_id, str) or not surface_id:
            fail(f"{location}.surface_id must be a non-empty string")
        if surface_id in seen_surface_ids:
            fail(f"{location}.surface_id '{surface_id}' is duplicated")
        seen_surface_ids.add(surface_id)
        if surface_id not in surfaces_by_id:
            fail(f"{location}.surface_id references unknown registry surface '{surface_id}'")
        if not isinstance(stability_tier, str) or not stability_tier:
            fail(f"{location}.stability_tier must be a non-empty string")
        if stability_tier not in tier_status_map:
            fail(f"{location}.stability_tier '{stability_tier}' is not supported")
        if surfaces_by_id[surface_id]["status"] not in tier_status_map[stability_tier]:
            fail(
                f"{location}.stability_tier '{stability_tier}' must match registry status "
                f"for surface '{surface_id}'"
            )
        if not isinstance(consumer_posture, str) or len(consumer_posture) < 3:
            fail(f"{location}.consumer_posture must be a string of length >= 3")
        if not isinstance(quarantine_policy, str) or len(quarantine_policy) < 3:
            fail(f"{location}.quarantine_policy must be a string of length >= 3")
        if not isinstance(stop_rule, str) or len(stop_rule) < 3:
            fail(f"{location}.stop_rule must be a string of length >= 3")
        if proof_gap_note is not None and (not isinstance(proof_gap_note, str) or len(proof_gap_note) < 10):
            fail(f"{location}.proof_gap_note must be a string of length >= 10 when present")

        proof_expectation_refs = validate_unique_string_list(
            surface.get("proof_expectation_refs"),
            label=f"{location}.proof_expectation_refs",
        )
        regrounding_mode_refs = validate_unique_string_list(
            surface.get("regrounding_mode_refs"),
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
        label="KAG maturity governance manifest surface coverage",
    )

    owner_wait_states = payload["owner_wait_states"]
    if not isinstance(owner_wait_states, list) or not owner_wait_states:
        fail("KAG maturity governance manifest owner_wait_states must be a non-empty list")
    owner_repo_order: list[str] = []
    for index, wait_state in enumerate(owner_wait_states):
        location = f"KAG maturity governance manifest owner_wait_states[{index}]"
        if not isinstance(wait_state, dict):
            fail(f"{location} must be an object")
        if set(wait_state) != {
            "owner_repo",
            "current_kag_posture",
            "waits_for",
            "forbidden_inference",
        }:
            fail(
                f"{location} must keep exactly owner_repo, current_kag_posture, "
                "waits_for, and forbidden_inference"
            )
        owner_repo = wait_state.get("owner_repo")
        current_kag_posture = wait_state.get("current_kag_posture")
        forbidden_inference = wait_state.get("forbidden_inference")
        if not isinstance(owner_repo, str) or not owner_repo:
            fail(f"{location}.owner_repo must be a non-empty string")
        owner_repo_order.append(owner_repo)
        if not isinstance(current_kag_posture, str) or len(current_kag_posture) < 10:
            fail(f"{location}.current_kag_posture must be a string of length >= 10")
        if not isinstance(forbidden_inference, str) or len(forbidden_inference) < 10:
            fail(f"{location}.forbidden_inference must be a string of length >= 10")
        validate_unique_string_list(
            wait_state.get("waits_for"),
            label=f"{location}.waits_for",
        )
    if owner_repo_order != EXPECTED_KAG_MATURITY_GOVERNANCE_OWNER_WAIT_REPO_ORDER:
        fail("KAG maturity governance manifest owner_wait_states must keep the current owner wait-state order")

    stop_rule = payload["stop_rule"]
    if not isinstance(stop_rule, dict):
        fail("KAG maturity governance manifest stop_rule must be an object")
    if set(stop_rule) != {
        "new_surface_growth",
        "current_program",
        "resume_when",
        "blocked_surface_ids",
        "pause_threshold",
    }:
        fail(
            "KAG maturity governance manifest stop_rule must keep exactly "
            "new_surface_growth, current_program, resume_when, blocked_surface_ids, and pause_threshold"
        )
    if not isinstance(stop_rule.get("new_surface_growth"), str) or len(stop_rule["new_surface_growth"]) < 3:
        fail("KAG maturity governance manifest stop_rule.new_surface_growth must be a string of length >= 3")
    if not isinstance(stop_rule.get("current_program"), str) or len(stop_rule["current_program"]) < 3:
        fail("KAG maturity governance manifest stop_rule.current_program must be a string of length >= 3")
    blocked_surface_ids = validate_unique_string_list(
        stop_rule.get("blocked_surface_ids"),
        label="KAG maturity governance manifest stop_rule.blocked_surface_ids",
    )
    validate_exact_set(
        blocked_surface_ids,
        {"AOA-K-0008"},
        label="KAG maturity governance manifest stop_rule.blocked_surface_ids",
    )
    validate_unique_string_list(
        stop_rule.get("resume_when"),
        label="KAG maturity governance manifest stop_rule.resume_when",
    )
    if not isinstance(stop_rule.get("pause_threshold"), str) or len(stop_rule["pause_threshold"]) < 10:
        fail("KAG maturity governance manifest stop_rule.pause_threshold must be a string of length >= 10")

    projection_recovery = payload["projection_recovery"]
    if not isinstance(projection_recovery, dict):
        fail("KAG maturity governance manifest projection_recovery must be an object")
    if set(projection_recovery) != {
        "stress_receipt_schema_ref",
        "regrounding_ticket_schema_ref",
        "stress_doc_ref",
        "quarantine_doc_ref",
        "regrounding_pack_ref",
        "health_states",
        "mode_refs",
        "quarantine_triggers",
        "quarantine_exit_requirements",
    }:
        fail(
            "KAG maturity governance manifest projection_recovery must keep exactly "
            "the current schema, doc, pack, health, mode, trigger, and exit fields"
        )
    for field_name in (
        "stress_receipt_schema_ref",
        "regrounding_ticket_schema_ref",
        "stress_doc_ref",
        "quarantine_doc_ref",
        "regrounding_pack_ref",
    ):
        ref = projection_recovery.get(field_name)
        if not isinstance(ref, str) or not ref:
            fail(f"KAG maturity governance manifest projection_recovery.{field_name} must be a non-empty string")
        resolve_known_ref(
            ref,
            label=f"KAG maturity governance manifest projection_recovery.{field_name}",
        )
    health_states = validate_unique_string_list(
        projection_recovery.get("health_states"),
        label="KAG maturity governance manifest projection_recovery.health_states",
    )
    if health_states != EXPECTED_KAG_MATURITY_GOVERNANCE_HEALTH_STATES:
        fail("KAG maturity governance manifest projection_recovery.health_states must keep the current health-state order")
    mode_refs = validate_unique_string_list(
        projection_recovery.get("mode_refs"),
        label="KAG maturity governance manifest projection_recovery.mode_refs",
    )
    if mode_refs != EXPECTED_KAG_MATURITY_GOVERNANCE_MODE_ORDER:
        fail("KAG maturity governance manifest projection_recovery.mode_refs must keep the current regrounding mode order")
    validate_unique_string_list(
        projection_recovery.get("quarantine_triggers"),
        label="KAG maturity governance manifest projection_recovery.quarantine_triggers",
    )
    validate_unique_string_list(
        projection_recovery.get("quarantine_exit_requirements"),
        label="KAG maturity governance manifest projection_recovery.quarantine_exit_requirements",
    )

    if payload["output_paths"] != EXPECTED_KAG_MATURITY_GOVERNANCE_OUTPUT_PATHS:
        fail("KAG maturity governance manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_KAG_MATURITY_GOVERNANCE_CONTRACT:
        fail("KAG maturity governance manifest bounded_output_contract must match the current source-first stop-rule contract")
