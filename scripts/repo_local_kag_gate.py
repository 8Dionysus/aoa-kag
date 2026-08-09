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
        "candidate_identity": snapshot.identity(),
        "cached_diff_digest": snapshot.cached_diff_digest,
        "worktree_diff_digest": snapshot.worktree_diff_digest,
        "untracked_digest": snapshot.untracked_digest,
        "untracked_paths_digest": sha256_bytes(
            canonical_json(list(snapshot.untracked_paths))
        ),
    }


def run_component(component: Component, *, repo_root: Path) -> ComponentResult:
    started = time.perf_counter()
    process = subprocess.run(
        component.command,
        cwd=repo_root,
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


def run_gate(
    *,
    repo_root: Path,
    output: str,
    history_ref: str,
    event_history_ref: str,
    budget_base_ref: str,
    jobs: int,
) -> tuple[int, dict[str, object]]:
    started = time.perf_counter()
    initial_identity = candidate_identity(repo_root)
    sentinel = Component(
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
    sentinel_result = run_component(sentinel, repo_root=repo_root)
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
        "refs": {
            "history_ref": history_ref,
            "event_history_ref": event_history_ref,
            "budget_base_ref": budget_base_ref,
        },
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
    parser.add_argument("--receipt-output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    if git_text(repo_root, "rev-parse", "--show-toplevel") != repo_root.as_posix():
        raise SystemExit("--repo-root must name the Git top level")
    budget_base_ref = args.budget_base_ref or args.history_ref
    code, receipt = run_gate(
        repo_root=repo_root,
        output=args.output,
        history_ref=args.history_ref,
        event_history_ref=args.event_history_ref,
        budget_base_ref=budget_base_ref,
        jobs=args.jobs,
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
