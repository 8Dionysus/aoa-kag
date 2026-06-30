#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence

try:  # Supports both direct script execution and package-style imports.
    from scripts.provider_registry import (
        provider_checkout_envs,
        pinned_provider_entries,
    )
except ImportError:  # pragma: no cover - exercised by direct script execution
    from provider_registry import provider_checkout_envs, pinned_provider_entries  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(command: Sequence[str], *, cwd: Path) -> None:
    subprocess.run(tuple(command), cwd=cwd, check=True)


def checkout_path(entry: dict[str, object], *, repo_root: Path = REPO_ROOT) -> Path:
    return (repo_root / str(entry["checkout_path"])).resolve()


def github_url(entry: dict[str, object]) -> str:
    return f"https://github.com/{entry['github_repository']}.git"


def sync_checkout(entry: dict[str, object], *, repo_root: Path = REPO_ROOT) -> Path:
    target = checkout_path(entry, repo_root=repo_root)
    pin = str(entry["pinned_ref"])
    repo = str(entry["repo"])
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        run(("git", "clone", "--no-checkout", github_url(entry), str(target)), cwd=repo_root)
    if not (target / ".git").exists():
        raise RuntimeError(f"{repo} checkout path is not a git repository: {target}")
    run(("git", "fetch", "--depth", "1", "origin", pin), cwd=target)
    run(("git", "checkout", "--detach", pin), cwd=target)
    run(("git", "reset", "--hard", pin), cwd=target)
    run(("git", "clean", "-ffd"), cwd=target)
    return target


def current_head(target: Path) -> str:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=target,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def check_checkout(entry: dict[str, object], *, repo_root: Path = REPO_ROOT) -> Path:
    target = checkout_path(entry, repo_root=repo_root)
    repo = str(entry["repo"])
    pin = str(entry["pinned_ref"])
    if not (target / ".git").exists():
        raise RuntimeError(f"{repo} checkout is missing: {target}")
    if current_head(target) != pin:
        raise RuntimeError(f"{repo} checkout must be pinned at {pin}")
    return target


def provider_env(*, repo_root: Path = REPO_ROOT) -> dict[str, str]:
    return {
        env_name: path.as_posix()
        for env_name, path in sorted(provider_checkout_envs(repo_root=repo_root).items())
    }


def print_env_exports(env: dict[str, str]) -> None:
    for name, value in env.items():
        print(f"export {name}={shlex.quote(value)}")


def strip_separator(command: Sequence[str]) -> tuple[str, ...]:
    if command and command[0] == "--":
        return tuple(command[1:])
    return tuple(command)


def resolve_command(command: Sequence[str]) -> tuple[str, ...]:
    if command and command[0] == "python":
        return (sys.executable, *command[1:])
    return tuple(command)


def sync_or_check(*, check: bool, repo_root: Path = REPO_ROOT) -> list[Path]:
    paths: list[Path] = []
    for entry in pinned_provider_entries():
        target = (
            check_checkout(entry, repo_root=repo_root)
            if check
            else sync_checkout(entry, repo_root=repo_root)
        )
        paths.append(target)
        print(
            f"[provider-checkout] {entry['repo']} {target.relative_to(repo_root).as_posix()} "
            f"{entry['pinned_ref']}"
        )
    return paths


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize provider registry checkouts and run commands with CI-equivalent provider roots."
    )
    parser.add_argument("--check", action="store_true", help="Verify existing checkouts.")
    parser.add_argument("--print-env", action="store_true", help="Print shell exports.")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    command = strip_separator(args.command)
    try:
        sync_or_check(check=args.check)
        env = provider_env()
        if args.print_env:
            print_env_exports(env)
        if command:
            command_env = os.environ.copy()
            command_env.update(env)
            return subprocess.run(resolve_command(command), cwd=REPO_ROOT, env=command_env).returncode
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"[provider-checkout] error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
