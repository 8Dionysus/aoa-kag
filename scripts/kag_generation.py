#!/usr/bin/env python3
from __future__ import annotations

import csv
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
TREE_OF_SOPHIA_ROOT = repo_root_from_env(
    "TREE_OF_SOPHIA_ROOT", REPO_ROOT.parent / "Tree-of-Sophia"
)

REGISTRY_MANIFEST_PATH = REPO_ROOT / "manifests" / "kag_registry.json"
TECHNIQUE_LIFT_MANIFEST_PATH = REPO_ROOT / "manifests" / "technique_lift_pack.json"
TOS_TEXT_CHUNK_MAP_MANIFEST_PATH = REPO_ROOT / "manifests" / "tos_text_chunk_map.json"
TOS_RETRIEVAL_AXIS_MANIFEST_PATH = (
    REPO_ROOT / "manifests" / "tos_retrieval_axis_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_PATH = (
    REPO_ROOT / "manifests" / "tos_zarathustra_route_pack.json"
)
REASONING_HANDOFF_MANIFEST_PATH = REPO_ROOT / "manifests" / "reasoning_handoff_pack.json"
SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_PATH = (
    REPO_ROOT / "manifests" / "source_owned_export_dependencies.json"
)
FEDERATION_SPINE_MANIFEST_PATH = REPO_ROOT / "manifests" / "federation_spine.json"
CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH = (
    REPO_ROOT / "manifests" / "cross_source_node_projection.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH = (
    REPO_ROOT / "manifests" / "counterpart_federation_exposure_review.json"
)
TINY_CONSUMER_BUNDLE_MANIFEST_PATH = (
    REPO_ROOT / "manifests" / "tiny_consumer_bundle.json"
)
RETURN_REGROUNDING_MANIFEST_PATH = (
    REPO_ROOT / "manifests" / "return_regrounding_pack.json"
)
REASONING_HANDOFF_GUARDRAIL_PATH = REPO_ROOT / "docs" / "REASONING_HANDOFF.md"
REASONING_HANDOFF_GUARDRAIL_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "reasoning-handoff-guardrail.schema.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_PATH = (
    REPO_ROOT / "docs" / "COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md"
)
COUNTERPART_CONSUMER_CONTRACT_DOC_PATH = (
    REPO_ROOT / "docs" / "COUNTERPART_CONSUMER_CONTRACT.md"
)
COUNTERPART_CONSUMER_CONTRACT_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "counterpart-consumer-contract.schema.json"
)
COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH = (
    REPO_ROOT / "examples" / "counterpart_consumer_contract.example.json"
)

REGISTRY_OUTPUT_PATH = REPO_ROOT / "generated" / "kag_registry.json"
REGISTRY_MIN_OUTPUT_PATH = REPO_ROOT / "generated" / "kag_registry.min.json"
TECHNIQUE_LIFT_OUTPUT_PATH = REPO_ROOT / "generated" / "technique_lift_pack.json"
TECHNIQUE_LIFT_MIN_OUTPUT_PATH = REPO_ROOT / "generated" / "technique_lift_pack.min.json"
TOS_TEXT_CHUNK_MAP_OUTPUT_PATH = REPO_ROOT / "generated" / "tos_text_chunk_map.json"
TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "tos_text_chunk_map.min.json"
)
TOS_RETRIEVAL_AXIS_OUTPUT_PATH = REPO_ROOT / "generated" / "tos_retrieval_axis_pack.json"
TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "tos_retrieval_axis_pack.min.json"
)
TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "tos_zarathustra_route_pack.json"
)
TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "tos_zarathustra_route_pack.min.json"
)
REASONING_HANDOFF_OUTPUT_PATH = REPO_ROOT / "generated" / "reasoning_handoff_pack.json"
REASONING_HANDOFF_MIN_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "reasoning_handoff_pack.min.json"
)
FEDERATION_SPINE_OUTPUT_PATH = REPO_ROOT / "generated" / "federation_spine.json"
FEDERATION_SPINE_MIN_OUTPUT_PATH = REPO_ROOT / "generated" / "federation_spine.min.json"
CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "cross_source_node_projection.json"
)
CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "cross_source_node_projection.min.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "counterpart_federation_exposure_review.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "counterpart_federation_exposure_review.min.json"
)
TINY_CONSUMER_BUNDLE_OUTPUT_PATH = REPO_ROOT / "generated" / "tiny_consumer_bundle.json"
TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "tiny_consumer_bundle.min.json"
)
RETURN_REGROUNDING_OUTPUT_PATH = REPO_ROOT / "generated" / "return_regrounding_pack.json"
RETURN_REGROUNDING_MIN_OUTPUT_PATH = (
    REPO_ROOT / "generated" / "return_regrounding_pack.min.json"
)

