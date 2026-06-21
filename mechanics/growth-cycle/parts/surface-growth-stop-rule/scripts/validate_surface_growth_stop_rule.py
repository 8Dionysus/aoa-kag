#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[5]

MATURITY_DOC = Path("mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-maturity-governance.md")
OWNER_WAIT_DOC = Path("mechanics/growth-cycle/parts/surface-growth-stop-rule/docs/kag-owner-wait-states.md")
PROOF_EXPECTATIONS_DOC = Path("mechanics/audit/parts/proof-expectation-refs/docs/kag-proof-expectations.md")
MATURITY_DECISION = Path("docs/decisions/AOA-KAG-D-0001-kag-maturity-hardening.md")
MANIFEST = Path("mechanics/growth-cycle/parts/surface-growth-stop-rule/manifests/kag_maturity_governance.json")
GENERATED_MIN = Path("mechanics/growth-cycle/parts/surface-growth-stop-rule/generated/kag_maturity_governance.min.json")
EXAMPLE = Path("mechanics/growth-cycle/parts/surface-growth-stop-rule/examples/kag_maturity_governance.example.json")
BLOCKED_SURFACE_IDS = ["AOA-K-0008"]
EXPECTED_OWNER_WAIT_REPOS = [
    "aoa-techniques",
    "Tree-of-Sophia",
    "aoa-memo",
    "aoa-evals",
    "aoa-playbooks",
    "aoa-agents",
    "aoa-skills",
    "aoa-routing",
    "aoa-stats",
]
EXPECTED_STABILITY_TIERS = [
    "planned_contract_only",
    "experimental_derived",
    "consumer_stable",
]
EXPECTED_BOUNDED_OUTPUT_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "routing_ownership": "forbidden",
    "memory_truth_ownership": "forbidden",
    "proof_ownership": "forbidden",
    "new_surface_growth": "paused_by_owner_need",
    "quarantine_shortcuts": "forbidden",
}
REQUIRED_MATURITY_DOC_SNIPPETS = (
    "refuse new surface growth unless a bounded need is explicit",
    "Stop-rule for new `AOA-K-*`",
    "Net-new `AOA-K-*` surfaces should be rare and gated.",
)
REQUIRED_OWNER_WAIT_DOC_SNIPPETS = (
    "not yet",
    "KAG must not infer",
    "`aoa-evals` | reference proof anchors",
)


class SurfaceGrowthStopRuleError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise SurfaceGrowthStopRuleError(message)


def display_path(path: Path, repo_root: Path = REPO_ROOT) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {display_path(path)}: {exc}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")


