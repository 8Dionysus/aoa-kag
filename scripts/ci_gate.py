#!/usr/bin/env python3
"""Run validation lanes for aoa-kag CI."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

try:  # Supports both ``python scripts/ci_gate.py`` and package-style imports.
    from scripts import validation_lanes
except ImportError:  # pragma: no cover - exercised by direct script execution
    import validation_lanes  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_PACKET_ENV = "AOA_KAG_COVERAGE_PACKET"


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
    run_sequence(validation_lanes.SOURCE_FAST_COMMAND_SEQUENCE)


def capture_generated_drift_snapshot() -> tuple[str, str]:
    return (
        capture_command_output(
            validation_lanes.GENERATED_DRIFT_SNAPSHOT_COMMAND
        ),
        capture_command_output(
            validation_lanes.GENERATED_DRIFT_STATUS_COMMAND
        ),
    )


@contextmanager
def coverage_packet_scope() -> Iterator[Path]:
    selected_parent = (
        os.environ.get("AOA_KAG_VALIDATION_ARTIFACT_PARENT")
        or os.environ.get("RUNNER_TEMP")
        or os.environ.get("TMPDIR")
    )
    parent = Path(selected_parent).resolve() if selected_parent else None
    if parent is not None and not parent.is_dir():
        raise OSError(f"generated lane temporary parent does not exist: {parent}")
    previous_packet = os.environ.get(COVERAGE_PACKET_ENV)
    with tempfile.TemporaryDirectory(
        prefix="aoa-kag-generated-lane-",
        dir=parent,
    ) as tmpdir:
        packet_path = Path(tmpdir) / "coverage.packet.json"
        os.environ[COVERAGE_PACKET_ENV] = str(packet_path)
        try:
            yield packet_path
        finally:
            if previous_packet is None:
                os.environ.pop(COVERAGE_PACKET_ENV, None)
            else:
                os.environ[COVERAGE_PACKET_ENV] = previous_packet


def run_generated() -> None:
    with coverage_packet_scope():
        before_snapshot = capture_generated_drift_snapshot()
        run_sequence(validation_lanes.GENERATED_CHECK_COMMAND_SEQUENCE)
        after_snapshot = capture_generated_drift_snapshot()
        if before_snapshot != after_snapshot:
            print(
                "[ci-gate] generated lane changed generated/read-model drift paths",
                file=sys.stderr,
            )
            raise subprocess.CalledProcessError(
                1,
                validation_lanes.GENERATED_DRIFT_SNAPSHOT_COMMAND,
            )
        untracked_paths = capture_command_output(
            validation_lanes.GENERATED_UNTRACKED_PATHS_COMMAND
        )
        if untracked_paths.strip():
            print(
                "[ci-gate] generated lane left required outputs untracked",
                file=sys.stderr,
            )
            print(untracked_paths.rstrip(), file=sys.stderr)
            raise subprocess.CalledProcessError(
                1,
                validation_lanes.GENERATED_UNTRACKED_PATHS_COMMAND,
            )


def run_incremental_federation() -> None:
    run_sequence(validation_lanes.INCREMENTAL_FEDERATION_COMMAND_SEQUENCE)


def run_release() -> None:
    run_command(("python", "scripts/release_check.py"))


def run_compatibility_canary() -> None:
    with coverage_packet_scope():
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
            "incremental-federation",
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
        elif args.mode == "incremental-federation":
            run_incremental_federation()
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