QUERY_MODE_HEADING = re.compile(r"^###\s+`([^`]+)`\s*$")
TOS_REPO = "Tree-of-Sophia"
KNOWN_REPO_ROOTS = {
    "aoa-kag": REPO_ROOT,
    "aoa-techniques": AOA_TECHNIQUES_ROOT,
    "aoa-playbooks": AOA_PLAYBOOKS_ROOT,
    "aoa-evals": AOA_EVALS_ROOT,
    "aoa-memo": AOA_MEMO_ROOT,
    "aoa-agents": AOA_AGENTS_ROOT,
    TOS_REPO: TREE_OF_SOPHIA_ROOT,
}
TOS_ROOT_README_PATH = "README.md"
TOS_TINY_ENTRY_DOCTRINE_PATH = "docs/TINY_ENTRY_ROUTE.md"
TOS_TINY_ENTRY_ROUTE_PATH = "examples/tos_tiny_entry_route.example.json"
TOS_TINY_ENTRY_ROUTE_ID = "tos-tiny-entry.zarathustra-prologue"
TOS_TINY_ENTRY_CAPSULE_PATH = "docs/ZARATHUSTRA_TRILINGUAL_ENTRY.md"
TOS_TINY_ENTRY_AUTHORITY_PATH = "examples/source_node.example.json"
TOS_TINY_ENTRY_PRIMARY_HOP_FIELD = "bounded_hop"
TOS_TINY_ENTRY_LEGACY_HOP_FIELD = "lineage_or_context_hop"
TOS_TINY_ENTRY_HOP_PATH = "examples/concept_node.example.json"
TOS_TINY_ENTRY_FALLBACK_PATH = "docs/KNOWLEDGE_MODEL.md"
TOS_ZARATHUSTRA_ROUTE_ID = "thus-spoke-zarathustra/prologue-1"
TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH = "docs/ZARATHUSTRA_TRILINGUAL_ENTRY.md"
TOS_ZARATHUSTRA_ROUTE_SOURCE_NODE_PATH = (
    "tree/source/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1/node.json"
)
TOS_ZARATHUSTRA_ROUTE_BECOMING_CONCEPT_PATH = "tree/concept/becoming/node.json"
TOS_ZARATHUSTRA_ROUTE_OVERCOMING_CONCEPT_PATH = "tree/concept/overcoming/node.json"
TOS_ZARATHUSTRA_ROUTE_LINEAGE_NODE_PATH = (
    "tree/lineage/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1/"
    "becoming-to-overcoming/node.json"
)
TOS_ZARATHUSTRA_ROUTE_PRINCIPLE_ROOT = (
    "tree/principle/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_EVENT_ROOT = (
    "tree/event/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_STATE_ROOT = (
    "tree/state/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_SUPPORT_ROOT = (
    "tree/support/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_ANALOGY_ROOT = (
    "tree/analogy/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_SYNTHESIS_ROOT = (
    "tree/synthesis/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1"
)
TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH = (
    "tree/relations/friedrich-nietzsche/thus-spoke-zarathustra/prologue-1/edges.csv"
)
TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER = [
    "source",
    "concept",
    "principle",
    "lineage",
    "event",
    "state",
    "support",
    "analogy",
    "synthesis",
]
TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS = {
    "source": 1,
    "concept": 2,
    "principle": 13,
    "lineage": 1,
    "event": 18,
    "state": 9,
    "support": 46,
    "analogy": 1,
    "synthesis": 1,
}
TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS = {
    "source_edge": 92,
    "bridge_edge": 11,
    "principle_edge": 22,
}
REASONING_HANDOFF_GUARDRAIL_REF = "docs/REASONING_HANDOFF.md"
REASONING_HANDOFF_GUARDRAIL_SCHEMA_REF = (
    "schemas/reasoning-handoff-guardrail.schema.json"
)
COUNTERPART_EDGE_CONTRACT_DOC_REF = "docs/COUNTERPART_EDGE_CONTRACTS.md"
COUNTERPART_EDGE_SCHEMA_REF = "schemas/counterpart-edge-surface.schema.json"
COUNTERPART_EDGE_EXAMPLE_REF = "examples/counterpart_edge_view.example.json"
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF = (
    "docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_REF = (
    "manifests/counterpart_federation_exposure_review.json"
)
COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF = (
    "generated/counterpart_federation_exposure_review.min.json"
)
COUNTERPART_CONSUMER_CONTRACT_DOC_REF = "docs/COUNTERPART_CONSUMER_CONTRACT.md"
COUNTERPART_CONSUMER_CONTRACT_SCHEMA_REF = (
    "schemas/counterpart-consumer-contract.schema.json"
)
COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF = (
    "examples/counterpart_consumer_contract.example.json"
)
TINY_CONSUMER_BUNDLE_MANIFEST_REF = "manifests/tiny_consumer_bundle.json"
RETURN_REGROUNDING_MODE_ORDER = [
    "source_export_reentry",
    "bridge_axis_reentry",
    "projection_boundary_reentry",
    "handoff_guardrail_reentry",
    "owner_boundary_reentry",
]
RETURN_REGROUNDING_EXPECTED_INPUT_REFS = {
    "boundaries_doc": "docs/BOUNDARIES.md",
    "bridge_contract_doc": "docs/BRIDGE_CONTRACTS.md",
    "reasoning_handoff_doc": "docs/REASONING_HANDOFF.md",
    "source_owned_export_dependencies_manifest": "manifests/source_owned_export_dependencies.json",
    "federation_spine_pack": "generated/federation_spine.min.json",
    "retrieval_axis_pack": "generated/tos_retrieval_axis_pack.min.json",
    "cross_source_projection_pack": "generated/cross_source_node_projection.min.json",
    "reasoning_handoff_pack": "generated/reasoning_handoff_pack.min.json",
    "aoa_techniques_kag_export": "aoa-techniques/generated/kag_export.min.json",
    "tos_kag_export": "Tree-of-Sophia/generated/kag_export.min.json",
    "tos_node_contract": "Tree-of-Sophia/docs/NODE_CONTRACT.md",
    "tos_source_node": "Tree-of-Sophia/examples/source_node.example.json",
    "memo_checkpoint_contract": "aoa-memo/examples/checkpoint_to_memory_contract.example.json",
}
RETURN_REGROUNDING_ALLOWED_SAME_RUN_INPUTS = {
    "generated/federation_spine.min.json",
    "generated/tos_retrieval_axis_pack.min.json",
    "generated/cross_source_node_projection.min.json",
    "generated/reasoning_handoff_pack.min.json",
}
RETURN_REGROUNDING_EXPECTED_REGISTRY_POSTURE = {
    "AOA-K-0006": "experimental",
    "AOA-K-0007": "experimental",
    "AOA-K-0008": "planned",
    "AOA-K-0009": "experimental",
}
RETURN_REGROUNDING_MODE_DETAILS = {
    "source_export_reentry": {
        "primary_input": "federation_spine_pack",
        "supporting_inputs": [
            "source_owned_export_dependencies_manifest",
            "aoa_techniques_kag_export",
            "tos_kag_export",
        ],
        "dependency_refs": [
            "aoa-techniques-kag-export",
            "tree-of-sophia-kag-export",
        ],
        "used_when": (
            "Use this mode when a caller needs the strongest current federation "
            "entry back to source-owned export capsules before wider derived "
            "synthesis resumes."
        ),
        "query_mode_hint": "local_search",
        "trigger_surface_refs": [
            "generated/federation_spine.min.json",
            "generated/reasoning_handoff_pack.min.json",
        ],
        "stronger_refs": [
            "aoa-techniques/generated/kag_export.min.json",
            "Tree-of-Sophia/generated/kag_export.min.json",
        ],
        "supporting_surface_refs": [
            "manifests/source_owned_export_dependencies.json",
            "docs/SOURCE_OWNED_EXPORT_DEPENDENCIES.md",
        ],
        "preserved_fields": [
            "provenance_note",
            "non_identity_boundary",
            "entry_surface_ref",
        ],
        "reentry_note": (
            "Return through the source-owned export capsule and its declared "
            "entry surface before asking the derived layer for broader synthesis."
        ),
        "non_identity_boundary": (
            "The federation spine is a guide to source-owned export entry and "
            "does not replace authored technique meaning or ToS authority."
        ),
        "prohibited_promotions": [
            "source_replacement",
            "routing_ownership",
            "canon_authorship",
        ],
    },
    "bridge_axis_reentry": {
        "primary_input": "retrieval_axis_pack",
        "supporting_inputs": [
            "bridge_contract_doc",
            "tos_node_contract",
            "tos_source_node",
        ],
        "dependency_refs": [],
        "used_when": (
            "Use this mode when retrieval drift appears in the ToS bridge path "
            "and the caller needs explicit source, lineage, conflict, practice, "
            "or memo-linked handles again."
        ),
        "query_mode_hint": "global_search",
        "trigger_surface_refs": [
            "generated/tos_retrieval_axis_pack.min.json",
            "examples/tos_retrieval_axis_surface.example.json",
            "docs/BRIDGE_CONTRACTS.md",
        ],
        "stronger_refs": [
            "Tree-of-Sophia/examples/source_node.example.json",
            "Tree-of-Sophia/docs/NODE_CONTRACT.md",
            "Tree-of-Sophia/docs/PRACTICE_BRANCH.md",
        ],
        "supporting_surface_refs": [
            "examples/aoa_tos_bridge_envelope.example.json",
            "aoa-memo/examples/memory_chunk_face.bridge.example.json",
            "aoa-memo/examples/memory_graph_face.bridge.example.json",
        ],
        "preserved_fields": [
            "source_refs",
            "lineage_refs",
            "conflict_refs",
            "practice_refs",
            "axis_summary",
        ],
        "reentry_note": (
            "Return through the retrieval-axis pack so the next pass keeps "
            "bounded handles back to stronger authored surfaces instead of "
            "inventing a wider hidden synthesis."
        ),
        "non_identity_boundary": (
            "The retrieval axis remains a derived bridge surface and does not "
            "replace authored ToS meaning, routing, or proof."
        ),
        "prohibited_promotions": [
            "source_replacement",
            "routing_ownership",
            "graph_normalization",
        ],
    },
    "projection_boundary_reentry": {
        "primary_input": "cross_source_projection_pack",
        "supporting_inputs": [
            "federation_spine_pack",
            "retrieval_axis_pack",
            "bridge_contract_doc",
        ],
        "dependency_refs": [
            "aoa-techniques-kag-export",
            "tree-of-sophia-kag-export",
        ],
        "used_when": (
            "Use this mode when a cross-source projection is being mistaken for "
            "identity, ontology merger, counterpart activation, or graph "
            "expansion."
        ),
        "query_mode_hint": "drift_search",
        "trigger_surface_refs": [
            "generated/cross_source_node_projection.min.json",
            "docs/CROSS_SOURCE_NODE_PROJECTION.md",
        ],
        "stronger_refs": [
            "aoa-techniques/generated/kag_export.min.json",
            "Tree-of-Sophia/generated/kag_export.min.json",
        ],
        "supporting_surface_refs": [
            "generated/federation_spine.min.json",
            "generated/tos_retrieval_axis_pack.min.json",
            "docs/COUNTERPART_FEDERATION_EXPOSURE_REVIEW.md",
        ],
        "preserved_fields": [
            "primary_input",
            "supporting_inputs",
            "retrieval_axis_ref",
            "federation_spine_ref",
            "non_identity_boundary",
        ],
        "reentry_note": (
            "Return through the one-hop projection boundary, then step back to "
            "the source-owned exports and the retrieval axis before any broader "
            "cross-source claim is allowed."
        ),
        "non_identity_boundary": (
            "A cross-source projection is a one-hop pairing, not identity, "
            "counterpart activation, ontology merger, or graph sovereignty."
        ),
        "prohibited_promotions": [
            "counterpart_activation",
            "graph_expansion",
            "source_replacement",
        ],
    },
    "handoff_guardrail_reentry": {
        "primary_input": "reasoning_handoff_pack",
        "supporting_inputs": [
            "reasoning_handoff_doc",
            "boundaries_doc",
            "memo_checkpoint_contract",
        ],
        "dependency_refs": [],
        "used_when": (
            "Use this mode when runtime-to-KAG handoff begins to overreach into "
            "routing, memory truth, proof, or canon authorship instead of "
            "staying a guide to stronger refs."
        ),
        "query_mode_hint": "global_search",
        "trigger_surface_refs": [
            "docs/REASONING_HANDOFF.md",
            "examples/reasoning_handoff_guardrail.example.json",
            "generated/reasoning_handoff_pack.min.json",
        ],
        "stronger_refs": [
            "aoa-playbooks/playbooks/long-horizon-model-tier-orchestra/PLAYBOOK.md",
            "aoa-playbooks/playbooks/restartable-inquiry-loop/PLAYBOOK.md",
            "aoa-evals/bundles/aoa-long-horizon-depth/EVAL.md",
            "aoa-memo/examples/checkpoint_to_memory_contract.example.json",
        ],
        "supporting_surface_refs": [
            "schemas/reasoning-handoff-guardrail.schema.json",
            "docs/BOUNDARIES.md",
        ],
        "preserved_fields": [
            "source_refs",
            "axis_summary",
            "provenance_note",
            "boundary_guardrails",
        ],
        "reentry_note": (
            "Return to the stronger scenario, eval, and memo refs already named "
            "by the handoff pack rather than extending KAG guidance into "
            "someone else's ownership."
        ),
        "non_identity_boundary": (
            "Reasoning handoff stays a derived guide to source and owner "
            "surfaces, not a new owner of routing, proof, memory truth, or "
            "canon."
        ),
        "prohibited_promotions": [
            "routing_ownership",
            "memory_truth_ownership",
            "canon_authorship",
            "proof_ownership",
        ],
    },
    "owner_boundary_reentry": {
        "primary_input": "reasoning_handoff_doc",
        "supporting_inputs": [
            "bridge_contract_doc",
            "boundaries_doc",
            "memo_checkpoint_contract",
            "tos_node_contract",
        ],
        "dependency_refs": [],
        "used_when": (
            "Use this mode when a caller reaches writeback, memory commitment, "
            "or canon-facing mutation and KAG must stop at the owner boundary."
        ),
        "query_mode_hint": "consumer_read_path",
        "trigger_surface_refs": [
            "docs/BRIDGE_CONTRACTS.md",
            "docs/REASONING_HANDOFF.md",
            "docs/BOUNDARIES.md",
        ],
        "stronger_refs": [
            "aoa-memo/examples/checkpoint_to_memory_contract.example.json",
            "Tree-of-Sophia/docs/NODE_CONTRACT.md",
            "Tree-of-Sophia/examples/source_node.example.json",
        ],
        "supporting_surface_refs": [
            "generated/reasoning_handoff_pack.min.json",
            "examples/aoa_tos_bridge_envelope.example.json",
        ],
        "preserved_fields": [
            "source_refs",
            "provenance_note",
            "boundary_guardrails",
        ],
        "reentry_note": (
            "KAG may prepare bounded guidance, but when the next move becomes "
            "memory writeback or canon mutation the caller must return to the "
            "owner surface instead of extending derived synthesis."
        ),
        "non_identity_boundary": (
            "Derived bridge substrate does not own memory truth or canon "
            "authorship and must stop at the owner boundary."
        ),
        "prohibited_promotions": [
            "memory_truth_ownership",
            "canon_authorship",
            "source_replacement",
        ],
    },
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        fail(f"missing required file: {path.as_posix()}")


def require_string_list(value: object, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        fail(f"{label} must be a non-empty list")
    normalized: list[str] = []
    for index, item in enumerate(value):
        normalized.append(require_string(item, label=f"{label}[{index}]"))
    return normalized


def require_string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def require_optional_string(value: object, *, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        fail(f"{label} must be a string when present")
    return value


def ensure_repo_relative_path(raw_path: object, *, label: str) -> str:
    value = require_string(raw_path, label=label).replace("\\", "/")
    if re.match(r"^[A-Za-z]:[/\\\\]", value) or value.startswith(("/", "\\")):
        fail(f"{label} must be repo-relative")
    if ".." in Path(value).parts:
        fail(f"{label} must not traverse outside the repository root")
    return value


def ensure_tos_relative_surface_path(raw_path: object, *, label: str) -> str:
    relative_path = ensure_repo_relative_path(raw_path, label=label)
    if ":" in relative_path:
        fail(f"{label} must stay Tree-of-Sophia-relative and must not use repo-qualified refs")
    if relative_path.startswith(("aoa-kag/", "aoa-routing/")):
        fail(f"{label} must stay inside Tree-of-Sophia and must not point at downstream repos")
    if not (TREE_OF_SOPHIA_ROOT / relative_path).exists():
        fail(f"{label} target is missing inside Tree-of-Sophia: {relative_path}")
    return relative_path


def ensure_local_ref_exists(
    raw_ref: object,
    *,
    label: str,
    allow_missing_refs: set[str] | None = None,
) -> str:
    relative_ref = ensure_repo_relative_path(raw_ref, label=label)
    target = REPO_ROOT / relative_ref
    if not target.exists() and (
        allow_missing_refs is None or relative_ref not in allow_missing_refs
    ):
        fail(f"{label} target is missing: {relative_ref}")
    return relative_ref


def list_family_node_paths(root: Path) -> list[Path]:
    if not root.exists():
        fail(f"missing required family root: {root.as_posix()}")
    if not root.is_dir():
        fail(f"family root must be a directory: {root.as_posix()}")
    node_paths = sorted(root.rglob("node.json"))
    if not node_paths:
        fail(f"family root does not contain any canonical node.json files: {root.as_posix()}")
    return node_paths


def tos_authority_ref_for_path(path: Path) -> str:
    try:
        relative_path = path.resolve().relative_to(TREE_OF_SOPHIA_ROOT.resolve())
    except ValueError:
        fail(f"path must stay inside Tree-of-Sophia: {path.as_posix()}")
    return repo_ref(TOS_REPO, relative_path.as_posix())


def load_tos_route_node_entry(path: Path, *, expected_node_type: str | None = None) -> dict[str, object]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        fail(f"canonical ToS node must be a JSON object: {path.as_posix()}")

    node_id = require_string(payload.get("node_id"), label=f"{path.as_posix()}.node_id")
    node_type = require_string(
        payload.get("node_type"), label=f"{path.as_posix()}.node_type"
    )
    if expected_node_type is not None and node_type != expected_node_type:
        fail(
            f"canonical ToS node {path.as_posix()} must keep node_type "
            f"'{expected_node_type}', got '{node_type}'"
        )

    key_terms = require_string_list(
        payload.get("key_terms"), label=f"{path.as_posix()}.key_terms"
    )
    interpretation_layers = require_string_list(
        payload.get("interpretation_layers"),
        label=f"{path.as_posix()}.interpretation_layers",
    )

    return {
        "node_id": node_id,
        "node_type": node_type,
        "authority_ref": tos_authority_ref_for_path(path),
        "source_anchor": require_string(
            payload.get("source_anchor"), label=f"{path.as_posix()}.source_anchor"
        ),
        "key_terms": key_terms,
        "distilled_thesis": require_string(
            payload.get("distilled_thesis"),
            label=f"{path.as_posix()}.distilled_thesis",
        ),
        "interpretation_layers": interpretation_layers,
    }


def load_tos_route_family_entries(
    root_relative_path: str, *, expected_node_type: str
) -> list[dict[str, object]]:
    root = TREE_OF_SOPHIA_ROOT / root_relative_path
    entries = [
        load_tos_route_node_entry(path, expected_node_type=expected_node_type)
        for path in list_family_node_paths(root)
    ]
    entries.sort(key=lambda entry: require_string(entry.get("node_id"), label="route family node_id"))
    return entries


def load_tos_route_relation_entries(path: Path) -> list[dict[str, object]]:
    rows = read_csv_rows(path)
    if not rows:
        fail(f"canonical ToS route relation pack must not be empty: {path.as_posix()}")

    normalized_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        location = f"{path.as_posix()} row {index + 1}"
        edge_id = require_string(row.get("edge_id"), label=f"{location}.edge_id")
        from_id = require_string(row.get("from_id"), label=f"{location}.from_id")
        to_id = require_string(row.get("to_id"), label=f"{location}.to_id")
        if not from_id.startswith("tos.") or not to_id.startswith("tos."):
            fail(f"{location} must keep canonical tos.* endpoint ids")
        if from_id.startswith("literal.") or to_id.startswith("literal."):
            fail(f"{location} must not include literal residue")

        confidence_text = require_string(
            row.get("confidence"), label=f"{location}.confidence"
        )
        try:
            confidence = int(confidence_text)
        except ValueError as exc:
            fail(f"{location}.confidence must be an integer: {exc}")

        normalized_rows.append(
            {
                "edge_id": edge_id,
                "edge_kind": require_string(
                    row.get("edge_kind"), label=f"{location}.edge_kind"
                ),
                "from_id": from_id,
                "predicate_id": require_string(
                    row.get("predicate_id"), label=f"{location}.predicate_id"
                ),
                "to_id": to_id,
                "layer": require_string(row.get("layer"), label=f"{location}.layer"),
                "anchor_mode": require_string(
                    row.get("anchor_mode"), label=f"{location}.anchor_mode"
                ),
                "anchor_start_secondary": require_optional_string(
                    row.get("anchor_start_secondary"),
                    label=f"{location}.anchor_start_secondary",
                ),
                "anchor_end_secondary": require_optional_string(
                    row.get("anchor_end_secondary"),
                    label=f"{location}.anchor_end_secondary",
                ),
                "anchor_segment_ids": require_string(
                    row.get("anchor_segment_ids"),
                    label=f"{location}.anchor_segment_ids",
                ),
                "witness_scope": require_string(
                    row.get("witness_scope"), label=f"{location}.witness_scope"
                ),
                "connectivity_role": require_string(
                    row.get("connectivity_role"),
                    label=f"{location}.connectivity_role",
                ),
                "confidence": confidence,
                "note": require_optional_string(
                    row.get("note"), label=f"{location}.note"
                ),
            }
        )
    return normalized_rows


def load_tos_tiny_entry_hop_surface(payload: dict[str, object], *, route_label: str) -> str:
    bounded_hop: str | None = None
    if payload.get(TOS_TINY_ENTRY_PRIMARY_HOP_FIELD) is not None:
        bounded_hop = ensure_tos_relative_surface_path(
            payload.get(TOS_TINY_ENTRY_PRIMARY_HOP_FIELD),
            label=f"{route_label}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD}",
        )

    legacy_hop: str | None = None
    if payload.get(TOS_TINY_ENTRY_LEGACY_HOP_FIELD) is not None:
        legacy_hop = ensure_tos_relative_surface_path(
            payload.get(TOS_TINY_ENTRY_LEGACY_HOP_FIELD),
            label=f"{route_label}.{TOS_TINY_ENTRY_LEGACY_HOP_FIELD}",
        )

    if bounded_hop is None and legacy_hop is None:
        fail(
            f"{route_label} must define '{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD}' or "
            f"'{TOS_TINY_ENTRY_LEGACY_HOP_FIELD}'"
        )
    if bounded_hop is not None and legacy_hop is not None and bounded_hop != legacy_hop:
        fail(
            f"{route_label}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD} and "
            f"{route_label}.{TOS_TINY_ENTRY_LEGACY_HOP_FIELD} must resolve to the "
            "same Tree-of-Sophia surface during transition"
        )

    hop_surface = bounded_hop or legacy_hop
    if hop_surface != TOS_TINY_ENTRY_HOP_PATH:
        fail(
            f"{route_label}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD} must stay "
            f"'{TOS_TINY_ENTRY_HOP_PATH}' in the current KAG wave"
        )
    return hop_surface


def load_tos_tiny_entry_route_payload() -> dict[str, object]:
    route_path = TREE_OF_SOPHIA_ROOT / TOS_TINY_ENTRY_ROUTE_PATH
    payload = read_json(route_path)
    if not isinstance(payload, dict):
        fail("Tree-of-Sophia tiny-entry route must be a JSON object")

    route_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)
    route_id = require_string(payload.get("route_id"), label=f"{route_label}.route_id")
    if route_id != TOS_TINY_ENTRY_ROUTE_ID:
        fail(f"{route_label}.route_id must stay '{TOS_TINY_ENTRY_ROUTE_ID}' in the current KAG wave")

    root_surface = ensure_tos_relative_surface_path(
        payload.get("root_surface"),
        label=f"{route_label}.root_surface",
    )
    if root_surface != TOS_ROOT_README_PATH:
        fail(f"{route_label}.root_surface must stay '{TOS_ROOT_README_PATH}'")

    require_string(payload.get("node_kind"), label=f"{route_label}.node_kind")
    require_string(payload.get("node_id"), label=f"{route_label}.node_id")

    capsule_surface = ensure_tos_relative_surface_path(
        payload.get("capsule_surface"),
        label=f"{route_label}.capsule_surface",
    )
    if capsule_surface != TOS_TINY_ENTRY_CAPSULE_PATH:
        fail(f"{route_label}.capsule_surface must stay '{TOS_TINY_ENTRY_CAPSULE_PATH}'")

    authority_surface = ensure_tos_relative_surface_path(
        payload.get("authority_surface"),
        label=f"{route_label}.authority_surface",
    )
    if authority_surface != TOS_TINY_ENTRY_AUTHORITY_PATH:
        fail(f"{route_label}.authority_surface must stay '{TOS_TINY_ENTRY_AUTHORITY_PATH}'")

    load_tos_tiny_entry_hop_surface(payload, route_label=route_label)

    fallback = ensure_tos_relative_surface_path(
        payload.get("fallback"),
        label=f"{route_label}.fallback",
    )
    if fallback != TOS_TINY_ENTRY_FALLBACK_PATH:
        fail(f"{route_label}.fallback must stay '{TOS_TINY_ENTRY_FALLBACK_PATH}'")

    boundary = require_string(
        payload.get("non_identity_boundary"),
        label=f"{route_label}.non_identity_boundary",
    )
    if "aoa-kag" not in boundary or "aoa-routing" not in boundary:
        fail(
            f"{route_label}.non_identity_boundary must explicitly keep aoa-kag and aoa-routing downstream"
        )

    return payload


def load_tos_source_node_payload() -> dict[str, object]:
    source_node_path = TREE_OF_SOPHIA_ROOT / TOS_TINY_ENTRY_AUTHORITY_PATH
    payload = read_json(source_node_path)
    if not isinstance(payload, dict):
        fail("Tree-of-Sophia source node authority surface must be a JSON object")

    source_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_AUTHORITY_PATH)
    route_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)
    route_payload = load_tos_tiny_entry_route_payload()
    expected_node_id = require_string(
        route_payload.get("node_id"),
        label=f"{route_label}.node_id",
    )

    node_id = require_string(payload.get("node_id"), label=f"{source_label}.node_id")
    if node_id != expected_node_id:
        fail(f"{source_label}.node_id must stay aligned with {route_label}.node_id")

    node_type = require_string(
        payload.get("node_type"),
        label=f"{source_label}.node_type",
    )
    if node_type != "source":
        fail(f"{source_label}.node_type must stay 'source' in the current KAG wave")

    require_string(
        payload.get("source_anchor"),
        label=f"{source_label}.source_anchor",
    )

    interpretation_layers = payload.get("interpretation_layers")
    if not isinstance(interpretation_layers, list) or not interpretation_layers:
        fail(f"{source_label}.interpretation_layers must be a non-empty list")
    for index, interpretation_layer in enumerate(interpretation_layers):
        if not isinstance(interpretation_layer, str) or not interpretation_layer:
            fail(
                f"{source_label}.interpretation_layers[{index}] must be a non-empty string"
            )

    language_witnesses = payload.get("language_witnesses")
    if not isinstance(language_witnesses, list) or not language_witnesses:
        fail(f"{source_label}.language_witnesses must be a non-empty list")

    translation_tensions = payload.get("translation_tensions", [])
    if translation_tensions is not None and not isinstance(translation_tensions, list):
        fail(f"{source_label}.translation_tensions must be a list when present")

    return payload


