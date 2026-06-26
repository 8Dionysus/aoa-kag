from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_return_regrounding_manifest() -> None:
    payload = read_json(RETURN_REGROUNDING_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("return regrounding manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_inputs",
        "mode_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"return regrounding manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("return regrounding manifest manifest_version must equal 1")
    if payload["pack_type"] != "return_regrounding_pack":
        fail("return regrounding manifest pack_type must equal 'return_regrounding_pack'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("return regrounding manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    input_order: list[str] = []
    for index, source_input in enumerate(source_inputs):
        location = f"return regrounding manifest source_inputs[{index}]"
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
        input_order.append(name)
        actual_source_inputs.add((name, repo, path, role))
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_RETURN_REGROUNDING_INPUTS:
        fail("return regrounding manifest source_inputs must match the current bounded donor set")
    if input_order != EXPECTED_RETURN_REGROUNDING_INPUT_ORDER:
        fail("return regrounding manifest source_inputs must keep the current additive donor order")

    mode_bindings = payload["mode_bindings"]
    if not isinstance(mode_bindings, list) or not mode_bindings:
        fail("return regrounding manifest mode_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = set()
    binding_order: list[str] = []
    for index, binding in enumerate(mode_bindings):
        location = f"return regrounding manifest mode_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        mode_ref = binding.get("mode_ref")
        primary_input = binding.get("primary_input")
        supporting_inputs = binding.get("supporting_inputs")
        dependency_refs = binding.get("dependency_refs", [])
        if not isinstance(mode_ref, str) or not mode_ref:
            fail(f"{location}.mode_ref must be a non-empty string")
        if not isinstance(primary_input, str) or not primary_input:
            fail(f"{location}.primary_input must be a non-empty string")
        if not isinstance(supporting_inputs, list) or not supporting_inputs:
            fail(f"{location}.supporting_inputs must be a non-empty list")
        if not all(isinstance(value, str) and value for value in supporting_inputs):
            fail(f"{location}.supporting_inputs contains an invalid entry")
        if not isinstance(dependency_refs, list):
            fail(f"{location}.dependency_refs must be a list when present")
        if not all(isinstance(value, str) and value for value in dependency_refs):
            fail(f"{location}.dependency_refs contains an invalid entry")
        actual_bindings.add(
            (
                mode_ref,
                primary_input,
                tuple(supporting_inputs),
                tuple(dependency_refs),
            )
        )
        binding_order.append(mode_ref)
    if actual_bindings != EXPECTED_RETURN_REGROUNDING_BINDINGS:
        fail("return regrounding manifest mode_bindings must match the current bounded mode contract")
    if binding_order != EXPECTED_RETURN_REGROUNDING_MODE_ORDER:
        fail("return regrounding manifest mode_bindings must keep the current stable mode order")

    if payload["output_paths"] != {
        "full": RETURN_REGROUNDING_OUTPUT_REF,
        "min": RETURN_REGROUNDING_MIN_OUTPUT_REF,
    }:
        fail("return regrounding manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_RETURN_REGROUNDING_CONTRACT:
        fail("return regrounding manifest bounded_output_contract must match the current source-first guardrail")
