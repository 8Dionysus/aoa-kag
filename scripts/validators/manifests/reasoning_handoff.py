from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_reasoning_handoff_manifest() -> None:
    payload = read_json(REASONING_HANDOFF_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("reasoning handoff manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_root_envs",
        "source_inputs",
        "scenario_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"reasoning handoff manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("reasoning handoff manifest manifest_version must equal 1")
    if payload["pack_type"] != "reasoning_handoff_pack":
        fail("reasoning handoff manifest pack_type must equal 'reasoning_handoff_pack'")
    if payload["source_root_envs"] != EXPECTED_REASONING_HANDOFF_SOURCE_ROOT_ENVS:
        fail("reasoning handoff manifest source_root_envs must match the current donor root contract")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("reasoning handoff manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"reasoning handoff manifest source_inputs[{index}]"
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
        actual_source_inputs.add((name, repo, path, role))
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_REASONING_HANDOFF_INPUTS:
        fail("reasoning handoff manifest source_inputs must match the current bounded donor set")

    scenario_bindings = payload["scenario_bindings"]
    if not isinstance(scenario_bindings, list) or not scenario_bindings:
        fail("reasoning handoff manifest scenario_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, tuple[str, ...], str | None, tuple[str, ...]]] = set()
    for index, binding in enumerate(scenario_bindings):
        location = f"reasoning handoff manifest scenario_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        scenario_ref = binding.get("scenario_ref")
        playbook_input = binding.get("playbook_input")
        eval_hook_input = binding.get("eval_hook_input")
        memo_contract_inputs = binding.get("memo_contract_inputs")
        continuity_input = binding.get("continuity_input")
        optional_trace_inputs = binding.get("optional_trace_inputs")
        if not all(isinstance(value, str) and value for value in (scenario_ref, playbook_input, eval_hook_input)):
            fail(f"{location} must keep scenario_ref, playbook_input, and eval_hook_input")
        if not isinstance(memo_contract_inputs, list) or not memo_contract_inputs:
            fail(f"{location}.memo_contract_inputs must be a non-empty list")
        if not all(isinstance(value, str) and value for value in memo_contract_inputs):
            fail(f"{location}.memo_contract_inputs contains an invalid entry")
        if continuity_input is not None and not isinstance(continuity_input, str):
            fail(f"{location}.continuity_input must be a string or null")
        if not isinstance(optional_trace_inputs, list):
            fail(f"{location}.optional_trace_inputs must be a list")
        if not all(isinstance(value, str) and value for value in optional_trace_inputs):
            fail(f"{location}.optional_trace_inputs contains an invalid entry")
        actual_bindings.add(
            (
                scenario_ref,
                playbook_input,
                eval_hook_input,
                tuple(memo_contract_inputs),
                continuity_input,
                tuple(optional_trace_inputs),
            )
        )
    if actual_bindings != EXPECTED_REASONING_HANDOFF_BINDINGS:
        fail("reasoning handoff manifest scenario_bindings must match the current bounded scenario contract")

    if payload["output_paths"] != EXPECTED_REASONING_HANDOFF_OUTPUT_PATHS:
        fail("reasoning handoff manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_REASONING_HANDOFF_CONTRACT:
        fail("reasoning handoff manifest bounded_output_contract must match the current source-first guardrail")