def load_source_owned_export_dependencies(
) -> tuple[dict[str, dict[str, object]], dict[tuple[str, str], dict[str, object]]]:
    payload = read_json(SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("source-owned export dependency manifest must be a JSON object")

    manifest_version = payload.get("manifest_version")
    contract_type = payload.get("contract_type")
    dependencies = payload.get("dependencies")
    if manifest_version != 1:
        fail("source-owned export dependency manifest manifest_version must equal 1")
    if contract_type != "source_owned_export_dependencies":
        fail(
            "source-owned export dependency manifest contract_type must equal "
            "'source_owned_export_dependencies'"
        )
    if not isinstance(dependencies, list) or not dependencies:
        fail("source-owned export dependency manifest must declare dependencies")

    dependencies_by_id: dict[str, dict[str, object]] = {}
    dependencies_by_source: dict[tuple[str, str], dict[str, object]] = {}
    for index, dependency in enumerate(dependencies):
        location = f"source-owned export dependency manifest dependencies[{index}]"
        if not isinstance(dependency, dict):
            fail(f"{location} must be an object")

        dependency_id = require_string(
            dependency.get("dependency_id"),
            label=f"{location}.dependency_id",
        )
        repo = require_string(dependency.get("repo"), label=f"{location}.repo")
        path = ensure_repo_relative_path(dependency.get("path"), label=f"{location}.path")
        expected_owner_repo = require_string(
            dependency.get("expected_owner_repo"),
            label=f"{location}.expected_owner_repo",
        )
        expected_kind = require_string(
            dependency.get("expected_kind"),
            label=f"{location}.expected_kind",
        )
        expected_object_id = require_string(
            dependency.get("expected_object_id"),
            label=f"{location}.expected_object_id",
        )
        required_fields = dependency.get("required_fields")
        if not isinstance(required_fields, list) or not required_fields:
            fail(f"{location}.required_fields must be a non-empty list")
        normalized_required_fields: list[str] = []
        for field_index, field_name in enumerate(required_fields):
            normalized_required_fields.append(
                require_string(
                    field_name,
                    label=f"{location}.required_fields[{field_index}]",
                )
            )
        if len(set(normalized_required_fields)) != len(normalized_required_fields):
            fail(f"{location}.required_fields must not contain duplicates")

        entry_surface = dependency.get("entry_surface")
        if not isinstance(entry_surface, dict):
            fail(f"{location}.entry_surface must be an object")
        entry_surface_repo = require_string(
            entry_surface.get("repo"),
            label=f"{location}.entry_surface.repo",
        )
        entry_surface_path = ensure_repo_relative_path(
            entry_surface.get("path"),
            label=f"{location}.entry_surface.path",
        )
        entry_match_key = require_string(
            entry_surface.get("match_key"),
            label=f"{location}.entry_surface.match_key",
        )
        entry_match_value = require_string(
            entry_surface.get("match_value"),
            label=f"{location}.entry_surface.match_value",
        )
        if entry_match_value != expected_object_id:
            fail(
                f"{location}.entry_surface.match_value must equal "
                f"{location}.expected_object_id"
            )

        consumed_by = dependency.get("consumed_by")
        if not isinstance(consumed_by, list) or not consumed_by:
            fail(f"{location}.consumed_by must be a non-empty list")
        normalized_consumed_by: list[str] = []
        for consumer_index, consumer_surface_id in enumerate(consumed_by):
            normalized_consumed_by.append(
                require_string(
                    consumer_surface_id,
                    label=f"{location}.consumed_by[{consumer_index}]",
                )
            )
        if len(set(normalized_consumed_by)) != len(normalized_consumed_by):
            fail(f"{location}.consumed_by must not contain duplicates")

        if expected_owner_repo != repo:
            fail(
                f"{location}.expected_owner_repo must equal {location}.repo in the "
                "current source-owned export contract"
            )
        if entry_surface_repo != expected_owner_repo:
            fail(
                f"{location}.entry_surface.repo must equal {location}.expected_owner_repo"
            )

        if dependency_id in dependencies_by_id:
            fail(f"{location}.dependency_id '{dependency_id}' is duplicated")
        source_key = (repo, path)
        if source_key in dependencies_by_source:
            fail(
                f"{location} duplicates repo/path dependency target "
                f"'{repo_ref(repo, path)}'"
            )

        if not resolve_repo_path(repo, path).exists():
            fail(f"{location}.path target is missing: {repo_ref(repo, path)}")
        if not resolve_repo_path(entry_surface_repo, entry_surface_path).exists():
            fail(
                f"{location}.entry_surface.path target is missing: "
                f"{repo_ref(entry_surface_repo, entry_surface_path)}"
            )

        normalized_dependency = {
            "dependency_id": dependency_id,
            "repo": repo,
            "path": path,
            "expected_owner_repo": expected_owner_repo,
            "expected_kind": expected_kind,
            "expected_object_id": expected_object_id,
            "required_fields": normalized_required_fields,
            "entry_surface": {
                "repo": entry_surface_repo,
                "path": entry_surface_path,
                "match_key": entry_match_key,
                "match_value": entry_match_value,
            },
            "consumed_by": normalized_consumed_by,
        }
        dependencies_by_id[dependency_id] = normalized_dependency
        dependencies_by_source[source_key] = normalized_dependency

    return dependencies_by_id, dependencies_by_source


def dependency_for_source_input(
    source_input: dict[str, str],
    *,
    consumer_surface_id: str,
) -> dict[str, object]:
    _, dependencies_by_source = load_source_owned_export_dependencies()
    source_key = (source_input["repo"], source_input["path"])
    dependency = dependencies_by_source.get(source_key)
    if dependency is None:
        fail(
            f"{consumer_surface_id} source input '{manifest_input_ref(source_input)}' "
            "must map to a declared source-owned export dependency"
        )

    dependency_id = require_string(
        dependency.get("dependency_id"),
        label=f"{consumer_surface_id} dependency_id",
    )
    consumed_by = dependency.get("consumed_by")
    if not isinstance(consumed_by, list) or consumer_surface_id not in consumed_by:
        fail(
            f"source-owned export dependency '{dependency_id}' must declare "
            f"'{consumer_surface_id}' in consumed_by"
        )
    return dependency


def load_federation_export_payload(
    source_input: dict[str, str],
    *,
    dependency: dict[str, object],
    consumer_surface_id: str,
) -> dict[str, object]:
    dependency_id = require_string(
        dependency.get("dependency_id"),
        label=f"{consumer_surface_id} dependency_id",
    )
    expected_repo = require_string(
        dependency.get("expected_owner_repo"),
        label=f"{dependency_id}.expected_owner_repo",
    )
    expected_kind = require_string(
        dependency.get("expected_kind"),
        label=f"{dependency_id}.expected_kind",
    )
    expected_object_id = require_string(
        dependency.get("expected_object_id"),
        label=f"{dependency_id}.expected_object_id",
    )
    dependency_repo = require_string(dependency.get("repo"), label=f"{dependency_id}.repo")
    dependency_path = ensure_repo_relative_path(
        dependency.get("path"),
        label=f"{dependency_id}.path",
    )
    required_fields = dependency.get("required_fields")
    dependency_entry_surface = dependency.get("entry_surface")
    if not isinstance(required_fields, list) or not required_fields:
        fail(f"source-owned export dependency '{dependency_id}' must keep required_fields")
    if not isinstance(dependency_entry_surface, dict):
        fail(f"source-owned export dependency '{dependency_id}' must keep entry_surface")

    if (
        source_input["repo"] != dependency_repo
        or source_input["path"] != dependency_path
    ):
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"must stay aligned with '{manifest_input_ref(source_input)}'"
        )

    payload = read_json(manifest_input_path(source_input))
    if not isinstance(payload, dict):
        fail(f"{manifest_input_ref(source_input)} must be a JSON object")

    for index, key in enumerate(required_fields):
        field_name = require_string(
            key,
            label=f"{dependency_id}.required_fields[{index}]",
        )
        if field_name not in payload:
            fail(
                f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
                f"is missing required key '{field_name}' in {manifest_input_ref(source_input)}"
            )

    owner_repo = require_string(
        payload.get("owner_repo"),
        label=f"{manifest_input_ref(source_input)}.owner_repo",
    )
    kind = require_string(
        payload.get("kind"),
        label=f"{manifest_input_ref(source_input)}.kind",
    )
    object_id = require_string(
        payload.get("object_id"),
        label=f"{manifest_input_ref(source_input)}.object_id",
    )
    if owner_repo != expected_repo:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.owner_repo to equal "
            f"'{expected_repo}'"
        )
    if kind != expected_kind:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.kind to equal '{expected_kind}'"
        )
    if object_id != expected_object_id:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.object_id to equal "
            f"'{expected_object_id}'"
        )

    source_inputs = payload.get("source_inputs")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail(f"{manifest_input_ref(source_input)}.source_inputs must be a non-empty list")
    primary_count = 0
    for index, export_source_input in enumerate(source_inputs):
        location = f"{manifest_input_ref(source_input)}.source_inputs[{index}]"
        if not isinstance(export_source_input, dict):
            fail(f"{location} must be an object")
        repo = require_string(export_source_input.get("repo"), label=f"{location}.repo")
        require_string(
            export_source_input.get("source_class"),
            label=f"{location}.source_class",
        )
        role = require_string(export_source_input.get("role"), label=f"{location}.role")
        if role == "primary":
            primary_count += 1
        if role not in {"primary", "supporting"}:
            fail(f"{location}.role must be 'primary' or 'supporting'")
        if repo != expected_repo:
            fail(f"{location}.repo must equal '{expected_repo}' in the current pilot export")
    if primary_count != 1:
        fail(f"{manifest_input_ref(source_input)}.source_inputs must contain exactly one primary input")

    payload_entry_surface = payload.get("entry_surface")
    if not isinstance(payload_entry_surface, dict):
        fail(f"{manifest_input_ref(source_input)}.entry_surface must be an object")
    entry_repo = require_string(
        payload_entry_surface.get("repo"),
        label=f"{manifest_input_ref(source_input)}.entry_surface.repo",
    )
    entry_path = require_string(
        payload_entry_surface.get("path"),
        label=f"{manifest_input_ref(source_input)}.entry_surface.path",
    )
    match_key = require_string(
        payload_entry_surface.get("match_key"),
        label=f"{manifest_input_ref(source_input)}.entry_surface.match_key",
    )
    match_value = require_string(
        payload_entry_surface.get("match_value"),
        label=f"{manifest_input_ref(source_input)}.entry_surface.match_value",
    )
    dependency_entry_repo = require_string(
        dependency_entry_surface.get("repo"),
        label=f"{dependency_id}.entry_surface.repo",
    )
    dependency_entry_path = ensure_repo_relative_path(
        dependency_entry_surface.get("path"),
        label=f"{dependency_id}.entry_surface.path",
    )
    dependency_match_key = require_string(
        dependency_entry_surface.get("match_key"),
        label=f"{dependency_id}.entry_surface.match_key",
    )
    dependency_match_value = require_string(
        dependency_entry_surface.get("match_value"),
        label=f"{dependency_id}.entry_surface.match_value",
    )
    if entry_repo != dependency_entry_repo:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.entry_surface.repo to equal "
            f"'{dependency_entry_repo}'"
        )
    if entry_path != dependency_entry_path:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.entry_surface.path to equal "
            f"'{dependency_entry_path}'"
        )
    if match_key != dependency_match_key:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.entry_surface.match_key to "
            f"equal '{dependency_match_key}'"
        )
    if match_value != dependency_match_value:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.entry_surface.match_value to "
            f"equal '{dependency_match_value}'"
        )
    resolve_repo_path(entry_repo, entry_path)

    section_handles = payload.get("section_handles")
    if not isinstance(section_handles, list) or not section_handles:
        fail(f"{manifest_input_ref(source_input)}.section_handles must be a non-empty list")
    direct_relations = payload.get("direct_relations")
    if not isinstance(direct_relations, list):
        fail(f"{manifest_input_ref(source_input)}.direct_relations must be a list")

    require_string(
        payload.get("summary_50"),
        label=f"{manifest_input_ref(source_input)}.summary_50",
    )
    require_string(
        payload.get("summary_200"),
        label=f"{manifest_input_ref(source_input)}.summary_200",
    )
    require_string(
        payload.get("primary_question"),
        label=f"{manifest_input_ref(source_input)}.primary_question",
    )
    require_string(
        payload.get("provenance_note"),
        label=f"{manifest_input_ref(source_input)}.provenance_note",
    )
    require_string(
        payload.get("non_identity_boundary"),
        label=f"{manifest_input_ref(source_input)}.non_identity_boundary",
    )

    return payload


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


