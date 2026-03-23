#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

from kag_generation import (
    AOA_AGENTS_ROOT,
    AOA_EVALS_ROOT,
    AOA_MEMO_ROOT,
    AOA_PLAYBOOKS_ROOT,
    AOA_TECHNIQUES_ROOT,
    REGISTRY_MANIFEST_PATH,
    REGISTRY_MIN_OUTPUT_PATH,
    REGISTRY_OUTPUT_PATH,
    REASONING_HANDOFF_MANIFEST_PATH,
    REASONING_HANDOFF_MIN_OUTPUT_PATH,
    REASONING_HANDOFF_OUTPUT_PATH,
    TECHNIQUE_LIFT_MANIFEST_PATH,
    TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
    TECHNIQUE_LIFT_OUTPUT_PATH,
    build_registry_payload,
    build_reasoning_handoff_pack_payload,
    build_technique_lift_pack_payload,
    encode_json,
    repo_ref,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def repo_root_from_env(env_name: str, default: Path) -> Path:
    override = os.environ.get(env_name)
    if not override:
        return default
    return Path(override).expanduser().resolve()


TREE_OF_SOPHIA_ROOT = repo_root_from_env(
    "TREE_OF_SOPHIA_ROOT", REPO_ROOT.parent / "Tree-of-Sophia"
)

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
TECHNIQUE_LIFT_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "technique-lift-pack-manifest.schema.json"
)
TECHNIQUE_LIFT_PACK_SCHEMA_PATH = REPO_ROOT / "schemas" / "technique-lift-pack.schema.json"
REASONING_HANDOFF_PACK_MANIFEST_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "reasoning-handoff-pack-manifest.schema.json"
)
REASONING_HANDOFF_PACK_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "reasoning-handoff-pack.schema.json"
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
EXPECTED_TECHNIQUE_LIFT_INPUTS = {
    ("technique_section_manifest", "generated/technique_section_manifest.min.json", "section_manifest"),
    ("technique_catalog", "generated/technique_catalog.json", "metadata_spine"),
    ("technique_evidence_note_manifest", "generated/technique_evidence_note_manifest.min.json", "provenance_handles"),
}
EXPECTED_TECHNIQUE_LIFT_BINDINGS = {
    (
        "AOA-K-0001",
        "technique-section-lift",
        "section_manifest",
        "section_lift",
        "technique_section_manifest",
    ),
    (
        "AOA-K-0002",
        "metadata-spine-projection",
        "metadata_spine",
        "metadata_spine",
        "technique_catalog",
    ),
    (
        "AOA-K-0003",
        "bounded-relation-view",
        "relation_view",
        "relation_view",
        "technique_catalog",
    ),
    (
        "AOA-K-0004",
        "provenance-note-view",
        "provenance_view",
        "provenance_view",
        "technique_evidence_note_manifest",
    ),
}
EXPECTED_TECHNIQUE_LIFT_OUTPUT_PATHS = {
    "full": "generated/technique_lift_pack.json",
    "min": "generated/technique_lift_pack.min.json",
}
EXPECTED_TECHNIQUE_LIFT_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "graph_sovereignty": "forbidden",
}
ALLOWED_CONTRACT_STRENGTH = {
    "schema_backed",
    "doc_backed",
    "playbook_declared",
}
EXPECTED_REASONING_HANDOFF_SOURCE_ROOT_ENVS = {
    "aoa-playbooks": "AOA_PLAYBOOKS_ROOT",
    "aoa-evals": "AOA_EVALS_ROOT",
    "aoa-memo": "AOA_MEMO_ROOT",
    "aoa-agents": "AOA_AGENTS_ROOT",
}
EXPECTED_REASONING_HANDOFF_INPUTS = {
    ("reasoning_handoff_doc", "aoa-kag", "docs/REASONING_HANDOFF.md", "kag_guardrail_doc"),
    ("artifact_to_verdict_hook_schema", "aoa-evals", "schemas/artifact-to-verdict-hook.schema.json", "eval_hook_schema"),
    ("aoa_p_0008_playbook", "aoa-playbooks", "playbooks/long-horizon-model-tier-orchestra/PLAYBOOK.md", "playbook_doc"),
    ("aoa_p_0008_hook", "aoa-evals", "examples/artifact_to_verdict_hook.long-horizon-model-tier-orchestra.example.json", "eval_hook_fixture"),
    ("aoa_p_0009_playbook", "aoa-playbooks", "playbooks/restartable-inquiry-loop/PLAYBOOK.md", "playbook_doc"),
    ("aoa_p_0009_hook", "aoa-evals", "examples/artifact_to_verdict_hook.restartable-inquiry-loop.example.json", "eval_hook_fixture"),
    ("checkpoint_to_memory_contract", "aoa-memo", "examples/checkpoint_to_memory_contract.example.json", "memo_contract_fixture"),
    ("inquiry_checkpoint_schema", "aoa-memo", "schemas/inquiry_checkpoint.schema.json", "memo_schema"),
    ("witness_trace_contract", "aoa-memo", "docs/WITNESS_TRACE_CONTRACT.md", "memo_doc"),
    ("witness_trace_schema", "aoa-memo", "schemas/witness-trace.schema.json", "memo_schema"),
}
EXPECTED_REASONING_HANDOFF_BINDINGS = {
    ("AOA-P-0008", "aoa_p_0008_playbook", "aoa_p_0008_hook", ("checkpoint_to_memory_contract",), None, ("witness_trace_contract", "witness_trace_schema")),
    ("AOA-P-0009", "aoa_p_0009_playbook", "aoa_p_0009_hook", ("checkpoint_to_memory_contract",), "inquiry_checkpoint_schema", ()),
}
EXPECTED_REASONING_HANDOFF_OUTPUT_PATHS = {
    "full": "generated/reasoning_handoff_pack.json",
    "min": "generated/reasoning_handoff_pack.min.json",
}
EXPECTED_REASONING_HANDOFF_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "routing_ownership": "forbidden",
    "memory_truth_ownership": "forbidden",
    "canon_authorship": "forbidden",
    "verdict_ownership": "forbidden",
}
EXPECTED_REASONING_HANDOFF_SCENARIOS = {"AOA-P-0008", "AOA-P-0009"}
MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VISIBLE_ROOTS = (
    REPO_ROOT,
    AOA_TECHNIQUES_ROOT,
    AOA_PLAYBOOKS_ROOT,
    AOA_EVALS_ROOT,
    AOA_MEMO_ROOT,
    AOA_AGENTS_ROOT,
    TREE_OF_SOPHIA_ROOT,
)


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


