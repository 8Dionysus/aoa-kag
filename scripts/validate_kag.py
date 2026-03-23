#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def repo_root_from_env(env_name: str, default: Path) -> Path:
    override = os.environ.get(env_name)
    if not override:
        return default
    return Path(override).expanduser().resolve()


TREE_OF_SOPHIA_ROOT = repo_root_from_env(
    "TREE_OF_SOPHIA_ROOT", REPO_ROOT.parent / "Tree-of-Sophia"
)
AOA_MEMO_ROOT = repo_root_from_env("AOA_MEMO_ROOT", REPO_ROOT.parent / "aoa-memo")

REGISTRY_PATH = REPO_ROOT / "generated" / "kag_registry.min.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "kag-registry.schema.json"
BRIDGE_SCHEMA_PATH = REPO_ROOT / "schemas" / "bridge-retrieval-surface.schema.json"
BRIDGE_EXAMPLE_PATH = REPO_ROOT / "examples" / "tos_retrieval_axis_surface.example.json"
COUNTERPART_SCHEMA_PATH = REPO_ROOT / "schemas" / "counterpart-edge-surface.schema.json"
COUNTERPART_EXAMPLE_PATH = REPO_ROOT / "examples" / "counterpart_edge_view.example.json"
REASONING_HANDOFF_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "reasoning-handoff-guardrail.schema.json"
)
REASONING_HANDOFF_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "reasoning_handoff_guardrail.example.json"
)

ALLOWED_STATUS = {"active", "planned", "experimental", "deprecated"}
ALLOWED_SOURCE_CLASS = {
    "technique_bundle",
    "skill_bundle",
    "eval_bundle",
    "playbook_bundle",
    "memo_object",
    "tos_text",
    "review_surface",
}
ALLOWED_DERIVED_KIND = {
    "section_manifest",
    "metadata_spine",
    "relation_view",
    "provenance_view",
    "chunk_map",
    "node_projection",
    "edge_projection",
    "retrieval_surface",
}
ALLOWED_PROVENANCE = {
    "strict_source_linked",
    "bounded_source_linked",
    "derived_with_handles",
}
ALLOWED_FRAMEWORK = {
    "neutral",
    "hipporag_ready",
    "llamaindex_ready",
    "multi_consumer_ready",
}
ALLOWED_SOURCE_INPUT_ROLE = {"primary", "supporting"}
ALLOWED_COUNTERPART_MODE = {"analogy", "support", "tension", "calibration"}
ALLOWED_QUERY_MODES = {"local_search", "global_search", "drift_search"}
EXPECTED_AUTHORITATIVE_SOURCE_REFS = {
    "Tree-of-Sophia/docs/NODE_CONTRACT.md",
    "Tree-of-Sophia/docs/PRACTICE_BRANCH.md",
    "aoa-memo/docs/WITNESS_TRACE_CONTRACT.md",
}
EXPECTED_DERIVED_SURFACE_REFS = {
    "docs/BRIDGE_CONTRACTS.md#retrieval-axis-contract",
    "examples/tos_retrieval_axis_surface.example.json",
    "docs/COUNTERPART_EDGE_CONTRACTS.md",
    "examples/counterpart_edge_view.example.json",
}
EXPECTED_PROVENANCE_POSTURE = {
    "primary_source_required": True,
    "supporting_sources_allowed": True,
    "source_trace_required": True,
    "derived_summary_posture": "guide_to_source_not_source_replacement",
}
EXPECTED_BOUNDARY_GUARDRAILS = {
    "routing_owner": "aoa-routing",
    "memory_owner": "aoa-memo",
    "canon_owner": "Tree-of-Sophia",
    "direct_canon_authorship": "forbidden",
}
EXPECTED_RETURN_MUST_INCLUDE = {"source_refs", "axis_summary", "provenance_note"}
EXPECTED_RETURN_MAY_INCLUDE = {
    "lineage_refs",
    "conflict_refs",
    "practice_refs",
    "counterpart_refs",
}
MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
VISIBLE_ROOTS = (REPO_ROOT, TREE_OF_SOPHIA_ROOT, AOA_MEMO_ROOT)


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def display_path(path: Path) -> str:
    for root in VISIBLE_ROOTS:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    return path.as_posix()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {display_path(path)}: {exc}")