def build_tos_text_chunk_map_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TOS_TEXT_CHUNK_MAP_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("ToS text chunk map manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")
    if manifest.get("source_repo") != TOS_REPO:
        fail("ToS text chunk map manifest source_repo must equal 'Tree-of-Sophia'")
    if manifest.get("source_root_env") != "TREE_OF_SOPHIA_ROOT":
        fail(
            "ToS text chunk map manifest source_root_env must equal 'TREE_OF_SOPHIA_ROOT'"
        )
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS text chunk map manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS text chunk map manifest must declare surface_bindings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")

    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("ToS text chunk map manifest source_inputs entries must be objects")
        name = source_input.get("name")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, path, role)):
            fail("ToS text chunk map manifest source_inputs must keep name, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate ToS text chunk map source input '{name}'")

        donor_path = TREE_OF_SOPHIA_ROOT / path
        if not donor_path.exists():
            fail(f"ToS text chunk map donor input does not exist: {repo_ref(TOS_REPO, path)}")

        normalized_input = {"path": path, "role": role}
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "role": role,
                "ref": repo_ref(TOS_REPO, path),
            }
        )

    source_node_input = inputs_by_name.get("tos_source_node")
    if source_node_input is None:
        fail("ToS text chunk map manifest must include tos_source_node")
    if source_node_input["path"] != TOS_TINY_ENTRY_AUTHORITY_PATH:
        fail(
            "ToS text chunk map manifest tos_source_node must point to the current source node authority surface"
        )

    route_doc_input = inputs_by_name.get("tos_tiny_entry_route_doc")
    if route_doc_input is None:
        fail("ToS text chunk map manifest must include tos_tiny_entry_route_doc")
    if route_doc_input["path"] != TOS_TINY_ENTRY_DOCTRINE_PATH:
        fail(
            "ToS text chunk map manifest tos_tiny_entry_route_doc must point to the current tiny-entry doctrine"
        )

    capsule_input = inputs_by_name.get("tos_zarathustra_capsule")
    if capsule_input is None:
        fail("ToS text chunk map manifest must include tos_zarathustra_capsule")
    if capsule_input["path"] != TOS_TINY_ENTRY_CAPSULE_PATH:
        fail(
            "ToS text chunk map manifest tos_zarathustra_capsule must point to the current Zarathustra capsule"
        )

    seen_surface_ids: set[str] = set()
    binding_surface: dict[str, object] | None = None
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("ToS text chunk map manifest surface_bindings entries must be objects")
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
            fail(
                "ToS text chunk map manifest surface_bindings must keep id, name, kind, slot, and source input"
            )
        if surface_id in seen_surface_ids:
            fail(f"duplicate ToS text chunk map surface binding '{surface_id}'")
        seen_surface_ids.add(surface_id)
        if source_input not in inputs_by_name:
            fail(
                f"ToS text chunk map binding '{surface_id}' references unknown source input '{source_input}'"
            )

        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(
                f"ToS text chunk map binding '{surface_id}' does not exist in the registry manifest"
            )
        if surface.get("name") != surface_name:
            fail(f"ToS text chunk map binding '{surface_id}' does not match registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(
                f"ToS text chunk map binding '{surface_id}' does not match registry derived_kind"
            )
        if surface.get("status") != "experimental":
            fail(
                f"ToS text chunk map binding '{surface_id}' must point to an experimental registry surface"
            )
        binding_surface = surface

    if binding_surface is None:
        fail("ToS text chunk map manifest must declare one experimental surface binding")

    route_payload = load_tos_tiny_entry_route_payload()
    source_node_payload = load_tos_source_node_payload()
    if require_string(
        route_payload.get("authority_surface"),
        label=f"{repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)}.authority_surface",
    ) != source_node_input["path"]:
        fail("ToS text chunk map source node must stay aligned with the tiny-entry authority surface")
    if require_string(
        route_payload.get("capsule_surface"),
        label=f"{repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)}.capsule_surface",
    ) != capsule_input["path"]:
        fail("ToS text chunk map capsule input must stay aligned with the tiny-entry capsule surface")

    source_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_AUTHORITY_PATH)
    node_id = require_string(
        source_node_payload.get("node_id"),
        label=f"{source_label}.node_id",
    )
    node_type = require_string(
        source_node_payload.get("node_type"),
        label=f"{source_label}.node_type",
    )
    source_anchor = require_string(
        source_node_payload.get("source_anchor"),
        label=f"{source_label}.source_anchor",
    )
    interpretation_layers = source_node_payload.get("interpretation_layers")
    if not isinstance(interpretation_layers, list) or not interpretation_layers:
        fail(f"{source_label}.interpretation_layers must be a non-empty list")

    raw_language_witnesses = source_node_payload.get("language_witnesses")
    if not isinstance(raw_language_witnesses, list) or not raw_language_witnesses:
        fail(f"{source_label}.language_witnesses must be a non-empty list")

    segment_order: list[str] = []
    expected_segment_order: list[str] | None = None
    seen_languages: set[str] = set()
    witness_entries_by_segment: dict[str, list[dict[str, str]]] = {}

    for witness_index, witness in enumerate(raw_language_witnesses):
        witness_label = f"{source_label}.language_witnesses[{witness_index}]"
        if not isinstance(witness, dict):
            fail(f"{witness_label} must be an object")
        language = require_string(
            witness.get("language"),
            label=f"{witness_label}.language",
        )
        role = require_string(
            witness.get("role"),
            label=f"{witness_label}.role",
        )
        if language in seen_languages:
            fail(f"{witness_label}.language '{language}' is duplicated")
        seen_languages.add(language)

        raw_segments = witness.get("segments")
        if not isinstance(raw_segments, list) or not raw_segments:
            fail(f"{witness_label}.segments must be a non-empty list")

        current_segment_order: list[str] = []
        seen_segment_ids: set[str] = set()
        for segment_index, segment in enumerate(raw_segments):
            segment_label = f"{witness_label}.segments[{segment_index}]"
            if not isinstance(segment, dict):
                fail(f"{segment_label} must be an object")
            segment_id = require_string(
                segment.get("segment_id"),
                label=f"{segment_label}.segment_id",
            )
            text = require_string(
                segment.get("text"),
                label=f"{segment_label}.text",
            )
            if segment_id in seen_segment_ids:
                fail(f"{segment_label}.segment_id '{segment_id}' is duplicated")
            seen_segment_ids.add(segment_id)
            current_segment_order.append(segment_id)
            witness_entries_by_segment.setdefault(segment_id, []).append(
                {
                    "language": language,
                    "role": role,
                    "text": text,
                }
            )

        if expected_segment_order is None:
            expected_segment_order = current_segment_order
            segment_order = list(current_segment_order)
        elif current_segment_order != expected_segment_order:
            fail(
                f"{witness_label}.segments must keep the same segment_id order as the canonical source witness"
            )

    translation_tensions_by_segment: dict[str, dict[str, str]] = {}
    raw_translation_tensions = source_node_payload.get("translation_tensions", [])
    if raw_translation_tensions is not None and not isinstance(raw_translation_tensions, list):
        fail(f"{source_label}.translation_tensions must be a list when present")
    for tension_index, tension in enumerate(raw_translation_tensions or []):
        tension_label = f"{source_label}.translation_tensions[{tension_index}]"
        if not isinstance(tension, dict):
            fail(f"{tension_label} must be an object")
        segment_id = require_string(
            tension.get("segment_id"),
            label=f"{tension_label}.segment_id",
        )
        note = require_string(
            tension.get("note"),
            label=f"{tension_label}.note",
        )
        if segment_id not in witness_entries_by_segment:
            fail(f"{tension_label}.segment_id '{segment_id}' must match a chunked witness segment")
        if segment_id in translation_tensions_by_segment:
            fail(f"{tension_label}.segment_id '{segment_id}' is duplicated")
        translation_tensions_by_segment[segment_id] = {
            "segment_id": segment_id,
            "note": note,
        }

    chunks: list[dict[str, object]] = []
    source_ref = repo_ref(TOS_REPO, source_node_input["path"])
    route_ref = repo_ref(TOS_REPO, route_doc_input["path"])
    capsule_ref = repo_ref(TOS_REPO, capsule_input["path"])
    witness_count = len(raw_language_witnesses)

    for segment_id in segment_order:
        chunk = {
            "chunk_id": f"{node_id}::{segment_id}",
            "node_id": node_id,
            "segment_id": segment_id,
            "source_anchor": source_anchor,
            "source_ref": source_ref,
            "route_ref": route_ref,
            "capsule_ref": capsule_ref,
            "interpretation_layers": interpretation_layers,
            "witness_count": witness_count,
            "witnesses": witness_entries_by_segment[segment_id],
        }
        translation_tension = translation_tensions_by_segment.get(segment_id)
        if translation_tension is not None:
            chunk["translation_tension"] = translation_tension
        chunks.append(chunk)

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_repo": manifest["source_repo"],
        "source_manifest_ref": "manifests/tos_text_chunk_map.json",
        "source_inputs": emitted_source_inputs,
        "surface_bindings": surface_bindings,
        "surface_id": binding_surface["id"],
        "surface_name": binding_surface["name"],
        "node_id": node_id,
        "node_type": node_type,
        "source_anchor": source_anchor,
        "authority_surface_ref": source_ref,
        "route_ref": route_ref,
        "capsule_ref": capsule_ref,
        "interpretation_layers": interpretation_layers,
        "chunk_count": len(chunks),
        "chunks": chunks,
        "bounded_output_contract": manifest["bounded_output_contract"],
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


