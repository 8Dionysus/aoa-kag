#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class GenerationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise GenerationError(message)


def repo_root_from_env(env_name: str, default: Path) -> Path:
    override = os.environ.get(env_name)
    if not override:
        return default
    return Path(override).expanduser().resolve()


AOA_TECHNIQUES_ROOT = repo_root_from_env(
    "AOA_TECHNIQUES_ROOT", REPO_ROOT.parent / "aoa-techniques"
)
AOA_PLAYBOOKS_ROOT = repo_root_from_env(
    "AOA_PLAYBOOKS_ROOT", REPO_ROOT.parent / "aoa-playbooks"
)
AOA_EVALS_ROOT = repo_root_from_env("AOA_EVALS_ROOT", REPO_ROOT.parent / "aoa-evals")
AOA_MEMO_ROOT = repo_root_from_env("AOA_MEMO_ROOT", REPO_ROOT.parent / "aoa-memo")
AOA_AGENTS_ROOT = repo_root_from_env("AOA_AGENTS_ROOT", REPO_ROOT.parent / "aoa-agents")

REGISTRY_MANIFEST_PATH = REPO_ROOT / "manifests" / "kag_registry.json"
TECHNIQUE_LIFT_MANIFEST_PATH = REPO_ROOT / "manifests" / "technique_lift_pack.json"
REASONING_HANDOFF_MANIFEST_PATH = REPO_ROOT / "manifests" / "reasoning_handoff_pack.json"
REASONING_HANDOFF_GUARDRAIL_PATH = REPO_ROOT / "docs" / "REASONING_HANDOFF.md"

REGISTRY_OUTPUT_PATH = REPO_ROOT / "generated" / "kag_registry.json"
REGISTRY_MIN_OUTPUT_PATH = REPO_ROOT / "generated" / "kag_registry.min.json"
TECHNIQUE_LIFT_OUTPUT_PATH = REPO_ROOT / "generated" / "technique_lift_pack.json"
TECHNIQUE_LIFT_MIN_OUTPUT_PATH = REPO_ROOT / "generated" / "technique_lift_pack.min.json"
REASONING_HANDOFF_OUTPUT_PATH = REPO_ROOT / "generated" / "reasoning_handoff_pack.json"
REASONING_HANDOFF_MIN_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "reasoning_handoff_pack.min.json"
)

QUERY_MODE_HEADING = re.compile(r"^###\s+`([^`]+)`\s*$")
KNOWN_REPO_ROOTS = {
    "aoa-kag": REPO_ROOT,
    "aoa-techniques": AOA_TECHNIQUES_ROOT,
    "aoa-playbooks": AOA_PLAYBOOKS_ROOT,
    "aoa-evals": AOA_EVALS_ROOT,
    "aoa-memo": AOA_MEMO_ROOT,
    "aoa-agents": AOA_AGENTS_ROOT,
}


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {path.as_posix()}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.as_posix()}: {exc}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.as_posix()}")


def encode_json(payload: object, *, pretty: bool) -> str:
    if pretty:
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n"


def write_json(path: Path, payload: object, *, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encode_json(payload, pretty=pretty), encoding="utf-8")


def ordered_unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def repo_ref(repo: str, path: str) -> str:
    clean_path = path.lstrip("/")
    if repo == "aoa-kag":
        return clean_path
    return f"{repo}/{clean_path}"


def resolve_repo_path(repo: str, path: str) -> Path:
    root = KNOWN_REPO_ROOTS.get(repo)
    if root is None:
        fail(f"unsupported repository '{repo}'")
    return root / path


def manifest_input_path(source_input: dict[str, str]) -> Path:
    return resolve_repo_path(source_input["repo"], source_input["path"])


def manifest_input_ref(source_input: dict[str, str]) -> str:
    return repo_ref(source_input["repo"], source_input["path"])