def validate_technique_lift_manifest_schema_surface() -> None:
    validate_top_level_schema(TECHNIQUE_LIFT_MANIFEST_SCHEMA_PATH, "technique lift manifest")


def validate_technique_lift_pack_schema_surface() -> None:
    validate_top_level_schema(TECHNIQUE_LIFT_PACK_SCHEMA_PATH, "technique lift pack")


def validate_reasoning_handoff_pack_manifest_schema_surface() -> None:
    validate_top_level_schema(
        REASONING_HANDOFF_PACK_MANIFEST_SCHEMA_PATH,
        "reasoning handoff pack manifest",
    )


def validate_reasoning_handoff_pack_schema_surface() -> None:
    validate_top_level_schema(
        REASONING_HANDOFF_PACK_SCHEMA_PATH,
        "reasoning handoff pack",
    )


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


def resolve_aoa_techniques_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-techniques/"):
        fail(f"{label} must reference aoa-techniques: {raw_ref}")
    return resolve_relative_ref(
        AOA_TECHNIQUES_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )


def resolve_aoa_playbooks_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-playbooks/"):
        fail(f"{label} must reference aoa-playbooks: {raw_ref}")
    return resolve_relative_ref(
        AOA_PLAYBOOKS_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )


def resolve_aoa_evals_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-evals/"):
        fail(f"{label} must reference aoa-evals: {raw_ref}")
    return resolve_relative_ref(
        AOA_EVALS_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )


def resolve_aoa_agents_ref(raw_ref: str, *, label: str) -> Path:
    if not raw_ref.startswith("aoa-agents/"):
        fail(f"{label} must reference aoa-agents: {raw_ref}")
    return resolve_relative_ref(
        AOA_AGENTS_ROOT,
        raw_ref.split("/", 1)[1],
        label=label,
    )