def load_counterpart_consumer_contract_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    payload = read_json(COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_PATH)
    if not isinstance(payload, dict):
        fail("counterpart consumer contract example must be a JSON object")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry payload must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    surface_id = require_string(
        payload.get("surface_id"),
        label="counterpart consumer contract example surface_id",
    )
    if surface_id != "AOA-K-0008":
        fail("counterpart consumer contract example surface_id must equal 'AOA-K-0008'")

    registry_surface = registry_by_id.get(surface_id)
    if registry_surface is None:
        fail("counterpart consumer contract example surface_id must exist in the registry")
    if registry_surface.get("status") != "planned":
        fail("counterpart consumer contract example requires AOA-K-0008 to remain planned")

    contract_type = require_string(
        payload.get("contract_type"),
        label="counterpart consumer contract example contract_type",
    )
    if contract_type != "counterpart_consumer_contract":
        fail(
            "counterpart consumer contract example contract_type must equal "
            "'counterpart_consumer_contract'"
        )

    surface_status = require_string(
        payload.get("surface_status"),
        label="counterpart consumer contract example surface_status",
    )
    if surface_status != "planned":
        fail("counterpart consumer contract example surface_status must equal 'planned'")

    consumer_surface_type = require_string(
        payload.get("consumer_surface_type"),
        label="counterpart consumer contract example consumer_surface_type",
    )
    if consumer_surface_type != "reasoning_handoff_guardrail":
        fail(
            "counterpart consumer contract example consumer_surface_type must equal "
            "'reasoning_handoff_guardrail'"
        )

    allowed_return_field = require_string(
        payload.get("allowed_return_field"),
        label="counterpart consumer contract example allowed_return_field",
    )
    if allowed_return_field != "counterpart_refs":
        fail(
            "counterpart consumer contract example allowed_return_field must equal "
            "'counterpart_refs'"
        )

    federation_exposure_review_ref = ensure_local_ref_exists(
        payload.get("federation_exposure_review_ref"),
        label="counterpart consumer contract example federation_exposure_review_ref",
        allow_missing_refs={COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF},
    )
    if federation_exposure_review_ref != COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF:
        fail(
            "counterpart consumer contract example federation_exposure_review_ref must "
            f"equal '{COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF}'"
        )

    required_contract_refs = payload.get("required_contract_refs")
    if not isinstance(required_contract_refs, dict):
        fail("counterpart consumer contract example required_contract_refs must be an object")
    expected_required_contract_refs = {
        "counterpart_contract_doc": COUNTERPART_EDGE_CONTRACT_DOC_REF,
        "counterpart_contract_schema": COUNTERPART_EDGE_SCHEMA_REF,
        "counterpart_contract_example": COUNTERPART_EDGE_EXAMPLE_REF,
    }
    for key, expected_ref in expected_required_contract_refs.items():
        actual_ref = ensure_local_ref_exists(
            required_contract_refs.get(key),
            label=f"counterpart consumer contract example required_contract_refs.{key}",
        )
        if actual_ref != expected_ref:
            fail(
                "counterpart consumer contract example "
                f"required_contract_refs.{key} must equal '{expected_ref}'"
            )

    allowed_refs = payload.get("allowed_refs")
    if not isinstance(allowed_refs, list) or not allowed_refs:
        fail("counterpart consumer contract example allowed_refs must be a non-empty list")
    normalized_allowed_refs = ordered_unique(
        [
            ensure_local_ref_exists(
                raw_ref,
                label=f"counterpart consumer contract example allowed_refs[{index}]",
            )
            for index, raw_ref in enumerate(allowed_refs)
        ]
    )
    if len(normalized_allowed_refs) != len(allowed_refs):
        fail("counterpart consumer contract example allowed_refs must not contain duplicates")
    expected_allowed_refs = [
        COUNTERPART_CONSUMER_CONTRACT_DOC_REF,
        COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF,
        COUNTERPART_EDGE_CONTRACT_DOC_REF,
        COUNTERPART_EDGE_EXAMPLE_REF,
    ]
    if normalized_allowed_refs != expected_allowed_refs:
        fail(
            "counterpart consumer contract example allowed_refs must match the current "
            "contract/example-only posture"
        )

    forbidden_interpretations = payload.get("forbidden_interpretations")
    if (
        not isinstance(forbidden_interpretations, list)
        or not forbidden_interpretations
    ):
        fail(
            "counterpart consumer contract example forbidden_interpretations must be "
            "a non-empty list"
        )
    normalized_forbidden_interpretations = ordered_unique(
        [
            require_string(
                raw_value,
                label=(
                    "counterpart consumer contract example "
                    f"forbidden_interpretations[{index}]"
                ),
            )
            for index, raw_value in enumerate(forbidden_interpretations)
        ]
    )
    if len(normalized_forbidden_interpretations) != len(forbidden_interpretations):
        fail(
            "counterpart consumer contract example forbidden_interpretations must not "
            "contain duplicates"
        )
    expected_forbidden_interpretations = [
        "identity_proof",
        "routing_authority",
        "graph_sovereign_activation",
        "silent_federation_exposure",
    ]
    if normalized_forbidden_interpretations != expected_forbidden_interpretations:
        fail(
            "counterpart consumer contract example forbidden_interpretations must match "
            "the bounded counterpart contract"
        )

    payload["federation_exposure_review_ref"] = federation_exposure_review_ref

    return payload


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
    kag_guardrail_refs: list[str],
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
            "kag_guardrail_refs": kag_guardrail_refs,
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

    counterpart_consumer_contract = load_counterpart_consumer_contract_payload()
    if counterpart_consumer_contract["consumer_surface_type"] != "reasoning_handoff_guardrail":
        fail(
            "counterpart consumer contract must stay bound to the reasoning handoff "
            "guardrail in the current wave"
        )

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
    kag_guardrail_refs = ordered_unique(
        [
            manifest_input_ref(source_input)
            for source_input in inputs_by_name.values()
            if source_input["repo"] == "aoa-kag"
            and source_input["role"]
            in {
                "kag_guardrail_doc",
                "kag_guardrail_schema",
                "kag_guardrail_example",
            }
        ]
    )
    if kag_guardrail_refs != [
        REASONING_HANDOFF_GUARDRAIL_REF,
        REASONING_HANDOFF_GUARDRAIL_SCHEMA_REF,
        COUNTERPART_CONSUMER_CONTRACT_DOC_REF,
        COUNTERPART_CONSUMER_CONTRACT_SCHEMA_REF,
        COUNTERPART_CONSUMER_CONTRACT_EXAMPLE_REF,
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
    ]:
        fail("reasoning handoff manifest must keep the current ordered KAG guardrail refs")

    scenarios = [
        build_reasoning_handoff_scenario(
            binding,
            inputs_by_name,
            query_modes,
            return_contract,
            boundary_guardrails,
            kag_guardrail_refs,
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


def build_tos_retrieval_axis_pack_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TOS_RETRIEVAL_AXIS_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("ToS retrieval axis manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS retrieval axis manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS retrieval axis manifest must declare surface_bindings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("ToS retrieval axis manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail("ToS retrieval axis manifest source_inputs must keep name, repo, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate ToS retrieval axis source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        if not manifest_input_path(normalized_input).exists():
            fail(f"ToS retrieval axis donor input does not exist: {repo_ref(repo, path)}")
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    required_input_names = (
        "tos_text_chunk_map",
        "bridge_contract_doc",
        "bridge_surface_example",
        "bridge_envelope_example",
        "memo_chunk_face",
        "memo_graph_face",
        "tos_node_contract",
        "tos_practice_branch",
        "tos_authority_surface",
        "tos_lineage_hop",
    )
    missing_inputs = [name for name in required_input_names if name not in inputs_by_name]
    if missing_inputs:
        fail(
            "ToS retrieval axis manifest is missing required inputs: "
            + ", ".join(sorted(missing_inputs))
        )

    chunk_map_input = inputs_by_name["tos_text_chunk_map"]
    if manifest_input_ref(chunk_map_input) != "generated/tos_text_chunk_map.min.json":
        fail(
            "ToS retrieval axis manifest tos_text_chunk_map must point to generated/tos_text_chunk_map.min.json"
        )
    if manifest_input_ref(inputs_by_name["bridge_contract_doc"]) != "docs/BRIDGE_CONTRACTS.md":
        fail("ToS retrieval axis manifest bridge_contract_doc must point to docs/BRIDGE_CONTRACTS.md")
    if manifest_input_ref(inputs_by_name["bridge_surface_example"]) != "examples/tos_retrieval_axis_surface.example.json":
        fail(
            "ToS retrieval axis manifest bridge_surface_example must point to examples/tos_retrieval_axis_surface.example.json"
        )
    if manifest_input_ref(inputs_by_name["bridge_envelope_example"]) != "examples/aoa_tos_bridge_envelope.example.json":
        fail(
            "ToS retrieval axis manifest bridge_envelope_example must point to examples/aoa_tos_bridge_envelope.example.json"
        )
    if manifest_input_ref(inputs_by_name["memo_chunk_face"]) != "aoa-memo/examples/memory_chunk_face.bridge.example.json":
        fail(
            "ToS retrieval axis manifest memo_chunk_face must point to aoa-memo/examples/memory_chunk_face.bridge.example.json"
        )
    if manifest_input_ref(inputs_by_name["memo_graph_face"]) != "aoa-memo/examples/memory_graph_face.bridge.example.json":
        fail(
            "ToS retrieval axis manifest memo_graph_face must point to aoa-memo/examples/memory_graph_face.bridge.example.json"
        )
    if manifest_input_ref(inputs_by_name["tos_node_contract"]) != "Tree-of-Sophia/docs/NODE_CONTRACT.md":
        fail("ToS retrieval axis manifest tos_node_contract must point to Tree-of-Sophia/docs/NODE_CONTRACT.md")
    if manifest_input_ref(inputs_by_name["tos_practice_branch"]) != "Tree-of-Sophia/docs/PRACTICE_BRANCH.md":
        fail(
            "ToS retrieval axis manifest tos_practice_branch must point to Tree-of-Sophia/docs/PRACTICE_BRANCH.md"
        )
    if manifest_input_ref(inputs_by_name["tos_authority_surface"]) != "Tree-of-Sophia/examples/source_node.example.json":
        fail(
            "ToS retrieval axis manifest tos_authority_surface must point to Tree-of-Sophia/examples/source_node.example.json"
        )
    if manifest_input_ref(inputs_by_name["tos_lineage_hop"]) != "Tree-of-Sophia/examples/concept_node.example.json":
        fail(
            "ToS retrieval axis manifest tos_lineage_hop must point to Tree-of-Sophia/examples/concept_node.example.json"
        )

    seen_surface_ids: set[str] = set()
    binding_surface: dict[str, object] | None = None
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("ToS retrieval axis manifest surface_bindings entries must be objects")
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
            fail(
                "ToS retrieval axis manifest surface_bindings must keep id, name, kind, slot, and source input"
            )
        if surface_id in seen_surface_ids:
            fail(f"duplicate ToS retrieval axis surface binding '{surface_id}'")
        seen_surface_ids.add(surface_id)
        if source_input not in inputs_by_name:
            fail(
                f"ToS retrieval axis binding '{surface_id}' references unknown source input '{source_input}'"
            )

        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(
                f"ToS retrieval axis binding '{surface_id}' does not exist in the registry manifest"
            )
        if surface.get("name") != surface_name:
            fail(f"ToS retrieval axis binding '{surface_id}' does not match registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(
                f"ToS retrieval axis binding '{surface_id}' does not match registry derived_kind"
            )
        if surface.get("status") != "experimental":
            fail(
                f"ToS retrieval axis binding '{surface_id}' must point to an experimental registry surface"
            )
        binding_surface = surface

    if binding_surface is None:
        fail("ToS retrieval axis manifest must declare one experimental surface binding")

    chunk_map_payload = build_tos_text_chunk_map_payload(registry_payload)
    chunks = chunk_map_payload.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        fail("ToS retrieval axis requires a non-empty ToS text chunk map")
    chunk_ids = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            fail("ToS retrieval axis requires chunk-map chunks to be objects")
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            fail("ToS retrieval axis requires every chunk-map chunk to keep chunk_id")
        chunk_ids.append(chunk_id)

    source_node_id = require_string(
        chunk_map_payload.get("node_id"),
        label="ToS retrieval axis source_node_id",
    )
    axis_summary = (
        "Bundles the current Zarathustra prologue chunk set with bounded source, "
        "lineage, conflict, practice, and memo bridge handles so AoA consumers can "
        "retrieve context without ranking, routing ownership, or graph claims."
    )

    axis = {
        "axis_id": f"AOA-K-0007::{source_node_id}",
        "source_node_id": source_node_id,
        "chunk_map_ref": manifest_input_ref(chunk_map_input),
        "chunk_ids": chunk_ids,
        "source_refs": [
            manifest_input_ref(inputs_by_name["tos_authority_surface"]),
            manifest_input_ref(inputs_by_name["tos_node_contract"]),
            manifest_input_ref(inputs_by_name["tos_practice_branch"]),
        ],
        "lineage_refs": [
            manifest_input_ref(inputs_by_name["tos_lineage_hop"]),
            manifest_input_ref(inputs_by_name["tos_node_contract"]),
        ],
        "conflict_refs": [
            manifest_input_ref(inputs_by_name["tos_node_contract"]),
        ],
        "practice_refs": [
            manifest_input_ref(inputs_by_name["tos_practice_branch"]),
        ],
        "bridge_surface_ref": manifest_input_ref(inputs_by_name["bridge_surface_example"]),
        "bridge_envelope_ref": manifest_input_ref(inputs_by_name["bridge_envelope_example"]),
        "memo_face_refs": [
            manifest_input_ref(inputs_by_name["memo_chunk_face"]),
            manifest_input_ref(inputs_by_name["memo_graph_face"]),
        ],
        "axis_summary": axis_summary,
    }

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": "manifests/tos_retrieval_axis_pack.json",
        "source_inputs": emitted_source_inputs,
        "surface_bindings": surface_bindings,
        "surface_id": binding_surface["id"],
        "surface_name": binding_surface["name"],
        "axis_count": 1,
        "axes": [axis],
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_tos_zarathustra_route_node_entry(relative_path: str) -> dict[str, object]:
    payload = read_json(TREE_OF_SOPHIA_ROOT / relative_path)
    if not isinstance(payload, dict):
        fail(f"ToS Zarathustra route node surface must be a JSON object: {relative_path}")

    node_id = require_string(payload.get("node_id"), label=f"{relative_path}.node_id")
    node_type = require_string(
        payload.get("node_type"),
        label=f"{relative_path}.node_type",
    )
    if node_type not in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER:
        fail(f"{relative_path}.node_type '{node_type}' is not allowed in the route pack")
    if node_id.startswith("literal."):
        fail(f"{relative_path}.node_id must not carry literal helper residue")

    return {
        "node_id": node_id,
        "node_type": node_type,
        "authority_ref": repo_ref(TOS_REPO, relative_path),
        "source_anchor": require_string(
            payload.get("source_anchor"),
            label=f"{relative_path}.source_anchor",
        ),
        "key_terms": require_string_list(
            payload.get("key_terms"),
            label=f"{relative_path}.key_terms",
        ),
        "distilled_thesis": require_string(
            payload.get("distilled_thesis"),
            label=f"{relative_path}.distilled_thesis",
        ),
        "interpretation_layers": require_string_list(
            payload.get("interpretation_layers"),
            label=f"{relative_path}.interpretation_layers",
        ),
    }


def load_tos_zarathustra_route_family(
    root_path: str,
    *,
    expected_type: str,
) -> list[dict[str, object]]:
    root = TREE_OF_SOPHIA_ROOT / root_path
    if not root.is_dir():
        fail(f"ToS Zarathustra route family root is missing: {root_path}")

    entries: list[dict[str, object]] = []
    for node_path in sorted(root.glob("**/node.json")):
        relative_path = node_path.relative_to(TREE_OF_SOPHIA_ROOT).as_posix()
        entry = build_tos_zarathustra_route_node_entry(relative_path)
        if entry["node_type"] != expected_type:
            fail(
                f"{relative_path}.node_type must stay '{expected_type}' under "
                f"{root_path}"
            )
        entries.append(entry)

    entries.sort(key=lambda record: str(record["node_id"]))
    return entries


def load_tos_zarathustra_route_edges(relative_path: str) -> list[dict[str, object]]:
    rows = read_csv_rows(TREE_OF_SOPHIA_ROOT / relative_path)
    if not rows:
        fail("ToS Zarathustra route relation pack must keep at least one edge row")

    required_columns = {
        "edge_id",
        "edge_kind",
        "from_id",
        "predicate_id",
        "to_id",
        "layer",
        "anchor_mode",
        "anchor_start_secondary",
        "anchor_end_secondary",
        "anchor_segment_ids",
        "witness_scope",
        "connectivity_role",
        "confidence",
        "note",
    }

    edges: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        missing = required_columns.difference(row)
        if missing:
            fail(
                "ToS Zarathustra route relation pack row is missing required columns: "
                + ", ".join(sorted(missing))
            )
        edge_id = require_string(row.get("edge_id"), label=f"{relative_path} row {index}.edge_id")
        from_id = require_string(row.get("from_id"), label=f"{relative_path} row {index}.from_id")
        to_id = require_string(row.get("to_id"), label=f"{relative_path} row {index}.to_id")
        if not from_id.startswith("tos.") or not to_id.startswith("tos."):
            fail(f"{relative_path} row {index} must keep canonical tos.* endpoints")
        if from_id.startswith("literal.") or to_id.startswith("literal."):
            fail(f"{relative_path} row {index} must not carry literal helper residue")

        confidence = require_string(
            row.get("confidence"),
            label=f"{relative_path} row {index}.confidence",
        )
        if not confidence.isdigit():
            fail(f"{relative_path} row {index}.confidence must stay integer-like")

        edges.append(
            {
                "edge_id": edge_id,
                "edge_kind": require_string(
                    row.get("edge_kind"),
                    label=f"{relative_path} row {index}.edge_kind",
                ),
                "from_id": from_id,
                "predicate_id": require_string(
                    row.get("predicate_id"),
                    label=f"{relative_path} row {index}.predicate_id",
                ),
                "to_id": to_id,
                "layer": require_string(
                    row.get("layer"),
                    label=f"{relative_path} row {index}.layer",
                ),
                "anchor_mode": require_string(
                    row.get("anchor_mode"),
                    label=f"{relative_path} row {index}.anchor_mode",
                ),
                "anchor_start_secondary": row.get("anchor_start_secondary", ""),
                "anchor_end_secondary": row.get("anchor_end_secondary", ""),
                "anchor_segment_ids": require_string(
                    row.get("anchor_segment_ids"),
                    label=f"{relative_path} row {index}.anchor_segment_ids",
                ),
                "witness_scope": require_string(
                    row.get("witness_scope"),
                    label=f"{relative_path} row {index}.witness_scope",
                ),
                "connectivity_role": require_string(
                    row.get("connectivity_role"),
                    label=f"{relative_path} row {index}.connectivity_role",
                ),
                "confidence": int(confidence),
                "note": row.get("note", ""),
            }
        )

    return edges


def build_tos_zarathustra_route_pack_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("ToS Zarathustra route pack manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS Zarathustra route pack manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS Zarathustra route pack manifest must declare surface_bindings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    surface_0010 = registry_by_id.get("AOA-K-0010")
    if surface_0010 is None:
        fail("registry manifest must declare AOA-K-0010 before building the route pack")
    if surface_0010.get("status") != "experimental":
        fail("AOA-K-0010 must remain experimental in the current route-pack wave")

    expected_inputs = {
        "tos_route_source_node": (
            TOS_ZARATHUSTRA_ROUTE_SOURCE_NODE_PATH,
            "authority_surface",
        ),
        "tos_becoming_concept": (
            TOS_ZARATHUSTRA_ROUTE_BECOMING_CONCEPT_PATH,
            "concept_surface",
        ),
        "tos_overcoming_concept": (
            TOS_ZARATHUSTRA_ROUTE_OVERCOMING_CONCEPT_PATH,
            "concept_surface",
        ),
        "tos_route_lineage_node": (
            TOS_ZARATHUSTRA_ROUTE_LINEAGE_NODE_PATH,
            "lineage_surface",
        ),
        "tos_route_principle_family_root": (
            TOS_ZARATHUSTRA_ROUTE_PRINCIPLE_ROOT,
            "family_root",
        ),
        "tos_route_event_family_root": (
            TOS_ZARATHUSTRA_ROUTE_EVENT_ROOT,
            "family_root",
        ),
        "tos_route_state_family_root": (
            TOS_ZARATHUSTRA_ROUTE_STATE_ROOT,
            "family_root",
        ),
        "tos_route_support_family_root": (
            TOS_ZARATHUSTRA_ROUTE_SUPPORT_ROOT,
            "family_root",
        ),
        "tos_route_analogy_family_root": (
            TOS_ZARATHUSTRA_ROUTE_ANALOGY_ROOT,
            "family_root",
        ),
        "tos_route_synthesis_family_root": (
            TOS_ZARATHUSTRA_ROUTE_SYNTHESIS_ROOT,
            "family_root",
        ),
        "tos_route_relation_pack": (
            TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH,
            "relation_pack",
        ),
        "tos_zarathustra_capsule": (
            TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH,
            "capsule_surface",
        ),
    }

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("ToS Zarathustra route pack manifest source_inputs entries must be objects")
        name = source_input.get("name")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, path, role)):
            fail(
                "ToS Zarathustra route pack manifest source_inputs must keep name, path, "
                "and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate ToS Zarathustra route pack source input '{name}'")
        expected = expected_inputs.get(name)
        if expected is None:
            fail(f"unexpected ToS Zarathustra route pack source input '{name}'")
        expected_path, expected_role = expected
        if path != expected_path or role != expected_role:
            fail(
                "ToS Zarathustra route pack manifest source_inputs must stay aligned "
                f"for '{name}'"
            )

        normalized_input = {
            "name": name,
            "repo": TOS_REPO,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        if role == "family_root":
            if not input_path.is_dir():
                fail(f"ToS Zarathustra route family root is missing: {repo_ref(TOS_REPO, path)}")
        elif not input_path.exists():
            fail(f"ToS Zarathustra route donor input does not exist: {repo_ref(TOS_REPO, path)}")

        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": TOS_REPO,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    if set(inputs_by_name) != set(expected_inputs):
        fail("ToS Zarathustra route pack manifest source_inputs must match the current canonical donor set")

    binding_surface: dict[str, object] | None = None
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("ToS Zarathustra route pack manifest surface_bindings entries must be objects")
        if (
            binding.get("surface_id") == "AOA-K-0010"
            and binding.get("surface_name") == "tos-zarathustra-route-pack"
        ):
            binding_surface = surface_0010
            break
    if binding_surface is None:
        fail("ToS Zarathustra route pack manifest must bind AOA-K-0010")

    nodes_by_type: dict[str, list[dict[str, object]]] = {
        "source": [
            build_tos_zarathustra_route_node_entry(TOS_ZARATHUSTRA_ROUTE_SOURCE_NODE_PATH)
        ],
        "concept": sorted(
            [
                build_tos_zarathustra_route_node_entry(
                    TOS_ZARATHUSTRA_ROUTE_BECOMING_CONCEPT_PATH
                ),
                build_tos_zarathustra_route_node_entry(
                    TOS_ZARATHUSTRA_ROUTE_OVERCOMING_CONCEPT_PATH
                ),
            ],
            key=lambda record: str(record["node_id"]),
        ),
        "principle": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_PRINCIPLE_ROOT,
            expected_type="principle",
        ),
        "lineage": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_LINEAGE_NODE_PATH.rsplit("/", 1)[0],
            expected_type="lineage",
        ),
        "event": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_EVENT_ROOT,
            expected_type="event",
        ),
        "state": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_STATE_ROOT,
            expected_type="state",
        ),
        "support": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_SUPPORT_ROOT,
            expected_type="support",
        ),
        "analogy": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_ANALOGY_ROOT,
            expected_type="analogy",
        ),
        "synthesis": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_SYNTHESIS_ROOT,
            expected_type="synthesis",
        ),
    }

    node_type_counts = {
        node_type: len(nodes_by_type[node_type])
        for node_type in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER
    }
    if node_type_counts != TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS:
        fail("ToS Zarathustra route pack node_type_counts must match the current canonical route")

    nodes: list[dict[str, object]] = []
    for node_type in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER:
        nodes.extend(nodes_by_type[node_type])

    edges = load_tos_zarathustra_route_edges(TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH)
    edge_kind_counts: dict[str, int] = {}
    for edge_kind in ("source_edge", "bridge_edge", "principle_edge"):
        edge_kind_counts[edge_kind] = len(
            [edge for edge in edges if edge["edge_kind"] == edge_kind]
        )
    if edge_kind_counts != TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS:
        fail("ToS Zarathustra route pack edge_kind_counts must match the canonical relation pack")

    if len(nodes) != sum(TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS.values()):
        fail("ToS Zarathustra route pack node_count drifted from the current canonical route")
    if len(edges) != sum(TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS.values()):
        fail("ToS Zarathustra route pack edge_count drifted from the canonical relation pack")

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_repo": manifest["source_repo"],
        "source_manifest_ref": "manifests/tos_zarathustra_route_pack.json",
        "source_inputs": emitted_source_inputs,
        "surface_bindings": surface_bindings,
        "surface_id": binding_surface["id"],
        "surface_name": binding_surface["name"],
        "route_id": TOS_ZARATHUSTRA_ROUTE_ID,
        "route_capsule_ref": repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH),
        "relation_pack_ref": repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": node_type_counts,
        "edge_kind_counts": edge_kind_counts,
        "nodes": nodes,
        "edges": edges,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_federation_spine_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(FEDERATION_SPINE_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("federation spine manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    repo_bindings = manifest.get("repo_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("federation spine manifest must declare source_inputs")
    if not isinstance(repo_bindings, list) or not repo_bindings:
        fail("federation spine manifest must declare repo_bindings")

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []

    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("federation spine manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail("federation spine manifest source_inputs must keep name, repo, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate federation spine source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        if not manifest_input_path(normalized_input).exists():
            fail(f"federation spine donor input does not exist: {repo_ref(repo, path)}")

        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    registry_surface_input = inputs_by_name.get("kag_registry_manifest")
    if registry_surface_input is None:
        fail("federation spine manifest must include kag_registry_manifest")
    if manifest_input_ref(registry_surface_input) != "manifests/kag_registry.json":
        fail(
            "federation spine manifest kag_registry_manifest must point to manifests/kag_registry.json"
        )

    technique_export_input = inputs_by_name.get("aoa_techniques_kag_export")
    if technique_export_input is None:
        fail("federation spine manifest must include aoa_techniques_kag_export")
    technique_dependency = dependency_for_source_input(
        technique_export_input,
        consumer_surface_id="AOA-K-0009",
    )
    technique_export_payload = load_federation_export_payload(
        technique_export_input,
        dependency=technique_dependency,
        consumer_surface_id="AOA-K-0009",
    )

    tos_export_input = inputs_by_name.get("tos_kag_export")
    if tos_export_input is None:
        fail("federation spine manifest must include tos_kag_export")
    tos_dependency = dependency_for_source_input(
        tos_export_input,
        consumer_surface_id="AOA-K-0009",
    )
    tos_export_payload = load_federation_export_payload(
        tos_export_input,
        dependency=tos_dependency,
        consumer_surface_id="AOA-K-0009",
    )
    export_payloads_by_repo = {
        "aoa-techniques": technique_export_payload,
        TOS_REPO: tos_export_payload,
    }

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    repos: list[dict[str, object]] = []
    seen_repos: set[str] = set()

    for binding in repo_bindings:
        if not isinstance(binding, dict):
            fail("federation spine manifest repo_bindings entries must be objects")

        surface_id = binding.get("surface_id")
        repo_name = binding.get("repo")
        pilot_posture = binding.get("pilot_posture")
        export_input_name = binding.get("export_input")
        provenance_note = binding.get("provenance_note")
        non_identity_boundary = binding.get("non_identity_boundary")

        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                repo_name,
                pilot_posture,
                export_input_name,
                provenance_note,
                non_identity_boundary,
            )
        ):
            fail("federation spine repo binding must keep required string fields")
        if repo_name in seen_repos:
            fail(f"duplicate federation spine repo binding '{repo_name}'")
        seen_repos.add(repo_name)

        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(f"federation spine binding '{surface_id}' does not exist in the registry manifest")
        if surface.get("status") != "experimental":
            fail(
                f"federation spine binding '{surface_id}' must point to an experimental registry surface"
            )

        export_input = inputs_by_name.get(export_input_name)
        if export_input is None:
            fail(
                f"federation spine repo binding references unknown export input '{export_input_name}'"
            )
        if export_input["repo"] != repo_name:
            fail(
                f"federation spine export input '{export_input_name}' must point to repo '{repo_name}'"
            )

        export_payload = export_payloads_by_repo.get(repo_name)
        if export_payload is None:
            fail(
                "federation spine currently supports only aoa-techniques and "
                "Tree-of-Sophia pilot repos"
            )

        entry_surface = export_payload.get("entry_surface")
        if not isinstance(entry_surface, dict):
            fail(f"{manifest_input_ref(export_input)}.entry_surface must be an object")
        entry_surface_repo = require_string(
            entry_surface.get("repo"),
            label=f"{manifest_input_ref(export_input)}.entry_surface.repo",
        )
        entry_surface_path = require_string(
            entry_surface.get("path"),
            label=f"{manifest_input_ref(export_input)}.entry_surface.path",
        )

        repos.append(
            {
                "repo": repo_name,
                "pilot_posture": pilot_posture,
                "export_ref": manifest_input_ref(export_input),
                "kind": export_payload["kind"],
                "object_id": export_payload["object_id"],
                "entry_surface_ref": repo_ref(entry_surface_repo, entry_surface_path),
                "summary_50": export_payload["summary_50"],
                "provenance_note": provenance_note,
                "non_identity_boundary": non_identity_boundary,
            }
        )

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": "manifests/federation_spine.json",
        "source_inputs": emitted_source_inputs,
        "repo_count": len(repos),
        "repos": repos,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_cross_source_node_projection_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("cross-source node projection manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")
    projection_pairings = manifest.get("projection_pairings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("cross-source node projection manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("cross-source node projection manifest must declare surface_bindings")
    if not isinstance(projection_pairings, list) or not projection_pairings:
        fail("cross-source node projection manifest must declare projection_pairings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("cross-source node projection manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(
                "cross-source node projection manifest source_inputs must keep name, repo, path, and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate cross-source node projection source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        allow_same_run_generated_input = (
            repo == "aoa-kag"
            and path in {
                "generated/tos_retrieval_axis_pack.min.json",
                "generated/federation_spine.min.json",
            }
        )
        if not input_path.exists() and not allow_same_run_generated_input:
            fail(
                "cross-source node projection donor input does not exist: "
                + repo_ref(repo, path)
            )
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    required_input_names = (
        "aoa_techniques_kag_export",
        "tos_kag_export",
        "tos_retrieval_axis_pack",
        "federation_spine",
    )
    missing_inputs = [name for name in required_input_names if name not in inputs_by_name]
    if missing_inputs:
        fail(
            "cross-source node projection manifest is missing required inputs: "
            + ", ".join(sorted(missing_inputs))
        )

    if manifest_input_ref(inputs_by_name["aoa_techniques_kag_export"]) != "aoa-techniques/generated/kag_export.min.json":
        fail(
            "cross-source node projection manifest aoa_techniques_kag_export must point to aoa-techniques/generated/kag_export.min.json"
        )
    if manifest_input_ref(inputs_by_name["tos_kag_export"]) != "Tree-of-Sophia/generated/kag_export.min.json":
        fail(
            "cross-source node projection manifest tos_kag_export must point to Tree-of-Sophia/generated/kag_export.min.json"
        )
    if manifest_input_ref(inputs_by_name["tos_retrieval_axis_pack"]) != "generated/tos_retrieval_axis_pack.min.json":
        fail(
            "cross-source node projection manifest tos_retrieval_axis_pack must point to generated/tos_retrieval_axis_pack.min.json"
        )
    if manifest_input_ref(inputs_by_name["federation_spine"]) != "generated/federation_spine.min.json":
        fail(
            "cross-source node projection manifest federation_spine must point to generated/federation_spine.min.json"
        )

    seen_surface_ids: set[str] = set()
    binding_surface: dict[str, object] | None = None
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("cross-source node projection manifest surface_bindings entries must be objects")
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
            fail(
                "cross-source node projection manifest surface_bindings must keep id, name, kind, slot, and source input"
            )
        if surface_id in seen_surface_ids:
            fail(f"duplicate cross-source node projection surface binding '{surface_id}'")
        seen_surface_ids.add(surface_id)
        if source_input not in inputs_by_name:
            fail(
                "cross-source node projection binding "
                f"'{surface_id}' references unknown source input '{source_input}'"
            )

        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(
                f"cross-source node projection binding '{surface_id}' does not exist in the registry manifest"
            )
        if surface.get("name") != surface_name:
            fail(
                f"cross-source node projection binding '{surface_id}' does not match registry surface name"
            )
        if surface.get("derived_kind") != derived_kind:
            fail(
                f"cross-source node projection binding '{surface_id}' does not match registry derived_kind"
            )
        if surface.get("status") != "experimental":
            fail(
                f"cross-source node projection binding '{surface_id}' must point to an experimental registry surface"
            )
        binding_surface = surface

    if binding_surface is None:
        fail("cross-source node projection manifest must declare one experimental surface binding")

    consumer_surface_id = require_string(
        binding_surface.get("id"),
        label="cross-source node projection consumer_surface_id",
    )
    technique_dependency = dependency_for_source_input(
        inputs_by_name["aoa_techniques_kag_export"],
        consumer_surface_id=consumer_surface_id,
    )
    tos_dependency = dependency_for_source_input(
        inputs_by_name["tos_kag_export"],
        consumer_surface_id=consumer_surface_id,
    )
    technique_export_payload = load_federation_export_payload(
        inputs_by_name["aoa_techniques_kag_export"],
        dependency=technique_dependency,
        consumer_surface_id=consumer_surface_id,
    )
    tos_export_payload = load_federation_export_payload(
        inputs_by_name["tos_kag_export"],
        dependency=tos_dependency,
        consumer_surface_id=consumer_surface_id,
    )
    export_payloads_by_input = {
        "aoa_techniques_kag_export": technique_export_payload,
        "tos_kag_export": tos_export_payload,
    }
    retrieval_axis_payload = build_tos_retrieval_axis_pack_payload(registry_payload)
    axes = retrieval_axis_payload.get("axes")
    if not isinstance(axes, list) or len(axes) != 1 or not isinstance(axes[0], dict):
        fail("cross-source node projection requires exactly one retrieval axis in the current pilot")
    axis = axes[0]
    axis_id = require_string(axis.get("axis_id"), label="cross-source node projection axis_id")
    if require_string(
        axis.get("source_node_id"),
        label="cross-source node projection source_node_id",
    ) != tos_export_payload["object_id"]:
        fail(
            "cross-source node projection retrieval axis must stay aligned with the Tree-of-Sophia export object_id"
        )

    federation_spine_payload = build_federation_spine_payload(registry_payload)
    federation_repos = federation_spine_payload.get("repos")
    if not isinstance(federation_repos, list) or len(federation_repos) != 2:
        fail("cross-source node projection requires exactly two repo entries in the current federation spine")
    federation_repo_map = {
        repo_entry["repo"]: repo_entry
        for repo_entry in federation_repos
        if isinstance(repo_entry, dict) and isinstance(repo_entry.get("repo"), str)
    }
    if set(federation_repo_map) != {"aoa-techniques", TOS_REPO}:
        fail("cross-source node projection requires aoa-techniques and Tree-of-Sophia federation entries")

    technique_spine_entry = federation_repo_map["aoa-techniques"]
    tos_spine_entry = federation_repo_map[TOS_REPO]
    if technique_spine_entry.get("export_ref") != manifest_input_ref(inputs_by_name["aoa_techniques_kag_export"]):
        fail("cross-source node projection primary export must stay aligned with the federation spine")
    if tos_spine_entry.get("export_ref") != manifest_input_ref(inputs_by_name["tos_kag_export"]):
        fail("cross-source node projection supporting export must stay aligned with the federation spine")

    if len(projection_pairings) != 1:
        fail(
            "cross-source node projection manifest must declare exactly one "
            "projection_pairings entry in the current pilot"
        )
    seen_pairing_ids: set[str] = set()
    projections: list[dict[str, object]] = []
    for index, pairing in enumerate(projection_pairings):
        location = (
            "cross-source node projection manifest "
            f"projection_pairings[{index}]"
        )
        if not isinstance(pairing, dict):
            fail(f"{location} must be an object")
        pairing_id = require_string(
            pairing.get("pairing_id"),
            label=f"{location}.pairing_id",
        )
        primary_export_input = require_string(
            pairing.get("primary_export_input"),
            label=f"{location}.primary_export_input",
        )
        supporting_export_inputs = pairing.get("supporting_export_inputs")
        if not isinstance(supporting_export_inputs, list) or not supporting_export_inputs:
            fail(f"{location}.supporting_export_inputs must be a non-empty list")
        normalized_supporting_inputs: list[str] = []
        for supporting_index, supporting_input in enumerate(supporting_export_inputs):
            normalized_supporting_inputs.append(
                require_string(
                    supporting_input,
                    label=f"{location}.supporting_export_inputs[{supporting_index}]",
                )
            )
        retrieval_axis_input = require_string(
            pairing.get("retrieval_axis_input"),
            label=f"{location}.retrieval_axis_input",
        )
        federation_spine_input = require_string(
            pairing.get("federation_spine_input"),
            label=f"{location}.federation_spine_input",
        )
        projection_summary = require_string(
            pairing.get("projection_summary"),
            label=f"{location}.projection_summary",
        )
        non_identity_boundary = require_string(
            pairing.get("non_identity_boundary"),
            label=f"{location}.non_identity_boundary",
        )
        if pairing_id in seen_pairing_ids:
            fail(f"{location}.pairing_id '{pairing_id}' is duplicated")
        seen_pairing_ids.add(pairing_id)
        if primary_export_input not in inputs_by_name:
            fail(f"{location}.primary_export_input references unknown source input")
        if len(normalized_supporting_inputs) != 1:
            fail(
                f"{location}.supporting_export_inputs must contain exactly one "
                "supporting export in the current pilot"
            )
        if retrieval_axis_input not in inputs_by_name:
            fail(f"{location}.retrieval_axis_input references unknown source input")
        if federation_spine_input not in inputs_by_name:
            fail(f"{location}.federation_spine_input references unknown source input")
        if inputs_by_name[primary_export_input]["role"] != "primary_export":
            fail(f"{location}.primary_export_input must point to a primary_export source input")
        supporting_input_name = normalized_supporting_inputs[0]
        if inputs_by_name[supporting_input_name]["role"] != "supporting_export":
            fail(
                f"{location}.supporting_export_inputs must point only to "
                "supporting_export source inputs"
            )
        if inputs_by_name[retrieval_axis_input]["role"] != "retrieval_axis":
            fail(f"{location}.retrieval_axis_input must point to a retrieval_axis source input")
        if inputs_by_name[federation_spine_input]["role"] != "federation_spine":
            fail(f"{location}.federation_spine_input must point to a federation_spine source input")

        primary_export_payload = export_payloads_by_input.get(primary_export_input)
        supporting_export_payload = export_payloads_by_input.get(supporting_input_name)
        if primary_export_payload is None or supporting_export_payload is None:
            fail(f"{location} must reference known source-owned export inputs")
        if axis.get("source_node_id") != supporting_export_payload["object_id"]:
            fail(
                f"{location}.supporting_export_inputs[0] must stay aligned with the "
                "current retrieval axis source_node_id"
            )
        if (
            technique_spine_entry.get("export_ref")
            != manifest_input_ref(inputs_by_name[primary_export_input])
        ):
            fail(
                f"{location}.primary_export_input must stay aligned with the "
                "aoa-techniques federation spine entry"
            )
        if (
            tos_spine_entry.get("export_ref")
            != manifest_input_ref(inputs_by_name[supporting_input_name])
        ):
            fail(
                f"{location}.supporting_export_inputs[0] must stay aligned with the "
                "Tree-of-Sophia federation spine entry"
            )

        projections.append(
            {
                "projection_id": (
                    "AOA-K-0006::"
                    f"{primary_export_payload['object_id']}::"
                    f"{supporting_export_payload['object_id']}"
                ),
                "primary_input": {
                    "repo": inputs_by_name[primary_export_input]["repo"],
                    "export_ref": manifest_input_ref(inputs_by_name[primary_export_input]),
                    "kind": primary_export_payload["kind"],
                    "object_id": primary_export_payload["object_id"],
                },
                "supporting_inputs": [
                    {
                        "repo": inputs_by_name[supporting_input_name]["repo"],
                        "export_ref": manifest_input_ref(
                            inputs_by_name[supporting_input_name]
                        ),
                        "kind": supporting_export_payload["kind"],
                        "object_id": supporting_export_payload["object_id"],
                    }
                ],
                "retrieval_axis_ref": manifest_input_ref(
                    inputs_by_name[retrieval_axis_input]
                ),
                "axis_id": axis_id,
                "federation_spine_ref": manifest_input_ref(
                    inputs_by_name[federation_spine_input]
                ),
                "projection_summary": projection_summary,
                "non_identity_boundary": non_identity_boundary,
            }
        )

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": "manifests/cross_source_node_projection.json",
        "source_inputs": emitted_source_inputs,
        "surface_bindings": surface_bindings,
        "surface_id": binding_surface["id"],
        "surface_name": binding_surface["name"],
        "projection_count": len(projections),
        "projections": projections,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_return_regrounding_pack_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(RETURN_REGROUNDING_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("return regrounding manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    mode_bindings = manifest.get("mode_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("return regrounding manifest must declare source_inputs")
    if not isinstance(mode_bindings, list) or not mode_bindings:
        fail("return regrounding manifest must declare mode_bindings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }
    for surface_id, expected_status in RETURN_REGROUNDING_EXPECTED_REGISTRY_POSTURE.items():
        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(f"return regrounding pack requires registry surface '{surface_id}'")
        if surface.get("status") != expected_status:
            fail(
                f"return regrounding pack requires {surface_id} to remain "
                f"'{expected_status}'"
            )

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("return regrounding manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(
                "return regrounding manifest source_inputs must keep name, repo, path, and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate return regrounding source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        allow_same_run_generated_input = (
            repo == "aoa-kag" and path in RETURN_REGROUNDING_ALLOWED_SAME_RUN_INPUTS
        )
        if not input_path.exists() and not allow_same_run_generated_input:
            fail(
                "return regrounding donor input does not exist: "
                + manifest_input_ref(normalized_input)
            )
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    missing_inputs = [
        name for name in RETURN_REGROUNDING_EXPECTED_INPUT_REFS if name not in inputs_by_name
    ]
    if missing_inputs:
        fail(
            "return regrounding manifest is missing required inputs: "
            + ", ".join(sorted(missing_inputs))
        )
    for input_name, expected_ref in RETURN_REGROUNDING_EXPECTED_INPUT_REFS.items():
        actual_ref = manifest_input_ref(inputs_by_name[input_name])
        if actual_ref != expected_ref:
            fail(
                f"return regrounding manifest {input_name} must point to "
                f"'{expected_ref}'"
            )

    dependency_refs_by_id, _ = load_source_owned_export_dependencies()

    modes: list[dict[str, object]] = []
    seen_mode_refs: set[str] = set()
    for binding in mode_bindings:
        if not isinstance(binding, dict):
            fail("return regrounding manifest mode_bindings entries must be objects")
        mode_ref = binding.get("mode_ref")
        primary_input = binding.get("primary_input")
        supporting_inputs = binding.get("supporting_inputs")
        dependency_refs = binding.get("dependency_refs", [])
        if not isinstance(mode_ref, str) or not mode_ref:
            fail("return regrounding mode binding must keep mode_ref")
        if mode_ref in seen_mode_refs:
            fail(f"duplicate return regrounding mode '{mode_ref}'")
        seen_mode_refs.add(mode_ref)
        if mode_ref not in RETURN_REGROUNDING_MODE_DETAILS:
            fail(f"unsupported return regrounding mode '{mode_ref}'")
        if not isinstance(primary_input, str) or not primary_input:
            fail(f"return regrounding mode '{mode_ref}' must keep primary_input")
        if not isinstance(supporting_inputs, list) or not supporting_inputs:
            fail(
                f"return regrounding mode '{mode_ref}' must keep supporting_inputs"
            )
        if not all(isinstance(value, str) and value for value in supporting_inputs):
            fail(
                f"return regrounding mode '{mode_ref}'.supporting_inputs contains an invalid entry"
            )
        if not isinstance(dependency_refs, list):
            fail(
                f"return regrounding mode '{mode_ref}'.dependency_refs must be a list when present"
            )
        if not all(isinstance(value, str) and value for value in dependency_refs):
            fail(
                f"return regrounding mode '{mode_ref}'.dependency_refs contains an invalid entry"
            )

        details = RETURN_REGROUNDING_MODE_DETAILS[mode_ref]
        if primary_input != details["primary_input"]:
            fail(
                f"return regrounding mode '{mode_ref}' must keep primary_input "
                f"'{details['primary_input']}'"
            )
        if supporting_inputs != details["supporting_inputs"]:
            fail(
                f"return regrounding mode '{mode_ref}' must keep the current supporting_inputs order"
            )
        if primary_input not in inputs_by_name:
            fail(
                f"return regrounding mode '{mode_ref}' references unknown primary input '{primary_input}'"
            )
        for supporting_input in supporting_inputs:
            if supporting_input not in inputs_by_name:
                fail(
                    "return regrounding mode "
                    f"'{mode_ref}' references unknown supporting input '{supporting_input}'"
                )
        for dependency_ref in dependency_refs:
            if dependency_ref not in dependency_refs_by_id:
                fail(
                    f"return regrounding mode '{mode_ref}' references unknown dependency '{dependency_ref}'"
                )
        if dependency_refs != details["dependency_refs"]:
            fail(
                f"return regrounding mode '{mode_ref}' must keep the current dependency_refs"
            )

        modes.append(
            {
                "mode_id": mode_ref,
                "used_when": details["used_when"],
                "query_mode_hint": details["query_mode_hint"],
                "trigger_surface_refs": list(details["trigger_surface_refs"]),
                "stronger_refs": list(details["stronger_refs"]),
                "supporting_surface_refs": list(details["supporting_surface_refs"]),
                "preserved_fields": list(details["preserved_fields"]),
                "reentry_note": details["reentry_note"],
                "non_identity_boundary": details["non_identity_boundary"],
                "prohibited_promotions": list(details["prohibited_promotions"]),
            }
        )

    if [mode["mode_id"] for mode in modes] != RETURN_REGROUNDING_MODE_ORDER:
        fail("return regrounding manifest mode_bindings must keep the current stable mode order")

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": "manifests/return_regrounding_pack.json",
        "source_inputs": emitted_source_inputs,
        "mode_count": len(modes),
        "modes": modes,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_counterpart_federation_exposure_review_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("counterpart federation exposure review manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    review_bindings = manifest.get("review_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("counterpart federation exposure review manifest must declare source_inputs")
    if not isinstance(review_bindings, list) or not review_bindings:
        fail("counterpart federation exposure review manifest must declare review_bindings")

    counterpart_consumer_contract = load_counterpart_consumer_contract_payload(
        registry_payload
    )
    reasoning_handoff_payload = build_reasoning_handoff_pack_payload()
    federation_spine_payload = build_federation_spine_payload(registry_payload)
    cross_source_payload = build_cross_source_node_projection_payload(registry_payload)
    tiny_bundle_payload = build_tiny_consumer_bundle_payload(registry_payload)

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    allow_same_run_generated_inputs = {
        "generated/reasoning_handoff_pack.min.json",
        "generated/tiny_consumer_bundle.min.json",
        "generated/federation_spine.min.json",
        "generated/cross_source_node_projection.min.json",
    }
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail(
                "counterpart federation exposure review manifest source_inputs entries "
                "must be objects"
            )
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(
                "counterpart federation exposure review manifest source_inputs must keep "
                "name, repo, path, and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate counterpart federation exposure review source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        allow_same_run_generated_input = repo == "aoa-kag" and path in allow_same_run_generated_inputs
        if not input_path.exists() and not allow_same_run_generated_input:
            fail(
                "counterpart federation exposure review donor input does not exist: "
                + repo_ref(repo, path)
            )
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    expected_input_order = [
        "reasoning_handoff_pack",
        "tiny_consumer_bundle",
        "federation_spine",
        "cross_source_node_projection",
        "counterpart_consumer_contract_doc",
        "counterpart_consumer_contract_example",
        "counterpart_edge_contract_doc",
        "counterpart_edge_contract_example",
    ]
    if list(inputs_by_name) != expected_input_order:
        fail(
            "counterpart federation exposure review manifest source_inputs must keep "
            "the current reviewed surface order"
        )

    current_allowed_refs = counterpart_consumer_contract["allowed_refs"]
    expected_reviewed_surface_ref = counterpart_consumer_contract[
        "federation_exposure_review_ref"
    ]
    if counterpart_consumer_contract["surface_status"] != "planned":
        fail(
            "counterpart federation exposure review requires AOA-K-0008 to remain "
            "planned in the current wave"
        )
    if expected_reviewed_surface_ref != COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF:
        fail(
            "counterpart federation exposure review requires the current counterpart "
            "consumer contract to stay aligned with the review artifact"
        )
    if (
        tiny_bundle_payload["deferred_counterpart"]["federation_exposure_review_ref"]
        != expected_reviewed_surface_ref
    ):
        fail(
            "counterpart federation exposure review requires the tiny consumer bundle "
            "to stay aligned with the review artifact"
        )

    reasoning_guardrail_refs = {
        ref
        for scenario in reasoning_handoff_payload["scenarios"]
        for ref in scenario["authoritative_refs"]["kag_guardrail_refs"]
    }
    if COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF not in reasoning_guardrail_refs:
        fail(
            "counterpart federation exposure review requires reasoning handoff "
            "guardrail refs to include the review doc"
        )

    federation_spine_refs = {
        source_input["ref"] for source_input in federation_spine_payload["source_inputs"]
    }
    if any(ref in current_allowed_refs for ref in federation_spine_refs):
        fail(
            "counterpart federation exposure review requires federation spine to avoid "
            "counterpart refs"
        )
    if any(
        repo.get("object_id") == "AOA-K-0008"
        for repo in federation_spine_payload["repos"]
        if isinstance(repo, dict)
    ):
        fail(
            "counterpart federation exposure review requires federation spine to avoid "
            "AOA-K-0008 activation hints"
        )

    cross_source_refs = {
        source_input["ref"] for source_input in cross_source_payload["source_inputs"]
    }
    if any(ref in current_allowed_refs for ref in cross_source_refs):
        fail(
            "counterpart federation exposure review requires cross-source projection to "
            "avoid counterpart refs"
        )
    if cross_source_payload["bounded_output_contract"].get("counterpart_activation") != "forbidden":
        fail(
            "counterpart federation exposure review requires cross-source projection to "
            "keep counterpart activation forbidden"
        )

    reviewed_surfaces: list[dict[str, object]] = []
    seen_surface_names: set[str] = set()
    for index, binding in enumerate(review_bindings):
        location = f"counterpart federation exposure review manifest review_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")

        surface_name = require_string(
            binding.get("surface_name"),
            label=f"{location}.surface_name",
        )
        surface_input = require_string(
            binding.get("surface_input"),
            label=f"{location}.surface_input",
        )
        exposure_posture = require_string(
            binding.get("exposure_posture"),
            label=f"{location}.exposure_posture",
        )
        review_note = require_string(
            binding.get("review_note"),
            label=f"{location}.review_note",
        )
        if surface_name in seen_surface_names:
            fail(f"{location}.surface_name must be unique")
        if surface_input not in inputs_by_name:
            fail(f"{location}.surface_input references unknown source input")
        if surface_name != surface_input:
            fail(f"{location}.surface_name must match surface_input in the current wave")
        seen_surface_names.add(surface_name)

        reviewed_surface: dict[str, object] = {
            "surface_name": surface_name,
            "surface_ref": manifest_input_ref(inputs_by_name[surface_input]),
            "exposure_posture": exposure_posture,
            "review_note": review_note,
        }

        allowed_counterpart_refs = binding.get("allowed_counterpart_refs")
        if allowed_counterpart_refs is not None:
            if not isinstance(allowed_counterpart_refs, list) or not allowed_counterpart_refs:
                fail(f"{location}.allowed_counterpart_refs must be a non-empty list")
            normalized_allowed_counterpart_refs = ordered_unique(
                [
                    ensure_local_ref_exists(
                        raw_ref,
                        label=f"{location}.allowed_counterpart_refs[{allowed_index}]",
                    )
                    for allowed_index, raw_ref in enumerate(allowed_counterpart_refs)
                ]
            )
            if len(normalized_allowed_counterpart_refs) != len(allowed_counterpart_refs):
                fail(f"{location}.allowed_counterpart_refs must not contain duplicates")
            if normalized_allowed_counterpart_refs != current_allowed_refs:
                fail(
                    f"{location}.allowed_counterpart_refs must stay aligned with the "
                    "current counterpart consumer contract"
                )
            reviewed_surface["allowed_counterpart_refs"] = normalized_allowed_counterpart_refs

        forbidden_refs = binding.get("forbidden_refs")
        if forbidden_refs is not None:
            if not isinstance(forbidden_refs, list) or not forbidden_refs:
                fail(f"{location}.forbidden_refs must be a non-empty list")
            normalized_forbidden_refs = ordered_unique(
                [
                    ensure_local_ref_exists(
                        raw_ref,
                        label=f"{location}.forbidden_refs[{forbidden_index}]",
                    )
                    for forbidden_index, raw_ref in enumerate(forbidden_refs)
                ]
            )
            if len(normalized_forbidden_refs) != len(forbidden_refs):
                fail(f"{location}.forbidden_refs must not contain duplicates")
            if normalized_forbidden_refs != current_allowed_refs:
                fail(
                    f"{location}.forbidden_refs must stay aligned with the current "
                    "forbidden counterpart ref set"
                )
            reviewed_surface["forbidden_refs"] = normalized_forbidden_refs

        reviewed_surfaces.append(reviewed_surface)

    if [record["surface_name"] for record in reviewed_surfaces] != expected_input_order:
        fail(
            "counterpart federation exposure review manifest review_bindings must keep "
            "the current reviewed surface order"
        )

    return {
        "review_version": manifest["manifest_version"],
        "review_type": manifest["review_type"],
        "source_manifest_ref": COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "surface_id": counterpart_consumer_contract["surface_id"],
        "surface_status": counterpart_consumer_contract["surface_status"],
        "review_status": "passed_for_planned_posture",
        "reviewed_surface_count": len(reviewed_surfaces),
        "reviewed_surfaces": reviewed_surfaces,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_tiny_consumer_bundle_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TINY_CONSUMER_BUNDLE_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("tiny consumer bundle manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    bundle_order = manifest.get("bundle_order")
    deferred_counterpart = manifest.get("deferred_counterpart")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("tiny consumer bundle manifest must declare source_inputs")
    if not isinstance(bundle_order, list) or not bundle_order:
        fail("tiny consumer bundle manifest must declare bundle_order")
    if not isinstance(deferred_counterpart, dict):
        fail("tiny consumer bundle manifest must declare deferred_counterpart")

    counterpart_consumer_contract = load_counterpart_consumer_contract_payload(
        registry_payload
    )

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    allow_same_run_generated_inputs = {
        "generated/tos_text_chunk_map.min.json",
        "generated/tos_retrieval_axis_pack.min.json",
        "generated/federation_spine.min.json",
        "generated/cross_source_node_projection.min.json",
    }
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("tiny consumer bundle manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(
                "tiny consumer bundle manifest source_inputs must keep name, repo, path, "
                "and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate tiny consumer bundle source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        allow_same_run_generated_input = (
            repo == "aoa-kag" and path in allow_same_run_generated_inputs
        )
        if not input_path.exists() and not allow_same_run_generated_input:
            fail(
                "tiny consumer bundle donor input does not exist: "
                + repo_ref(repo, path)
            )
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    ordered_input_names = [
        require_string(
            raw_name,
            label=f"tiny consumer bundle manifest bundle_order[{index}]",
        )
        for index, raw_name in enumerate(bundle_order)
    ]
    if len(ordered_unique(ordered_input_names)) != len(ordered_input_names):
        fail("tiny consumer bundle manifest bundle_order must not contain duplicates")
    if set(ordered_input_names) != set(inputs_by_name):
        fail(
            "tiny consumer bundle manifest bundle_order must reference each declared "
            "source input exactly once"
        )
    if ordered_input_names != [
        "tos_text_chunk_map",
        "tos_retrieval_axis_pack",
        "federation_spine",
        "cross_source_node_projection",
        "consumer_guide",
        "counterpart_consumer_contract_doc",
        "counterpart_consumer_contract_example",
    ]:
        fail(
            "tiny consumer bundle manifest bundle_order must keep the current stable "
            "consumer chain order"
        )

    surface_id = require_string(
        deferred_counterpart.get("surface_id"),
        label="tiny consumer bundle manifest deferred_counterpart.surface_id",
    )
    surface_status = require_string(
        deferred_counterpart.get("surface_status"),
        label="tiny consumer bundle manifest deferred_counterpart.surface_status",
    )
    posture = require_string(
        deferred_counterpart.get("posture"),
        label="tiny consumer bundle manifest deferred_counterpart.posture",
    )
    federation_exposure_review_ref = ensure_local_ref_exists(
        deferred_counterpart.get("federation_exposure_review_ref"),
        label=(
            "tiny consumer bundle manifest deferred_counterpart."
            "federation_exposure_review_ref"
        ),
        allow_missing_refs={COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_REF},
    )
    if surface_id != counterpart_consumer_contract["surface_id"]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart.surface_id must stay "
            "aligned with the counterpart consumer contract"
        )
    if surface_status != counterpart_consumer_contract["surface_status"]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart.surface_status must stay "
            "aligned with the counterpart consumer contract"
        )
    if posture != "planned_contract_only":
        fail(
            "tiny consumer bundle manifest deferred_counterpart.posture must equal "
            "'planned_contract_only'"
        )
    if (
        federation_exposure_review_ref
        != counterpart_consumer_contract["federation_exposure_review_ref"]
    ):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "federation_exposure_review_ref must stay aligned with the counterpart "
            "consumer contract"
        )

    allowed_refs = deferred_counterpart.get("allowed_refs")
    if not isinstance(allowed_refs, list) or not allowed_refs:
        fail(
            "tiny consumer bundle manifest deferred_counterpart.allowed_refs must be a "
            "non-empty list"
        )
    normalized_allowed_refs = ordered_unique(
        [
            ensure_local_ref_exists(
                raw_ref,
                label=(
                    "tiny consumer bundle manifest deferred_counterpart."
                    f"allowed_refs[{index}]"
                ),
            )
            for index, raw_ref in enumerate(allowed_refs)
        ]
    )
    if len(normalized_allowed_refs) != len(allowed_refs):
        fail(
            "tiny consumer bundle manifest deferred_counterpart.allowed_refs must not "
            "contain duplicates"
        )
    if normalized_allowed_refs != counterpart_consumer_contract["allowed_refs"]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart.allowed_refs must stay "
            "aligned with the counterpart consumer contract"
        )

    forbidden_active_payload_refs = deferred_counterpart.get(
        "forbidden_active_payload_refs"
    )
    if (
        not isinstance(forbidden_active_payload_refs, list)
        or not forbidden_active_payload_refs
    ):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_active_payload_refs must be a non-empty list"
        )
    normalized_forbidden_active_payload_refs = ordered_unique(
        [
            ensure_local_ref_exists(
                raw_ref,
                label=(
                    "tiny consumer bundle manifest deferred_counterpart."
                    f"forbidden_active_payload_refs[{index}]"
                ),
            )
            for index, raw_ref in enumerate(forbidden_active_payload_refs)
        ]
    )
    if (
        len(normalized_forbidden_active_payload_refs)
        != len(forbidden_active_payload_refs)
    ):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_active_payload_refs must not contain duplicates"
        )
    if normalized_forbidden_active_payload_refs != [COUNTERPART_EDGE_EXAMPLE_REF]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_active_payload_refs must keep the current deferred counterpart "
            "payload boundary"
        )

    forbidden_interpretations = deferred_counterpart.get("forbidden_interpretations")
    if (
        not isinstance(forbidden_interpretations, list)
        or not forbidden_interpretations
    ):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_interpretations must be a non-empty list"
        )
    normalized_forbidden_interpretations = ordered_unique(
        [
            require_string(
                raw_value,
                label=(
                    "tiny consumer bundle manifest deferred_counterpart."
                    f"forbidden_interpretations[{index}]"
                ),
            )
            for index, raw_value in enumerate(forbidden_interpretations)
        ]
    )
    if len(normalized_forbidden_interpretations) != len(forbidden_interpretations):
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_interpretations must not contain duplicates"
        )
    if normalized_forbidden_interpretations != [
        "active_retrieval_payload",
        "active_projection_payload",
    ]:
        fail(
            "tiny consumer bundle manifest deferred_counterpart."
            "forbidden_interpretations must keep the current deferred posture"
        )

    bundle_items = [
        {
            "order": index + 1,
            "name": input_name,
            "role": inputs_by_name[input_name]["role"],
            "ref": manifest_input_ref(inputs_by_name[input_name]),
        }
        for index, input_name in enumerate(ordered_input_names)
    ]

    return {
        "bundle_version": manifest["manifest_version"],
        "bundle_type": manifest["bundle_type"],
        "source_manifest_ref": TINY_CONSUMER_BUNDLE_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "bundle_item_count": len(bundle_items),
        "bundle_items": bundle_items,
        "deferred_counterpart": {
            "surface_id": surface_id,
            "surface_status": surface_status,
            "posture": posture,
            "federation_exposure_review_ref": federation_exposure_review_ref,
            "allowed_refs": normalized_allowed_refs,
            "forbidden_active_payload_refs": (
                normalized_forbidden_active_payload_refs
            ),
            "forbidden_interpretations": normalized_forbidden_interpretations,
        },
    }


