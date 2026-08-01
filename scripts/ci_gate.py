#!/usr/bin/env python3
"""Run validation lanes for aoa-kag CI."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

try:  # Supports both ``python scripts/ci_gate.py`` and package-style imports.
    from scripts import source_fast_handoff, validation_lanes
    from scripts.coverage_run import coverage_run_scope
except ImportError:  # pragma: no cover - exercised by direct script execution
    import source_fast_handoff  # type: ignore
    import validation_lanes  # type: ignore
    from coverage_run import coverage_run_scope  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]


def resolve_command(command: Sequence[str]) -> tuple[str, ...]:
    if command and command[0] == "python":
        return (sys.executable, *command[1:])
    return tuple(command)


def run_command(command: Sequence[str], repo_root: Path = REPO_ROOT) -> None:
    print(f"[ci-gate] {' '.join(command)}", flush=True)
    subprocess.run(resolve_command(command), cwd=repo_root, check=True)


def capture_command_output(command: Sequence[str], repo_root: Path = REPO_ROOT) -> str:
    result = subprocess.run(
        resolve_command(command),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def run_sequence(commands: Sequence[Sequence[str]]) -> None:
    for command in commands:
        run_command(command)


def run_source_fast() -> None:
    with coverage_run_scope(lane="source-fast"):
        run_sequence(validation_lanes.SOURCE_FAST_COMMAND_SEQUENCE)


def run_generated_sequence(
    commands: Sequence[Sequence[str]],
    *,
    lane: str,
) -> None:
    with coverage_run_scope(lane=lane):
        before_snapshot = capture_command_output(
            validation_lanes.GENERATED_DRIFT_SNAPSHOT_COMMAND
        )
        run_sequence(commands)
        after_snapshot = capture_command_output(
            validation_lanes.GENERATED_DRIFT_SNAPSHOT_COMMAND
        )
        if before_snapshot != after_snapshot:
            print(
                "[ci-gate] generated lane changed generated/read-model drift paths",
                file=sys.stderr,
            )
            raise subprocess.CalledProcessError(
                1,
                validation_lanes.GENERATED_DRIFT_SNAPSHOT_COMMAND,
            )


def run_generated() -> None:
    run_generated_sequence(
        validation_lanes.GENERATED_CHECK_COMMAND_SEQUENCE,
        lane="generated",
    )


def run_generated_continuation() -> None:
    encoded_receipt = os.environ.get(source_fast_handoff.RECEIPT_ENV, "")
    verification = source_fast_handoff.verify_encoded_receipt(encoded_receipt)
    if not verification.accepted:
        print(
            "[ci-gate] generated continuation rejected source-fast handoff: "
            f"{verification.reason}",
            file=sys.stderr,
        )
        raise subprocess.CalledProcessError(
            1,
            ("source-fast-handoff", "verify"),
        )
    print(
        "[ci-gate] generated continuation accepted exact source-fast handoff "
        f"digest={verification.receipt_digest}",
        flush=True,
    )
    run_generated_sequence(
        validation_lanes.GENERATED_CONTINUATION_COMMAND_SEQUENCE,
        lane="generated-continuation",
    )


def run_release() -> None:
    run_command(("python", "scripts/release_check.py"))


def run_compatibility_canary() -> None:
    with coverage_run_scope(lane="compatibility-canary"):
        run_sequence(validation_lanes.COMPATIBILITY_CANARY_COMMAND_SEQUENCE)


def run_advisory() -> None:
    print(
        json.dumps(
            {
                "lane": "advisory",
                "posture": "non_blocking",
                "boundaries": validation_lanes.ADVISORY_BOUNDARIES,
            },
            indent=2,
            sort_keys=True,
        )
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run aoa-kag validation lanes.")
    parser.add_argument(
        "--mode",
        choices=(
            "source-fast",
            "generated",
            "generated-continuation",
            "release",
            "compatibility-canary",
            "advisory",
        ),
        required=True,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.mode == "source-fast":
            run_source_fast()
        elif args.mode == "generated":
            run_generated()
        elif args.mode == "generated-continuation":
            run_generated_continuation()
        elif args.mode == "release":
            run_release()
        elif args.mode == "compatibility-canary":
            run_compatibility_canary()
        elif args.mode == "advisory":
            run_advisory()
        else:  # pragma: no cover - argparse enforces choices
            raise ValueError(args.mode)
    except subprocess.CalledProcessError as exc:
        print(f"[ci-gate] command failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