def markdown_anchor(text: str) -> str:
    anchor = text.strip().lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    anchor = re.sub(r"-+", "-", anchor)
    return anchor.strip("-")


@lru_cache(maxsize=None)
def markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = MARKDOWN_HEADING.match(line)
        if not match:
            continue
        base = markdown_anchor(match.group(2))
        if not base:
            continue
        suffix = seen.get(base, 0)
        seen[base] = suffix + 1
        anchors.add(base if suffix == 0 else f"{base}-{suffix}")
    return anchors


def validate_top_level_schema(path: Path, label: str) -> None:
    schema = read_json(path)
    if not isinstance(schema, dict):
        fail(f"{label} schema file must contain a JSON object")
    required_top_level = {"$schema", "$id", "title", "type", "properties", "required"}
    missing = sorted(required_top_level - set(schema))
    if missing:
        fail(f"{label} schema is missing required top-level keys: {', '.join(missing)}")


def validate_schema_surface() -> None:
    validate_top_level_schema(SCHEMA_PATH, "registry")


def validate_bridge_schema_surface() -> None:
    validate_top_level_schema(BRIDGE_SCHEMA_PATH, "bridge")


def validate_counterpart_schema_surface() -> None:
    validate_top_level_schema(COUNTERPART_SCHEMA_PATH, "counterpart")


def validate_reasoning_handoff_schema_surface() -> None:
    validate_top_level_schema(REASONING_HANDOFF_SCHEMA_PATH, "reasoning handoff")


