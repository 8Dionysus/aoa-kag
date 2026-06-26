from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_reasoning_handoff_pack(payload: object) -> None:
    if not isinstance(payload, dict):
        fail("reasoning handoff pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "scenario_count",
        "scenarios",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"reasoning handoff pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("reasoning handoff pack pack_version must equal 1")
    if payload["pack_type"] != "reasoning_handoff_pack":
        fail("reasoning handoff pack pack_type must equal 'reasoning_handoff_pack'")
    if payload["source_manifest_ref"] != REASONING_HANDOFF_MANIFEST_REF:
        fail(
            "reasoning handoff pack source_manifest_ref must point to "
            f"{REASONING_HANDOFF_MANIFEST_REF}"
        )
    if payload["bounded_output_contract"] != EXPECTED_REASONING_HANDOFF_CONTRACT:
        fail("reasoning handoff pack bounded_output_contract must match the current source-first guardrail")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("reasoning handoff pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"reasoning handoff pack source_inputs[{index}]"
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
    if actual_source_inputs != EXPECTED_REASONING_HANDOFF_INPUTS:
        fail("reasoning handoff pack source_inputs must match the manifest-driven donor set")

    scenarios = payload["scenarios"]
    if not isinstance(scenarios, list) or not scenarios:
        fail("reasoning handoff pack scenarios must be a non-empty list")
    scenario_count = payload["scenario_count"]
    if not isinstance(scenario_count, int) or scenario_count != len(scenarios):
        fail("reasoning handoff pack scenario_count must equal the number of scenarios")

    seen_scenarios: set[str] = set()
    for index, scenario in enumerate(scenarios):
        location = f"reasoning handoff pack scenarios[{index}]"
        if not isinstance(scenario, dict):
            fail(f"{location} must be an object")
        for key in (
            "scenario_ref",
            "playbook_ref",
            "artifact_spine",
            "eval_bridge",
            "memo_bridge",
            "compatible_query_modes",
            "authoritative_refs",
            "return_contract",
            "boundary_guardrails",
        ):
            if key not in scenario:
                fail(f"{location} is missing required key '{key}'")

        scenario_ref = scenario["scenario_ref"]
        playbook_ref = scenario["playbook_ref"]
        if not isinstance(scenario_ref, str) or not re.match(r"^AOA-P-[0-9]{4}$", scenario_ref):
            fail(f"{location}.scenario_ref must be an AOA playbook id")
        if scenario_ref in seen_scenarios:
            fail(f"{location}.scenario_ref '{scenario_ref}' is duplicated")
        seen_scenarios.add(scenario_ref)
        if not isinstance(playbook_ref, str) or not playbook_ref.startswith("aoa-playbooks/"):
            fail(f"{location}.playbook_ref must point to aoa-playbooks")
        resolve_known_ref(playbook_ref, label=f"{location}.playbook_ref")

        query_modes = validate_unique_string_list(
            scenario["compatible_query_modes"],
            label=f"{location}.compatible_query_modes",
        )
        validate_exact_set(
            query_modes,
            ALLOWED_QUERY_MODES,
            label=f"{location}.compatible_query_modes",
        )

        return_contract = scenario["return_contract"]
        if not isinstance(return_contract, dict):
            fail(f"{location}.return_contract must be an object")
        must_include = validate_unique_string_list(
            return_contract.get("must_include"),
            label=f"{location}.return_contract.must_include",
        )
        validate_exact_set(
            must_include,
            EXPECTED_RETURN_MUST_INCLUDE,
            label=f"{location}.return_contract.must_include",
        )
        may_include = validate_unique_string_list(
            return_contract.get("may_include"),
            label=f"{location}.return_contract.may_include",
            allow_empty=True,
        )
        validate_exact_set(
            may_include,
            EXPECTED_RETURN_MAY_INCLUDE,
            label=f"{location}.return_contract.may_include",
        )
        normalized_return_fields = validate_unique_string_list(
            return_contract.get("normalized_return_fields"),
            label=f"{location}.return_contract.normalized_return_fields",
        )
        if normalized_return_fields != ["axis_summary"]:
            fail(f"{location}.return_contract.normalized_return_fields must equal ['axis_summary']")

        if scenario["boundary_guardrails"] != EXPECTED_BOUNDARY_GUARDRAILS:
            fail(f"{location}.boundary_guardrails must match the current handoff guardrail contract")

        authoritative_refs = scenario["authoritative_refs"]
        if not isinstance(authoritative_refs, dict):
            fail(f"{location}.authoritative_refs must be an object")
        for key, prefix in (
            ("playbook_refs", "aoa-playbooks/"),
            ("eval_refs", "aoa-evals/"),
            ("memo_refs", "aoa-memo/"),
        ):
            refs = validate_unique_string_list(
                authoritative_refs.get(key),
                label=f"{location}.authoritative_refs.{key}",
            )
            for ref in refs:
                if not ref.startswith(prefix):
                    fail(f"{location}.authoritative_refs.{key} contains a ref outside {prefix}")
                resolve_known_ref(ref, label=f"{location}.authoritative_refs.{key}")
        guardrail_refs = validate_unique_string_list(
            authoritative_refs.get("kag_guardrail_refs"),
            label=f"{location}.authoritative_refs.kag_guardrail_refs",
        )
        if guardrail_refs != EXPECTED_REASONING_HANDOFF_KAG_GUARDRAIL_REFS:
            fail(f"{location}.authoritative_refs.kag_guardrail_refs must match the local KAG guardrail refs")
        for ref in guardrail_refs:
            resolve_known_ref(ref, label=f"{location}.authoritative_refs.kag_guardrail_refs")
        artifact_schema_refs = validate_unique_string_list(
            authoritative_refs.get("artifact_schema_refs"),
            label=f"{location}.authoritative_refs.artifact_schema_refs",
        )
        for ref in artifact_schema_refs:
            if not ref.endswith(".schema.json"):
                fail(f"{location}.authoritative_refs.artifact_schema_refs must only contain schema refs")
            resolve_known_ref(ref, label=f"{location}.authoritative_refs.artifact_schema_refs")

        artifact_spine = scenario["artifact_spine"]
        if not isinstance(artifact_spine, dict):
            fail(f"{location}.artifact_spine must be an object")
        verification_surface = validate_reasoning_artifact_descriptor(
            artifact_spine.get("verification_surface"),
            label=f"{location}.artifact_spine.verification_surface",
        )
        continuity_surface = artifact_spine.get("continuity_surface")
        if continuity_surface is not None:
            validate_reasoning_artifact_descriptor(
                continuity_surface,
                label=f"{location}.artifact_spine.continuity_surface",
            )
        supporting_artifacts = artifact_spine.get("supporting_artifacts")
        if not isinstance(supporting_artifacts, list):
            fail(f"{location}.artifact_spine.supporting_artifacts must be a list")
        supporting_names: list[str] = []
        for artifact_index, artifact in enumerate(supporting_artifacts):
            descriptor = validate_reasoning_artifact_descriptor(
                artifact,
                label=f"{location}.artifact_spine.supporting_artifacts[{artifact_index}]",
            )
            supporting_names.append(descriptor["artifact_name"])
        optional_trace_sidecars = artifact_spine.get("optional_trace_sidecars")
        if not isinstance(optional_trace_sidecars, list):
            fail(f"{location}.artifact_spine.optional_trace_sidecars must be a list")
        trace_sidecar_names: list[str] = []
        for artifact_index, artifact in enumerate(optional_trace_sidecars):
            descriptor = validate_reasoning_artifact_descriptor(
                artifact,
                label=f"{location}.artifact_spine.optional_trace_sidecars[{artifact_index}]",
            )
            trace_sidecar_names.append(descriptor["artifact_name"])

        eval_bridge = scenario["eval_bridge"]
        if not isinstance(eval_bridge, dict):
            fail(f"{location}.eval_bridge must be an object")
        eval_anchor_refs = validate_unique_string_list(
            eval_bridge.get("eval_anchor_refs"),
            label=f"{location}.eval_bridge.eval_anchor_refs",
        )
        for ref in eval_anchor_refs:
            resolve_known_ref(ref, label=f"{location}.eval_bridge.eval_anchor_refs")
        if eval_bridge.get("verification_surface") != verification_surface["artifact_name"]:
            fail(f"{location}.eval_bridge.verification_surface must match artifact_spine.verification_surface")
        trace_surfaces = validate_unique_string_list(
            eval_bridge.get("trace_surfaces"),
            label=f"{location}.eval_bridge.trace_surfaces",
            allow_empty=True,
        )
        for ref in trace_surfaces:
            resolve_known_ref(ref, label=f"{location}.eval_bridge.trace_surfaces")
        eval_contract_refs = validate_unique_string_list(
            eval_bridge.get("artifact_contract_refs"),
            label=f"{location}.eval_bridge.artifact_contract_refs",
        )
        for ref in eval_contract_refs:
            resolve_known_ref(ref, label=f"{location}.eval_bridge.artifact_contract_refs")
        report_expectation = eval_bridge.get("report_expectation")
        if not isinstance(report_expectation, dict):
            fail(f"{location}.eval_bridge.report_expectation must be an object")
        for key in ("report_format", "verdict_shape", "review_required"):
            if key not in report_expectation:
                fail(f"{location}.eval_bridge.report_expectation is missing '{key}'")

        memo_bridge = scenario["memo_bridge"]
        if not isinstance(memo_bridge, dict):
            fail(f"{location}.memo_bridge must be an object")
        memo_contract_refs = validate_unique_string_list(
            memo_bridge.get("memo_contract_refs"),
            label=f"{location}.memo_bridge.memo_contract_refs",
        )
        for ref in memo_contract_refs:
            resolve_known_ref(ref, label=f"{location}.memo_bridge.memo_contract_refs")
        memo_writeback_targets = validate_unique_string_list(
            memo_bridge.get("memo_writeback_targets"),
            label=f"{location}.memo_bridge.memo_writeback_targets",
        )
        delta_split = memo_bridge.get("delta_split")

        if scenario_ref == "AOA-P-0008":
            if verification_surface["artifact_name"] != "verification_result":
                fail(f"{location} must keep verification_result as the verification surface")
            if continuity_surface is not None:
                fail(f"{location} must not declare a continuity surface")
            if supporting_names != [
                "route_decision",
                "bounded_plan",
                "transition_decision",
                "distillation_pack",
            ]:
                fail(f"{location}.artifact_spine.supporting_artifacts must keep the bounded AOA-P-0008 route artifacts")
            if trace_sidecar_names != ["WitnessTrace"]:
                fail(f"{location}.artifact_spine.optional_trace_sidecars must keep WitnessTrace as the only optional sidecar")
            if trace_surfaces != ["aoa-memo/mechanics/recurrence-support/docs/WITNESS_TRACE_CONTRACT.md"]:
                fail(f"{location}.eval_bridge.trace_surfaces must keep the witness trace contract")
            if memo_writeback_targets != ["decision", "claim", "pattern"]:
                fail(f"{location}.memo_bridge.memo_writeback_targets must keep the bounded AOA-P-0008 writeback targets")
            if delta_split is not None:
                fail(f"{location}.memo_bridge.delta_split must stay null for AOA-P-0008")
            validate_exact_set(
                set(artifact_schema_refs),
                {
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.route_decision.schema.json",
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.bounded_plan.schema.json",
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.verification_result.schema.json",
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.transition_decision.schema.json",
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.distillation_pack.schema.json",
                    "aoa-memo/mechanics/recurrence-support/parts/witness-trace-contract/schemas/witness-trace.schema.json",
                },
                label=f"{location}.authoritative_refs.artifact_schema_refs",
            )
        elif scenario_ref == "AOA-P-0009":
            if verification_surface["artifact_name"] != "inquiry_checkpoint":
                fail(f"{location} must keep inquiry_checkpoint as the verification surface")
            if not isinstance(continuity_surface, dict) or continuity_surface.get("artifact_name") != "inquiry_checkpoint":
                fail(f"{location} must keep inquiry_checkpoint as the continuity surface")
            if supporting_names != [
                "decision_ledger",
                "contradiction_map",
                "memory_delta",
                "canon_delta",
                "next_pass_brief",
            ]:
                fail(f"{location}.artifact_spine.supporting_artifacts must keep the bounded AOA-P-0009 route artifacts")
            if trace_sidecar_names:
                fail(f"{location}.artifact_spine.optional_trace_sidecars must stay empty for AOA-P-0009")
            if trace_surfaces:
                fail(f"{location}.eval_bridge.trace_surfaces must stay empty for AOA-P-0009")
            if memo_writeback_targets != ["state_capsule", "decision"]:
                fail(f"{location}.memo_bridge.memo_writeback_targets must keep the bounded AOA-P-0009 writeback targets")
            if not isinstance(delta_split, dict):
                fail(f"{location}.memo_bridge.delta_split must be an object for AOA-P-0009")
            expected_delta_split = {
                "memory_delta": {
                    "artifact_name": "memory_delta",
                    "checkpoint_field": "memory_delta_refs",
                    "field_contract_ref": "aoa-memo/mechanics/checkpoint/parts/checkpoint-carry-contract/schemas/inquiry_checkpoint.schema.json",
                },
                "canon_delta": {
                    "artifact_name": "canon_delta",
                    "checkpoint_field": "canon_delta_refs",
                    "field_contract_ref": "aoa-memo/mechanics/checkpoint/parts/checkpoint-carry-contract/schemas/inquiry_checkpoint.schema.json",
                },
            }
            if delta_split != expected_delta_split:
                fail(f"{location}.memo_bridge.delta_split must keep the explicit inquiry checkpoint memory/canon split")
            validate_exact_set(
                set(artifact_schema_refs),
                {
                    "aoa-memo/mechanics/checkpoint/parts/checkpoint-carry-contract/schemas/inquiry_checkpoint.schema.json",
                    "aoa-memo/mechanics/checkpoint/parts/checkpoint-to-memory-mapping/schemas/checkpoint-to-memory-contract.schema.json",
                },
                label=f"{location}.authoritative_refs.artifact_schema_refs",
            )
        else:
            fail(f"{location}.scenario_ref '{scenario_ref}' is not supported in this pack")

    validate_exact_set(
        seen_scenarios,
        EXPECTED_REASONING_HANDOFF_SCENARIOS,
        label="reasoning handoff pack scenarios",
    )