def write_generated_outputs() -> list[Path]:
    registry_payload = build_registry_payload()
    technique_lift_pack_payload = build_technique_lift_pack_payload(registry_payload)
    tos_text_chunk_map_payload = build_tos_text_chunk_map_payload(registry_payload)
    tos_retrieval_axis_pack_payload = build_tos_retrieval_axis_pack_payload(
        registry_payload
    )
    tos_zarathustra_route_pack_payload = build_tos_zarathustra_route_pack_payload(
        registry_payload
    )
    reasoning_handoff_pack_payload = build_reasoning_handoff_pack_payload()
    federation_spine_payload = build_federation_spine_payload(registry_payload)
    cross_source_node_projection_payload = build_cross_source_node_projection_payload(
        registry_payload
    )
    return_regrounding_pack_payload = build_return_regrounding_pack_payload(
        registry_payload
    )
    counterpart_federation_exposure_review_payload = (
        build_counterpart_federation_exposure_review_payload(registry_payload)
    )
    tiny_consumer_bundle_payload = build_tiny_consumer_bundle_payload(registry_payload)

    write_json(REGISTRY_OUTPUT_PATH, registry_payload, pretty=True)
    write_json(REGISTRY_MIN_OUTPUT_PATH, registry_payload, pretty=False)
    write_json(TECHNIQUE_LIFT_OUTPUT_PATH, technique_lift_pack_payload, pretty=True)
    write_json(TECHNIQUE_LIFT_MIN_OUTPUT_PATH, technique_lift_pack_payload, pretty=False)
    write_json(TOS_TEXT_CHUNK_MAP_OUTPUT_PATH, tos_text_chunk_map_payload, pretty=True)
    write_json(
        TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
        tos_text_chunk_map_payload,
        pretty=False,
    )
    write_json(
        TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
        tos_retrieval_axis_pack_payload,
        pretty=True,
    )
    write_json(
        TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
        tos_retrieval_axis_pack_payload,
        pretty=False,
    )
    write_json(
        TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH,
        tos_zarathustra_route_pack_payload,
        pretty=True,
    )
    write_json(
        TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH,
        tos_zarathustra_route_pack_payload,
        pretty=False,
    )
    write_json(REASONING_HANDOFF_OUTPUT_PATH, reasoning_handoff_pack_payload, pretty=True)
    write_json(
        REASONING_HANDOFF_MIN_OUTPUT_PATH,
        reasoning_handoff_pack_payload,
        pretty=False,
    )
    write_json(FEDERATION_SPINE_OUTPUT_PATH, federation_spine_payload, pretty=True)
    write_json(
        FEDERATION_SPINE_MIN_OUTPUT_PATH,
        federation_spine_payload,
        pretty=False,
    )
    write_json(
        CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
        cross_source_node_projection_payload,
        pretty=True,
    )
    write_json(
        CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
        cross_source_node_projection_payload,
        pretty=False,
    )
    write_json(
        RETURN_REGROUNDING_OUTPUT_PATH,
        return_regrounding_pack_payload,
        pretty=True,
    )
    write_json(
        RETURN_REGROUNDING_MIN_OUTPUT_PATH,
        return_regrounding_pack_payload,
        pretty=False,
    )
    write_json(
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
        counterpart_federation_exposure_review_payload,
        pretty=True,
    )
    write_json(
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
        counterpart_federation_exposure_review_payload,
        pretty=False,
    )
    write_json(TINY_CONSUMER_BUNDLE_OUTPUT_PATH, tiny_consumer_bundle_payload, pretty=True)
    write_json(
        TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
        tiny_consumer_bundle_payload,
        pretty=False,
    )

    return [
        REGISTRY_OUTPUT_PATH,
        REGISTRY_MIN_OUTPUT_PATH,
        TECHNIQUE_LIFT_OUTPUT_PATH,
        TECHNIQUE_LIFT_MIN_OUTPUT_PATH,
        TOS_TEXT_CHUNK_MAP_OUTPUT_PATH,
        TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_PATH,
        TOS_RETRIEVAL_AXIS_OUTPUT_PATH,
        TOS_RETRIEVAL_AXIS_MIN_OUTPUT_PATH,
        TOS_ZARATHUSTRA_ROUTE_PACK_OUTPUT_PATH,
        TOS_ZARATHUSTRA_ROUTE_PACK_MIN_OUTPUT_PATH,
        REASONING_HANDOFF_OUTPUT_PATH,
        REASONING_HANDOFF_MIN_OUTPUT_PATH,
        FEDERATION_SPINE_OUTPUT_PATH,
        FEDERATION_SPINE_MIN_OUTPUT_PATH,
        CROSS_SOURCE_NODE_PROJECTION_OUTPUT_PATH,
        CROSS_SOURCE_NODE_PROJECTION_MIN_OUTPUT_PATH,
        RETURN_REGROUNDING_OUTPUT_PATH,
        RETURN_REGROUNDING_MIN_OUTPUT_PATH,
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_OUTPUT_PATH,
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH,
        TINY_CONSUMER_BUNDLE_OUTPUT_PATH,
        TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH,
    ]