def validate_unique_string_list(
    value: object,
    *,
    label: str,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    if not value and not allow_empty:
        fail(f"{label} must be a non-empty list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or len(item) < 1:
            fail(f"{label} contains an invalid entry")
        result.append(item)
    if len(result) != len(set(result)):
        fail(f"{label} must not contain duplicates")
    return result


def resolve_relative_ref(root: Path, raw_ref: str, *, label: str) -> Path:
    path_text, _, anchor = raw_ref.partition("#")
    target = root / path_text
    if not target.exists():
        fail(f"{label} references a missing path: {raw_ref}")
    if anchor:
        if target.suffix.lower() != ".md":
            fail(f"{label} uses a markdown anchor on a non-markdown target: {raw_ref}")
        if anchor not in markdown_anchors(target):
            fail(f"{label} references a missing markdown anchor: {raw_ref}")
    return target


def resolve_authoritative_ref(raw_ref: str, *, label: str) -> Path:
    if raw_ref.startswith("Tree-of-Sophia/"):
        return resolve_relative_ref(
            TREE_OF_SOPHIA_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    if raw_ref.startswith("aoa-memo/"):
        return resolve_relative_ref(
            AOA_MEMO_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    fail(f"{label} must reference Tree-of-Sophia or aoa-memo: {raw_ref}")


def validate_exact_set(
    values: list[str],
    expected: set[str],
    *,
    label: str,
) -> None:
    if set(values) != expected:
        fail(f"{label} must match the exact expected set")


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
                        fail(
                            f"{input_location}.source_class must match top-level source_class for the primary input"
                        )

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
        validate_unique_string_list(value, label=f"bridge example '{key}'")

    for key in ("conflict_refs", "practice_refs"):
        value = payload.get(key)
        if value is None:
            continue
        validate_unique_string_list(value, label=f"bridge example '{key}'")

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
            refs = validate_unique_string_list(
                supporting_refs,
                label=f"{location}.supporting_refs",
            )
            for supporting_ref in refs:
                if "/" not in supporting_ref:
                    fail(f"{location}.supporting_refs contains an invalid repo-qualified ref")
                supporting_repo = supporting_ref.split("/", 1)[0]
                if supporting_repo not in supporting_repos:
                    fail(f"{location}.supporting_refs repo '{supporting_repo}' must match a supporting source repo")

    if seen_modes != ALLOWED_COUNTERPART_MODE:
        fail("counterpart example must cover all supported counterpart modes at least once")


def validate_reasoning_handoff_example() -> None:
    payload = read_json(REASONING_HANDOFF_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("reasoning handoff example must be a JSON object")

    for key in (
        "surface_type",
        "handoff_id",
        "supported_query_modes",
        "authoritative_source_refs",
        "derived_surface_refs",
        "provenance_posture",
        "return_contract",
        "boundary_guardrails",
    ):
        if key not in payload:
            fail(f"reasoning handoff example is missing required key '{key}'")

    if payload["surface_type"] != "reasoning_handoff_guardrail":
        fail("reasoning handoff example surface_type must equal 'reasoning_handoff_guardrail'")

    handoff_id = payload["handoff_id"]
    if not isinstance(handoff_id, str) or len(handoff_id) < 3:
        fail("reasoning handoff example handoff_id must be a string of length >= 3")

    query_modes = validate_unique_string_list(
        payload["supported_query_modes"],
        label="reasoning handoff example supported_query_modes",
    )
    validate_exact_set(
        query_modes,
        ALLOWED_QUERY_MODES,
        label="reasoning handoff example supported_query_modes",
    )

    authoritative_source_refs = validate_unique_string_list(
        payload["authoritative_source_refs"],
        label="reasoning handoff example authoritative_source_refs",
    )
    validate_exact_set(
        authoritative_source_refs,
        EXPECTED_AUTHORITATIVE_SOURCE_REFS,
        label="reasoning handoff example authoritative_source_refs",
    )
    for ref in authoritative_source_refs:
        resolve_authoritative_ref(ref, label="reasoning handoff example authoritative_source_refs")

    derived_surface_refs = validate_unique_string_list(
        payload["derived_surface_refs"],
        label="reasoning handoff example derived_surface_refs",
    )
    validate_exact_set(
        derived_surface_refs,
        EXPECTED_DERIVED_SURFACE_REFS,
        label="reasoning handoff example derived_surface_refs",
    )
    for ref in derived_surface_refs:
        resolve_relative_ref(
            REPO_ROOT,
            ref,
            label="reasoning handoff example derived_surface_refs",
        )

    provenance_posture = payload["provenance_posture"]
    if provenance_posture != EXPECTED_PROVENANCE_POSTURE:
        fail("reasoning handoff example provenance_posture must match the bounded guardrail contract")

    return_contract = payload["return_contract"]
    if not isinstance(return_contract, dict):
        fail("reasoning handoff example return_contract must be an object")

    for key in ("must_include", "may_include"):
        if key not in return_contract:
            fail(f"reasoning handoff example return_contract is missing '{key}'")

    must_include = validate_unique_string_list(
        return_contract["must_include"],
        label="reasoning handoff example return_contract.must_include",
    )
    validate_exact_set(
        must_include,
        EXPECTED_RETURN_MUST_INCLUDE,
        label="reasoning handoff example return_contract.must_include",
    )

    may_include = validate_unique_string_list(
        return_contract["may_include"],
        label="reasoning handoff example return_contract.may_include",
    )
    validate_exact_set(
        may_include,
        EXPECTED_RETURN_MAY_INCLUDE,
        label="reasoning handoff example return_contract.may_include",
    )

    if set(must_include) & set(may_include):
        fail("reasoning handoff example return_contract must not overlap must_include and may_include")

    boundary_guardrails = payload["boundary_guardrails"]
    if boundary_guardrails != EXPECTED_BOUNDARY_GUARDRAILS:
        fail("reasoning handoff example boundary_guardrails must match the bounded guardrail contract")


def main() -> int:
    try:
        validate_schema_surface()
        validate_bridge_schema_surface()
        validate_counterpart_schema_surface()
        validate_reasoning_handoff_schema_surface()
        surfaces_by_id = validate_registry()
        validate_bridge_example(surfaces_by_id)
        validate_counterpart_example(surfaces_by_id)
        validate_reasoning_handoff_example()
    except ValidationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print("[ok] validated KAG registry schema surface")
    print("[ok] validated bridge retrieval surface schema")
    print("[ok] validated counterpart edge surface schema")
    print("[ok] validated reasoning handoff guardrail schema")
    print("[ok] validated generated/kag_registry.min.json")
    print("[ok] validated bridge retrieval example")
    print("[ok] validated counterpart edge example")
    print("[ok] validated reasoning handoff guardrail example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
