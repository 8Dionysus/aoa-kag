from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_cross_source_node_projection_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
    source_owned_export_dependencies: dict[tuple[str, str], dict[str, object]],
) -> None:
    payload = read_json(CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("cross-source node projection manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_inputs",
        "surface_bindings",
        "projection_pairings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"cross-source node projection manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("cross-source node projection manifest manifest_version must equal 1")
    if payload["pack_type"] != "cross_source_node_projection":
        fail("cross-source node projection manifest pack_type must equal 'cross_source_node_projection'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("cross-source node projection manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    source_inputs_by_name: dict[str, tuple[str, str, str]] = {}
    for index, source_input in enumerate(source_inputs):
        location = f"cross-source node projection manifest source_inputs[{index}]"
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
        source_inputs_by_name[name] = (repo, path, role)
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_INPUTS:
        fail("cross-source node projection manifest source_inputs must match the current bounded donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("cross-source node projection manifest surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"cross-source node projection manifest surface_bindings[{index}]"
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
        if surface.get("status") != "experimental":
            fail(f"{location} must only bind experimental registry surfaces")
    if actual_bindings != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_BINDINGS:
        fail("cross-source node projection manifest surface_bindings must match the current bounded projection contract")

    projection_pairings = payload["projection_pairings"]
    if not isinstance(projection_pairings, list) or not projection_pairings:
        fail("cross-source node projection manifest projection_pairings must be a non-empty list")
    if len(projection_pairings) != 1:
        fail(
            "cross-source node projection manifest projection_pairings must keep "
            "exactly one pairing in the current pilot"
        )
    seen_pairing_ids: set[str] = set()
    for index, pairing in enumerate(projection_pairings):
        location = f"cross-source node projection manifest projection_pairings[{index}]"
        if not isinstance(pairing, dict):
            fail(f"{location} must be an object")
        pairing_id = pairing.get("pairing_id")
        primary_export_input = pairing.get("primary_export_input")
        supporting_export_inputs = pairing.get("supporting_export_inputs")
        retrieval_axis_input = pairing.get("retrieval_axis_input")
        federation_spine_input = pairing.get("federation_spine_input")
        projection_summary = pairing.get("projection_summary")
        non_identity_boundary = pairing.get("non_identity_boundary")
        if not all(
            isinstance(value, str) and value
            for value in (
                pairing_id,
                primary_export_input,
                retrieval_axis_input,
                federation_spine_input,
                projection_summary,
                non_identity_boundary,
            )
        ):
            fail(
                f"{location} must keep pairing_id, primary_export_input, "
                "retrieval_axis_input, federation_spine_input, projection_summary, "
                "and non_identity_boundary"
            )
        if pairing_id in seen_pairing_ids:
            fail(f"{location}.pairing_id '{pairing_id}' is duplicated")
        seen_pairing_ids.add(pairing_id)
        if not isinstance(supporting_export_inputs, list) or not supporting_export_inputs:
            fail(f"{location}.supporting_export_inputs must be a non-empty list")
        if len(supporting_export_inputs) != 1:
            fail(
                f"{location}.supporting_export_inputs must keep exactly one "
                "supporting export in the current pilot"
            )
        supporting_input_name = supporting_export_inputs[0]
        if not isinstance(supporting_input_name, str) or not supporting_input_name:
            fail(f"{location}.supporting_export_inputs[0] must be a non-empty string")
        for label, input_name, expected_role in (
            ("primary_export_input", primary_export_input, "primary_export"),
            ("supporting_export_inputs[0]", supporting_input_name, "supporting_export"),
            ("retrieval_axis_input", retrieval_axis_input, "retrieval_axis"),
            ("federation_spine_input", federation_spine_input, "federation_spine"),
        ):
            source_input_entry = source_inputs_by_name.get(input_name)
            if source_input_entry is None:
                fail(f"{location}.{label} references unknown source input '{input_name}'")
            input_repo, input_path, input_role = source_input_entry
            if input_role != expected_role:
                fail(f"{location}.{label} must point to a {expected_role} source input")
            if expected_role in {"primary_export", "supporting_export"}:
                dependency = source_owned_export_dependencies.get((input_repo, input_path))
                if dependency is None:
                    fail(f"{location}.{label} must map to a declared source-owned export dependency")
                dependency_id = dependency["dependency_id"]
                if "AOA-K-0006" not in dependency["consumed_by"]:
                    fail(
                        f"{location}.{label} dependency '{dependency_id}' must declare "
                        "'AOA-K-0006' in consumed_by"
                    )
        if len(projection_summary) < 20:
            fail(f"{location}.projection_summary must be a string of length >= 20")
        if len(non_identity_boundary) < 20:
            fail(f"{location}.non_identity_boundary must be a string of length >= 20")

    if payload["output_paths"] != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATHS:
        fail("cross-source node projection manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_CONTRACT:
        fail("cross-source node projection manifest bounded_output_contract must match the current source-first guardrail")