def build_registry_payload() -> dict[str, object]:
    payload = read_json(REGISTRY_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("registry manifest must be a JSON object")
    return payload


def build_technique_lift_pack_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TECHNIQUE_LIFT_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("technique lift manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")

    if not isinstance(source_inputs, list) or not source_inputs:
        fail("technique lift manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("technique lift manifest must declare surface_bindings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")

    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    inputs_by_name: dict[str, dict[str, str]] = {}
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("technique lift manifest source_inputs entries must be objects")
        name = source_input.get("name")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, path, role)):
            fail("technique lift manifest source_inputs must keep name, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate technique lift source input '{name}'")
        inputs_by_name[name] = {"path": path, "role": role}

    seen_surface_ids: set[str] = set()
    seen_slots: set[str] = set()
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("technique lift manifest surface_bindings entries must be objects")
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
            fail("technique lift manifest surface_bindings must keep id, name, kind, slot, and source input")
        if surface_id in seen_surface_ids:
            fail(f"duplicate technique lift surface binding '{surface_id}'")
        if derived_slot in seen_slots:
            fail(f"duplicate technique lift derived slot '{derived_slot}'")
        seen_surface_ids.add(surface_id)
        seen_slots.add(derived_slot)
        if source_input not in inputs_by_name:
            fail(f"technique lift binding '{surface_id}' references unknown source input '{source_input}'")

        registry_surface = registry_by_id.get(surface_id)
        if registry_surface is None:
            fail(f"technique lift binding '{surface_id}' does not exist in the registry manifest")
        if registry_surface.get("name") != surface_name:
            fail(f"technique lift binding '{surface_id}' does not match registry surface name")
        if registry_surface.get("derived_kind") != derived_kind:
            fail(f"technique lift binding '{surface_id}' does not match registry derived_kind")
        if registry_surface.get("status") != "active":
            fail(f"technique lift binding '{surface_id}' must point to an active registry surface")

    section_manifest = read_json(
        AOA_TECHNIQUES_ROOT / inputs_by_name["technique_section_manifest"]["path"]
    )
    catalog = read_json(AOA_TECHNIQUES_ROOT / inputs_by_name["technique_catalog"]["path"])
    evidence_manifest = read_json(
        AOA_TECHNIQUES_ROOT / inputs_by_name["technique_evidence_note_manifest"]["path"]
    )

    if not all(
        isinstance(payload, dict)
        for payload in (section_manifest, catalog, evidence_manifest)
    ):
        fail("aoa-techniques donor manifests must be JSON objects")

    catalog_techniques = catalog.get("techniques")
    section_techniques = section_manifest.get("techniques")
    evidence_techniques = evidence_manifest.get("techniques")
    section_scope = section_manifest.get("section_scope")

    if not isinstance(catalog_techniques, list) or not catalog_techniques:
        fail("technique catalog must declare techniques")
    if not isinstance(section_techniques, list) or not section_techniques:
        fail("technique section manifest must declare techniques")
    if not isinstance(evidence_techniques, list) or not evidence_techniques:
        fail("technique evidence note manifest must declare techniques")
    if not isinstance(section_scope, list) or not section_scope:
        fail("technique section manifest must declare section_scope")

    section_by_id = {
        technique["id"]: technique
        for technique in section_techniques
        if isinstance(technique, dict) and isinstance(technique.get("id"), str)
    }
    evidence_by_id = {
        technique["id"]: technique
        for technique in evidence_techniques
        if isinstance(technique, dict) and isinstance(technique.get("id"), str)
    }

    techniques: list[dict[str, object]] = []

    for technique in catalog_techniques:
        if not isinstance(technique, dict):
            fail("technique catalog entries must be objects")

        technique_id = technique.get("id")
        technique_name = technique.get("name")
        technique_path = technique.get("technique_path")

        if not all(
            isinstance(value, str) and value
            for value in (technique_id, technique_name, technique_path)
        ):
            fail("technique catalog entries must keep id, name, and technique_path")

        section_entry = section_by_id.get(technique_id)
        evidence_entry = evidence_by_id.get(technique_id)
        if section_entry is None:
            fail(f"technique section manifest is missing '{technique_id}'")
        if evidence_entry is None:
            fail(f"technique evidence note manifest is missing '{technique_id}'")

        raw_sections = section_entry.get("sections")
        raw_relations = technique.get("relations", [])
        raw_notes = evidence_entry.get("notes", [])

        if not isinstance(raw_sections, list) or not raw_sections:
            fail(f"technique section manifest entry '{technique_id}' must keep sections")
        if not isinstance(raw_relations, list):
            fail(f"technique catalog entry '{technique_id}' relations must be a list")
        if not isinstance(raw_notes, list):
            fail(f"technique evidence note manifest entry '{technique_id}' notes must be a list")

        sections: list[dict[str, object]] = []
        for section in raw_sections:
            if not isinstance(section, dict):
                fail(f"technique section manifest entry '{technique_id}' contains an invalid section")
            heading = section.get("heading")
            order = section.get("order")
            if not isinstance(heading, str) or not heading:
                fail(f"technique section manifest entry '{technique_id}' contains a section without heading")
            if not isinstance(order, int) or order < 1:
                fail(f"technique section manifest entry '{technique_id}' contains a section without positive order")
            sections.append({"heading": heading, "order": order})

        relations: list[dict[str, str]] = []
        for relation in raw_relations:
            if not isinstance(relation, dict):
                fail(f"technique catalog entry '{technique_id}' contains an invalid relation")
            relation_type = relation.get("type")
            target = relation.get("target")
            if not isinstance(relation_type, str) or not relation_type:
                fail(f"technique catalog entry '{technique_id}' contains a relation without type")
            if not isinstance(target, str) or not target:
                fail(f"technique catalog entry '{technique_id}' contains a relation without target")
            relations.append(
                {
                    "relation_type": relation_type,
                    "target_ref": f"aoa-techniques/{target}",
                }
            )

        note_handles: list[dict[str, str]] = []
        for note in raw_notes:
            if not isinstance(note, dict):
                fail(f"technique evidence note manifest entry '{technique_id}' contains an invalid note")
            kind = note.get("kind")
            title = note.get("title")
            note_path = note.get("note_path")
            if not all(isinstance(value, str) and value for value in (kind, title, note_path)):
                fail(f"technique evidence note manifest entry '{technique_id}' contains an incomplete note handle")
            note_handles.append(
                {
                    "kind": kind,
                    "title": title,
                    "note_ref": f"aoa-techniques/{note_path}",
                }
            )

        public_safety_reviewed_at = technique.get("public_safety_reviewed_at")
        if not isinstance(public_safety_reviewed_at, str) or not public_safety_reviewed_at:
            fail(f"technique catalog entry '{technique_id}' must keep public_safety_reviewed_at")

        metadata_spine = {
            "domain": technique["domain"],
            "status": technique["status"],
            "summary": technique["summary"],
            "maturity_score": technique["maturity_score"],
            "rigor_level": technique["rigor_level"],
            "reversibility": technique["reversibility"],
            "review_required": technique["review_required"],
            "validation_strength": technique["validation_strength"],
            "export_ready": technique["export_ready"],
        }

        techniques.append(
            {
                "technique_id": technique_id,
                "technique_name": technique_name,
                "source_ref": f"aoa-techniques/{technique_path}",
                "section_lift": {
                    "section_count": len(sections),
                    "sections": sections,
                },
                "metadata_spine": metadata_spine,
                "relation_view": {
                    "relation_count": len(relations),
                    "relations": relations,
                },
                "provenance_view": {
                    "public_safety_reviewed_at": public_safety_reviewed_at,
                    "note_count": len(note_handles),
                    "note_handles": note_handles,
                },
            }
        )

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_repo": manifest["source_repo"],
        "source_manifest_ref": "manifests/technique_lift_pack.json",
        "source_inputs": [
            {
                "name": source_input["name"],
                "role": source_input["role"],
                "ref": f"aoa-techniques/{source_input['path']}",
            }
            for source_input in source_inputs
        ],
        "surface_bindings": surface_bindings,
        "section_scope": section_scope,
        "technique_count": len(techniques),
        "techniques": techniques,
    }


