from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_technique_lift_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    payload = read_json(TECHNIQUE_LIFT_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("technique lift manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_repo",
        "source_root_env",
        "source_inputs",
        "surface_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"technique lift manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("technique lift manifest manifest_version must equal 1")
    if payload["pack_type"] != "technique_lift_pack":
        fail("technique lift manifest pack_type must equal 'technique_lift_pack'")
    if payload["source_repo"] != "aoa-techniques":
        fail("technique lift manifest source_repo must equal 'aoa-techniques'")
    if payload["source_root_env"] != "AOA_TECHNIQUES_ROOT":
        fail("technique lift manifest source_root_env must equal 'AOA_TECHNIQUES_ROOT'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("technique lift manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"technique lift manifest source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, path, role)):
            fail(f"{location} must keep name, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        actual_source_inputs.add((name, path, role))
        donor_path = AOA_TECHNIQUES_ROOT / path
        if not donor_path.exists():
            fail(f"{location} references a missing donor path: aoa-techniques/{path}")
    if actual_source_inputs != EXPECTED_TECHNIQUE_LIFT_INPUTS:
        fail("technique lift manifest source_inputs must match the current bounded technique lift contract")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("technique lift manifest surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"technique lift manifest surface_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_id = binding.get("surface_id")
        surface_name = binding.get("surface_name")
        derived_kind = binding.get("derived_kind")
        derived_slot = binding.get("derived_slot")
        source_input = binding.get("source_input")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                surface_name,
                derived_kind,
                derived_slot,
                source_input,
            )
        ):
            fail(f"{location} must keep id, name, kind, slot, and source input")
        actual_bindings.add(
            (surface_id, surface_name, derived_kind, derived_slot, source_input)
        )

        surface = surfaces_by_id.get(surface_id)
        if surface is None:
            fail(f"{location} references unknown registry surface '{surface_id}'")
        if surface.get("name") != surface_name:
            fail(f"{location} does not match registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(f"{location} does not match registry derived_kind")
        if surface.get("status") != "active":
            fail(f"{location} must only bind active registry surfaces")
        if surface.get("source_repos") != ["aoa-techniques"]:
            fail(f"{location} must point to aoa-techniques-only active surfaces in this first pack")

    if actual_bindings != EXPECTED_TECHNIQUE_LIFT_BINDINGS:
        fail("technique lift manifest surface_bindings must match the current bounded technique pack")

    output_paths = payload["output_paths"]
    if output_paths != EXPECTED_TECHNIQUE_LIFT_OUTPUT_PATHS:
        fail("technique lift manifest output_paths must match the committed generated output paths")

    if payload["bounded_output_contract"] != EXPECTED_TECHNIQUE_LIFT_CONTRACT:
        fail("technique lift manifest bounded_output_contract must match the current source-first guardrail")
