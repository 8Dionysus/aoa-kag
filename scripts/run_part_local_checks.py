#!/usr/bin/env python3
"""Run discovered part-local builder and validator checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
PART_LOCAL_SCRIPT_GLOB = "mechanics/*/parts/*/scripts/*.py"


def discovered_part_local_scripts(repo_root: Path = REPO_ROOT) -> tuple[Path, ...]:
    return tuple(sorted(repo_root.glob(PART_LOCAL_SCRIPT_GLOB)))


def check_command_for(script_path: Path, repo_root: Path = REPO_ROOT) -> tuple[str, ...]:
    relative_path = script_path.relative_to(repo_root).as_posix()
    if script_path.name.startswith("build_"):
        return ("python", relative_path, "--check")
    if script_path.name.startswith("validate_"):
        return ("python", relative_path)
    raise ValueError(f"unsupported part-local script: {relative_path}")


def coverage_commands(repo_root: Path = REPO_ROOT) -> tuple[tuple[str, ...], ...]:
    return tuple(
        check_command_for(script_path, repo_root)
        for script_path in discovered_part_local_scripts(repo_root)
    )


def resolve_command(command: tuple[str, ...]) -> tuple[str, ...]:
    if command and command[0] == "python":
        return (sys.executable, *command[1:])
    return command


def run_commands(commands: Iterable[tuple[str, ...]], repo_root: Path = REPO_ROOT) -> int:
    ran = 0
    for command in commands:
        print(f"[part-local] {' '.join(command)}", flush=True)
        subprocess.run(resolve_command(command), cwd=repo_root, check=True)
        ran += 1
    return ran


def main() -> int:
    commands = coverage_commands(REPO_ROOT)
    if not commands:
        print("[error] no part-local builder or validator scripts were discovered", file=sys.stderr)
        return 1

    run_commands(commands, REPO_ROOT)
    print(f"[ok] completed part-local script checks across {len(commands)} commands")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
