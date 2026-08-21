#!/usr/bin/env python3
"""Run the early SCC sentinel beside provider checkout, then fail closed.

This schedules only independent preparation work.  The canonical owner proof
and release continuation still run afterward without consuming a verdict from
this command.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoa-kag-ci-preflight-dag-receipt-v1"


@dataclass(frozen=True)
class ProcessResult:
    command: tuple[str, ...]
    returncode: int
    duration_ms: int
    cancelled_by_peer: bool


def resolve_command(command: Sequence[str]) -> tuple[str, ...]:
    if command and command[0] == "python":
        return (sys.executable, *command[1:])
    return tuple(command)


def terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=5)


def run_parallel_preflight(
    checkout_command: Sequence[str],
    sentinel_command: Sequence[str],
    *,
    repo_root: Path,
) -> tuple[ProcessResult, ProcessResult]:
    started = time.perf_counter()
    checkout = subprocess.Popen(
        resolve_command(checkout_command),
        cwd=repo_root,
        start_new_session=True,
    )
    try:
        sentinel = subprocess.Popen(
            resolve_command(sentinel_command),
            cwd=repo_root,
            start_new_session=True,
        )
    except BaseException:
        terminate_process_group(checkout)
        raise
    checkout_finished: float | None = None
    sentinel_finished: float | None = None
    checkout_cancelled = False
    sentinel_cancelled = False
    try:
        while checkout.poll() is None or sentinel.poll() is None:
            now = time.perf_counter()
            if checkout.poll() is not None and checkout_finished is None:
                checkout_finished = now
                if checkout.returncode and sentinel.poll() is None:
                    sentinel_cancelled = True
                    terminate_process_group(sentinel)
                    sentinel_finished = time.perf_counter()
            if sentinel.poll() is not None and sentinel_finished is None:
                sentinel_finished = now
                if sentinel.returncode and checkout.poll() is None:
                    checkout_cancelled = True
                    terminate_process_group(checkout)
                    checkout_finished = time.perf_counter()
            if checkout.poll() is None or sentinel.poll() is None:
                time.sleep(0.05)
    except BaseException:
        terminate_process_group(checkout)
        terminate_process_group(sentinel)
        raise
    finished = time.perf_counter()
    checkout_finished = checkout_finished or finished
    sentinel_finished = sentinel_finished or finished
    return (
        ProcessResult(
            tuple(checkout_command),
            int(checkout.returncode or 0),
            round((checkout_finished - started) * 1000),
            checkout_cancelled,
        ),
        ProcessResult(
            tuple(sentinel_command),
            int(sentinel.returncode or 0),
            round((sentinel_finished - started) * 1000),
            sentinel_cancelled,
        ),
    )


def process_payload(result: ProcessResult) -> dict[str, object]:
    return {
        "command": list(result.command),
        "return_code": result.returncode,
        "duration_ms": result.duration_ms,
        "cancelled_by_peer": result.cancelled_by_peer,
    }


def write_receipt(path: Path | None, receipt: dict[str, object]) -> None:
    encoded = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(encoded + "\n", encoding="utf-8")
        os.replace(temporary, path)
    print(encoded)


def load_child_receipt(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def child_receipt_error(
    receipt: dict[str, object] | None,
    *,
    returncode: int,
) -> str | None:
    if receipt is None:
        return "missing-or-invalid-json"
    if receipt.get("schema_version") != "aoa-kag-prepare-landing-receipt-v1":
        return "schema-version-mismatch"
    if receipt.get("mode") != "sentinel":
        return "mode-mismatch"
    verdict = receipt.get("verdict")
    expected = {"passed", "inapplicable"} if returncode == 0 else {"drift", "failed"}
    if verdict not in expected:
        return "verdict-return-code-mismatch"
    if receipt.get("partial_result_is_green") is not False:
        return "partial-result-boundary-missing"
    return None


def sentinel_failure(
    receipt: dict[str, object],
    *,
    default_failure_type: str,
) -> tuple[str, str]:
    failure_type = str(receipt.get("failure_type") or default_failure_type)
    action_class = str(receipt.get("action_class") or "code_fix")
    return failure_type, action_class


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Overlap the preparation-only coverage sentinel with provider checkout."
    )
    parser.add_argument("--base-ref", required=True)
    parser.add_argument(
        "--coverage-seed-ref",
        help=(
            "Preparation-only external coverage seed ref. This is separate "
            "from the historical base-ref and never changes downstream proof."
        ),
    )
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument(
        "--mode",
        choices=("candidate", "direct-control"),
        default="candidate",
        help="Exact-head hosted experiment selector; PR/default execution uses candidate.",
    )
    parser.add_argument("--receipt-output", type=Path)
    return parser.parse_args(argv)


def run_preflight(
    args: argparse.Namespace,
    *,
    receipt_parent: Path,
) -> int:
    started = time.perf_counter()
    coverage_seed_ref = str(
        getattr(args, "coverage_seed_ref", None) or args.base_ref
    )
    coverage_receipt = receipt_parent / "coverage-sentinel.json"
    generated_receipt = receipt_parent / "generated-sentinel.json"
    checkout_command = (
        "python",
        "scripts/sync_provider_checkouts.py",
        "--jobs",
        str(args.jobs),
        "--exclude-secret-checkouts",
    )
    if args.mode == "direct-control":
        completed = subprocess.run(
            resolve_command(checkout_command),
            cwd=REPO_ROOT,
            check=False,
        )
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "experiment_mode": "direct-control",
            "verdict": "passed" if completed.returncode == 0 else "failed",
            "partial_result_is_green": False,
            "base_ref": args.base_ref,
            "coverage_seed_ref": coverage_seed_ref,
            "checkout": {
                "command": list(checkout_command),
                "return_code": completed.returncode,
            },
            "proof_boundary": {
                "claim": "exact-head-direct-checkout-control-only",
                "does_not_replace": [
                    "provider-identity-proof",
                    "full-owner-proof",
                    "release-audit",
                    "landing-verdict",
                ],
            },
            "action_class": (
                "continue_unchanged_full_owner_proof"
                if completed.returncode == 0
                else "retry_or_fix_provider_checkout"
            ),
            "duration_ms": round((time.perf_counter() - started) * 1000),
        }
        if completed.returncode:
            receipt["failure_type"] = "provider_checkout_failure"
        write_receipt(args.receipt_output, receipt)
        return 0 if completed.returncode == 0 else 1
    coverage_command = (
        "python",
        "scripts/prepare_landing.py",
        "--sentinel",
        "--coverage-only",
        "--external-seed-ref",
        coverage_seed_ref,
        "--receipt-output",
        coverage_receipt.as_posix(),
    )
    checkout, coverage = run_parallel_preflight(
        checkout_command,
        coverage_command,
        repo_root=REPO_ROOT,
    )
    receipt: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "experiment_mode": "candidate",
        "verdict": "failed",
        "partial_result_is_green": False,
        "base_ref": args.base_ref,
        "coverage_seed_ref": coverage_seed_ref,
        "parallel": {
            "checkout": process_payload(checkout),
            "coverage_sentinel": process_payload(coverage),
        },
        "proof_boundary": {
            "claim": "checkout-and-preparation-scheduling-only",
            "does_not_replace": [
                "provider-identity-proof",
                "full-owner-proof",
                "release-audit",
                "landing-verdict",
            ],
        },
    }
    coverage_payload = load_child_receipt(coverage_receipt)
    receipt["coverage_sentinel_receipt"] = coverage_payload
    coverage_receipt_error = child_receipt_error(
        coverage_payload,
        returncode=coverage.returncode,
    )
    if checkout.returncode or coverage.returncode:
        if checkout.returncode and not checkout.cancelled_by_peer:
            receipt["failure_type"] = "provider_checkout_failure"
            receipt["action_class"] = "retry_or_fix_provider_checkout"
        elif coverage_receipt_error is not None or coverage_payload is None:
            receipt["failure_type"] = "sentinel_receipt_invalid"
            receipt["action_class"] = "code_fix"
            receipt["receipt_error"] = coverage_receipt_error
        else:
            failure_type, action_class = sentinel_failure(
                coverage_payload,
                default_failure_type="early_scc_drift",
            )
            receipt["failure_type"] = failure_type
            receipt["action_class"] = action_class
        receipt["duration_ms"] = round((time.perf_counter() - started) * 1000)
        write_receipt(args.receipt_output, receipt)
        return 1
    if coverage_receipt_error is not None:
        receipt["failure_type"] = "sentinel_receipt_invalid"
        receipt["action_class"] = "code_fix"
        receipt["receipt_error"] = coverage_receipt_error
        receipt["duration_ms"] = round((time.perf_counter() - started) * 1000)
        write_receipt(args.receipt_output, receipt)
        return 1

    generated_command = (
        "python",
        "scripts/prepare_landing.py",
        "--sentinel",
        "--generated-only",
        "--external-seed-ref",
        coverage_seed_ref,
        "--receipt-output",
        generated_receipt.as_posix(),
    )
    generated_started = time.perf_counter()
    generated = subprocess.run(
        resolve_command(generated_command),
        cwd=REPO_ROOT,
        check=False,
    )
    generated_payload = load_child_receipt(generated_receipt)
    generated_receipt_error = child_receipt_error(
        generated_payload,
        returncode=generated.returncode,
    )
    receipt["generated_sentinel"] = {
        "command": list(generated_command),
        "return_code": generated.returncode,
        "duration_ms": round((time.perf_counter() - generated_started) * 1000),
        "receipt": generated_payload,
    }
    receipt["duration_ms"] = round((time.perf_counter() - started) * 1000)
    if generated_receipt_error is not None:
        receipt["failure_type"] = "sentinel_receipt_invalid"
        receipt["action_class"] = "code_fix"
        receipt["receipt_error"] = generated_receipt_error
        write_receipt(args.receipt_output, receipt)
        return 1
    if generated.returncode:
        assert generated_payload is not None
        failure_type, action_class = sentinel_failure(
            generated_payload,
            default_failure_type="generated_projection_drift",
        )
        receipt["failure_type"] = failure_type
        receipt["action_class"] = action_class
        write_receipt(args.receipt_output, receipt)
        return 1
    receipt["verdict"] = "passed"
    receipt["action_class"] = "continue_unchanged_full_owner_proof"
    write_receipt(args.receipt_output, receipt)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.jobs < 1:
        raise SystemExit("--jobs must be positive")
    receipt_parent = Path(
        tempfile.mkdtemp(
            prefix="aoa-kag-ci-preflight-",
            dir=os.environ.get("RUNNER_TEMP") or None,
        )
    )
    try:
        return run_preflight(args, receipt_parent=receipt_parent)
    finally:
        shutil.rmtree(receipt_parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
