#!/usr/bin/env python3
"""Prepare any AbyssOS owner's repo-local KAG family in isolation.

The caller candidate is copied into a detached temporary worktree.  The
portable family is regenerated and all canonical owner-family commands are
then checked against that exact staged candidate.  ``--check`` never changes
the caller; ``--apply`` applies only the generated family patch and preserves
the caller's Git index.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Sequence

try:
    from scripts import prepare_landing as isolation
    from scripts import repo_local_kag_gate as owner_gate
except ImportError:  # pragma: no cover - direct script execution
    import prepare_landing as isolation  # type: ignore
    import repo_local_kag_gate as owner_gate  # type: ignore


KAG_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoa-kag-owner-prepare-landing-receipt-v1"
DEFAULT_OUTPUT = "kag/indexes/source_surface_index.json"
OWNER_OUTPUT_PATHS = (
    "kag/indexes/index_family.manifest.json",
    "kag/indexes/shards",
    "kag/receipts/index_family_budget",
)


def generator_command(
    *,
    repo_root: Path,
    output: str,
    refs: isolation.ResolvedRefs,
    check: bool = False,
    write_budget_receipt: bool = False,
    budget_reason: str | None = None,
    budget_cause_class: str | None = None,
    budget_review_ref: str | None = None,
) -> tuple[str, ...]:
    command = [
        sys.executable,
        (KAG_ROOT / "scripts" / "generate_repo_local_kag_index.py").as_posix(),
        "--repo-root",
        repo_root.as_posix(),
        "--output",
        output,
        "--portable-family",
        "--history-ref",
        refs.history_ref,
        "--event-history-ref",
        refs.event_history_ref,
    ]
    if check or write_budget_receipt:
        command.extend(("--budget-base-ref", refs.budget_base_ref))
    if write_budget_receipt:
        command.extend(
            (
                "--write-budget-receipt",
                "--budget-reason",
                budget_reason or "",
                "--budget-cause-class",
                budget_cause_class or "",
                "--budget-review-ref",
                budget_review_ref or "",
            )
        )
    if check:
        command.append("--check")
    return tuple(command)


def stage_owner_outputs(repo_root: Path) -> None:
    stageable = tuple(
        path
        for path in OWNER_OUTPUT_PATHS
        if (repo_root / path).exists()
        or isolation.git_bytes(repo_root, "ls-files", "--", path)
    )
    if stageable:
        isolation.stage_paths(repo_root, stageable)


def generate_owner_family(
    repo_root: Path,
    *,
    output: str,
    refs: isolation.ResolvedRefs,
    budget_reason: str | None,
    budget_cause_class: str | None = None,
    budget_review_ref: str | None = None,
) -> str:
    isolation.run_command(
        generator_command(repo_root=repo_root, output=output, refs=refs),
        repo_root=repo_root,
    )
    stage_owner_outputs(repo_root)
    check = isolation.run_command(
        generator_command(repo_root=repo_root, output=output, refs=refs, check=True),
        repo_root=repo_root,
        allow_failure=True,
    )
    if check.returncode == 0:
        combined = check.stdout + check.stderr
        return "accepted" if "receipt=accepted" in combined else "not_required"

    combined = check.stdout + check.stderr
    receipt_failure = (
        "no matching receipt exists" in combined
        or "receipt field" in combined
        or "receipt scope" in combined
        or "receipt approval" in combined
        or "semantic admission" in combined
        or "semantic evidence" in combined
    )
    if not receipt_failure:
        raise isolation.PreparationFailure(
            "owner-family parity or budget check failed for a non-receipt reason",
            failure_type="owner_family_generation_failure",
            action_class="code_fix",
            command=check.command,
            details={"return_code": check.returncode, "duration_ms": check.duration_ms},
        )
    if (
        not budget_reason
        or not budget_reason.strip()
        or not budget_cause_class
        or not budget_cause_class.strip()
        or not budget_review_ref
        or not budget_review_ref.strip()
    ):
        raise isolation.PreparationFailure(
            "owner family requires typed semantic budget evidence",
            failure_type="budget_receipt_authority_required",
            action_class="provide_budget_evidence",
            command=check.command,
            details={"budget_base_ref": refs.budget_base_ref},
        )
    isolation.run_command(
        generator_command(
            repo_root=repo_root,
            output=output,
            refs=refs,
            write_budget_receipt=True,
            budget_reason=budget_reason,
            budget_cause_class=budget_cause_class,
            budget_review_ref=budget_review_ref,
        ),
        repo_root=repo_root,
        failure_type="budget_receipt_generation_failure",
    )
    stage_owner_outputs(repo_root)
    isolation.run_command(
        generator_command(repo_root=repo_root, output=output, refs=refs, check=True),
        repo_root=repo_root,
        failure_type="budget_receipt_mismatch",
    )
    return "created"


def require_owner_output_scope(paths: Sequence[str]) -> None:
    unexpected = sorted(
        path
        for path in paths
        if not any(isolation.path_is_within(path, allowed) for allowed in OWNER_OUTPUT_PATHS)
    )
    if unexpected:
        raise isolation.PreparationFailure(
            "owner preparation changed paths outside repo-local KAG output authority",
            failure_type="preparation_output_scope_violation",
            action_class="code_fix",
            details={"unexpected_paths": unexpected},
        )


def receipt_base(
    *,
    mode: str,
    source_root: Path,
    snapshot: isolation.CandidateSnapshot | None,
    refs: isolation.ResolvedRefs | None,
    started: float,
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "verdict": "failed",
        "partial_result_is_green": False,
        "owner_root": source_root.as_posix(),
        "candidate": (
            {
                "head": snapshot.head,
                "index_tree": snapshot.index_tree,
                "identity": snapshot.identity(),
                "untracked_count": len(snapshot.untracked_paths),
            }
            if snapshot is not None
            else {"state": "unavailable"}
        ),
        "duration_ms": round((time.perf_counter() - started) * 1000),
    }
    if refs is not None:
        receipt["refs"] = {
            "history_ref": refs.history_ref,
            "event_history_ref": refs.event_history_ref,
            "budget_base_ref": refs.budget_base_ref,
        }
    return receipt


def prepare_owner_landing(
    source_root: Path,
    *,
    mode: str,
    output: str,
    history_ref: str | None,
    event_history_ref: str | None,
    budget_base_ref: str | None,
    budget_reason: str | None,
    jobs: int,
    temp_root: Path | None,
    budget_cause_class: str | None = None,
    budget_review_ref: str | None = None,
) -> tuple[int, dict[str, object]]:
    started = time.perf_counter()
    source_root = source_root.resolve()
    snapshot: isolation.CandidateSnapshot | None = None
    refs: isolation.ResolvedRefs | None = None
    temporary_parent: Path | None = None
    temporary_worktree: Path | None = None
    try:
        snapshot = isolation.capture_candidate_snapshot(source_root)
        refs = isolation.resolve_refs(
            source_root,
            history_ref=history_ref,
            event_history_ref=event_history_ref,
            budget_base_ref=budget_base_ref,
        )
        if temp_root is not None:
            temp_root.mkdir(parents=True, exist_ok=True)
        temporary_parent = Path(
            tempfile.mkdtemp(
                prefix="aoa-kag-prepare-owner-",
                dir=temp_root.as_posix() if temp_root is not None else None,
            )
        )
        temporary_worktree = temporary_parent / "worktree"
        subprocess.run(
            (
                "git",
                "worktree",
                "add",
                "--detach",
                temporary_worktree.as_posix(),
                snapshot.head,
            ),
            cwd=source_root,
            check=True,
            capture_output=True,
            text=True,
        )
        initial_tree = isolation.materialize_candidate(
            source_root,
            temporary_worktree,
            snapshot,
        )
        isolation.require_candidate_unchanged(source_root, snapshot)
        budget_receipt = generate_owner_family(
            temporary_worktree,
            output=output,
            refs=refs,
            budget_reason=budget_reason,
            budget_cause_class=budget_cause_class,
            budget_review_ref=budget_review_ref,
        )
        prepared_tree = isolation.git_text(temporary_worktree, "write-tree")
        gate_code, gate_receipt = owner_gate.run_gate(
            repo_root=temporary_worktree,
            output=output,
            history_ref=refs.history_ref,
            event_history_ref=refs.event_history_ref,
            budget_base_ref=refs.budget_base_ref,
            jobs=jobs,
        )
        if gate_code:
            raise isolation.PreparationFailure(
                "canonical owner-family gate rejected the prepared candidate",
                failure_type=str(gate_receipt.get("failure_type") or "owner_family_proof_failed"),
                action_class=str(gate_receipt.get("action_class") or "code_fix"),
                details={"owner_family_gate": gate_receipt},
            )
        isolation.require_candidate_unchanged(source_root, snapshot)
        changed_paths = isolation.changed_tree_paths(
            temporary_worktree,
            initial_tree,
            prepared_tree,
        )
        require_owner_output_scope(changed_paths)
        patch = isolation.tree_patch(temporary_worktree, initial_tree, prepared_tree)
        if mode == "apply" and patch:
            isolation.apply_generated_patch(
                source_root,
                patch,
                expected_snapshot=snapshot,
            )
        receipt = receipt_base(
            mode=mode,
            source_root=source_root,
            snapshot=snapshot,
            refs=refs,
            started=started,
        )
        receipt.update(
            {
                "verdict": "prepared" if mode == "apply" else "clean",
                "action_class": "none" if not patch else (
                    "generated_patch_applied" if mode == "apply" else "run_prepare_owner_landing_apply"
                ),
                "generated_patch": {
                    "initial_tree": initial_tree,
                    "final_tree": prepared_tree,
                    "patch_digest": isolation.sha256_bytes(patch),
                    "patch_bytes": len(patch),
                    "drift_detected": bool(patch),
                    "changed_paths": list(changed_paths),
                },
                "budget_receipt": budget_receipt,
                "owner_family_gate": gate_receipt,
                "proof_boundary": {
                    "claim": "isolated-owner-family-preparation-and-canonical-parity",
                    "does_not_replace": [
                        "owner-source-fast",
                        "owner-release-gate",
                        "os-wide-provider-proof",
                        "landing-verdict",
                    ],
                },
                "duration_ms": round((time.perf_counter() - started) * 1000),
            }
        )
        if mode == "check" and patch:
            receipt["verdict"] = "drift"
            return 1, receipt
        return 0, receipt
    except isolation.PreparationFailure as exc:
        receipt = receipt_base(
            mode=mode,
            source_root=source_root,
            snapshot=snapshot,
            refs=refs,
            started=started,
        )
        receipt.update(
            {
                "failure_type": exc.failure_type,
                "action_class": exc.action_class,
                "message": str(exc),
                "command": list(exc.command),
                "details": exc.details,
                "duration_ms": round((time.perf_counter() - started) * 1000),
            }
        )
        return 1, receipt
    except subprocess.CalledProcessError as exc:
        receipt = receipt_base(
            mode=mode,
            source_root=source_root,
            snapshot=snapshot,
            refs=refs,
            started=started,
        )
        receipt.update(
            {
                "failure_type": "preparation_infrastructure_failure",
                "action_class": "retry_same_candidate",
                "message": str(exc),
                "command": list(exc.cmd) if isinstance(exc.cmd, (list, tuple)) else [str(exc.cmd)],
                "details": {"return_code": exc.returncode},
                "duration_ms": round((time.perf_counter() - started) * 1000),
            }
        )
        return 1, receipt
    finally:
        if temporary_worktree is not None and temporary_worktree.exists():
            subprocess.run(
                ("git", "worktree", "remove", "--force", temporary_worktree.as_posix()),
                cwd=source_root,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        if temporary_parent is not None and temporary_parent.exists():
            shutil.rmtree(temporary_parent, ignore_errors=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare any owner repo-local KAG family in an isolated worktree."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--history-ref")
    parser.add_argument("--event-history-ref")
    parser.add_argument("--budget-base-ref")
    parser.add_argument("--budget-reason")
    parser.add_argument("--budget-cause-class")
    parser.add_argument("--budget-review-ref")
    parser.add_argument("--jobs", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--temp-root", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    return parser.parse_args(argv)


def write_receipt(path: Path, receipt: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, path)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    code, receipt = prepare_owner_landing(
        args.repo_root,
        mode="apply" if args.apply else "check",
        output=args.output,
        history_ref=args.history_ref,
        event_history_ref=args.event_history_ref,
        budget_base_ref=args.budget_base_ref,
        budget_reason=args.budget_reason,
        jobs=args.jobs,
        temp_root=args.temp_root,
        budget_cause_class=args.budget_cause_class,
        budget_review_ref=args.budget_review_ref,
    )
    if args.receipt_output is not None:
        write_receipt(args.receipt_output, receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
