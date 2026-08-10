#!/usr/bin/env python3
"""Run the common owner-family KAG gate as a fail-fast component DAG.

The gate preserves the existing blocking commands.  It runs the incremental
parity check first as a drift sentinel; only a clean candidate fans out to the
full parity check, family validator, and deterministic compatibility assembly.
Parallelism changes scheduling only.  Every canonical command must still pass.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

try:
    from scripts import prepare_landing as isolation
except ImportError:  # pragma: no cover - direct script execution
    import prepare_landing as isolation  # type: ignore


KAG_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoa-kag-owner-family-gate-receipt-v1"
SENTINEL_SCHEMA_VERSION = "aoa-kag-owner-family-sentinel-receipt-v1"
DEFAULT_OUTPUT = "kag/indexes/source_surface_index.json"
MAX_OUTPUT_CHARS = 4_000


@dataclass(frozen=True)
class Component:
    component_id: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class ComponentResult:
    component_id: str
    command: tuple[str, ...]
    returncode: int
    duration_ms: int
    stdout: str
    stderr: str

    def payload(self) -> dict[str, object]:
        return {
            "component_id": self.component_id,
            "command": list(self.command),
            "returncode": self.returncode,
            "duration_ms": self.duration_ms,
            "stdout_tail": self.stdout[-MAX_OUTPUT_CHARS:],
            "stderr_tail": self.stderr[-MAX_OUTPUT_CHARS:],
        }


def canonical_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def git_bytes(repo_root: Path, *args: str) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout


def git_text(repo_root: Path, *args: str) -> str:
    return git_bytes(repo_root, *args).decode("utf-8", errors="strict").strip()


def candidate_identity(repo_root: Path) -> dict[str, str]:
    snapshot = isolation.capture_candidate_snapshot(repo_root)
    return {
        "repo_root": repo_root.as_posix(),
        "head": snapshot.head,
        "index_tree": snapshot.index_tree,
        # A read-only validator can advance access times merely by observing
        # candidate bytes. Full isolation still binds and restores atime via
        # CandidateSnapshot.identity and equality; same-candidate scheduling
        # must distinguish those observations from actual candidate mutation.
        "candidate_identity": snapshot.mutation_identity(),
        "cached_diff_digest": snapshot.cached_diff_digest,
        "worktree_diff_digest": snapshot.worktree_diff_digest,
        "untracked_digest": snapshot.untracked_digest,
        "untracked_paths_digest": sha256_bytes(
            canonical_json(list(snapshot.untracked_paths))
        ),
    }


def run_component(component: Component, *, repo_root: Path) -> ComponentResult:
    started = time.perf_counter()
    environment = dict(os.environ)
    # Fresh Python checkouts otherwise create ignored __pycache__ directories.
    # Their creation changes protected parent-directory mtimes and violates the
    # same-candidate contract even though every canonical command is --check.
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(
        component.command,
        cwd=repo_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    return ComponentResult(
        component_id=component.component_id,
        command=component.command,
        returncode=process.returncode,
        duration_ms=round((time.perf_counter() - started) * 1000),
        stdout=process.stdout,
        stderr=process.stderr,
    )


def generator_command(
    *,
    repo_root: Path,
    output: str,
    history_ref: str,
    event_history_ref: str,
    budget_base_ref: str,
    incremental: bool,
) -> tuple[str, ...]:
    command = [
        sys.executable,
        (KAG_ROOT / "scripts" / "generate_repo_local_kag_index.py").as_posix(),
        "--repo-root",
        repo_root.as_posix(),
        "--output",
        output,
        "--portable-family",
    ]
    if incremental:
        command.append("--incremental")
    command.extend(
        (
            "--history-ref",
            history_ref,
            "--event-history-ref",
            event_history_ref,
            "--budget-base-ref",
            budget_base_ref,
            "--check",
        )
    )
    return tuple(command)


def downstream_components(
    *,
    repo_root: Path,
    output: str,
    history_ref: str,
    event_history_ref: str,
    budget_base_ref: str,
    compatibility_output: Path,
) -> tuple[Component, ...]:
    return (
        Component(
            "full-parity",
            generator_command(
                repo_root=repo_root,
                output=output,
                history_ref=history_ref,
                event_history_ref=event_history_ref,
                budget_base_ref=budget_base_ref,
                incremental=False,
            ),
        ),
        Component(
            "family-contract",
            (
                sys.executable,
                (KAG_ROOT / "scripts" / "validate_repo_local_kag_family.py").as_posix(),
                "--repo-root",
                repo_root.as_posix(),
                "--source-index",
                output,
            ),
        ),
        Component(
            "compatibility-assembly",
            (
                sys.executable,
                (KAG_ROOT / "scripts" / "assemble_repo_local_kag_family.py").as_posix(),
                "--repo-root",
                repo_root.as_posix(),
                "--output-dir",
                compatibility_output.as_posix(),
            ),
        ),
    )


def sentinel_component(
    *,
    repo_root: Path,
    output: str,
    history_ref: str,
    event_history_ref: str,
    budget_base_ref: str,
) -> Component:
    return Component(
        "incremental-drift-sentinel",
        generator_command(
            repo_root=repo_root,
            output=output,
            history_ref=history_ref,
            event_history_ref=event_history_ref,
            budget_base_ref=budget_base_ref,
            incremental=True,
        ),
    )


def run_sentinel_gate(
    *,
    repo_root: Path,
    output: str,
    history_ref: str,
    event_history_ref: str,
    budget_base_ref: str,
) -> tuple[int, dict[str, object]]:
    started = time.perf_counter()
    initial_identity = candidate_identity(repo_root)
    sentinel = sentinel_component(
        repo_root=repo_root,
        output=output,
        history_ref=history_ref,
        event_history_ref=event_history_ref,
        budget_base_ref=budget_base_ref,
    )
    result = run_component(sentinel, repo_root=repo_root)
    identity_stable = candidate_identity(repo_root) == initial_identity
    successful = result.returncode == 0 and identity_stable
    receipt: dict[str, object] = {
        "schema_version": SENTINEL_SCHEMA_VERSION,
        "verdict": "verified" if successful else "failed",
        "candidate": initial_identity,
        "candidate_stable": identity_stable,
        "refs": {
            "history_ref": history_ref,
            "event_history_ref": event_history_ref,
            "budget_base_ref": budget_base_ref,
        },
        "components": [result.payload()],
        "duration_ms": round((time.perf_counter() - started) * 1000),
        "proof_boundary": {
            "claim": "same-candidate-incremental-drift-sentinel",
            "does_not_replace": [
                "full-parity",
                "family-contract",
                "compatibility-assembly",
                "owner-release-gate",
            ],
        },
    }
    if not identity_stable:
        receipt["failure_type"] = "candidate_identity_changed"
        receipt["action_class"] = "retry_stable_candidate"
    elif result.returncode != 0:
        receipt["failure_type"] = "owner_family_drift"
        receipt["action_class"] = "regenerate_owner_family"
    return (0 if successful else 1), receipt


def validated_sentinel_handoff(
    payload: object,
    *,
    candidate: dict[str, str],
    expected_component: Component,
    refs: dict[str, str],
) -> ComponentResult:
    if not isinstance(payload, dict):
        raise ValueError("sentinel handoff is not an object")
    if payload.get("schema_version") != SENTINEL_SCHEMA_VERSION:
        raise ValueError("sentinel handoff schema is invalid")
    if payload.get("verdict") != "verified" or payload.get("candidate_stable") is not True:
        raise ValueError("sentinel handoff is not a stable verified result")
    if payload.get("candidate") != candidate:
        raise ValueError("sentinel handoff candidate identity does not match")
    if payload.get("refs") != refs:
        raise ValueError("sentinel handoff history boundaries do not match")
    components = payload.get("components")
    if not isinstance(components, list) or len(components) != 1:
        raise ValueError("sentinel handoff must contain exactly one component")
    component = components[0]
    if not isinstance(component, dict):
        raise ValueError("sentinel handoff component is not an object")
    if component.get("component_id") != expected_component.component_id:
        raise ValueError("sentinel handoff component id does not match")
    if component.get("command") != list(expected_component.command):
        raise ValueError("sentinel handoff command does not match")
    if component.get("returncode") != 0:
        raise ValueError("sentinel handoff component did not pass")
    return ComponentResult(
        component_id=expected_component.component_id,
        command=expected_component.command,
        returncode=0,
        duration_ms=int(component.get("duration_ms") or 0),
        stdout=str(component.get("stdout_tail") or ""),
        stderr=str(component.get("stderr_tail") or ""),
    )


def run_gate(
    *,
    repo_root: Path,
    output: str,
    history_ref: str,
    event_history_ref: str,
    budget_base_ref: str,
    jobs: int,
    sentinel_receipt: object | None = None,
) -> tuple[int, dict[str, object]]:
    started = time.perf_counter()
    initial_identity = candidate_identity(repo_root)
    refs = {
        "history_ref": history_ref,
        "event_history_ref": event_history_ref,
        "budget_base_ref": budget_base_ref,
    }
    sentinel = sentinel_component(
        repo_root=repo_root,
        output=output,
        history_ref=history_ref,
        event_history_ref=event_history_ref,
        budget_base_ref=budget_base_ref,
    )
    handoff_error: str | None = None
    if sentinel_receipt is None:
        sentinel_result = run_component(sentinel, repo_root=repo_root)
        sentinel_source = "inline"
    else:
        sentinel_source = "same-run-handoff"
        try:
            sentinel_result = validated_sentinel_handoff(
                sentinel_receipt,
                candidate=initial_identity,
                expected_component=sentinel,
                refs=refs,
            )
        except (TypeError, ValueError) as exc:
            handoff_error = str(exc)
            sentinel_result = ComponentResult(
                component_id=sentinel.component_id,
                command=sentinel.command,
                returncode=1,
                duration_ms=0,
                stdout="",
                stderr=handoff_error,
            )
    results = [sentinel_result]
    if sentinel_result.returncode == 0:
        with tempfile.TemporaryDirectory(prefix="aoa-kag-owner-family-") as temp_dir:
            components = downstream_components(
                repo_root=repo_root,
                output=output,
                history_ref=history_ref,
                event_history_ref=event_history_ref,
                budget_base_ref=budget_base_ref,
                compatibility_output=Path(temp_dir) / "compatibility",
            )
            if jobs == 1:
                results.extend(
                    run_component(component, repo_root=repo_root)
                    for component in components
                )
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
                    futures = {
                        component.component_id: pool.submit(
                            run_component,
                            component,
                            repo_root=repo_root,
                        )
                        for component in components
                    }
                    for component in components:
                        results.append(futures[component.component_id].result())

    final_identity = candidate_identity(repo_root)
    identity_stable = final_identity == initial_identity
    successful = all(result.returncode == 0 for result in results)
    complete = len(results) == 4
    receipt: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "verdict": "verified" if successful and complete and identity_stable else "failed",
        "candidate": initial_identity,
        "candidate_stable": identity_stable,
        "refs": refs,
        "sentinel_source": sentinel_source,
        "scheduler": {
            "jobs": jobs,
            "sentinel_first": True,
            "downstream_fanout": [
                "full-parity",
                "family-contract",
                "compatibility-assembly",
            ],
        },
        "components": [result.payload() for result in results],
        "duration_ms": round((time.perf_counter() - started) * 1000),
        "proof_boundary": {
            "claim": "same-candidate-canonical-owner-family-commands",
            "does_not_replace": [
                "source-fast",
                "owner-release-gate",
                "os-wide-provider-proof",
                "landing-verdict",
            ],
        },
    }
    if not identity_stable:
        receipt["failure_type"] = "candidate_identity_changed"
    elif handoff_error is not None:
        receipt["failure_type"] = "sentinel_handoff_invalid"
        receipt["action_class"] = "rerun_stable_candidate"
        receipt["handoff_error"] = handoff_error
    elif sentinel_result.returncode != 0:
        receipt["failure_type"] = "owner_family_drift"
        receipt["action_class"] = "regenerate_owner_family"
    elif not successful or not complete:
        receipt["failure_type"] = "owner_family_proof_failed"
        receipt["action_class"] = "fix_candidate"
    return (0 if receipt["verdict"] == "verified" else 1), receipt


def write_receipt(path: Path, receipt: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, path)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the canonical repo-local KAG family gate as a fail-fast DAG."
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--history-ref", required=True)
    parser.add_argument("--event-history-ref", required=True)
    parser.add_argument("--budget-base-ref")
    parser.add_argument("--jobs", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--sentinel-only", action="store_true")
    parser.add_argument("--sentinel-receipt", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    if git_text(repo_root, "rev-parse", "--show-toplevel") != repo_root.as_posix():
        raise SystemExit("--repo-root must name the Git top level")
    budget_base_ref = args.budget_base_ref or args.history_ref
    if args.sentinel_only and args.sentinel_receipt is not None:
        raise SystemExit("--sentinel-only and --sentinel-receipt are mutually exclusive")
    if args.sentinel_only:
        code, receipt = run_sentinel_gate(
            repo_root=repo_root,
            output=args.output,
            history_ref=args.history_ref,
            event_history_ref=args.event_history_ref,
            budget_base_ref=budget_base_ref,
        )
    else:
        sentinel_receipt: object | None = None
        if args.sentinel_receipt is not None:
            try:
                sentinel_receipt = json.loads(args.sentinel_receipt.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                sentinel_receipt = {"load_error": str(exc)}
        code, receipt = run_gate(
            repo_root=repo_root,
            output=args.output,
            history_ref=args.history_ref,
            event_history_ref=args.event_history_ref,
            budget_base_ref=budget_base_ref,
            jobs=args.jobs,
            sentinel_receipt=sentinel_receipt,
        )
    for component in receipt["components"]:
        if component["returncode"] != 0:
            print(
                f"[repo-local-kag-gate] {component['component_id']} failed",
                file=sys.stderr,
            )
            if component["stdout_tail"]:
                print(component["stdout_tail"], file=sys.stderr)
            if component["stderr_tail"]:
                print(component["stderr_tail"], file=sys.stderr)
    if args.receipt_output is not None:
        write_receipt(args.receipt_output, receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