def resolve_known_ref(raw_ref: str, *, label: str) -> Path:
    if raw_ref.startswith("aoa-techniques/"):
        return resolve_aoa_techniques_ref(raw_ref, label=label)
    if raw_ref.startswith("aoa-playbooks/"):
        return resolve_aoa_playbooks_ref(raw_ref, label=label)
    if raw_ref.startswith("aoa-evals/"):
        return resolve_aoa_evals_ref(raw_ref, label=label)
    if raw_ref.startswith("aoa-memo/"):
        return resolve_relative_ref(
            AOA_MEMO_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    if raw_ref.startswith("aoa-agents/"):
        return resolve_aoa_agents_ref(raw_ref, label=label)
    if raw_ref.startswith("Tree-of-Sophia/"):
        return resolve_relative_ref(
            TREE_OF_SOPHIA_ROOT,
            raw_ref.split("/", 1)[1],
            label=label,
        )
    return resolve_relative_ref(REPO_ROOT, raw_ref, label=label)


def validate_exact_set(
    values: list[str] | set[str],
    expected: set[str],
    *,
    label: str,
) -> None:
    if set(values) != expected:
        fail(f"{label} must match the exact expected set")


def validate_registry_payload(
    payload: object,
    *,
    label: str,
) -> dict[str, dict[str, object]]:
    if not isinstance(payload, dict):
        fail(f"{label} must be a JSON object")

    for key in ("version", "layer", "surfaces"):
        if key not in payload:
            fail(f"{label} is missing required key '{key}'")

    if not isinstance(payload["version"], int) or payload["version"] < 1:
        fail(f"{label} 'version' must be an integer >= 1")
    if payload["layer"] != "aoa-kag":
        fail(f"{label} 'layer' must equal 'aoa-kag'")

    surfaces = payload["surfaces"]
    if not isinstance(surfaces, list) or not surfaces:
        fail(f"{label} 'surfaces' must be a non-empty list")

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
        location = f"{label} surfaces[{index}]"
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
            fail(f"duplicate KAG surface id in {label}: '{surface_id}'")
        seen_ids.add(surface_id)
        surfaces_by_id[surface_id] = surface

        if not isinstance(name, str) or len(name) < 3:
            fail(f"{location}.name must be a string of length >= 3")
        if name in seen_names:
            fail(f"duplicate KAG surface name in {label}: '{name}'")
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
        fail(f"{label} is missing required seed surfaces: {', '.join(missing_seed)}")
    validate_special_registry_surfaces(surfaces_by_id, label=label)
    return surfaces_by_id


def validate_special_registry_surfaces(
    surfaces_by_id: dict[str, dict[str, object]],
    *,
    label: str,
) -> None:
    surface_0007 = surfaces_by_id.get("AOA-K-0007")
    if surface_0007 is None:
        fail(f"{label} is missing required surface 'AOA-K-0007'")
    if surface_0007.get("name") != "tos-retrieval-axis-surface":
        fail(f"{label} AOA-K-0007 must keep name 'tos-retrieval-axis-surface'")
    if surface_0007.get("status") != "planned":
        fail(f"{label} AOA-K-0007 must remain planned")

    surface_0008 = surfaces_by_id.get("AOA-K-0008")
    if surface_0008 is None:
        fail(f"{label} is missing required surface 'AOA-K-0008'")
    if surface_0008.get("name") != "counterpart-edge-view":
        fail(f"{label} AOA-K-0008 must keep name 'counterpart-edge-view'")
    if surface_0008.get("status") != "planned":
        fail(f"{label} AOA-K-0008 must remain planned")
    if surface_0008.get("source_class") != "tos_text":
        fail(f"{label} AOA-K-0008 must keep 'tos_text' as its primary source_class")
    if surface_0008.get("derived_kind") != "edge_projection":
        fail(f"{label} AOA-K-0008 must keep 'edge_projection' as its derived_kind")

    source_inputs = surface_0008.get("source_inputs")
    if not isinstance(source_inputs, list):
        fail(f"{label} AOA-K-0008 must declare source_inputs")
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
        fail(f"{label} AOA-K-0008 source_inputs must match the current counterpart bridge source contract")


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


def validate_reasoning_artifact_descriptor(
    payload: object,
    *,
    label: str,
) -> dict[str, object]:
    if not isinstance(payload, dict):
        fail(f"{label} must be an object")
    for key in ("artifact_name", "contract_strength", "artifact_contract_refs"):
        if key not in payload:
            fail(f"{label} is missing required key '{key}'")
    artifact_name = payload["artifact_name"]
    contract_strength = payload["contract_strength"]
    artifact_contract_refs = payload["artifact_contract_refs"]
    if not isinstance(artifact_name, str) or not artifact_name:
        fail(f"{label}.artifact_name must be a non-empty string")
    if contract_strength not in ALLOWED_CONTRACT_STRENGTH:
        fail(f"{label}.contract_strength '{contract_strength}' is not allowed")
    refs = validate_unique_string_list(
        artifact_contract_refs,
        label=f"{label}.artifact_contract_refs",
    )
    for ref in refs:
        resolve_known_ref(ref, label=f"{label}.artifact_contract_refs")
    if contract_strength == "schema_backed" and not any(ref.endswith(".schema.json") for ref in refs):
        fail(f"{label} marked as schema_backed must include at least one schema ref")
    return payload


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
    if payload["source_manifest_ref"] != "manifests/reasoning_handoff_pack.json":
        fail("reasoning handoff pack source_manifest_ref must point to manifests/reasoning_handoff_pack.json")
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
        if set(guardrail_refs) != {
            "docs/REASONING_HANDOFF.md",
            "schemas/reasoning-handoff-guardrail.schema.json",
        }:
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
            if trace_surfaces != ["aoa-memo/docs/WITNESS_TRACE_CONTRACT.md"]:
                fail(f"{location}.eval_bridge.trace_surfaces must keep the witness trace contract")
            if memo_writeback_targets != ["decision", "claim", "pattern"]:
                fail(f"{location}.memo_bridge.memo_writeback_targets must keep the bounded AOA-P-0008 writeback targets")
            if delta_split is not None:
                fail(f"{location}.memo_bridge.delta_split must stay null for AOA-P-0008")
            validate_exact_set(
                set(artifact_schema_refs),
                {
                    "aoa-agents/schemas/artifact.route_decision.schema.json",
                    "aoa-agents/schemas/artifact.bounded_plan.schema.json",
                    "aoa-agents/schemas/artifact.verification_result.schema.json",
                    "aoa-agents/schemas/artifact.transition_decision.schema.json",
                    "aoa-agents/schemas/artifact.distillation_pack.schema.json",
                    "aoa-memo/schemas/witness-trace.schema.json",
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
                    "field_contract_ref": "aoa-memo/schemas/inquiry_checkpoint.schema.json",
                },
                "canon_delta": {
                    "artifact_name": "canon_delta",
                    "checkpoint_field": "canon_delta_refs",
                    "field_contract_ref": "aoa-memo/schemas/inquiry_checkpoint.schema.json",
                },
            }
            if delta_split != expected_delta_split:
                fail(f"{location}.memo_bridge.delta_split must keep the explicit inquiry checkpoint memory/canon split")
            validate_exact_set(
                set(artifact_schema_refs),
                {
                    "aoa-memo/schemas/inquiry_checkpoint.schema.json",
                    "aoa-memo/schemas/checkpoint-to-memory-contract.schema.json",
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


def validate_generated_text(path: Path, expected_text: str, *, label: str) -> None:
    try:
        actual_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"{label} is missing at {display_path(path)}")
    if actual_text != expected_text:
        fail(f"{label} is out of date; run python scripts/generate_kag.py")


def validate_technique_lift_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    if not isinstance(payload, dict):
        fail("technique lift pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "section_scope",
        "technique_count",
        "techniques",
    ):
        if key not in payload:
            fail(f"technique lift pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("technique lift pack pack_version must equal 1")
    if payload["pack_type"] != "technique_lift_pack":
        fail("technique lift pack pack_type must equal 'technique_lift_pack'")
    if payload["source_repo"] != "aoa-techniques":
        fail("technique lift pack source_repo must equal 'aoa-techniques'")
    if payload["source_manifest_ref"] != "manifests/technique_lift_pack.json":
        fail("technique lift pack source_manifest_ref must point to manifests/technique_lift_pack.json")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("technique lift pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str]] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"technique lift pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, role, ref)):
            fail(f"{location} must keep name, role, and ref")
        resolve_aoa_techniques_ref(ref, label=location)
        actual_source_inputs.add((name, ref.split("/", 1)[1], role))
    if actual_source_inputs != EXPECTED_TECHNIQUE_LIFT_INPUTS:
        fail("technique lift pack source_inputs must match the manifest-driven donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("technique lift pack surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"technique lift pack surface_bindings[{index}]"
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
            fail(f"{location} does not match the generated registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(f"{location} does not match the generated registry derived_kind")
        if surface.get("status") != "active":
            fail(f"{location} must only point to active registry surfaces")
    if actual_bindings != EXPECTED_TECHNIQUE_LIFT_BINDINGS:
        fail("technique lift pack surface_bindings must match the current bounded technique lift bindings")

    section_scope = validate_unique_string_list(
        payload["section_scope"],
        label="technique lift pack section_scope",
    )

    techniques = payload["techniques"]
    if not isinstance(techniques, list) or not techniques:
        fail("technique lift pack techniques must be a non-empty list")
    technique_count = payload["technique_count"]
    if not isinstance(technique_count, int) or technique_count != len(techniques):
        fail("technique lift pack technique_count must equal the number of techniques")

    seen_technique_ids: set[str] = set()
    for index, technique in enumerate(techniques):
        location = f"technique lift pack techniques[{index}]"
        if not isinstance(technique, dict):
            fail(f"{location} must be an object")

        for key in (
            "technique_id",
            "technique_name",
            "source_ref",
            "section_lift",
            "metadata_spine",
            "relation_view",
            "provenance_view",
        ):
            if key not in technique:
                fail(f"{location} is missing required key '{key}'")

        technique_id = technique["technique_id"]
        technique_name = technique["technique_name"]
        source_ref = technique["source_ref"]
        if not isinstance(technique_id, str) or not re.match(r"^AOA-T-[0-9]{4}$", technique_id):
            fail(f"{location}.technique_id must be an AOA technique id")
        if technique_id in seen_technique_ids:
            fail(f"{location}.technique_id '{technique_id}' is duplicated")
        seen_technique_ids.add(technique_id)
        if not isinstance(technique_name, str) or not technique_name:
            fail(f"{location}.technique_name must be a non-empty string")
        if not isinstance(source_ref, str) or not source_ref.startswith("aoa-techniques/"):
            fail(f"{location}.source_ref must point to aoa-techniques")
        resolve_aoa_techniques_ref(source_ref, label=f"{location}.source_ref")

        section_lift = technique["section_lift"]
        if not isinstance(section_lift, dict):
            fail(f"{location}.section_lift must be an object")
        section_count = section_lift.get("section_count")
        sections = section_lift.get("sections")
        if not isinstance(sections, list) or not sections:
            fail(f"{location}.section_lift.sections must be a non-empty list")
        if not isinstance(section_count, int) or section_count != len(sections):
            fail(f"{location}.section_lift.section_count must equal the number of sections")
        seen_headings: set[str] = set()
        for section_index, section in enumerate(sections):
            section_location = f"{location}.section_lift.sections[{section_index}]"
            if not isinstance(section, dict):
                fail(f"{section_location} must be an object")
            heading = section.get("heading")
            order = section.get("order")
            if not isinstance(heading, str) or not heading:
                fail(f"{section_location}.heading must be a non-empty string")
            if heading not in section_scope:
                fail(f"{section_location}.heading '{heading}' must appear in section_scope")
            if heading in seen_headings:
                fail(f"{section_location}.heading '{heading}' is duplicated for {technique_id}")
            seen_headings.add(heading)
            if not isinstance(order, int) or order < 1:
                fail(f"{section_location}.order must be a positive integer")

        metadata_spine = technique["metadata_spine"]
        if not isinstance(metadata_spine, dict):
            fail(f"{location}.metadata_spine must be an object")
        for key in (
            "domain",
            "status",
            "summary",
            "maturity_score",
            "rigor_level",
            "reversibility",
            "review_required",
            "validation_strength",
            "export_ready",
        ):
            if key not in metadata_spine:
                fail(f"{location}.metadata_spine is missing '{key}'")
        if not isinstance(metadata_spine["domain"], str) or not metadata_spine["domain"]:
            fail(f"{location}.metadata_spine.domain must be a non-empty string")
        if not isinstance(metadata_spine["status"], str) or not metadata_spine["status"]:
            fail(f"{location}.metadata_spine.status must be a non-empty string")
        if not isinstance(metadata_spine["summary"], str) or len(metadata_spine["summary"]) < 10:
            fail(f"{location}.metadata_spine.summary must be a string of length >= 10")
        if not isinstance(metadata_spine["maturity_score"], int) or metadata_spine["maturity_score"] < 0:
            fail(f"{location}.metadata_spine.maturity_score must be a non-negative integer")
        if not isinstance(metadata_spine["review_required"], bool):
            fail(f"{location}.metadata_spine.review_required must be a boolean")
        if not isinstance(metadata_spine["export_ready"], bool):
            fail(f"{location}.metadata_spine.export_ready must be a boolean")

        relation_view = technique["relation_view"]
        if not isinstance(relation_view, dict):
            fail(f"{location}.relation_view must be an object")
        relation_count = relation_view.get("relation_count")
        relations = relation_view.get("relations")
        if not isinstance(relations, list):
            fail(f"{location}.relation_view.relations must be a list")
        if not isinstance(relation_count, int) or relation_count != len(relations):
            fail(f"{location}.relation_view.relation_count must equal the number of relations")
        for relation_index, relation in enumerate(relations):
            relation_location = f"{location}.relation_view.relations[{relation_index}]"
            if not isinstance(relation, dict):
                fail(f"{relation_location} must be an object")
            relation_type = relation.get("relation_type")
            target_ref = relation.get("target_ref")
            if not isinstance(relation_type, str) or not relation_type:
                fail(f"{relation_location}.relation_type must be a non-empty string")
            if not isinstance(target_ref, str) or not target_ref.startswith("aoa-techniques/AOA-T-"):
                fail(f"{relation_location}.target_ref must be an aoa-techniques technique ref")

        provenance_view = technique["provenance_view"]
        if not isinstance(provenance_view, dict):
            fail(f"{location}.provenance_view must be an object")
        reviewed_at = provenance_view.get("public_safety_reviewed_at")
        note_count = provenance_view.get("note_count")
        note_handles = provenance_view.get("note_handles")
        if not isinstance(reviewed_at, str) or not DATE_RE.match(reviewed_at):
            fail(f"{location}.provenance_view.public_safety_reviewed_at must be a YYYY-MM-DD string")
        if not isinstance(note_handles, list):
            fail(f"{location}.provenance_view.note_handles must be a list")
        if not isinstance(note_count, int) or note_count != len(note_handles):
            fail(f"{location}.provenance_view.note_count must equal the number of note handles")
        seen_note_refs: set[str] = set()
        for note_index, note_handle in enumerate(note_handles):
            note_location = f"{location}.provenance_view.note_handles[{note_index}]"
            if not isinstance(note_handle, dict):
                fail(f"{note_location} must be an object")
            kind = note_handle.get("kind")
            title = note_handle.get("title")
            note_ref = note_handle.get("note_ref")
            if not all(isinstance(value, str) and value for value in (kind, title, note_ref)):
                fail(f"{note_location} must keep kind, title, and note_ref")
            if note_ref in seen_note_refs:
                fail(f"{note_location}.note_ref '{note_ref}' is duplicated for {technique_id}")
            seen_note_refs.add(note_ref)
            resolve_aoa_techniques_ref(note_ref, label=f"{note_location}.note_ref")


def validate_bridge_example(surfaces_by_id: dict[str, dict[str, object]]) -> None:
    payload = read_json(BRIDGE_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("bridge example must be a JSON object")

    surface_id = payload.get("surface_id")
    if surface_id != "AOA-K-0007":
        fail("bridge example surface_id must equal 'AOA-K-0007'")
    if surface_id not in surfaces_by_id:
        fail("bridge example surface_id must exist in the generated registry")

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
        fail("counterpart example surface_id must exist in the generated registry")

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
        validate_technique_lift_manifest_schema_surface()
        validate_technique_lift_pack_schema_surface()
        validate_reasoning_handoff_pack_manifest_schema_surface()
        validate_reasoning_handoff_pack_schema_surface()

        registry_manifest_payload = read_json(REGISTRY_MANIFEST_PATH)
        registry_manifest_surfaces = validate_registry_payload(
            registry_manifest_payload,
            label="registry manifest",
        )
        validate_technique_lift_manifest(registry_manifest_surfaces)
        validate_reasoning_handoff_manifest()

        expected_registry_payload = build_registry_payload()
        expected_technique_lift_pack_payload = build_technique_lift_pack_payload(
            expected_registry_payload
        )
        expected_reasoning_handoff_pack_payload = build_reasoning_handoff_pack_payload()

        validate_generated_text(
            REGISTRY_OUTPUT_PATH,
            encode_json(expected_registry_payload, pretty=True),
            label="generated registry",
        )
        validate_generated_text(
            REGISTRY_MIN_OUTPUT_PATH,
            encode_json(expected_registry_payload, pretty=False),
            label="generated compact registry",
        )
        validate_generated_text(
            TECHNIQUE_LIFT_OUTPUT_PATH,
            encode_json(expected_technique_lift_pack_payload, pretty=True),
            label="generated technique lift pack",
        )
        validate_generated_text(
            TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
            encode_json(expected_technique_lift_pack_payload, pretty=False),
            label="generated compact technique lift pack",
        )
        validate_generated_text(
            REASONING_HANDOFF_OUTPUT_PATH,
            encode_json(expected_reasoning_handoff_pack_payload, pretty=True),
            label="generated reasoning handoff pack",
        )
        validate_generated_text(
            REASONING_HANDOFF_MIN_OUTPUT_PATH,
            encode_json(expected_reasoning_handoff_pack_payload, pretty=False),
            label="generated compact reasoning handoff pack",
        )

        generated_registry_payload = read_json(REGISTRY_MIN_OUTPUT_PATH)
        generated_surfaces_by_id = validate_registry_payload(
            generated_registry_payload,
            label="generated registry",
        )
        validate_technique_lift_pack(
            read_json(TECHNIQUE_LIFT_MIN_OUTPUT_PATH),
            generated_surfaces_by_id,
        )
        validate_reasoning_handoff_pack(
            read_json(REASONING_HANDOFF_MIN_OUTPUT_PATH),
        )
        validate_bridge_example(generated_surfaces_by_id)
        validate_counterpart_example(generated_surfaces_by_id)
        validate_reasoning_handoff_example()
    except ValidationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print("[ok] validated KAG registry schema surface")
    print("[ok] validated bridge retrieval surface schema")
    print("[ok] validated counterpart edge surface schema")
    print("[ok] validated reasoning handoff guardrail schema")
    print("[ok] validated technique lift manifest schema")
    print("[ok] validated technique lift pack schema")
    print("[ok] validated reasoning handoff pack manifest schema")
    print("[ok] validated reasoning handoff pack schema")
    print("[ok] validated manifests/kag_registry.json")
    print("[ok] validated manifests/technique_lift_pack.json")
    print("[ok] validated manifests/reasoning_handoff_pack.json")
    print("[ok] validated generated registry outputs are up to date")
    print("[ok] validated generated technique lift pack outputs are up to date")
    print("[ok] validated generated reasoning handoff pack outputs are up to date")
    print("[ok] validated generated technique lift pack structure")
    print("[ok] validated generated reasoning handoff pack structure")
    print("[ok] validated bridge retrieval example")
    print("[ok] validated counterpart edge example")
    print("[ok] validated reasoning handoff guardrail example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