def require_mapping(payload: object, label: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        fail(f"{label} must be a JSON object")
    return payload


def require_non_empty_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        fail(f"{label} must be a non-empty list")
    if any(not isinstance(item, str) or not item for item in value):
        fail(f"{label} must contain non-empty strings only")
    return list(value)


def validate_docs(repo_root: Path) -> None:
    maturity_doc = read_text(repo_root / MATURITY_DOC)
    for snippet in REQUIRED_MATURITY_DOC_SNIPPETS:
        if snippet not in maturity_doc:
            fail(f"{MATURITY_DOC.as_posix()} must mention {snippet!r}")

    owner_wait_doc = read_text(repo_root / OWNER_WAIT_DOC)
    for snippet in REQUIRED_OWNER_WAIT_DOC_SNIPPETS:
        if snippet not in owner_wait_doc:
            fail(f"{OWNER_WAIT_DOC.as_posix()} must mention {snippet!r}")

    for path in (PROOF_EXPECTATIONS_DOC, MATURITY_DECISION):
        if not (repo_root / path).is_file():
            fail(f"missing required file: {path.as_posix()}")


def validate_manifest_payload(payload: dict[str, Any]) -> None:
    if payload.get("manifest_version") != 1:
        fail("maturity manifest version must stay 1")
    if payload.get("pack_type") != "kag_maturity_governance":
        fail("maturity manifest pack_type must equal kag_maturity_governance")

    source_inputs = payload.get("source_inputs")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("maturity manifest source_inputs must be a non-empty list")
    source_input_refs = {
        entry.get("path")
        for entry in source_inputs
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }
    for required in (
        MATURITY_DOC.as_posix(),
        OWNER_WAIT_DOC.as_posix(),
        PROOF_EXPECTATIONS_DOC.as_posix(),
        MATURITY_DECISION.as_posix(),
    ):
        if required not in source_input_refs:
            fail(f"maturity manifest source_inputs must include {required}")

    tier_names = [
        tier.get("tier")
        for tier in payload.get("stability_tiers", [])
        if isinstance(tier, dict)
    ]
    if tier_names != EXPECTED_STABILITY_TIERS:
        fail("maturity manifest stability_tiers must keep the current stable order")

    owner_wait_states = payload.get("owner_wait_states")
    if not isinstance(owner_wait_states, list):
        fail("maturity manifest owner_wait_states must be a list")
    owner_repos = [
        state.get("owner_repo")
        for state in owner_wait_states
        if isinstance(state, dict)
    ]
    if owner_repos != EXPECTED_OWNER_WAIT_REPOS:
        fail("maturity manifest owner_wait_states must keep the current owner wait-state order")
    for state in owner_wait_states:
        if not isinstance(state, dict):
            fail("maturity manifest owner_wait_states entries must be objects")
        waits_for = require_non_empty_string_list(
            state.get("waits_for"),
            f"maturity manifest owner_wait_state {state.get('owner_repo')}.waits_for",
        )
        forbidden_inference = state.get("forbidden_inference")
        if not isinstance(forbidden_inference, str) or "Do not infer" not in forbidden_inference:
            fail(
                f"maturity manifest owner_wait_state {state.get('owner_repo')} must keep explicit forbidden inference"
            )
        if len(waits_for) < 1:
            fail(f"maturity manifest owner_wait_state {state.get('owner_repo')} waits_for is empty")

    stop_rule = require_mapping(payload.get("stop_rule"), "maturity manifest stop_rule")
    if stop_rule.get("new_surface_growth") != "paused_by_default":
        fail("maturity manifest stop_rule.new_surface_growth must stay paused_by_default")
    if stop_rule.get("current_program") != "stabilize_existing_aoa_k_surfaces":
        fail("maturity manifest stop_rule.current_program must stabilize existing surfaces")
    if stop_rule.get("blocked_surface_ids") != BLOCKED_SURFACE_IDS:
        fail("maturity manifest stop_rule.blocked_surface_ids must keep AOA-K-0008 blocked")
    require_non_empty_string_list(
        stop_rule.get("resume_when"),
        "maturity manifest stop_rule.resume_when",
    )
    pause_threshold = stop_rule.get("pause_threshold")
    if not isinstance(pause_threshold, str) or "No new AOA-K surfaces" not in pause_threshold:
        fail("maturity manifest stop_rule.pause_threshold must keep the no-new-surface pause")

    if payload.get("bounded_output_contract") != EXPECTED_BOUNDED_OUTPUT_CONTRACT:
        fail("maturity manifest bounded_output_contract must keep source-first stop-rule contract")


def validate_generated_payload(payload: dict[str, Any], manifest: dict[str, Any]) -> None:
    if payload.get("source_manifest_ref") != MANIFEST.as_posix():
        fail("maturity pack source_manifest_ref must point to the manifest")
    if payload.get("stop_rule") != manifest.get("stop_rule"):
        fail("maturity pack stop_rule must match the manifest")
    if payload.get("bounded_output_contract") != manifest.get("bounded_output_contract"):
        fail("maturity pack bounded_output_contract must match the manifest")

    owner_wait_states = payload.get("owner_wait_states")
    if not isinstance(owner_wait_states, list):
        fail("maturity pack owner_wait_states must be a list")
    if payload.get("owner_wait_state_count") != len(owner_wait_states):
        fail("maturity pack owner_wait_state_count must match owner_wait_states")
    owner_repos = [
        state.get("owner_repo")
        for state in owner_wait_states
        if isinstance(state, dict)
    ]
    if owner_repos != EXPECTED_OWNER_WAIT_REPOS:
        fail("maturity pack owner_wait_states must keep the current owner wait-state order")

    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        fail("maturity pack surfaces must be a non-empty list")
    surfaces_by_id = {
        surface.get("surface_id"): surface
        for surface in surfaces
        if isinstance(surface, dict)
    }
    blocked_surface = surfaces_by_id.get("AOA-K-0008")
    if not isinstance(blocked_surface, dict):
        fail("maturity pack must keep AOA-K-0008 visible")
    if blocked_surface.get("stability_tier") != "planned_contract_only":
        fail("maturity pack must keep AOA-K-0008 planned_contract_only")
    if blocked_surface.get("stop_rule") != "blocked_until_owner_exports_and_proof_lanes_strengthen":
        fail("maturity pack must keep AOA-K-0008 blocked by owner exports and proof lanes")


def validate_example_payload(payload: dict[str, Any]) -> None:
    if payload.get("source_manifest_ref") != MANIFEST.as_posix():
        fail("maturity example source_manifest_ref must point to the manifest")
    if payload.get("bounded_output_contract") != EXPECTED_BOUNDED_OUTPUT_CONTRACT:
        fail("maturity example bounded_output_contract must keep source-first stop-rule contract")
    stop_rule = require_mapping(payload.get("stop_rule"), "maturity example stop_rule")
    if stop_rule.get("blocked_surface_ids") != BLOCKED_SURFACE_IDS:
        fail("maturity example must keep AOA-K-0008 blocked")
    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces or not isinstance(surfaces[0], dict):
        fail("maturity example must expose at least one surface")
    if surfaces[0].get("surface_id") != "AOA-K-0008":
        fail("maturity example must center AOA-K-0008")
    if surfaces[0].get("stability_tier") != "planned_contract_only":
        fail("maturity example must keep AOA-K-0008 planned_contract_only")


def validate_surface_growth_stop_rule(repo_root: Path = REPO_ROOT) -> None:
    validate_docs(repo_root)
    manifest = require_mapping(read_json(repo_root / MANIFEST), "maturity manifest")
    validate_manifest_payload(manifest)
    generated = require_mapping(read_json(repo_root / GENERATED_MIN), "maturity pack")
    validate_generated_payload(generated, manifest)
    example = require_mapping(read_json(repo_root / EXAMPLE), "maturity example")
    validate_example_payload(example)


def main() -> int:
    try:
        validate_surface_growth_stop_rule(REPO_ROOT)
    except SurfaceGrowthStopRuleError as exc:
        print(f"[error] {exc}")
        return 1
    print("[ok] validated surface-growth stop-rule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
