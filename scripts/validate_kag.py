#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "generated" / "kag_registry.min.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "kag-registry.schema.json"
BRIDGE_SCHEMA_PATH = REPO_ROOT / "schemas" / "bridge-retrieval-surface.schema.json"
BRIDGE_EXAMPLE_PATH = REPO_ROOT / "examples" / "tos_retrieval_axis_surface.example.json"
COUNTERPART_SCHEMA_PATH = REPO_ROOT / "schemas" / "counterpart-edge-surface.schema.json"
COUNTERPART_EXAMPLE_PATH = REPO_ROOT / "examples" / "counterpart_edge_view.example.json"

ALLOWED_STATUS = {"active", "planned", "experimental", "deprecated"}
ALLOWED_SOURCE_CLASS = {"technique_bundle", "skill_bundle", "eval_bundle", "playbook_bundle", "memo_object", "tos_text", "review_surface"}
ALLOWED_DERIVED_KIND = {"section_manifest", "metadata_spine", "relation_view", "provenance_view", "chunk_map", "node_projection", "edge_projection", "retrieval_surface"}
ALLOWED_PROVENANCE = {"strict_source_linked", "bounded_source_linked", "derived_with_handles"}
ALLOWED_FRAMEWORK = {"neutral", "hipporag_ready", "llamaindex_ready", "multi_consumer_ready"}
ALLOWED_SOURCE_INPUT_ROLE = {"primary", "supporting"}
ALLOWED_COUNTERPART_MODE = {"analogy", "support", "tension", "calibration"}


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(REPO_ROOT).as_posix()}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(REPO_ROOT).as_posix()}: {exc}")


