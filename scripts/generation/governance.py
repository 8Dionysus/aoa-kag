from __future__ import annotations

from .common import *
from .registry import build_registry_payload
from .regrounding import build_return_regrounding_pack_payload

def build_kag_maturity_governance_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(KAG_MATURITY_GOVERNANCE_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("KAG maturity governance manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    stability_tiers = manifest.get("stability_tiers")
    surface_governance = manifest.get("surface_governance")
    owner_wait_states = manifest.get("owner_wait_states")
    stop_rule = manifest.get("stop_rule")
    projection_recovery = manifest.get("projection_recovery")
    output_paths = manifest.get("output_paths")
    bounded_output_contract = manifest.get("bounded_output_contract")

    if not isinstance(source_inputs, list) or not source_inputs:
        fail("KAG maturity governance manifest must declare source_inputs")
    if not isinstance(stability_tiers, list) or not stability_tiers:
        fail("KAG maturity governance manifest must declare stability_tiers")
    if not isinstance(surface_governance, list) or not surface_governance:
        fail("KAG maturity governance manifest must declare surface_governance")
    if not isinstance(owner_wait_states, list) or not owner_wait_states:
        fail("KAG maturity governance manifest must declare owner_wait_states")
    if not isinstance(stop_rule, dict):
        fail("KAG maturity governance manifest must declare stop_rule")
    if not isinstance(projection_recovery, dict):
        fail("KAG maturity governance manifest must declare projection_recovery")
    if not isinstance(output_paths, dict):
        fail("KAG maturity governance manifest must declare output_paths")
    if not isinstance(bounded_output_contract, dict):
        fail("KAG maturity governance manifest must declare bounded_output_contract")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry payload must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    emitted_source_inputs: list[dict[str, str]] = []
    seen_source_input_names: set[str] = set()
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("KAG maturity governance source_inputs entries must be objects")
        name = require_string(
            source_input.get("name"),
            label="KAG maturity governance source_input.name",
        )
        repo = require_string(
            source_input.get("repo"),
            label=f"KAG maturity governance source_input '{name}'.repo",
        )
        path = ensure_repo_relative_path(
            source_input.get("path"),
            label=f"KAG maturity governance source_input '{name}'.path",
        )
        role = require_string(
            source_input.get("role"),
            label=f"KAG maturity governance source_input '{name}'.role",
        )
        if name in seen_source_input_names:
            fail(f"duplicate KAG maturity governance source input '{name}'")
        seen_source_input_names.add(name)
        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        if not input_path.exists():
            fail(
                "KAG maturity governance donor input does not exist: "
                + manifest_input_ref(normalized_input)
            )
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    emitted_stability_tiers: list[dict[str, object]] = []
    tier_details_by_name: dict[str, dict[str, object]] = {}
    seen_tier_names: set[str] = set()
    for tier in stability_tiers:
        if not isinstance(tier, dict):
            fail("KAG maturity governance stability_tiers entries must be objects")
        tier_name = require_string(
            tier.get("tier"),
            label="KAG maturity governance stability_tier.tier",
        )
        if tier_name in seen_tier_names:
            fail(f"duplicate KAG maturity governance tier '{tier_name}'")
        seen_tier_names.add(tier_name)
        registry_statuses = require_string_list(
            tier.get("registry_statuses"),
            label=f"KAG maturity governance tier '{tier_name}'.registry_statuses",
        )
        consumer_posture = require_string(
            tier.get("consumer_posture"),
            label=f"KAG maturity governance tier '{tier_name}'.consumer_posture",
        )
        expansion_posture = require_string(
            tier.get("expansion_posture"),
            label=f"KAG maturity governance tier '{tier_name}'.expansion_posture",
        )
        live_payload_allowed = tier.get("live_payload_allowed")
        if not isinstance(live_payload_allowed, bool):
            fail(
                f"KAG maturity governance tier '{tier_name}'.live_payload_allowed "
                "must be a boolean"
            )
        normalized_tier = {
            "tier": tier_name,
            "registry_statuses": registry_statuses,
            "consumer_posture": consumer_posture,
            "expansion_posture": expansion_posture,
            "live_payload_allowed": live_payload_allowed,
        }
        emitted_stability_tiers.append(normalized_tier)
        tier_details_by_name[tier_name] = normalized_tier

    return_regrounding_pack_payload = build_return_regrounding_pack_payload(
        registry_payload
    )
    mode_ids = [
        mode["mode_id"]
        for mode in return_regrounding_pack_payload["modes"]
        if isinstance(mode, dict) and isinstance(mode.get("mode_id"), str)
    ]

    emitted_surfaces: list[dict[str, object]] = []
    seen_surface_ids: set[str] = set()
    for binding in surface_governance:
        if not isinstance(binding, dict):
            fail("KAG maturity governance surface_governance entries must be objects")
        surface_id = require_string(
            binding.get("surface_id"),
            label="KAG maturity governance surface_governance.surface_id",
        )
        if surface_id in seen_surface_ids:
            fail(f"duplicate KAG maturity governance surface '{surface_id}'")
        seen_surface_ids.add(surface_id)
        stability_tier = require_string(
            binding.get("stability_tier"),
            label=f"KAG maturity governance surface '{surface_id}'.stability_tier",
        )
        tier_details = tier_details_by_name.get(stability_tier)
        if tier_details is None:
            fail(
                f"KAG maturity governance surface '{surface_id}' references unknown "
                f"stability tier '{stability_tier}'"
            )
        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(
                f"KAG maturity governance surface '{surface_id}' does not exist in the registry"
            )
        registry_status = surface.get("status")
        if registry_status not in tier_details["registry_statuses"]:
            fail(
                f"KAG maturity governance surface '{surface_id}' status '{registry_status}' "
                f"does not match tier '{stability_tier}'"
            )

        consumer_posture = require_string(
            binding.get("consumer_posture"),
            label=f"KAG maturity governance surface '{surface_id}'.consumer_posture",
        )
        proof_expectation_refs = require_string_list(
            binding.get("proof_expectation_refs"),
            label=f"KAG maturity governance surface '{surface_id}'.proof_expectation_refs",
        )
        regrounding_mode_refs = require_string_list(
            binding.get("regrounding_mode_refs"),
            label=f"KAG maturity governance surface '{surface_id}'.regrounding_mode_refs",
        )
        quarantine_policy = require_string(
            binding.get("quarantine_policy"),
            label=f"KAG maturity governance surface '{surface_id}'.quarantine_policy",
        )
        surface_stop_rule = require_string(
            binding.get("stop_rule"),
            label=f"KAG maturity governance surface '{surface_id}'.stop_rule",
        )
        proof_gap_note = require_optional_string(
            binding.get("proof_gap_note"),
            label=f"KAG maturity governance surface '{surface_id}'.proof_gap_note",
        )

        for proof_ref in proof_expectation_refs:
            if not proof_ref.startswith("aoa-evals/"):
                fail(
                    f"KAG maturity governance surface '{surface_id}' proof ref must "
                    f"stay in aoa-evals: {proof_ref}"
                )
            proof_path = resolve_repo_path("aoa-evals", proof_ref.split("/", 1)[1])
            if not proof_path.exists():
                fail(
                    f"KAG maturity governance surface '{surface_id}' references missing "
                    f"proof anchor '{proof_ref}'"
                )
        for mode_ref in regrounding_mode_refs:
            if mode_ref not in mode_ids:
                fail(
                    f"KAG maturity governance surface '{surface_id}' references unknown "
                    f"regrounding mode '{mode_ref}'"
                )

        emitted_surface = {
            "surface_id": surface_id,
            "surface_name": surface["name"],
            "registry_status": registry_status,
            "source_repos": list(surface["source_repos"]),
            "derived_kind": surface["derived_kind"],
            "stability_tier": stability_tier,
            "consumer_posture": consumer_posture,
            "proof_expectation_refs": proof_expectation_refs,
            "regrounding_mode_refs": regrounding_mode_refs,
            "quarantine_policy": quarantine_policy,
            "stop_rule": surface_stop_rule,
        }
        if proof_gap_note:
            emitted_surface["proof_gap_note"] = proof_gap_note
        emitted_surfaces.append(emitted_surface)

    if set(seen_surface_ids) != set(registry_by_id):
        fail(
            "KAG maturity governance surface_governance must cover every registry surface exactly once"
        )

    emitted_owner_wait_states: list[dict[str, object]] = []
    seen_owner_wait_repos: set[str] = set()
    for wait_state in owner_wait_states:
        if not isinstance(wait_state, dict):
            fail("KAG maturity governance owner_wait_states entries must be objects")
        owner_repo = require_string(
            wait_state.get("owner_repo"),
            label="KAG maturity governance owner_wait_state.owner_repo",
        )
        if owner_repo in seen_owner_wait_repos:
            fail(f"duplicate KAG maturity governance owner wait-state '{owner_repo}'")
        seen_owner_wait_repos.add(owner_repo)
        current_kag_posture = require_string(
            wait_state.get("current_kag_posture"),
            label=f"KAG maturity governance owner_wait_state '{owner_repo}'.current_kag_posture",
        )
        waits_for = require_string_list(
            wait_state.get("waits_for"),
            label=f"KAG maturity governance owner_wait_state '{owner_repo}'.waits_for",
        )
        forbidden_inference = require_string(
            wait_state.get("forbidden_inference"),
            label=f"KAG maturity governance owner_wait_state '{owner_repo}'.forbidden_inference",
        )
        emitted_owner_wait_states.append(
            {
                "owner_repo": owner_repo,
                "current_kag_posture": current_kag_posture,
                "waits_for": waits_for,
                "forbidden_inference": forbidden_inference,
            }
        )

    new_surface_growth = require_string(
        stop_rule.get("new_surface_growth"),
        label="KAG maturity governance stop_rule.new_surface_growth",
    )
    current_program = require_string(
        stop_rule.get("current_program"),
        label="KAG maturity governance stop_rule.current_program",
    )
    resume_when = require_string_list(
        stop_rule.get("resume_when"),
        label="KAG maturity governance stop_rule.resume_when",
    )
    blocked_surface_ids = require_string_list(
        stop_rule.get("blocked_surface_ids"),
        label="KAG maturity governance stop_rule.blocked_surface_ids",
    )
    pause_threshold = require_string(
        stop_rule.get("pause_threshold"),
        label="KAG maturity governance stop_rule.pause_threshold",
    )
    for blocked_surface_id in blocked_surface_ids:
        if blocked_surface_id not in registry_by_id:
            fail(
                f"KAG maturity governance stop_rule references unknown surface "
                f"'{blocked_surface_id}'"
            )

    stress_receipt_schema_ref = ensure_local_ref_exists(
        projection_recovery.get("stress_receipt_schema_ref"),
        label="KAG maturity governance projection_recovery.stress_receipt_schema_ref",
    )
    regrounding_ticket_schema_ref = ensure_local_ref_exists(
        projection_recovery.get("regrounding_ticket_schema_ref"),
        label="KAG maturity governance projection_recovery.regrounding_ticket_schema_ref",
    )
    stress_doc_ref = ensure_local_ref_exists(
        projection_recovery.get("stress_doc_ref"),
        label="KAG maturity governance projection_recovery.stress_doc_ref",
    )
    quarantine_doc_ref = ensure_local_ref_exists(
        projection_recovery.get("quarantine_doc_ref"),
        label="KAG maturity governance projection_recovery.quarantine_doc_ref",
    )
    regrounding_pack_ref = ensure_local_ref_exists(
        projection_recovery.get("regrounding_pack_ref"),
        label="KAG maturity governance projection_recovery.regrounding_pack_ref",
        allow_missing_refs={RETURN_REGROUNDING_MIN_OUTPUT_REF},
    )
    health_states = require_string_list(
        projection_recovery.get("health_states"),
        label="KAG maturity governance projection_recovery.health_states",
    )
    recovery_mode_refs = require_string_list(
        projection_recovery.get("mode_refs"),
        label="KAG maturity governance projection_recovery.mode_refs",
    )
    quarantine_triggers = require_string_list(
        projection_recovery.get("quarantine_triggers"),
        label="KAG maturity governance projection_recovery.quarantine_triggers",
    )
    quarantine_exit_requirements = require_string_list(
        projection_recovery.get("quarantine_exit_requirements"),
        label="KAG maturity governance projection_recovery.quarantine_exit_requirements",
    )
    for mode_ref in recovery_mode_refs:
        if mode_ref not in mode_ids:
            fail(
                f"KAG maturity governance projection_recovery references unknown "
                f"regrounding mode '{mode_ref}'"
            )

    full_output_path = ensure_local_ref_exists(
        output_paths.get("full"),
        label="KAG maturity governance output_paths.full",
        allow_missing_refs={KAG_MATURITY_GOVERNANCE_OUTPUT_REF},
    )
    min_output_path = ensure_local_ref_exists(
        output_paths.get("min"),
        label="KAG maturity governance output_paths.min",
        allow_missing_refs={KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_REF},
    )
    if full_output_path != KAG_MATURITY_GOVERNANCE_OUTPUT_REF:
        fail(
            "KAG maturity governance output_paths.full must stay "
            f"{KAG_MATURITY_GOVERNANCE_OUTPUT_REF}"
        )
    if min_output_path != KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_REF:
        fail(
            "KAG maturity governance output_paths.min must stay "
            f"{KAG_MATURITY_GOVERNANCE_MIN_OUTPUT_REF}"
        )

    source_trace_required = bounded_output_contract.get("source_trace_required")
    if not isinstance(source_trace_required, bool):
        fail("KAG maturity governance bounded_output_contract.source_trace_required must be a boolean")
    normalized_bounded_output_contract = {
        "source_trace_required": source_trace_required,
        "source_replacement": require_string(
            bounded_output_contract.get("source_replacement"),
            label="KAG maturity governance bounded_output_contract.source_replacement",
        ),
        "routing_ownership": require_string(
            bounded_output_contract.get("routing_ownership"),
            label="KAG maturity governance bounded_output_contract.routing_ownership",
        ),
        "memory_truth_ownership": require_string(
            bounded_output_contract.get("memory_truth_ownership"),
            label="KAG maturity governance bounded_output_contract.memory_truth_ownership",
        ),
        "proof_ownership": require_string(
            bounded_output_contract.get("proof_ownership"),
            label="KAG maturity governance bounded_output_contract.proof_ownership",
        ),
        "new_surface_growth": require_string(
            bounded_output_contract.get("new_surface_growth"),
            label="KAG maturity governance bounded_output_contract.new_surface_growth",
        ),
        "quarantine_shortcuts": require_string(
            bounded_output_contract.get("quarantine_shortcuts"),
            label="KAG maturity governance bounded_output_contract.quarantine_shortcuts",
        ),
    }

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": KAG_MATURITY_GOVERNANCE_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "stability_tier_count": len(emitted_stability_tiers),
        "stability_tiers": emitted_stability_tiers,
        "surface_count": len(emitted_surfaces),
        "surfaces": emitted_surfaces,
        "owner_wait_state_count": len(emitted_owner_wait_states),
        "owner_wait_states": emitted_owner_wait_states,
        "stop_rule": {
            "new_surface_growth": new_surface_growth,
            "current_program": current_program,
            "resume_when": resume_when,
            "blocked_surface_ids": blocked_surface_ids,
            "pause_threshold": pause_threshold,
        },
        "projection_recovery": {
            "stress_receipt_schema_ref": stress_receipt_schema_ref,
            "regrounding_ticket_schema_ref": regrounding_ticket_schema_ref,
            "stress_doc_ref": stress_doc_ref,
            "quarantine_doc_ref": quarantine_doc_ref,
            "regrounding_pack_ref": regrounding_pack_ref,
            "health_states": health_states,
            "mode_refs": recovery_mode_refs,
            "quarantine_triggers": quarantine_triggers,
            "quarantine_exit_requirements": quarantine_exit_requirements,
        },
        "bounded_output_contract": normalized_bounded_output_contract,
    }
