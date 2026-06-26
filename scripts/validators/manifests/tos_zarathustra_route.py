from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_tos_zarathustra_route_pack_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    payload = read_json(TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("ToS Zarathustra route pack manifest must be a JSON object")

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
            fail(f"ToS Zarathustra route pack manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("ToS Zarathustra route pack manifest manifest_version must equal 1")
    if payload["pack_type"] != "tos_zarathustra_route_pack":
        fail(
            "ToS Zarathustra route pack manifest pack_type must equal "
            "'tos_zarathustra_route_pack'"
        )
    if payload["source_repo"] != TOS_REPO:
        fail("ToS Zarathustra route pack manifest source_repo must equal 'Tree-of-Sophia'")
    if payload["source_root_env"] != "TREE_OF_SOPHIA_ROOT":
        fail(
            "ToS Zarathustra route pack manifest source_root_env must equal "
            "'TREE_OF_SOPHIA_ROOT'"
        )

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS Zarathustra route pack manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"ToS Zarathustra route pack manifest source_inputs[{index}]"
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
        actual_source_inputs.add((name, TOS_REPO, path, role))
        resolve_known_ref(repo_ref(TOS_REPO, path), label=location)
        if path.startswith("intake/"):
            fail(f"{location} must not point at Tree-of-Sophia/intake")
        if path.startswith("examples/"):
            fail(f"{location} must not point at Tree-of-Sophia/examples")
        if path.startswith("generated/kag_export"):
            fail(f"{location} must not point at Tree-of-Sophia/ToS/derived-exports/kag_export")
    if actual_source_inputs != EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_INPUTS:
        fail(
            "ToS Zarathustra route pack manifest source_inputs must match the current "
            "canonical donor set"
        )

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS Zarathustra route pack manifest surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"ToS Zarathustra route pack manifest surface_bindings[{index}]"
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
        if surface.get("status") != "experimental":
            fail(f"{location} must only bind experimental registry surfaces")
        if surface.get("source_repos") != [TOS_REPO]:
            fail(f"{location} must stay Tree-of-Sophia-only in this additive route scope")
    if actual_bindings != EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_BINDINGS:
        fail(
            "ToS Zarathustra route pack manifest surface_bindings must match the "
            "current bounded route-pack contract"
        )

    if payload["output_paths"] != EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATHS:
        fail(
            "ToS Zarathustra route pack manifest output_paths must match the "
            "committed generated output paths"
        )
    if payload["bounded_output_contract"] != EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_CONTRACT:
        fail(
            "ToS Zarathustra route pack manifest bounded_output_contract must match "
            "the current source-first guardrail"
        )