def validate_schema_surface() -> None:
    schema = read_json(SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("schema file must contain a JSON object")
    required_top_level = {"$schema", "$id", "title", "type", "properties", "required"}
    missing = sorted(required_top_level - set(schema))
    if missing:
        fail(f"schema is missing required top-level keys: {', '.join(missing)}")


def validate_bridge_schema_surface() -> None:
    schema = read_json(BRIDGE_SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("bridge schema file must contain a JSON object")
    required_top_level = {"$schema", "$id", "title", "type", "properties", "required"}
    missing = sorted(required_top_level - set(schema))
    if missing:
        fail(f"bridge schema is missing required top-level keys: {', '.join(missing)}")


def validate_counterpart_schema_surface() -> None:
    schema = read_json(COUNTERPART_SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("counterpart schema file must contain a JSON object")
    required_top_level = {"$schema", "$id", "title", "type", "properties", "required"}
    missing = sorted(required_top_level - set(schema))
    if missing:
        fail(f"counterpart schema is missing required top-level keys: {', '.join(missing)}")


def validate_registry() -> dict[str, dict[str, object]]:
    payload = read_json(REGISTRY_PATH)
    if not isinstance(payload, dict):
        fail("KAG registry must be a JSON object")

    for key in ("version", "layer", "surfaces"):
        if key not in payload:
            fail(f"KAG registry is missing required key '{key}'")

    if not isinstance(payload["version"], int) or payload["version"] < 1:
        fail("registry 'version' must be an integer >= 1")
    if payload["layer"] != "aoa-kag":
        fail("registry 'layer' must equal 'aoa-kag'")

    surfaces = payload["surfaces"]
    if not isinstance(surfaces, list) or not surfaces:
        fail("registry 'surfaces' must be a non-empty list")

    seen_ids: set[str] = set()
    required_seed = {
        "technique-section-lift",
        "metadata-spine-projection",
        "bounded-relation-view",
        "provenance-note-view",
        "tos-text-chunk-map",
        "cross-source-node-projection",
        "tos-retrieval-axis-surface",
        "counterpart-edge-view",
    }
    seen_names: set[str] = set()
    surfaces_by_id: dict[str, dict[str, object]] = {}

    for index, surface in enumerate(surfaces):
        location = f"surfaces[{index}]"
        if not isinstance(surface, dict):
            fail(f"{location} must be an object")

        for key in (
            "id",
            "name",
            "status",
            "summary",
            "source_class",
            "derived_kind",
            "provenance_mode",
            "normalization_scope",
            "framework_readiness",
            "source_repos",
        ):
            if key not in surface:
                fail(f"{location} is missing required key '{key}'")

        surface_id = surface["id"]
        name = surface["name"]
        status = surface["status"]
        summary = surface["summary"]
        source_class = surface["source_class"]
        derived_kind = surface["derived_kind"]
        provenance_mode = surface["provenance_mode"]
        normalization_scope = surface["normalization_scope"]
        framework_readiness = surface["framework_readiness"]
        source_repos = surface["source_repos"]
        source_inputs = surface.get("source_inputs")

        if not isinstance(surface_id, str) or len(surface_id) < 3:
            fail(f"{location}.id must be a string of length >= 3")
        if surface_id in seen_ids:
            fail(f"duplicate KAG surface id in registry: '{surface_id}'")
        seen_ids.add(surface_id)
        surfaces_by_id[surface_id] = surface

        if not isinstance(name, str) or len(name) < 3:
            fail(f"{location}.name must be a string of length >= 3")
        if name in seen_names:
            fail(f"duplicate KAG surface name in registry: '{name}'")
        seen_names.add(name)
        if status not in ALLOWED_STATUS:
            fail(f"{location}.status '{status}' is not allowed")
        if not isinstance(summary, str) or len(summary) < 10:
            fail(f"{location}.summary must be a string of length >= 10")
        if source_class not in ALLOWED_SOURCE_CLASS:
            fail(f"{location}.source_class '{source_class}' is not allowed")
        if derived_kind not in ALLOWED_DERIVED_KIND:
            fail(f"{location}.derived_kind '{derived_kind}' is not allowed")
        if provenance_mode not in ALLOWED_PROVENANCE:
            fail(f"{location}.provenance_mode '{provenance_mode}' is not allowed")
        if not isinstance(normalization_scope, str) or len(normalization_scope) < 3:
            fail(f"{location}.normalization_scope must be a string of length >= 3")
        if framework_readiness not in ALLOWED_FRAMEWORK:
            fail(f"{location}.framework_readiness '{framework_readiness}' is not allowed")
        if not isinstance(source_repos, list) or not source_repos:
            fail(f"{location}.source_repos must be a non-empty list")
        for repo in source_repos:
            if not isinstance(repo, str) or len(repo) < 2:
                fail(f"{location}.source_repos contains an invalid entry")

        if source_inputs is not None:
            if not isinstance(source_inputs, list) or not source_inputs:
                fail(f"{location}.source_inputs must be a non-empty list when present")

            primary_count = 0
            input_repos: set[str] = set()
            for input_index, source_input in enumerate(source_inputs):
                input_location = f"{location}.source_inputs[{input_index}]"
                if not isinstance(source_input, dict):
                    fail(f"{input_location} must be an object")
                for key in ("repo", "source_class", "role"):
                    if key not in source_input:
                        fail(f"{input_location} is missing required key '{key}'")

                input_repo = source_input["repo"]
                input_source_class = source_input["source_class"]
                input_role = source_input["role"]

                if not isinstance(input_repo, str) or len(input_repo) < 2:
                    fail(f"{input_location}.repo must be a string of length >= 2")
                if input_repo not in source_repos:
                    fail(f"{input_location}.repo '{input_repo}' must also appear in source_repos")
                if input_repo in input_repos:
                    fail(f"{input_location}.repo '{input_repo}' is duplicated")
                input_repos.add(input_repo)

                if input_source_class not in ALLOWED_SOURCE_CLASS:
                    fail(f"{input_location}.source_class '{input_source_class}' is not allowed")
                if input_role not in ALLOWED_SOURCE_INPUT_ROLE:
                    fail(f"{input_location}.role '{input_role}' is not allowed")
                if input_role == "primary":
                    primary_count += 1
                    if input_source_class != source_class:
                        fail(f"{input_location}.source_class must match top-level source_class for the primary input")

            if primary_count != 1:
                fail(f"{location}.source_inputs must contain exactly one primary input")

        if len(source_repos) > 1 and source_inputs is None:
            fail(f"{location}.source_inputs is required when more than one source repo is declared")

    missing_seed = sorted(required_seed - seen_names)
    if missing_seed:
        fail(f"KAG registry is missing required seed surfaces: {', '.join(missing_seed)}")
    validate_special_registry_surfaces(surfaces_by_id)
    return surfaces_by_id


def validate_special_registry_surfaces(surfaces_by_id: dict[str, dict[str, object]]) -> None:
    surface_0007 = surfaces_by_id.get("AOA-K-0007")
    if surface_0007 is None:
        fail("KAG registry is missing required surface 'AOA-K-0007'")
    if surface_0007.get("name") != "tos-retrieval-axis-surface":
        fail("AOA-K-0007 must keep name 'tos-retrieval-axis-surface'")
    if surface_0007.get("status") != "planned":
        fail("AOA-K-0007 must remain planned")

    surface_0008 = surfaces_by_id.get("AOA-K-0008")
    if surface_0008 is None:
        fail("KAG registry is missing required surface 'AOA-K-0008'")
    if surface_0008.get("name") != "counterpart-edge-view":
        fail("AOA-K-0008 must keep name 'counterpart-edge-view'")
    if surface_0008.get("status") != "planned":
        fail("AOA-K-0008 must remain planned")
    if surface_0008.get("source_class") != "tos_text":
        fail("AOA-K-0008 must keep 'tos_text' as its primary source_class")
    if surface_0008.get("derived_kind") != "edge_projection":
        fail("AOA-K-0008 must keep 'edge_projection' as its derived_kind")

    source_inputs = surface_0008.get("source_inputs")
    if not isinstance(source_inputs, list):
        fail("AOA-K-0008 must declare source_inputs")
    expected_inputs = {
        ("Tree-of-Sophia", "tos_text", "primary"),
        ("aoa-techniques", "technique_bundle", "supporting"),
        ("aoa-playbooks", "playbook_bundle", "supporting"),
        ("aoa-evals", "eval_bundle", "supporting"),
    }
    actual_inputs = {
        (item.get("repo"), item.get("source_class"), item.get("role"))
        for item in source_inputs
        if isinstance(item, dict)
    }
    if actual_inputs != expected_inputs:
        fail("AOA-K-0008 source_inputs must match the current counterpart bridge source contract")


def validate_bridge_example(surfaces_by_id: dict[str, dict[str, object]]) -> None:
    payload = read_json(BRIDGE_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("bridge example must be a JSON object")

    surface_id = payload.get("surface_id")
    if surface_id != "AOA-K-0007":
        fail("bridge example surface_id must equal 'AOA-K-0007'")
    if surface_id not in surfaces_by_id:
        fail("bridge example surface_id must exist in generated/kag_registry.min.json")

    registry_entry = surfaces_by_id[surface_id]
    if registry_entry["derived_kind"] != "retrieval_surface":
        fail("AOA-K-0007 must remain a retrieval_surface")
    if registry_entry["source_class"] != "tos_text":
        fail("AOA-K-0007 must keep 'tos_text' as its primary source_class")

    for key in ("source_refs", "lineage_refs"):
        value = payload.get(key)
        if not isinstance(value, list) or not value:
            fail(f"bridge example '{key}' must be a non-empty list")
        if len(value) != len(set(value)):
            fail(f"bridge example '{key}' must not contain duplicates")
        for item in value:
            if not isinstance(item, str) or len(item) < 1:
                fail(f"bridge example '{key}' contains an invalid entry")

    for key in ("conflict_refs", "practice_refs"):
        value = payload.get(key)
        if value is None:
            continue
        if not isinstance(value, list):
            fail(f"bridge example '{key}' must be a list when present")
        if len(value) != len(set(value)):
            fail(f"bridge example '{key}' must not contain duplicates")
        for item in value:
            if not isinstance(item, str) or len(item) < 1:
                fail(f"bridge example '{key}' contains an invalid entry")

    axis_summary = payload.get("axis_summary")
    if not isinstance(axis_summary, str) or len(axis_summary) < 20:
        fail("bridge example 'axis_summary' must be a string of length >= 20")


def validate_counterpart_example(surfaces_by_id: dict[str, dict[str, object]]) -> None:
    payload = read_json(COUNTERPART_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("counterpart example must be a JSON object")

    surface_id = payload.get("surface_id")
    if surface_id != "AOA-K-0008":
        fail("counterpart example surface_id must equal 'AOA-K-0008'")
    if surface_id not in surfaces_by_id:
        fail("counterpart example surface_id must exist in generated/kag_registry.min.json")

    registry_entry = surfaces_by_id[surface_id]
    if registry_entry["derived_kind"] != "edge_projection":
        fail("AOA-K-0008 must remain an edge_projection")
    if registry_entry["status"] != "planned":
        fail("AOA-K-0008 must remain planned in the registry")
    if registry_entry["source_class"] != "tos_text":
        fail("AOA-K-0008 must keep 'tos_text' as its primary source_class")

    mappings = payload.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        fail("counterpart example 'mappings' must be a non-empty list")

    seen_mapping_ids: set[str] = set()
    seen_modes: set[str] = set()
    source_inputs = registry_entry.get("source_inputs")
    supporting_repos = {
        item["repo"]
        for item in source_inputs
        if isinstance(item, dict) and item.get("role") == "supporting"
    }

    for index, mapping in enumerate(mappings):
        location = f"counterpart example mappings[{index}]"
        if not isinstance(mapping, dict):
            fail(f"{location} must be an object")
        for key in (
            "mapping_id",
            "concept_ref",
            "operational_ref",
            "counterpart_mode",
            "evidence_note",
            "non_identity_note",
        ):
            if key not in mapping:
                fail(f"{location} is missing required key '{key}'")

        mapping_id = mapping["mapping_id"]
        concept_ref = mapping["concept_ref"]
        operational_ref = mapping["operational_ref"]
        counterpart_mode = mapping["counterpart_mode"]
        evidence_note = mapping["evidence_note"]
        non_identity_note = mapping["non_identity_note"]
        supporting_refs = mapping.get("supporting_refs")

        if not isinstance(mapping_id, str) or len(mapping_id) < 1:
            fail(f"{location}.mapping_id must be a non-empty string")
        if mapping_id in seen_mapping_ids:
            fail(f"{location}.mapping_id '{mapping_id}' is duplicated")
        seen_mapping_ids.add(mapping_id)

        if not isinstance(concept_ref, str) or not concept_ref.startswith("Tree-of-Sophia/"):
            fail(f"{location}.concept_ref must point to a Tree-of-Sophia surface")
        if not isinstance(operational_ref, str) or "/" not in operational_ref:
            fail(f"{location}.operational_ref must be a non-empty repo-qualified string")
        operational_repo = operational_ref.split("/", 1)[0]
        if operational_repo not in supporting_repos:
            fail(f"{location}.operational_ref repo '{operational_repo}' must match a supporting source repo")

        if counterpart_mode not in ALLOWED_COUNTERPART_MODE:
            fail(f"{location}.counterpart_mode '{counterpart_mode}' is not allowed")
        seen_modes.add(counterpart_mode)

        if not isinstance(evidence_note, str) or len(evidence_note) < 20:
            fail(f"{location}.evidence_note must be a string of length >= 20")
        if not isinstance(non_identity_note, str) or len(non_identity_note) < 20:
            fail(f"{location}.non_identity_note must be a string of length >= 20")

        if supporting_refs is not None:
            if not isinstance(supporting_refs, list):
                fail(f"{location}.supporting_refs must be a list when present")
            if len(supporting_refs) != len(set(supporting_refs)):
                fail(f"{location}.supporting_refs must not contain duplicates")
            for supporting_ref in supporting_refs:
                if not isinstance(supporting_ref, str) or "/" not in supporting_ref:
                    fail(f"{location}.supporting_refs contains an invalid repo-qualified ref")
                supporting_repo = supporting_ref.split("/", 1)[0]
                if supporting_repo not in supporting_repos:
                    fail(f"{location}.supporting_refs repo '{supporting_repo}' must match a supporting source repo")

    if seen_modes != ALLOWED_COUNTERPART_MODE:
        fail("counterpart example must cover all supported counterpart modes at least once")


def main() -> int:
    try:
        validate_schema_surface()
        validate_bridge_schema_surface()
        validate_counterpart_schema_surface()
        surfaces_by_id = validate_registry()
        validate_bridge_example(surfaces_by_id)
        validate_counterpart_example(surfaces_by_id)
    except ValidationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print("[ok] validated KAG registry schema surface")
    print("[ok] validated bridge retrieval surface schema")
    print("[ok] validated counterpart edge surface schema")
    print("[ok] validated generated/kag_registry.min.json")
    print("[ok] validated bridge retrieval example")
    print("[ok] validated counterpart edge example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
