from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_federation_spine_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
    source_owned_export_dependencies: dict[tuple[str, str], dict[str, object]],
    federation_export_registry_entries: dict[tuple[str, str], dict[str, object]],
) -> None:
    payload = read_json(FEDERATION_SPINE_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("federation spine manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_inputs",
        "repo_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"federation spine manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("federation spine manifest manifest_version must equal 1")
    if payload["pack_type"] != "federation_spine":
        fail("federation spine manifest pack_type must equal 'federation_spine'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("federation spine manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    source_input_order: list[str] = []
    source_inputs_by_name: dict[str, tuple[str, str, str]] = {}
    for index, source_input in enumerate(source_inputs):
        location = f"federation spine manifest source_inputs[{index}]"
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
        source_inputs_by_name[name] = (repo, path, role)
        resolve_known_ref(repo_ref(repo, path), label=location)
    if actual_source_inputs != EXPECTED_FEDERATION_SPINE_SOURCE_INPUTS:
        fail("federation spine manifest source_inputs must match the current bounded donor set")
    if source_input_order != EXPECTED_FEDERATION_SPINE_SOURCE_INPUT_ORDER:
        fail("federation spine manifest source_inputs must keep the current additive donor order")
    registry_manifest_input = source_inputs_by_name.get("federation_export_registry_manifest")
    if registry_manifest_input != (
        "aoa-kag",
        FEDERATION_EXPORT_REGISTRY_MANIFEST_REF,
        "activation_manifest",
    ):
        fail(
            "federation spine manifest must keep federation_export_registry_manifest "
            f"pointing to {FEDERATION_EXPORT_REGISTRY_MANIFEST_REF}"
        )

    repo_bindings = payload["repo_bindings"]
    if not isinstance(repo_bindings, list) or not repo_bindings:
        fail("federation spine manifest repo_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str]] = set()
    repo_binding_order: list[str] = []
    for index, binding in enumerate(repo_bindings):
        location = f"federation spine manifest repo_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_id = binding.get("surface_id")
        repo_name = binding.get("repo")
        pilot_posture = binding.get("pilot_posture")
        export_input = binding.get("export_input")
        adjunct_surfaces = binding.get("adjunct_surfaces")
        provenance_note = binding.get("provenance_note")
        non_identity_boundary = binding.get("non_identity_boundary")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                repo_name,
                pilot_posture,
                export_input,
                provenance_note,
                non_identity_boundary,
            )
        ):
            fail(
                f"{location} must keep surface_id, repo, pilot_posture, export_input, provenance_note, and non_identity_boundary"
            )
        if len(provenance_note) < 20:
            fail(f"{location}.provenance_note must be a string of length >= 20")
        if len(non_identity_boundary) < 20:
            fail(f"{location}.non_identity_boundary must be a string of length >= 20")
        if not isinstance(adjunct_surfaces, list):
            fail(f"{location}.adjunct_surfaces must be a list")

        surface = surfaces_by_id.get(surface_id)
        if surface is None:
            fail(f"{location} references unknown registry surface '{surface_id}'")
        if surface.get("status") != "experimental":
            fail(f"{location} must point to an experimental registry surface")
        repo_binding_order.append(repo_name)
        source_input_entry = source_inputs_by_name.get(export_input)
        if source_input_entry is None:
            fail(f"{location}.export_input references unknown source input '{export_input}'")
        input_repo, input_path, _ = source_input_entry
        dependency = source_owned_export_dependencies.get((input_repo, input_path))
        if dependency is None:
            fail(
                f"{location}.export_input must map to a declared source-owned export "
                "dependency"
            )
        dependency_id = dependency["dependency_id"]
        if surface_id not in dependency["consumed_by"]:
            fail(
                f"{location}.export_input dependency '{dependency_id}' must declare "
                f"'{surface_id}' in consumed_by"
            )
        registry_entry = federation_export_registry_entries.get((input_repo, input_path))
        if registry_entry is None:
            fail(
                f"{location}.export_input must map to a declared federation export "
                "registry entry"
            )
        activation = registry_entry["activation"]
        if activation["spine_visible"] is not True:
            fail(f"{location}.export_input must stay spine-visible in the donor registry")
        if registry_entry["owner_repo"] != repo_name:
            fail(f"{location}.export_input must stay aligned with owner_repo '{repo_name}'")

        normalized_adjunct_surfaces: list[dict[str, object]] = []
        for adjunct_index, adjunct in enumerate(adjunct_surfaces):
            adjunct_location = f"{location}.adjunct_surfaces[{adjunct_index}]"
            if not isinstance(adjunct, dict):
                fail(f"{adjunct_location} must be an object")
            if set(adjunct) != {
                "surface_id",
                "surface_name",
                "surface_ref",
                "match_key",
                "target_value",
                "route_id",
                "adjunct_budget",
                "subordinate_posture",
            }:
                fail(
                    f"{adjunct_location} must keep exactly surface_id, surface_name, "
                    "surface_ref, match_key, target_value, route_id, adjunct_budget, "
                    "and subordinate_posture"
                )
            adjunct_surface_id = adjunct.get("surface_id")
            adjunct_surface_name = adjunct.get("surface_name")
            adjunct_surface_ref = adjunct.get("surface_ref")
            adjunct_match_key = adjunct.get("match_key")
            adjunct_target_value = adjunct.get("target_value")
            adjunct_route_id = adjunct.get("route_id")
            adjunct_budget = adjunct.get("adjunct_budget")
            subordinate_posture = adjunct.get("subordinate_posture")
            if not all(
                isinstance(value, str) and value
                for value in (
                    adjunct_surface_id,
                    adjunct_surface_name,
                    adjunct_surface_ref,
                    adjunct_match_key,
                    adjunct_target_value,
                    adjunct_route_id,
                )
            ):
                fail(
                    f"{adjunct_location} must keep surface_id, surface_name, "
                    "surface_ref, match_key, target_value, and route_id"
                )
            if adjunct_budget != EXPECTED_TOS_STANDALONE_ADJUNCT_BUDGET:
                fail(
                    f"{adjunct_location}.adjunct_budget must match the current "
                    "standalone adjunct budget"
                )
            if (
                subordinate_posture
                != EXPECTED_TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE
            ):
                fail(
                    f"{adjunct_location}.subordinate_posture must match the "
                    "current source-first subordinate posture"
                )
            adjunct_surface = surfaces_by_id.get(adjunct_surface_id)
            if adjunct_surface is None:
                fail(
                    f"{adjunct_location} references unknown registry surface "
                    f"'{adjunct_surface_id}'"
                )
            if adjunct_surface.get("status") != "experimental":
                fail(f"{adjunct_location} must point to an experimental registry surface")
            if adjunct_surface.get("name") != adjunct_surface_name:
                fail(
                    f"{adjunct_location}.surface_name must match registry surface "
                    f"'{adjunct_surface.get('name')}'"
                )
            if adjunct_match_key != "retrieval_id":
                fail(f"{adjunct_location}.match_key must equal 'retrieval_id'")
            if adjunct_target_value != TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID:
                fail(
                    f"{adjunct_location}.target_value must equal "
                    f"'{TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID}'"
                )
            if adjunct_route_id != TOS_ZARATHUSTRA_ROUTE_ID:
                fail(
                    f"{adjunct_location}.route_id must equal "
                    f"'{TOS_ZARATHUSTRA_ROUTE_ID}'"
                )
            resolve_known_ref(
                repo_ref(KAG_REPO, adjunct_surface_ref),
                label=f"{adjunct_location}.surface_ref",
            )
            normalized_adjunct_surfaces.append(
                {
                    "surface_id": adjunct_surface_id,
                    "surface_name": adjunct_surface_name,
                    "surface_ref": adjunct_surface_ref,
                    "match_key": adjunct_match_key,
                    "target_value": adjunct_target_value,
                    "route_id": adjunct_route_id,
                    "adjunct_budget": adjunct_budget,
                    "subordinate_posture": subordinate_posture,
                }
            )

        expected_adjunct_surfaces = EXPECTED_FEDERATION_SPINE_ADJUNCTS_BY_REPO.get(repo_name)
        if expected_adjunct_surfaces is None:
            fail(f"{location}.repo '{repo_name}' is not allowed in the current spine scope")
        if normalized_adjunct_surfaces != expected_adjunct_surfaces:
            fail(
                f"{location}.adjunct_surfaces must match the current bounded adjunct "
                f"contract for '{repo_name}'"
            )

        actual_bindings.add((surface_id, repo_name, pilot_posture, export_input))
    if actual_bindings != EXPECTED_FEDERATION_SPINE_BINDINGS:
        fail("federation spine manifest repo_bindings must match the current bounded spine contract")
    if repo_binding_order != EXPECTED_FEDERATION_SPINE_REPO_ORDER:
        fail("federation spine manifest repo_bindings must keep the current stable repo order")

    if payload["output_paths"] != EXPECTED_FEDERATION_SPINE_OUTPUT_PATHS:
        fail("federation spine manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_FEDERATION_SPINE_CONTRACT:
        fail("federation spine manifest bounded_output_contract must match the current source-first guardrail")
