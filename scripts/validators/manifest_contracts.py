from __future__ import annotations

from .common import *
from .local_contracts import *
from .source_refs import *

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

def validate_tos_text_chunk_map_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    payload = read_json(TOS_TEXT_CHUNK_MAP_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("ToS text chunk map manifest must be a JSON object")

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
            fail(f"ToS text chunk map manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("ToS text chunk map manifest manifest_version must equal 1")
    if payload["pack_type"] != "tos_text_chunk_map":
        fail("ToS text chunk map manifest pack_type must equal 'tos_text_chunk_map'")
    if payload["source_repo"] != TOS_REPO:
        fail("ToS text chunk map manifest source_repo must equal 'Tree-of-Sophia'")
    if payload["source_root_env"] != "TREE_OF_SOPHIA_ROOT":
        fail("ToS text chunk map manifest source_root_env must equal 'TREE_OF_SOPHIA_ROOT'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS text chunk map manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"ToS text chunk map manifest source_inputs[{index}]"
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
        resolve_known_ref(repo_ref(TOS_REPO, path), label=location)
    if actual_source_inputs != EXPECTED_TOS_TEXT_CHUNK_MAP_INPUTS:
        fail("ToS text chunk map manifest source_inputs must match the current bounded donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS text chunk map manifest surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"ToS text chunk map manifest surface_bindings[{index}]"
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
            fail(
                f"{location} must point to Tree-of-Sophia-only experimental surfaces in this chunk-map pilot"
            )

    if actual_bindings != EXPECTED_TOS_TEXT_CHUNK_MAP_BINDINGS:
        fail("ToS text chunk map manifest surface_bindings must match the current bounded chunk-map contract")

    if payload["output_paths"] != EXPECTED_TOS_TEXT_CHUNK_MAP_OUTPUT_PATHS:
        fail("ToS text chunk map manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_TOS_TEXT_CHUNK_MAP_CONTRACT:
        fail("ToS text chunk map manifest bounded_output_contract must match the current source-first guardrail")

def validate_tos_retrieval_axis_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    payload = read_json(TOS_RETRIEVAL_AXIS_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("ToS retrieval axis manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_inputs",
        "surface_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS retrieval axis manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("ToS retrieval axis manifest manifest_version must equal 1")
    if payload["pack_type"] != "tos_retrieval_axis_pack":
        fail("ToS retrieval axis manifest pack_type must equal 'tos_retrieval_axis_pack'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS retrieval axis manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"ToS retrieval axis manifest source_inputs[{index}]"
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
    if actual_source_inputs != EXPECTED_TOS_RETRIEVAL_AXIS_INPUTS:
        fail("ToS retrieval axis manifest source_inputs must match the current bounded donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS retrieval axis manifest surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"ToS retrieval axis manifest surface_bindings[{index}]"
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
    if actual_bindings != EXPECTED_TOS_RETRIEVAL_AXIS_BINDINGS:
        fail("ToS retrieval axis manifest surface_bindings must match the current bounded retrieval contract")

    if payload["output_paths"] != EXPECTED_TOS_RETRIEVAL_AXIS_OUTPUT_PATHS:
        fail("ToS retrieval axis manifest output_paths must match the committed generated output paths")
    if payload["bounded_output_contract"] != EXPECTED_TOS_RETRIEVAL_AXIS_CONTRACT:
        fail("ToS retrieval axis manifest bounded_output_contract must match the current source-first guardrail")

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

def validate_tos_zarathustra_route_retrieval_pack_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    payload = read_json(TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("ToS Zarathustra route retrieval pack manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "source_inputs",
        "surface_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(
                "ToS Zarathustra route retrieval pack manifest is missing required "
                f"key '{key}'"
            )

    if payload["manifest_version"] != 1:
        fail("ToS Zarathustra route retrieval pack manifest manifest_version must equal 1")
    if payload["pack_type"] != "tos_zarathustra_route_retrieval_pack":
        fail(
            "ToS Zarathustra route retrieval pack manifest pack_type must equal "
            "'tos_zarathustra_route_retrieval_pack'"
        )

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail(
            "ToS Zarathustra route retrieval pack manifest source_inputs must be a "
            "non-empty list"
        )
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = (
            "ToS Zarathustra route retrieval pack manifest "
            f"source_inputs[{index}]"
        )
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(
            isinstance(value, str) and value for value in (name, repo, path, role)
        ):
            fail(f"{location} must keep name, repo, path, and role")
        if name in seen_input_names:
            fail(f"{location} duplicates source input '{name}'")
        seen_input_names.add(name)
        actual_source_inputs.add((name, repo, path, role))
        resolve_known_ref(repo_ref(repo, path), label=location)
        if repo == TOS_REPO and path.startswith("intake/"):
            fail(f"{location} must not point at Tree-of-Sophia/intake")
        if repo == "aoa-memo":
            fail(f"{location} must not point at aoa-memo")
        if repo == "aoa-routing":
            fail(f"{location} must not point at aoa-routing")
    if actual_source_inputs != EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_INPUTS:
        fail(
            "ToS Zarathustra route retrieval pack manifest source_inputs must match "
            "the current single-donor route-pack contract"
        )

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail(
            "ToS Zarathustra route retrieval pack manifest surface_bindings must be a "
            "non-empty list"
        )
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = (
            "ToS Zarathustra route retrieval pack manifest "
            f"surface_bindings[{index}]"
        )
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
            fail(
                f"{location} must stay Tree-of-Sophia-only in this standalone retrieval scope"
            )
    if actual_bindings != EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_BINDINGS:
        fail(
            "ToS Zarathustra route retrieval pack manifest surface_bindings must "
            "match the current bounded retrieval contract"
        )

    if payload["output_paths"] != EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_OUTPUT_PATHS:
        fail(
            "ToS Zarathustra route retrieval pack manifest output_paths must match "
            "the committed generated output paths"
        )
    if payload["adjunct_budget"] != EXPECTED_TOS_STANDALONE_ADJUNCT_BUDGET:
        fail(
            "ToS Zarathustra route retrieval pack manifest adjunct_budget must "
            "match the current standalone adjunct budget"
        )
    if (
        payload["subordinate_posture"]
        != EXPECTED_TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE
    ):
        fail(
            "ToS Zarathustra route retrieval pack manifest subordinate_posture "
            "must match the current source-first subordinate posture"
        )
    if (
        payload["bounded_output_contract"]
        != EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_CONTRACT
    ):
        fail(
            "ToS Zarathustra route retrieval pack manifest bounded_output_contract "
            "must match the current source-first guardrail"
        )

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

def validate_source_owned_export_dependency_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> dict[tuple[str, str], dict[str, object]]:
    payload = read_json(SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("source-owned export dependency manifest must be a JSON object")

    for key in ("manifest_version", "contract_type", "dependencies"):
        if key not in payload:
            fail(f"source-owned export dependency manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("source-owned export dependency manifest manifest_version must equal 1")
    if payload["contract_type"] != "source_owned_export_dependencies":
        fail(
            "source-owned export dependency manifest contract_type must equal "
            "'source_owned_export_dependencies'"
        )

    dependencies = payload["dependencies"]
    if not isinstance(dependencies, list) or not dependencies:
        fail("source-owned export dependency manifest dependencies must be a non-empty list")

    dependencies_by_source: dict[tuple[str, str], dict[str, object]] = {}
    seen_dependency_ids: set[str] = set()
    for index, dependency in enumerate(dependencies):
        location = f"source-owned export dependency manifest dependencies[{index}]"
        if not isinstance(dependency, dict):
            fail(f"{location} must be an object")

        dependency_id = dependency.get("dependency_id")
        repo = dependency.get("repo")
        path = dependency.get("path")
        expected_owner_repo = dependency.get("expected_owner_repo")
        expected_kind = dependency.get("expected_kind")
        expected_object_id = dependency.get("expected_object_id")
        required_fields = dependency.get("required_fields")
        entry_surface = dependency.get("entry_surface")
        consumed_by = dependency.get("consumed_by")
        if not all(
            isinstance(value, str) and value
            for value in (
                dependency_id,
                repo,
                path,
                expected_owner_repo,
                expected_kind,
                expected_object_id,
            )
        ):
            fail(
                f"{location} must keep dependency_id, repo, path, expected_owner_repo, "
                "expected_kind, and expected_object_id"
            )
        if dependency_id in seen_dependency_ids:
            fail(f"{location}.dependency_id '{dependency_id}' is duplicated")
        seen_dependency_ids.add(dependency_id)
        if repo != expected_owner_repo:
            fail(f"{location}.expected_owner_repo must equal {location}.repo")
        if not isinstance(required_fields, list) or not required_fields:
            fail(f"{location}.required_fields must be a non-empty list")
        normalized_required_fields: list[str] = []
        for field_index, field_name in enumerate(required_fields):
            if not isinstance(field_name, str) or not field_name:
                fail(f"{location}.required_fields[{field_index}] must be a non-empty string")
            normalized_required_fields.append(field_name)
        if len(set(normalized_required_fields)) != len(normalized_required_fields):
            fail(f"{location}.required_fields must not contain duplicates")
        if not isinstance(entry_surface, dict):
            fail(f"{location}.entry_surface must be an object")
        entry_surface_repo = entry_surface.get("repo")
        entry_surface_path = entry_surface.get("path")
        entry_match_key = entry_surface.get("match_key")
        entry_match_value = entry_surface.get("match_value")
        if not all(
            isinstance(value, str) and value
            for value in (
                entry_surface_repo,
                entry_surface_path,
                entry_match_key,
                entry_match_value,
            )
        ):
            fail(
                f"{location}.entry_surface must keep repo, path, match_key, and match_value"
            )
        if entry_surface_repo != expected_owner_repo:
            fail(f"{location}.entry_surface.repo must equal {location}.expected_owner_repo")
        if entry_match_value != expected_object_id:
            fail(
                f"{location}.entry_surface.match_value must equal "
                f"{location}.expected_object_id"
            )
        if not isinstance(consumed_by, list):
            fail(f"{location}.consumed_by must be a list")
        normalized_consumed_by: list[str] = []
        for consumer_index, consumer_surface_id in enumerate(consumed_by):
            if not isinstance(consumer_surface_id, str) or not consumer_surface_id:
                fail(f"{location}.consumed_by[{consumer_index}] must be a non-empty string")
            if consumer_surface_id not in surfaces_by_id:
                fail(
                    f"{location}.consumed_by[{consumer_index}] references unknown "
                    f"registry surface '{consumer_surface_id}'"
                )
            normalized_consumed_by.append(consumer_surface_id)
        if len(set(normalized_consumed_by)) != len(normalized_consumed_by):
            fail(f"{location}.consumed_by must not contain duplicates")

        source_key = (repo, path)
        if source_key in dependencies_by_source:
            fail(f"{location} duplicates repo/path target '{repo_ref(repo, path)}'")

        export_path = resolve_known_ref(repo_ref(repo, path), label=location)
        entry_surface_ref = repo_ref(entry_surface_repo, entry_surface_path)
        resolve_known_ref(entry_surface_ref, label=f"{location}.entry_surface")
        export_payload = read_json(export_path)
        if not isinstance(export_payload, dict):
            fail(f"{location} target export must be a JSON object")
        for field_name in normalized_required_fields:
            if field_name not in export_payload:
                fail(
                    f"{location} requires target export '{repo_ref(repo, path)}' to keep "
                    f"'{field_name}'"
                )
        if export_payload.get("owner_repo") != expected_owner_repo:
            fail(f"{location} target export owner_repo must equal '{expected_owner_repo}'")
        if export_payload.get("kind") != expected_kind:
            fail(f"{location} target export kind must equal '{expected_kind}'")
        if export_payload.get("object_id") != expected_object_id:
            fail(f"{location} target export object_id must equal '{expected_object_id}'")

        export_source_inputs = export_payload.get("source_inputs")
        if not isinstance(export_source_inputs, list) or not export_source_inputs:
            fail(f"{location} target export source_inputs must be a non-empty list")
        primary_count = 0
        for source_input_index, source_input in enumerate(export_source_inputs):
            source_location = f"{location} target export source_inputs[{source_input_index}]"
            if not isinstance(source_input, dict):
                fail(f"{source_location} must be an object")
            source_repo = source_input.get("repo")
            source_role = source_input.get("role")
            source_class = source_input.get("source_class")
            if not all(
                isinstance(value, str) and value
                for value in (source_repo, source_role, source_class)
            ):
                fail(f"{source_location} must keep repo, role, and source_class")
            if source_role == "primary":
                primary_count += 1
                if source_repo != expected_owner_repo:
                    fail(f"{source_location}.repo must equal '{expected_owner_repo}'")
            elif source_role != "supporting":
                fail(f"{source_location}.role must be 'primary' or 'supporting'")
        if primary_count != 1:
            fail(f"{location} target export must contain exactly one primary source input")

        export_entry_surface = export_payload.get("entry_surface")
        if not isinstance(export_entry_surface, dict):
            fail(f"{location} target export entry_surface must be an object")
        if export_entry_surface.get("repo") != entry_surface_repo:
            fail(f"{location} target export entry_surface.repo must equal '{entry_surface_repo}'")
        if not path_matches_current_or_alias(
            entry_surface_repo,
            entry_surface_path,
            export_entry_surface.get("path"),
        ):
            fail(f"{location} target export entry_surface.path must equal '{entry_surface_path}'")
        if export_entry_surface.get("match_key") != entry_match_key:
            fail(
                f"{location} target export entry_surface.match_key must equal "
                f"'{entry_match_key}'"
            )
        if export_entry_surface.get("match_value") != entry_match_value:
            fail(
                f"{location} target export entry_surface.match_value must equal "
                f"'{entry_match_value}'"
            )

        dependencies_by_source[source_key] = {
            "dependency_id": dependency_id,
            "repo": repo,
            "path": path,
            "expected_owner_repo": expected_owner_repo,
            "consumed_by": normalized_consumed_by,
        }

    return dependencies_by_source

def validate_federation_export_registry_manifest(
    source_owned_export_dependencies: dict[tuple[str, str], dict[str, object]],
) -> dict[tuple[str, str], dict[str, object]]:
    payload = read_json(FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("federation export registry manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "exports",
        "output_paths",
    ):
        if key not in payload:
            fail(f"federation export registry manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("federation export registry manifest manifest_version must equal 1")
    if payload["pack_type"] != "federation_export_registry":
        fail("federation export registry manifest pack_type must equal 'federation_export_registry'")

    exports = payload["exports"]
    if not isinstance(exports, list) or not exports:
        fail("federation export registry manifest exports must be a non-empty list")

    exports_by_source: dict[tuple[str, str], dict[str, object]] = {}
    seen_dependency_ids: set[str] = set()
    seen_routing_entry_ids: set[str] = set()
    for index, export in enumerate(exports):
        location = f"federation export registry manifest exports[{index}]"
        if not isinstance(export, dict):
            fail(f"{location} must be an object")
        if set(export) != {
            "dependency_id",
            "owner_repo",
            "export_repo",
            "export_path",
            "package_tier",
            "activation",
            "routing_binding",
            "adjunct_surfaces",
        }:
            fail(
                f"{location} must keep exactly dependency_id, owner_repo, export_repo, "
                "export_path, package_tier, activation, routing_binding, and adjunct_surfaces"
            )

        dependency_id = export.get("dependency_id")
        owner_repo = export.get("owner_repo")
        export_repo = export.get("export_repo")
        export_path = export.get("export_path")
        package_tier = export.get("package_tier")
        activation = export.get("activation")
        routing_binding = export.get("routing_binding")
        adjunct_surfaces = export.get("adjunct_surfaces")
        if not all(
            isinstance(value, str) and value
            for value in (
                dependency_id,
                owner_repo,
                export_repo,
                export_path,
                package_tier,
            )
        ):
            fail(
                f"{location} must keep dependency_id, owner_repo, export_repo, "
                "export_path, and package_tier"
            )
        if dependency_id in seen_dependency_ids:
            fail(f"{location}.dependency_id '{dependency_id}' is duplicated")
        seen_dependency_ids.add(dependency_id)
        resolve_known_ref(repo_ref(export_repo, export_path), label=location)

        dependency = source_owned_export_dependencies.get((export_repo, export_path))
        if dependency is None:
            fail(
                f"{location} must map to a declared source-owned export dependency"
            )
        if dependency["dependency_id"] != dependency_id:
            fail(
                f"{location}.dependency_id must match dependency '{dependency['dependency_id']}'"
            )
        if dependency["expected_owner_repo"] != owner_repo:
            fail(
                f"{location}.owner_repo must match dependency expected_owner_repo "
                f"'{dependency['expected_owner_repo']}'"
            )

        if not isinstance(activation, dict):
            fail(f"{location}.activation must be an object")
        if set(activation) != {
            "registry_visible",
            "spine_visible",
            "routing_visible",
        }:
            fail(
                f"{location}.activation must keep exactly registry_visible, "
                "spine_visible, and routing_visible"
            )
        registry_visible = activation.get("registry_visible")
        spine_visible = activation.get("spine_visible")
        routing_visible = activation.get("routing_visible")
        if not all(isinstance(value, bool) for value in (registry_visible, spine_visible, routing_visible)):
            fail(
                f"{location}.activation must keep boolean registry_visible, "
                "spine_visible, and routing_visible"
            )
        if spine_visible and not registry_visible:
            fail(f"{location}.activation.spine_visible requires registry_visible=true")
        if routing_visible and not spine_visible:
            fail(f"{location}.activation.routing_visible requires spine_visible=true")
        live_spine_consumed = "AOA-K-0009" in dependency["consumed_by"]
        if spine_visible != live_spine_consumed:
            fail(
                f"{location}.activation.spine_visible must stay aligned with "
                "AOA-K-0009 presence in consumed_by"
            )

        normalized_routing_binding: dict[str, str] | None
        if routing_visible:
            if not isinstance(routing_binding, dict):
                fail(f"{location}.routing_binding must be an object when routing_visible=true")
            binding_kind = routing_binding.get("kind")
            entry_id = routing_binding.get("entry_id")
            if not all(
                isinstance(value, str) and value for value in (binding_kind, entry_id)
            ):
                fail(
                    f"{location}.routing_binding must keep kind and entry_id"
                )
            if binding_kind != "kag_view":
                fail(f"{location}.routing_binding.kind must equal 'kag_view'")
            if entry_id in seen_routing_entry_ids:
                fail(f"{location}.routing_binding.entry_id '{entry_id}' is duplicated")
            seen_routing_entry_ids.add(entry_id)
            normalized_routing_binding = {
                "kind": binding_kind,
                "entry_id": entry_id,
            }
        else:
            if routing_binding is not None:
                fail(f"{location}.routing_binding must be null when routing_visible=false")
            normalized_routing_binding = None

        if not isinstance(adjunct_surfaces, list):
            fail(f"{location}.adjunct_surfaces must be a list")
        if adjunct_surfaces and not spine_visible:
            fail(f"{location}.adjunct_surfaces require spine_visible=true")
        normalized_adjunct_surfaces: list[dict[str, str]] = []
        seen_adjunct_refs: set[str] = set()
        for adjunct_index, adjunct in enumerate(adjunct_surfaces):
            adjunct_location = f"{location}.adjunct_surfaces[{adjunct_index}]"
            if not isinstance(adjunct, dict):
                fail(f"{adjunct_location} must be an object")
            if set(adjunct) != {
                "surface_id",
                "surface_ref",
                "match_key",
                "target_value",
            }:
                fail(
                    f"{adjunct_location} must keep exactly surface_id, surface_ref, "
                    "match_key, and target_value"
                )
            surface_id = adjunct.get("surface_id")
            surface_ref = adjunct.get("surface_ref")
            match_key = adjunct.get("match_key")
            target_value = adjunct.get("target_value")
            if not all(
                isinstance(value, str) and value
                for value in (surface_id, surface_ref, match_key, target_value)
            ):
                fail(
                    f"{adjunct_location} must keep surface_id, surface_ref, "
                    "match_key, and target_value"
                )
            if surface_ref in seen_adjunct_refs:
                fail(f"{adjunct_location}.surface_ref '{surface_ref}' is duplicated")
            seen_adjunct_refs.add(surface_ref)
            resolve_known_ref(repo_ref(KAG_REPO, surface_ref), label=adjunct_location)
            normalized_adjunct_surfaces.append(
                {
                    "surface_id": surface_id,
                    "surface_ref": surface_ref,
                    "match_key": match_key,
                    "target_value": target_value,
                }
            )

        source_key = (export_repo, export_path)
        if source_key in exports_by_source:
            fail(f"{location} duplicates export target '{repo_ref(export_repo, export_path)}'")
        exports_by_source[source_key] = {
            "dependency_id": dependency_id,
            "owner_repo": owner_repo,
            "activation": {
                "registry_visible": registry_visible,
                "spine_visible": spine_visible,
                "routing_visible": routing_visible,
            },
            "routing_binding": normalized_routing_binding,
            "adjunct_surfaces": normalized_adjunct_surfaces,
        }

    if payload["output_paths"] != EXPECTED_FEDERATION_EXPORT_REGISTRY_OUTPUT_PATHS:
        fail(
            "federation export registry manifest output_paths must match the committed "
            "generated output paths"
        )

    return exports_by_source

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

def validate_tiny_consumer_bundle_manifest(
    surfaces_by_id: dict[str, dict[str, object]]
) -> None:
    payload = read_json(TINY_CONSUMER_BUNDLE_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("tiny consumer bundle manifest must be a JSON object")

    for key in (
        "manifest_version",
        "bundle_type",
        "source_inputs",
        "bundle_order",
        "deferred_counterpart",
        "output_paths",
    ):
        if key not in payload:
            fail(f"tiny consumer bundle manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("tiny consumer bundle manifest manifest_version must equal 1")
    if payload["bundle_type"] != "tiny_consumer_bundle":
        fail("tiny consumer bundle manifest bundle_type must equal 'tiny_consumer_bundle'")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("tiny consumer bundle manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"tiny consumer bundle manifest source_inputs[{index}]"
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
    if actual_source_inputs != EXPECTED_TINY_CONSUMER_BUNDLE_INPUTS:
        fail("tiny consumer bundle manifest source_inputs must match the current bounded donor set")

    bundle_order = validate_unique_string_list(
        payload["bundle_order"],
        label="tiny consumer bundle manifest bundle_order",
    )
    if bundle_order != EXPECTED_TINY_CONSUMER_BUNDLE_ORDER:
        fail("tiny consumer bundle manifest bundle_order must keep the current stable bundle order")
    if set(bundle_order) != {name for name, _, _, _ in EXPECTED_TINY_CONSUMER_BUNDLE_INPUTS}:
        fail("tiny consumer bundle manifest bundle_order must reference each declared source input exactly once")

    deferred_counterpart = payload["deferred_counterpart"]
    if not isinstance(deferred_counterpart, dict):
        fail("tiny consumer bundle manifest deferred_counterpart must be an object")
    if deferred_counterpart != EXPECTED_TINY_CONSUMER_BUNDLE_DEFERRED_COUNTERPART:
        fail("tiny consumer bundle manifest deferred_counterpart must match the contract-only posture")

    surface_id = deferred_counterpart["surface_id"]
    if surface_id not in surfaces_by_id:
        fail("tiny consumer bundle manifest deferred_counterpart.surface_id must exist in the registry")
    if surfaces_by_id[surface_id].get("status") != "planned":
        fail("tiny consumer bundle manifest deferred_counterpart.surface_id must remain planned in the registry")
    resolve_known_ref(
        deferred_counterpart["federation_exposure_review_ref"],
        label="tiny consumer bundle manifest deferred_counterpart.federation_exposure_review_ref",
    )
    for index, ref in enumerate(deferred_counterpart["allowed_refs"]):
        resolve_known_ref(
            ref,
            label=f"tiny consumer bundle manifest deferred_counterpart.allowed_refs[{index}]",
        )
    for index, ref in enumerate(deferred_counterpart["forbidden_active_payload_refs"]):
        resolve_known_ref(
            ref,
            label=(
                "tiny consumer bundle manifest "
                f"deferred_counterpart.forbidden_active_payload_refs[{index}]"
            ),
        )

    if payload["output_paths"] != EXPECTED_TINY_CONSUMER_BUNDLE_OUTPUT_PATHS:
        fail("tiny consumer bundle manifest output_paths must match the committed generated output paths")

def validate_counterpart_federation_exposure_review_manifest() -> None:
    payload = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("counterpart federation exposure review manifest must be a JSON object")

    for key in (
        "manifest_version",
        "review_type",
        "source_inputs",
        "review_bindings",
        "output_paths",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(
                "counterpart federation exposure review manifest is missing required "
                f"key '{key}'"
            )

    if payload["manifest_version"] != 1:
        fail("counterpart federation exposure review manifest manifest_version must equal 1")
    if payload["review_type"] != "counterpart_federation_exposure_review":
        fail(
            "counterpart federation exposure review manifest review_type must equal "
            "'counterpart_federation_exposure_review'"
        )

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("counterpart federation exposure review manifest source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    source_input_order: list[str] = []
    seen_input_names: set[str] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"counterpart federation exposure review manifest source_inputs[{index}]"
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
    if actual_source_inputs != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_INPUTS:
        fail(
            "counterpart federation exposure review manifest source_inputs must match "
            "the current reviewed donor set"
        )
    if source_input_order != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER:
        fail(
            "counterpart federation exposure review manifest source_inputs must keep "
            "the current reviewed surface order"
        )

    review_bindings = payload["review_bindings"]
    if not isinstance(review_bindings, list) or not review_bindings:
        fail("counterpart federation exposure review manifest review_bindings must be a non-empty list")
    actual_review_order: list[str] = []
    seen_review_names: set[str] = set()
    for index, binding in enumerate(review_bindings):
        location = f"counterpart federation exposure review manifest review_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
        surface_name = binding.get("surface_name")
        surface_input = binding.get("surface_input")
        exposure_posture = binding.get("exposure_posture")
        review_note = binding.get("review_note")
        if not all(
            isinstance(value, str) and value
            for value in (surface_name, surface_input, exposure_posture, review_note)
        ):
            fail(
                f"{location} must keep surface_name, surface_input, exposure_posture, "
                "and review_note"
            )
        if surface_name in seen_review_names:
            fail(f"{location} duplicates review binding '{surface_name}'")
        seen_review_names.add(surface_name)
        actual_review_order.append(surface_name)
        if surface_name != surface_input:
            fail(f"{location}.surface_name must match surface_input in the current review scope")
        if exposure_posture != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_POSTURES.get(surface_name):
            fail(
                f"{location}.exposure_posture must match the current reviewed posture "
                f"for '{surface_name}'"
            )

        allowed_counterpart_refs = binding.get("allowed_counterpart_refs")
        forbidden_refs = binding.get("forbidden_refs")
        if surface_name in {"reasoning_handoff_pack", "tiny_consumer_bundle"}:
            if allowed_counterpart_refs != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.allowed_counterpart_refs must match the current "
                    "contract-only counterpart refs"
                )
            for ref_index, ref in enumerate(allowed_counterpart_refs):
                resolve_known_ref(
                    ref,
                    label=f"{location}.allowed_counterpart_refs[{ref_index}]",
                )
            if forbidden_refs is not None:
                fail(f"{location}.forbidden_refs must stay absent when counterpart refs are allowed")
        elif surface_name in {"federation_spine", "cross_source_node_projection"}:
            if forbidden_refs != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.forbidden_refs must match the current forbidden "
                    "counterpart exposure set"
                )
            for ref_index, ref in enumerate(forbidden_refs):
                resolve_known_ref(
                    ref,
                    label=f"{location}.forbidden_refs[{ref_index}]",
                )
            if allowed_counterpart_refs is not None:
                fail(
                    f"{location}.allowed_counterpart_refs must stay absent for "
                    "non-exposing surfaces"
                )
        else:
            if allowed_counterpart_refs is not None or forbidden_refs is not None:
                fail(
                    f"{location} must not declare allowed_counterpart_refs or "
                    "forbidden_refs for contract/example review surfaces"
                )

    if actual_review_order != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER:
        fail(
            "counterpart federation exposure review manifest review_bindings must keep "
            "the current reviewed surface order"
        )
    if payload["output_paths"] != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATHS:
        fail(
            "counterpart federation exposure review manifest output_paths must match "
            "the committed generated output paths"
        )
    if payload["bounded_output_contract"] != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_CONTRACT:
        fail(
            "counterpart federation exposure review manifest bounded_output_contract "
            "must match the current review guardrail"
        )