def read_markdown_frontmatter(path: Path) -> dict[str, object]:
    lines = read_text(path).splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"markdown file is missing frontmatter fence: {path.as_posix()}")

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        fail(f"markdown file is missing closing frontmatter fence: {path.as_posix()}")

    payload: dict[str, object] = {}
    current_list_key: str | None = None

    for raw_line in lines[1:closing_index]:
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  - "):
            if current_list_key is None:
                fail(f"frontmatter list item without a key in {path.as_posix()}")
            current_value = payload.get(current_list_key)
            if not isinstance(current_value, list):
                fail(f"frontmatter key '{current_list_key}' is not a list in {path.as_posix()}")
            current_value.append(line[4:].strip())
            continue
        if ":" not in line:
            fail(f"unsupported frontmatter line in {path.as_posix()}: {line}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            fail(f"frontmatter key cannot be empty in {path.as_posix()}")
        if value:
            payload[key] = value
            current_list_key = None
            continue
        payload[key] = []
        current_list_key = key

    return payload


def get_frontmatter_string(
    payload: dict[str, object], key: str, *, label: str
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{label} must keep '{key}' as a non-empty string")
    return value


def get_frontmatter_list(
    payload: dict[str, object], key: str, *, label: str
) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{label} must keep '{key}' as a non-empty list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            fail(f"{label} contains an invalid '{key}' entry")
        result.append(item)
    return result


def normalize_repo_pointer(raw_ref: str) -> str:
    if not raw_ref.startswith("repo:"):
        fail(f"expected repo-qualified ref, received '{raw_ref}'")
    pointer = raw_ref[5:]
    parts = pointer.split("/")
    if len(parts) < 2:
        fail(f"invalid repo-qualified ref '{raw_ref}'")

    repo_name = parts[0]
    remainder = parts[1:]
    if repo_name not in KNOWN_REPO_ROOTS and len(parts) >= 3 and parts[1] in KNOWN_REPO_ROOTS:
        repo_name = parts[1]
        remainder = parts[2:]
    if repo_name not in KNOWN_REPO_ROOTS:
        fail(f"unsupported repo-qualified ref '{raw_ref}'")
    if not remainder:
        fail(f"repo-qualified ref is missing a path '{raw_ref}'")
    return repo_ref(repo_name, "/".join(remainder))


def normalize_relative_ref(repo: str, raw_ref: str) -> str:
    if raw_ref.startswith("repo:"):
        return normalize_repo_pointer(raw_ref)
    return repo_ref(repo, raw_ref)


def markdown_section_lines(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    inside = False
    target_level = heading.count("#")
    section_lines: list[str] = []

    for line in lines:
        if line.strip() == heading:
            inside = True
            continue
        if inside and line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= target_level:
                break
        if inside:
            section_lines.append(line)

    if not section_lines:
        fail(f"missing markdown section '{heading}' in {REASONING_HANDOFF_GUARDRAIL_PATH.as_posix()}")
    return section_lines


def extract_query_modes_from_doc(path: Path) -> list[str]:
    section_lines = markdown_section_lines(read_text(path), "## Query modes")
    query_modes: list[str] = []
    for line in section_lines:
        match = QUERY_MODE_HEADING.match(line.strip())
        if match:
            query_modes.append(match.group(1))
    if not query_modes:
        fail("reasoning handoff doc must declare query modes")
    return query_modes


def extract_bullets_after_marker(text: str, marker: str) -> list[str]:
    lines = text.splitlines()
    collecting = False
    items: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped == marker:
            collecting = True
            continue
        if not collecting:
            continue
        if stripped.startswith("- "):
            items.append(stripped[2:].strip().strip("`"))
            continue
        if items and not stripped:
            break

    if not items:
        fail(f"reasoning handoff doc is missing bullet list after '{marker}'")
    return items


def extract_boundary_guardrails_from_doc(path: Path) -> dict[str, str]:
    bullets = [
        line.strip()[2:].strip()
        for line in markdown_section_lines(read_text(path), "## Boundary guardrails")
        if line.strip().startswith("- ")
    ]
    if not bullets:
        fail("reasoning handoff doc must declare boundary guardrails")

    boundary_guardrails: dict[str, str] = {}
    for bullet in bullets:
        if bullet.startswith("`aoa-routing` owns "):
            boundary_guardrails["routing_owner"] = "aoa-routing"
        elif bullet.startswith("`aoa-memo` owns "):
            boundary_guardrails["memory_owner"] = "aoa-memo"
        elif bullet.startswith("`Tree-of-Sophia` owns "):
            boundary_guardrails["canon_owner"] = "Tree-of-Sophia"
        elif "direct canon authorship" in bullet and "forbidden" in bullet:
            boundary_guardrails["direct_canon_authorship"] = "forbidden"

    expected_keys = {
        "routing_owner",
        "memory_owner",
        "canon_owner",
        "direct_canon_authorship",
    }
    if set(boundary_guardrails) != expected_keys:
        fail("reasoning handoff doc boundary guardrails are incomplete")
    return boundary_guardrails


def build_artifact_descriptor(
    artifact_name: str,
    contract_strength: str,
    artifact_contract_refs: list[str],
) -> dict[str, object]:
    refs = ordered_unique(artifact_contract_refs)
    if not refs:
        fail(f"artifact '{artifact_name}' must keep at least one contract ref")
    return {
        "artifact_name": artifact_name,
        "contract_strength": contract_strength,
        "artifact_contract_refs": refs,
    }


def build_eval_anchor_refs(eval_anchors: list[str]) -> list[str]:
    refs: list[str] = []
    for eval_anchor in eval_anchors:
        eval_bundle_path = AOA_EVALS_ROOT / "bundles" / eval_anchor / "EVAL.md"
        if not eval_bundle_path.exists():
            fail(f"missing eval bundle for anchor '{eval_anchor}'")
        refs.append(repo_ref("aoa-evals", f"bundles/{eval_anchor}/EVAL.md"))
    return refs


def build_reasoning_handoff_scenario(
    binding: dict[str, object],
    inputs_by_name: dict[str, dict[str, str]],
    query_modes: list[str],
    return_contract: dict[str, object],
    boundary_guardrails: dict[str, str],
) -> dict[str, object]:
    scenario_ref = binding["scenario_ref"]
    playbook_input = inputs_by_name[binding["playbook_input"]]
    eval_hook_input = inputs_by_name[binding["eval_hook_input"]]
    memo_contract_inputs = [
        inputs_by_name[input_name]
        for input_name in binding["memo_contract_inputs"]
    ]
    optional_trace_inputs = [
        inputs_by_name[input_name]
        for input_name in binding["optional_trace_inputs"]
    ]

    playbook_path = manifest_input_path(playbook_input)
    playbook_meta = read_markdown_frontmatter(playbook_path)
    playbook_id = get_frontmatter_string(
        playbook_meta,
        "id",
        label=f"playbook frontmatter for {scenario_ref}",
    )
    if playbook_id != scenario_ref:
        fail(f"playbook '{playbook_path.as_posix()}' does not match scenario '{scenario_ref}'")

    expected_artifacts = get_frontmatter_list(
        playbook_meta,
        "expected_artifacts",
        label=f"playbook frontmatter for {scenario_ref}",
    )
    eval_anchors = get_frontmatter_list(
        playbook_meta,
        "eval_anchors",
        label=f"playbook frontmatter for {scenario_ref}",
    )
    memo_contract_refs = [
        normalize_relative_ref("aoa-memo", ref)
        for ref in get_frontmatter_list(
            playbook_meta,
            "memo_contract_refs",
            label=f"playbook frontmatter for {scenario_ref}",
        )
    ]
    memo_writeback_targets = get_frontmatter_list(
        playbook_meta,
        "memo_writeback_targets",
        label=f"playbook frontmatter for {scenario_ref}",
    )

    for ref in memo_contract_refs:
        repo_name, relative_path = ref.split("/", 1)
        if not resolve_repo_path(repo_name, relative_path).exists():
            fail(f"playbook memo contract ref does not exist: {ref}")

    eval_hook_payload = read_json(manifest_input_path(eval_hook_input))
    if not isinstance(eval_hook_payload, dict):
        fail(f"eval hook fixture for {scenario_ref} must be a JSON object")
    if eval_hook_payload.get("playbook_id") != scenario_ref:
        fail(f"eval hook fixture for {scenario_ref} must keep matching playbook_id")

    verification_surface = eval_hook_payload.get("verification_surface")
    if not isinstance(verification_surface, str) or not verification_surface:
        fail(f"eval hook fixture for {scenario_ref} must keep verification_surface")
    if verification_surface not in expected_artifacts:
        fail(f"verification surface '{verification_surface}' must be declared in the playbook expected_artifacts")

    hook_eval_anchor = eval_hook_payload.get("eval_anchor")
    if not isinstance(hook_eval_anchor, str) or hook_eval_anchor not in eval_anchors:
        fail(f"eval hook fixture for {scenario_ref} must point to a playbook-declared eval anchor")

    hook_artifact_inputs = eval_hook_payload.get("artifact_inputs")
    if not isinstance(hook_artifact_inputs, list) or not hook_artifact_inputs:
        fail(f"eval hook fixture for {scenario_ref} must keep artifact_inputs")

    normalized_hook_contract_refs = [
        normalize_repo_pointer(raw_ref)
        for raw_ref in eval_hook_payload.get("artifact_contract_refs", [])
    ]
    if not normalized_hook_contract_refs:
        fail(f"eval hook fixture for {scenario_ref} must keep artifact_contract_refs")

    normalized_trace_surfaces = [
        normalize_repo_pointer(raw_ref)
        for raw_ref in eval_hook_payload.get("trace_surfaces", [])
    ]
    report_expectation = eval_hook_payload.get("report_expectation")
    if not isinstance(report_expectation, dict):
        fail(f"eval hook fixture for {scenario_ref} must keep report_expectation")

    checkpoint_contract_payload = read_json(manifest_input_path(memo_contract_inputs[0]))
    if not isinstance(checkpoint_contract_payload, dict):
        fail(f"memo contract input for {scenario_ref} must be a JSON object")
    if checkpoint_contract_payload.get("contract_type") != "checkpoint_to_memory_contract":
        fail(f"memo contract input for {scenario_ref} must keep contract_type")

    playbook_ref = manifest_input_ref(playbook_input)
    playbook_artifact_ref = f"{playbook_ref}#expected-artifacts"

    if scenario_ref == "AOA-P-0008":
        schema_refs_by_artifact: dict[str, list[str]] = {}
        for contract_ref in normalized_hook_contract_refs:
            if not contract_ref.startswith("aoa-agents/schemas/artifact."):
                continue
            schema_name = Path(contract_ref).name
            artifact_name = schema_name.removeprefix("artifact.").removesuffix(".schema.json")
            schema_refs_by_artifact[artifact_name] = [contract_ref]

        missing_artifacts = [
            artifact_name
            for artifact_name in expected_artifacts
            if artifact_name not in schema_refs_by_artifact
        ]
        if missing_artifacts:
            fail(f"AOA-P-0008 is missing schema-backed artifact refs for: {', '.join(missing_artifacts)}")

        verification_descriptor = build_artifact_descriptor(
            "verification_result",
            "schema_backed",
            schema_refs_by_artifact["verification_result"],
        )
        supporting_descriptors = [
            build_artifact_descriptor(
                artifact_name,
                "schema_backed",
                schema_refs_by_artifact[artifact_name],
            )
            for artifact_name in expected_artifacts
            if artifact_name != "verification_result"
        ]

        witness_trace_contract = next(
            (
                source_input
                for source_input in optional_trace_inputs
                if source_input["name"] == "witness_trace_contract"
            ),
            None,
        )
        if witness_trace_contract is None:
            fail("AOA-P-0008 must declare witness_trace_contract as an optional trace input")

        witness_trace_schema = next(
            (
                source_input
                for source_input in optional_trace_inputs
                if source_input["name"] == "witness_trace_schema"
            ),
            None,
        )
        if witness_trace_schema is None:
            fail("AOA-P-0008 must declare witness_trace_schema as an optional trace input")

        optional_trace_sidecars = [
            build_artifact_descriptor(
                "WitnessTrace",
                "doc_backed",
                [manifest_input_ref(witness_trace_contract)],
            )
        ]
        continuity_surface = None
        memo_refs = ordered_unique(
            memo_contract_refs + [manifest_input_ref(witness_trace_contract)]
        )
        artifact_schema_refs = ordered_unique(
            normalized_hook_contract_refs + [manifest_input_ref(witness_trace_schema)]
        )
        delta_split = None
    elif scenario_ref == "AOA-P-0009":
        continuity_input_name = binding.get("continuity_input")
        if not isinstance(continuity_input_name, str) or not continuity_input_name:
            fail("AOA-P-0009 must declare a continuity_input")
        continuity_input = inputs_by_name[continuity_input_name]
        continuity_schema_payload = read_json(manifest_input_path(continuity_input))
        if not isinstance(continuity_schema_payload, dict):
            fail("AOA-P-0009 continuity schema must be a JSON object")

        continuity_schema_ref = manifest_input_ref(continuity_input)
        verification_descriptor = build_artifact_descriptor(
            "inquiry_checkpoint",
            "schema_backed",
            [continuity_schema_ref],
        )
        continuity_surface = build_artifact_descriptor(
            "inquiry_checkpoint",
            "schema_backed",
            [continuity_schema_ref],
        )
        supporting_descriptors = [
            build_artifact_descriptor(
                artifact_name,
                "playbook_declared",
                [playbook_artifact_ref],
            )
            for artifact_name in expected_artifacts
            if artifact_name != "inquiry_checkpoint"
        ]
        optional_trace_sidecars = []
        memo_refs = memo_contract_refs
        artifact_schema_refs = ordered_unique(
            [
                continuity_schema_ref,
                normalize_repo_pointer(
                    "repo:aoa-memo/schemas/checkpoint-to-memory-contract.schema.json"
                ),
            ]
        )
        delta_split = {
            "memory_delta": {
                "artifact_name": "memory_delta",
                "checkpoint_field": "memory_delta_refs",
                "field_contract_ref": continuity_schema_ref,
            },
            "canon_delta": {
                "artifact_name": "canon_delta",
                "checkpoint_field": "canon_delta_refs",
                "field_contract_ref": continuity_schema_ref,
            },
        }
    else:
        fail(f"unsupported reasoning handoff scenario '{scenario_ref}'")

    if hook_artifact_inputs != expected_artifacts:
        fail(f"eval hook fixture for {scenario_ref} must match playbook expected_artifacts exactly")

    eval_anchor_refs = build_eval_anchor_refs(eval_anchors)
    verdict_bundle_ref = eval_hook_payload.get("verdict_bundle_ref")
    if not isinstance(verdict_bundle_ref, str) or not verdict_bundle_ref:
        fail(f"eval hook fixture for {scenario_ref} must keep verdict_bundle_ref")
    eval_refs = ordered_unique(
        eval_anchor_refs
        + [normalize_repo_pointer(verdict_bundle_ref)]
        + [
            normalize_repo_pointer(raw_ref)
            for raw_ref in eval_hook_payload.get("contract_test_refs", [])
        ]
    )
    if len(eval_refs) == len(eval_anchor_refs):
        fail(f"eval hook fixture for {scenario_ref} must keep contract_test_refs")

    return {
        "scenario_ref": scenario_ref,
        "playbook_ref": playbook_ref,
        "artifact_spine": {
            "verification_surface": verification_descriptor,
            "continuity_surface": continuity_surface,
            "supporting_artifacts": supporting_descriptors,
            "optional_trace_sidecars": optional_trace_sidecars,
        },
        "eval_bridge": {
            "eval_anchor_refs": eval_anchor_refs,
            "verification_surface": verification_surface,
            "trace_surfaces": normalized_trace_surfaces,
            "artifact_contract_refs": normalized_hook_contract_refs,
            "report_expectation": report_expectation,
        },
        "memo_bridge": {
            "memo_contract_refs": memo_contract_refs,
            "memo_writeback_targets": memo_writeback_targets,
            "delta_split": delta_split,
        },
        "compatible_query_modes": query_modes,
        "authoritative_refs": {
            "playbook_refs": [playbook_ref],
            "eval_refs": eval_refs,
            "memo_refs": memo_refs,
            "kag_guardrail_refs": [
                repo_ref("aoa-kag", "docs/REASONING_HANDOFF.md"),
                repo_ref("aoa-kag", "schemas/reasoning-handoff-guardrail.schema.json"),
            ],
            "artifact_schema_refs": artifact_schema_refs,
        },
        "return_contract": return_contract,
        "boundary_guardrails": boundary_guardrails,
    }


def build_reasoning_handoff_pack_payload() -> dict[str, object]:
    manifest = read_json(REASONING_HANDOFF_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("reasoning handoff manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    scenario_bindings = manifest.get("scenario_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("reasoning handoff manifest must declare source_inputs")
    if not isinstance(scenario_bindings, list) or not scenario_bindings:
        fail("reasoning handoff manifest must declare scenario_bindings")

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []

    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("reasoning handoff manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail("reasoning handoff manifest source_inputs must keep name, repo, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate reasoning handoff source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        if not manifest_input_path(normalized_input).exists():
            fail(f"reasoning handoff donor input does not exist: {repo_ref(repo, path)}")

        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    guardrail_doc_input = inputs_by_name.get("reasoning_handoff_doc")
    if guardrail_doc_input is None:
        fail("reasoning handoff manifest must include reasoning_handoff_doc")
    guardrail_doc_path = manifest_input_path(guardrail_doc_input)

    artifact_hook_schema = inputs_by_name.get("artifact_to_verdict_hook_schema")
    if artifact_hook_schema is None:
        fail("reasoning handoff manifest must include artifact_to_verdict_hook_schema")
    hook_schema_payload = read_json(manifest_input_path(artifact_hook_schema))
    if not isinstance(hook_schema_payload, dict):
        fail("artifact_to_verdict_hook_schema must be a JSON object")

    guardrail_text = read_text(guardrail_doc_path)
    query_modes = extract_query_modes_from_doc(guardrail_doc_path)
    return_contract = {
        "must_include": extract_bullets_after_marker(
            guardrail_text,
            "Every reasoning handoff should be able to return:",
        ),
        "may_include": extract_bullets_after_marker(
            guardrail_text,
            "It may also return:",
        ),
        "normalized_return_fields": ["axis_summary"],
    }
    boundary_guardrails = extract_boundary_guardrails_from_doc(guardrail_doc_path)

    scenarios = [
        build_reasoning_handoff_scenario(
            binding,
            inputs_by_name,
            query_modes,
            return_contract,
            boundary_guardrails,
        )
        for binding in scenario_bindings
        if isinstance(binding, dict)
    ]
    if len(scenarios) != len(scenario_bindings):
        fail("reasoning handoff manifest scenario_bindings entries must be objects")

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": "manifests/reasoning_handoff_pack.json",
        "source_inputs": emitted_source_inputs,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def write_generated_outputs() -> list[Path]:
    registry_payload = build_registry_payload()
    technique_lift_pack_payload = build_technique_lift_pack_payload(registry_payload)
    reasoning_handoff_pack_payload = build_reasoning_handoff_pack_payload()

    write_json(REGISTRY_OUTPUT_PATH, registry_payload, pretty=True)
    write_json(REGISTRY_MIN_OUTPUT_PATH, registry_payload, pretty=False)
    write_json(TECHNIQUE_LIFT_OUTPUT_PATH, technique_lift_pack_payload, pretty=True)
    write_json(TECHNIQUE_LIFT_MIN_OUTPUT_PATH, technique_lift_pack_payload, pretty=False)
    write_json(REASONING_HANDOFF_OUTPUT_PATH, reasoning_handoff_pack_payload, pretty=True)
    write_json(
        REASONING_HANDOFF_MIN_OUTPUT_PATH,
        reasoning_handoff_pack_payload,
        pretty=False,
    )

    return [
        REGISTRY_OUTPUT_PATH,
        REGISTRY_MIN_OUTPUT_PATH,
        TECHNIQUE_LIFT_OUTPUT_PATH,
        TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
        REASONING_HANDOFF_OUTPUT_PATH,
        REASONING_HANDOFF_MIN_OUTPUT_PATH,
    ]
