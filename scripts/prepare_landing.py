#!/usr/bin/env python3
"""Prepare one KAG landing candidate through an isolated staged fixed point.

This is a preparation tool, not a replacement for any validation lane.  It
copies the caller's final working-tree content into a detached temporary Git
worktree, stages that candidate there, converges the root KAG SCC, and either
reports the required patch (``--check``) or applies only that generated patch
back to the caller's working tree (``--apply``).  The caller's Git index is
never changed.
"""

from __future__ import annotations

import argparse
import copy
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoa-kag-prepare-landing-receipt-v1"
PREPARATION_COVERAGE_CACHE_SCHEMA = "aoa-kag-preparation-coverage-cache-v2"
DEFAULT_MAX_ITERATIONS = 6
GENERATED_PATHS = ("generated",)
COVERAGE_PATHS = (
    "generated/repo_local_kag_coverage.json",
    "generated/repo_local_kag_coverage.min.json",
)
PORTABLE_FAMILY_PATHS = (
    "kag/indexes/index_family.manifest.json",
    "kag/indexes/shards",
)
BUDGET_RECEIPT_PATHS = ("kag/receipts/index_family_budget",)
PREPARATION_OUTPUT_PATHS = (
    *GENERATED_PATHS,
    *PORTABLE_FAMILY_PATHS,
    *BUDGET_RECEIPT_PATHS,
)
SELF_OWNER = "aoa-kag"
CHECKOUT_CONVERSION_CONFIG_PATTERN = (
    r"^(extensions\.worktreeconfig|core\."
    r"(autocrlf|eol|safecrlf|symlinks|attributesfile|sparsecheckout|sparsecheckoutcone|worktree)"
    r"|filter\..*\.(clean|smudge|process|required))$"
)
PORTABLE_LOCAL_CONFIG_KEYS = frozenset(
    {
        "core.bare",
        "core.filemode",
        "core.logallrefupdates",
        "core.repositoryformatversion",
        "user.email",
        "user.name",
    }
)
PORTABLE_LOCAL_CONFIG_PREFIXES = ("branch.",)
ISOLATION_LOCAL_CONFIG_KEYS = frozenset({"core.fsmonitor", "core.hookspath"})
PORTABLE_REMOTE_CONFIG_SUFFIXES = (".url", ".fetch")


@dataclass(frozen=True)
class CandidateSnapshot:
    head: str
    root_mode: int
    index_tree: str
    index_version: int
    index_mode: int
    index_bytes: bytes
    cached_patch_bytes: bytes
    unstaged_patch_bytes: bytes
    candidate_patch_bytes: bytes
    cached_diff_digest: str
    worktree_diff_digest: str
    untracked_digest: str
    untracked_paths: tuple[str, ...]
    directory_digest: str
    directories: tuple[str, ...]
    worktree_hardlink_groups: tuple[tuple[str, ...], ...]
    tracked_file_modes: tuple[tuple[str, int], ...]
    directory_mtimes: tuple[tuple[str, int], ...]
    worktree_xattrs: tuple[tuple[str, tuple[tuple[str, bytes], ...]], ...]
    intent_to_add_paths: tuple[str, ...]

    def identity(self) -> str:
        payload = {
            "head": self.head,
            "root_mode": self.root_mode,
            "index_tree": self.index_tree,
            "index_version": self.index_version,
            "index_mode": self.index_mode,
            "index_bytes": [len(self.index_bytes), sha256_bytes(self.index_bytes)],
            "cached_patch_bytes": [
                len(self.cached_patch_bytes),
                sha256_bytes(self.cached_patch_bytes),
            ],
            "unstaged_patch_bytes": [
                len(self.unstaged_patch_bytes),
                sha256_bytes(self.unstaged_patch_bytes),
            ],
            "candidate_patch_bytes": [
                len(self.candidate_patch_bytes),
                sha256_bytes(self.candidate_patch_bytes),
            ],
            "cached_diff_digest": self.cached_diff_digest,
            "worktree_diff_digest": self.worktree_diff_digest,
            "untracked_digest": self.untracked_digest,
            "untracked_paths": list(self.untracked_paths),
            "directory_digest": self.directory_digest,
            "directories": list(self.directories),
            "worktree_hardlink_groups": [
                list(group) for group in self.worktree_hardlink_groups
            ],
            "tracked_file_modes": [list(row) for row in self.tracked_file_modes],
            "directory_mtimes": [list(row) for row in self.directory_mtimes],
            "worktree_xattrs": [
                [
                    path,
                    [
                        [name, len(value), sha256_bytes(value)]
                        for name, value in attributes
                    ],
                ]
                for path, attributes in self.worktree_xattrs
            ],
            "intent_to_add_paths": list(self.intent_to_add_paths),
        }
        return sha256_bytes(canonical_json(payload))


@dataclass(frozen=True)
class NestedGitSnapshot:
    candidate: CandidateSnapshot
    root_mode: int
    git_admin_security_label: bytes | None
    git_admin_directories: tuple[tuple[str, int], ...]
    git_admin_files: tuple[tuple[str, int, int, bytes], ...]
    symbolic_head: str | None
    origin_head: str | None
    git_refs: tuple[tuple[str, str], ...]
    ref_root_mode: int | None
    ref_directories: tuple[tuple[str, int], ...]
    loose_ref_files: tuple[tuple[str, int, bytes], ...]
    packed_refs_mode: int | None
    packed_refs_bytes: bytes | None
    shallow_boundaries: tuple[str, ...]
    local_config: tuple[tuple[str, str], ...]
    remote_config: tuple[tuple[str, str], ...]
    local_config_mode: int
    local_config_bytes: bytes
    isolated_config_bytes: bytes
    reflog_root_mode: int | None
    reflog_directories: tuple[tuple[str, int], ...]
    reflog_files: tuple[tuple[str, int, bytes], ...]
    index_version: int
    index_mode: int
    index_bytes: bytes
    object_inventory_count: int
    object_inventory_digest: str
    object_storage_state: tuple[tuple[str, str, int, int, str], ...]
    worktree_hardlink_groups: tuple[tuple[str, ...], ...]
    worktree_mtimes: tuple[tuple[str, int], ...]
    worktree_xattrs: tuple[tuple[str, tuple[tuple[str, bytes], ...]], ...]
    tracked_paths: tuple[str, ...]
    tracked_worktree_digest: str
    effective_checkout_settings: tuple[str, ...]
    effective_git_config: tuple[tuple[str, str, str], ...]

    def identity(self) -> str:
        payload = {
            "candidate_identity": self.candidate.identity(),
            "root_mode": self.root_mode,
            "git_admin_security_label": (
                None
                if self.git_admin_security_label is None
                else [
                    len(self.git_admin_security_label),
                    sha256_bytes(self.git_admin_security_label),
                ]
            ),
            "git_admin_directories": [
                list(row) for row in self.git_admin_directories
            ],
            "git_admin_files": [
                [path, mode, mtime_ns, len(content), sha256_bytes(content)]
                for path, mode, mtime_ns, content in self.git_admin_files
            ],
            "symbolic_head": self.symbolic_head,
            "origin_head": self.origin_head,
            "git_refs": [list(row) for row in self.git_refs],
            "ref_root_mode": self.ref_root_mode,
            "ref_directories": [list(row) for row in self.ref_directories],
            "loose_ref_files": [
                [path, mode, len(content), sha256_bytes(content)]
                for path, mode, content in self.loose_ref_files
            ],
            "packed_refs_mode": self.packed_refs_mode,
            "packed_refs_bytes": (
                None
                if self.packed_refs_bytes is None
                else [
                    len(self.packed_refs_bytes),
                    sha256_bytes(self.packed_refs_bytes),
                ]
            ),
            "shallow_boundaries": list(self.shallow_boundaries),
            "local_config": [list(row) for row in self.local_config],
            "remote_config": [list(row) for row in self.remote_config],
            "local_config_mode": self.local_config_mode,
            "local_config_bytes": [
                len(self.local_config_bytes),
                sha256_bytes(self.local_config_bytes),
            ],
            "isolated_config_bytes": [
                len(self.isolated_config_bytes),
                sha256_bytes(self.isolated_config_bytes),
            ],
            "reflog_root_mode": self.reflog_root_mode,
            "reflog_directories": [list(row) for row in self.reflog_directories],
            "reflog_files": [
                [path, mode, len(content), sha256_bytes(content)]
                for path, mode, content in self.reflog_files
            ],
            "index_version": self.index_version,
            "index_mode": self.index_mode,
            "index_bytes": [len(self.index_bytes), sha256_bytes(self.index_bytes)],
            "object_inventory_count": self.object_inventory_count,
            "object_inventory_digest": self.object_inventory_digest,
            "object_storage_digest": sha256_bytes(
                canonical_json(self.object_storage_state)
            ),
            "worktree_hardlink_groups": [
                list(group) for group in self.worktree_hardlink_groups
            ],
            "worktree_mtimes": [list(row) for row in self.worktree_mtimes],
            "worktree_xattrs": [
                [
                    path,
                    [
                        [name, len(value), sha256_bytes(value)]
                        for name, value in attributes
                    ],
                ]
                for path, attributes in self.worktree_xattrs
            ],
            "tracked_paths": list(self.tracked_paths),
            "tracked_worktree_digest": self.tracked_worktree_digest,
            "effective_checkout_settings": list(self.effective_checkout_settings),
            "effective_git_config": [list(row) for row in self.effective_git_config],
        }
        return sha256_bytes(canonical_json(payload))


@dataclass(frozen=True)
class ResolvedRefs:
    history_ref: str
    event_history_ref: str
    budget_base_ref: str


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int


class PreparationFailure(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        failure_type: str,
        action_class: str,
        command: Sequence[str] | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.failure_type = failure_type
        self.action_class = action_class
        self.command = tuple(command or ())
        self.details = dict(details or {})


class PreparationSeedInapplicable(RuntimeError):
    """The preparation shortcut cannot prove its seed assumptions."""


def canonical_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def resolve_command(command: Sequence[str]) -> tuple[str, ...]:
    if command and command[0] == "python":
        return (sys.executable, *command[1:])
    return tuple(command)


def git_bytes(
    repo_root: Path,
    *args: str,
    input_bytes: bytes | None = None,
    check: bool = True,
    env: Mapping[str, str] | None = None,
) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        input=input_bytes,
        check=check,
        capture_output=True,
        env=env,
    )
    return result.stdout


def git_text(repo_root: Path, *args: str) -> str:
    return git_bytes(repo_root, *args).decode("utf-8", errors="strict").strip()


def checked_relative_path(raw: str) -> Path:
    path = Path(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        raise PreparationFailure(
            f"unsafe candidate path: {raw!r}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    return path


def untracked_paths(
    repo_root: Path,
    *,
    include_ignored: bool = False,
) -> tuple[str, ...]:
    outputs = [
        git_bytes(
            repo_root,
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        )
    ]
    if include_ignored:
        outputs.append(
            git_bytes(
                repo_root,
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
                "-z",
            )
        )
    paths = {
        item
        for raw in outputs
        for item in raw.decode("utf-8", errors="surrogateescape").split("\0")
        if item
    }
    for item in paths:
        checked_relative_path(item)
    return tuple(sorted(paths))


def untracked_content_digest(repo_root: Path, paths: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for raw in paths:
        _update_untracked_path_digest(digest, repo_root, checked_relative_path(raw))
    return "sha256:" + digest.hexdigest()


def _ignored_directory_paths(repo_root: Path, paths: Sequence[str]) -> set[str]:
    if not paths:
        return set()
    result = subprocess.run(
        ("git", "check-ignore", "-z", "--stdin"),
        cwd=repo_root,
        input=b"\0".join(
            raw.encode("utf-8", errors="surrogateescape") for raw in paths
        )
        + b"\0",
        check=False,
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        raise PreparationFailure(
            "cannot inspect candidate directory ignore state",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": result.stderr.decode("utf-8", errors="replace").strip()},
        )
    return {
        item.decode("utf-8", errors="surrogateescape").rstrip("/")
        for item in result.stdout.split(b"\0")
        if item
    }


def _ignored_directory_roots(repo_root: Path) -> set[str]:
    raw = git_bytes(
        repo_root,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "--directory",
        "-z",
    )
    roots: set[str] = set()
    for item in raw.decode("utf-8", errors="surrogateescape").split("\0"):
        if not item:
            continue
        relative = checked_relative_path(item.rstrip("/"))
        candidate = repo_root / relative
        if candidate.is_dir() and not candidate.is_symlink():
            roots.add(relative.as_posix())
    return roots


def _ignored_nested_checkout_paths(repo_root: Path) -> tuple[str, ...]:
    """Discover ignored Git roots without admitting ordinary ignored artifacts."""
    raw = git_bytes(
        repo_root,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
    )
    inspected: set[str] = set()
    roots: set[str] = set()
    for item in raw.decode("utf-8", errors="surrogateescape").split("\0"):
        if not item:
            continue
        relative = checked_relative_path(item.rstrip("/"))
        # Repo-local provider checkouts are separately pinned and verified by
        # verify_provider_identities(); they are inputs, not candidate state.
        if relative.parts[0] == ".deps":
            continue
        for parent in (relative, *relative.parents):
            if parent == Path("."):
                continue
            label = parent.as_posix()
            if label in roots:
                break
            if label in inspected:
                continue
            inspected.add(label)
            candidate = repo_root / parent
            if (candidate / ".git").exists() and _is_nested_git_checkout(candidate):
                roots.add(label)
                break
    return tuple(f"{label}/" for label in sorted(roots))


def candidate_directory_paths(
    repo_root: Path,
    *,
    include_ignored: bool = False,
) -> tuple[str, ...]:
    """Capture directories exposed to validation, including ignored nested state."""
    ignored_roots = set() if include_ignored else _ignored_directory_roots(repo_root)
    discovered: list[str] = []
    for current, dirnames, _filenames in os.walk(repo_root, topdown=True):
        current_path = Path(current)
        retained: list[str] = []
        for name in sorted(dirnames):
            child = current_path / name
            relative = child.relative_to(repo_root)
            raw = relative.as_posix()
            if (
                relative == Path(".git")
                or raw in ignored_roots
                or child.is_symlink()
            ):
                continue
            if (child / ".git").exists() and _is_nested_git_checkout(child):
                continue
            retained.append(name)
            discovered.append(raw)
        dirnames[:] = retained

    ignored = set() if include_ignored else _ignored_directory_paths(repo_root, discovered)
    return tuple(raw for raw in discovered if raw not in ignored)


def candidate_directory_digest(repo_root: Path, paths: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for raw in paths:
        relative = checked_relative_path(raw)
        metadata = (repo_root / relative).lstat()
        if not stat.S_ISDIR(metadata.st_mode):
            raise PreparationFailure(
                f"candidate directory changed type: {raw}",
                failure_type="candidate_snapshot_changed",
                action_class="retry_same_candidate",
            )
        digest.update(raw.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(str(stat.S_IMODE(metadata.st_mode)).encode("ascii"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _require_isolated_git_environment(path: Path, *, subject: str) -> None:
    object_storage_environment = tuple(
        name
        for name in (
            "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        )
        if os.environ.get(name, "").strip()
    )
    if object_storage_environment:
        raise PreparationFailure(
            f"{subject} is exposed to external Git object storage: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "git_object_storage_environment": list(object_storage_environment)
            },
        )
    repository_routing_environment = tuple(
        name
        for name in (
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_COMMON_DIR",
            "GIT_IMPLICIT_WORK_TREE",
            "GIT_INDEX_FILE",
            "GIT_GRAFT_FILE",
            "GIT_SHALLOW_FILE",
            "GIT_REPLACE_REF_BASE",
            "GIT_NO_REPLACE_OBJECTS",
            "GIT_NAMESPACE",
            "GIT_CONFIG",
            "GIT_CONFIG_PARAMETERS",
            "GIT_CONFIG_COUNT",
            "GIT_PREFIX",
        )
        if os.environ.get(name, "").strip()
    )
    if repository_routing_environment:
        raise PreparationFailure(
            f"{subject} is exposed to ambient Git repository state: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "git_repository_environment": list(repository_routing_environment)
            },
        )


def _is_nested_git_checkout(path: Path) -> bool:
    try:
        if (
            not stat.S_ISDIR(path.lstat().st_mode)
            or not (path / ".git").exists()
        ):
            return False
    except FileNotFoundError:
        return False
    _require_isolated_git_environment(path, subject="nested checkout")
    probe = subprocess.run(
        ("git", "rev-parse", "--show-toplevel"),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    return probe.returncode == 0 and probe.stdout.strip() == path.resolve().as_posix()


def _nested_checkout_roots_with_tracked_content(
    repo_root: Path,
    paths: Sequence[str],
) -> tuple[str, ...]:
    """Find nested Git roots which overlap the outer repository index."""
    candidates: set[Path] = set()
    for raw in paths:
        relative = checked_relative_path(raw)
        for parent in (relative, *relative.parents):
            if parent == Path("."):
                continue
            candidate = repo_root / parent
            if (candidate / ".git").exists():
                candidates.add(candidate)
    return tuple(
        sorted(
            candidate.relative_to(repo_root).as_posix()
            for candidate in candidates
            if _is_nested_git_checkout(candidate)
        )
    )


def _populated_submodule_paths(path: Path) -> tuple[str, ...]:
    populated: list[str] = []
    for entry in git_bytes(path, "ls-files", "--stage", "-z").split(b"\0"):
        if not entry:
            continue
        metadata, separator, raw_path = entry.partition(b"\t")
        if not separator or metadata.split(b" ", 1)[0] != b"160000":
            continue
        relative = checked_relative_path(raw_path.decode("utf-8", errors="surrogateescape"))
        worktree_path = path / relative
        if worktree_path.is_symlink() or worktree_path.is_file():
            populated.append(relative.as_posix())
        elif worktree_path.is_dir() and next(worktree_path.iterdir(), None) is not None:
            populated.append(relative.as_posix())
    return tuple(populated)


def _effective_checkout_settings(path: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ("git", "config", "--get-regexp", CHECKOUT_CONVERSION_CONFIG_PATTERN),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect effective nested checkout settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": result.stderr.strip()},
        )
    return tuple(sorted(line for line in result.stdout.splitlines() if line))


def _effective_hook_settings(path: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ("git", "config", "--get-regexp", r"^(core\.hookspath|init\.templatedir)$"),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect nested checkout hook settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": result.stderr.strip()},
        )
    settings = tuple(sorted(line for line in result.stdout.splitlines() if line))
    return tuple(
        line
        for line in settings
        if line.strip().lower() != "core.hookspath /dev/null"
    )


def _default_hook_paths(path: Path) -> tuple[str, ...]:
    configured = subprocess.run(
        ("git", "config", "--path", "--get", "core.hooksPath"),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if configured.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect nested checkout hook path: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": configured.stderr.strip()},
        )
    if configured.returncode == 0:
        return ()
    hooks_raw = git_text(path, "rev-parse", "--git-path", "hooks")
    hooks = Path(hooks_raw)
    if not hooks.is_absolute():
        hooks = path / hooks
    if not hooks.exists():
        return ()
    if not hooks.is_dir() or hooks.is_symlink():
        raise PreparationFailure(
            f"nested checkout has unsupported default hooks path: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    return tuple(
        child.name
        for child in sorted(hooks.iterdir(), key=lambda item: os.fsencode(item.name))
        if not child.name.endswith(".sample")
    )


def _effective_fsmonitor_settings(path: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ("git", "config", "--null", "--get", "core.fsmonitor"),
        cwd=path,
        check=False,
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect nested checkout fsmonitor setting: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": result.stderr.decode("utf-8", errors="replace").strip()},
        )
    values = tuple(
        value.decode("utf-8", errors="surrogateescape")
        for value in result.stdout.split(b"\0")
        if value
    )
    disabled = {"false", "no", "off", "0"}
    return tuple(value for value in values if value.strip().lower() not in disabled)


def _local_config_rows(path: Path) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for entry in git_bytes(path, "config", "--local", "--null", "--list").split(b"\0"):
        if not entry:
            continue
        raw_key, separator, raw_value = entry.partition(b"\n")
        if not separator:
            raise PreparationFailure(
                f"cannot parse nested checkout local config: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        rows.append(
            (
                raw_key.decode("utf-8", errors="surrogateescape"),
                raw_value.decode("utf-8", errors="surrogateescape"),
            )
        )
    return tuple(rows)


def _portable_local_config(path: Path) -> tuple[tuple[str, str], ...]:
    rows = _local_config_rows(path)
    unsupported = tuple(
        sorted(
            {
                key
                for key, _value in rows
                if key not in PORTABLE_LOCAL_CONFIG_KEYS
                and key not in ISOLATION_LOCAL_CONFIG_KEYS
                and not key.startswith("remote.")
                and not key.startswith(PORTABLE_LOCAL_CONFIG_PREFIXES)
            }
        )
    )
    if unsupported:
        raise PreparationFailure(
            f"nested checkout has unsupported local Git configuration: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"unsupported_local_config_keys": list(unsupported)},
        )
    return tuple(
        row
        for row in rows
        if row[0] not in ISOLATION_LOCAL_CONFIG_KEYS
        and not row[0].startswith("remote.")
    )


def _remote_local_config(path: Path) -> tuple[tuple[str, str], ...]:
    rows = tuple(
        row for row in _local_config_rows(path) if row[0].startswith("remote.")
    )
    unsupported = tuple(
        sorted(
            {
                key
                for key, _value in rows
                if not key.endswith(PORTABLE_REMOTE_CONFIG_SUFFIXES)
            }
        )
    )
    if unsupported:
        raise PreparationFailure(
            f"nested checkout has unsupported remote Git configuration: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"unsupported_remote_config_keys": list(unsupported)},
        )
    nonlocal_remote = tuple(
        sorted(
            {
                (scope, key)
                for scope, key, _value in _effective_git_config(
                    path, include_remote=True
                )
                if key.startswith("remote.") and scope != "local"
            }
        )
    )
    if nonlocal_remote:
        raise PreparationFailure(
            f"nested checkout has nonlocal remote Git configuration: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"nonlocal_remote_config": [list(row) for row in nonlocal_remote]},
        )
    return rows


def _neutralized_remote_config(
    remote_config: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (key, "." if key.endswith(".url") else value)
        for key, value in remote_config
    )


def _git_local_config_state(path: Path) -> tuple[int, bytes]:
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    raw_config_path = Path(git_text(path, "rev-parse", "--git-path", "config"))
    if not raw_config_path.is_absolute():
        raw_config_path = path / raw_config_path
    config_path = Path(os.path.abspath(raw_config_path))
    try:
        config_path.relative_to(git_dir)
    except ValueError as exc:
        raise PreparationFailure(
            f"nested checkout config is outside its Git directory: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"config_path": config_path.as_posix()},
        ) from exc
    try:
        metadata = config_path.lstat()
    except FileNotFoundError as exc:
        raise PreparationFailure(
            f"nested checkout config is missing: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        ) from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise PreparationFailure(
            f"nested checkout config is not a regular file: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"config_path": config_path.as_posix()},
        )
    return stat.S_IMODE(metadata.st_mode), config_path.read_bytes()


def _neutralized_local_config_bytes(
    path: Path,
    config_bytes: bytes,
    remote_config: Sequence[tuple[str, str]],
) -> bytes:
    url_keys = tuple(
        sorted({key for key, _value in remote_config if key.endswith(".url")})
    )
    with tempfile.TemporaryDirectory(prefix=".aoa-kag-neutral-config-") as temp_dir:
        config_path = Path(temp_dir) / "config"
        config_path.write_bytes(config_bytes)
        replacements = (
            *((key, ".") for key in url_keys),
            ("core.hookspath", "/dev/null"),
            ("core.fsmonitor", "false"),
        )
        for key, value in replacements:
            result = subprocess.run(
                (
                    "git",
                    "config",
                    "--file",
                    config_path.as_posix(),
                    "--replace-all",
                    key,
                    value,
                ),
                cwd=path,
                check=False,
                capture_output=True,
            )
            if result.returncode != 0:
                raise PreparationFailure(
                    f"cannot isolate nested checkout local config: {path}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                    details={
                        "config_key": key,
                        "stderr": result.stderr.decode(
                            "utf-8", errors="replace"
                        ).strip(),
                    },
                )
        return config_path.read_bytes()


def _require_local_config_state_match(
    path: Path,
    expected: NestedGitSnapshot,
) -> None:
    observed = _git_local_config_state(path)
    wanted = (expected.local_config_mode, expected.isolated_config_bytes)
    if observed != wanted:
        raise PreparationFailure(
            "nested checkout raw local config differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "expected_digest": sha256_bytes(expected.isolated_config_bytes),
                "actual_digest": sha256_bytes(observed[1]),
            },
        )


def _restore_local_config_state(path: Path, expected: NestedGitSnapshot) -> None:
    raw_config_path = Path(git_text(path, "rev-parse", "--git-path", "config"))
    if not raw_config_path.is_absolute():
        raw_config_path = path / raw_config_path
    config_path = Path(os.path.abspath(raw_config_path))
    config_path.write_bytes(expected.isolated_config_bytes)
    config_path.chmod(expected.local_config_mode)
    _require_local_config_state_match(path, expected)
    if _portable_local_config(path) != expected.local_config:
        raise PreparationFailure(
            "nested checkout portable local config differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    observed_remote = _remote_local_config(path)
    wanted_remote = _neutralized_remote_config(expected.remote_config)
    if observed_remote != wanted_remote:
        raise PreparationFailure(
            "nested checkout remote config is not neutralized after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )


def _effective_git_config(
    path: Path,
    *,
    include_remote: bool = False,
) -> tuple[tuple[str, str, str], ...]:
    parts = git_bytes(path, "config", "--null", "--show-scope", "--list").split(b"\0")
    if parts and not parts[-1]:
        parts.pop()
    if len(parts) % 2:
        raise PreparationFailure(
            f"cannot parse effective nested checkout config: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    rows: list[tuple[str, str, str]] = []
    for offset in range(0, len(parts), 2):
        scope = parts[offset].decode("utf-8", errors="surrogateescape")
        raw_key, separator, raw_value = parts[offset + 1].partition(b"\n")
        if not separator:
            raise PreparationFailure(
                f"cannot parse effective nested checkout config: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        key = raw_key.decode("utf-8", errors="surrogateescape")
        value = raw_value.decode("utf-8", errors="surrogateescape")
        if key in ISOLATION_LOCAL_CONFIG_KEYS:
            continue
        if key.startswith("remote.") and not include_remote:
            continue
        rows.append((scope, key, value))
    return tuple(rows)


def _effective_url_rewrite_settings(path: Path) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (scope, key)
                for scope, key, _value in _effective_git_config(
                    path, include_remote=True
                )
                if key.startswith("url.")
                and key.endswith((".insteadof", ".pushinsteadof"))
            }
        )
    )


def _effective_submodule_transport_settings(
    path: Path,
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (scope, key)
                for scope, key, _value in _effective_git_config(
                    path, include_remote=True
                )
                if key.startswith("submodule.") and key.endswith(".url")
            }
        )
    )


def _require_effective_git_config_match(
    destination: Path,
    expected: NestedGitSnapshot,
) -> None:
    observed = _effective_git_config(destination)
    if observed != expected.effective_git_config:
        raise PreparationFailure(
            "nested checkout effective Git configuration differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "source_config_digest": sha256_bytes(
                    canonical_json(expected.effective_git_config)
                ),
                "destination_config_digest": sha256_bytes(canonical_json(observed)),
            },
        )


def _effective_external_rule_settings(path: Path) -> tuple[str, ...]:
    result = subprocess.run(
        (
            "git",
            "config",
            "--get-regexp",
            r"^(core\.excludesfile|core\.attributesfile)$",
        ),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect nested checkout external rule settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": result.stderr.strip()},
        )
    return tuple(sorted(line for line in result.stdout.splitlines() if line))


def _implicit_rule_sources() -> tuple[str, ...]:
    xdg_root = os.environ.get("XDG_CONFIG_HOME", "").strip()
    if xdg_root:
        config_root = Path(xdg_root)
    else:
        home = os.environ.get("HOME", "").strip()
        config_root = Path(home) / ".config" if home else Path("/nonexistent")
    candidates = (
        config_root / "git" / "attributes",
        config_root / "git" / "ignore",
        Path("/usr/etc/gitattributes"),
        Path("/etc/gitattributes"),
    )
    active: list[str] = []
    for candidate in candidates:
        if not candidate.is_file():
            continue
        if any(
            line.strip() and not line.lstrip().startswith(b"#")
            for line in candidate.read_bytes().splitlines()
        ):
            active.append(candidate.as_posix())
    return tuple(active)


def _partial_clone_settings(path: Path) -> tuple[str, ...]:
    result = subprocess.run(
        (
            "git",
            "config",
            "--local",
            "--get-regexp",
            r"^(extensions\.partialclone|remote\..*\.(promisor|partialclonefilter))$",
        ),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect nested checkout partial-clone settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": result.stderr.strip()},
        )
    return tuple(sorted(line for line in result.stdout.splitlines() if line))


def _replacement_refs(path: Path) -> tuple[str, ...]:
    bases = {"refs/replace/"}
    custom_base = os.environ.get("GIT_REPLACE_REF_BASE", "").strip()
    if custom_base:
        bases.add(custom_base.rstrip("/") + "/")
    refs: set[str] = set()
    for base in bases:
        if not base.startswith("refs/"):
            raise PreparationFailure(
                f"nested checkout has unsupported replacement-ref base: {base}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        output = git_text(path, "for-each-ref", "--format=%(refname)", base)
        refs.update(line for line in output.splitlines() if line)
    return tuple(sorted(refs))


def _active_filter_attribute_paths(
    path: Path,
    paths: Sequence[str],
    *,
    source: str | None = None,
) -> tuple[str, ...]:
    if not paths:
        return ()
    command = ["check-attr"]
    if source is not None:
        command.append(f"--source={source}")
    command.extend(("-z", "--stdin", "filter"))
    raw = git_bytes(
        path,
        *command,
        input_bytes=b"\0".join(
            item.encode("utf-8", errors="surrogateescape") for item in paths
        )
        + b"\0",
    )
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 3:
        raise PreparationFailure(
            f"cannot inspect nested checkout filter attributes: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    active: list[str] = []
    for offset in range(0, len(fields), 3):
        raw_path, attribute, value = fields[offset : offset + 3]
        if attribute != b"filter" or value in (b"unspecified", b"unset"):
            continue
        active.append(raw_path.decode("utf-8", errors="surrogateescape"))
    return tuple(active)


def _has_filter_attribute_declaration(content: bytes) -> bool:
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(b"#"):
            continue
        for token in re.split(rb"\s+", stripped):
            attribute = token.lstrip(b"-!")
            if attribute == b"filter" or attribute.startswith(b"filter="):
                return True
    return False


def _filter_attribute_sources(
    path: Path,
    candidate_paths: Sequence[str],
    head: str,
) -> tuple[str, ...]:
    sources: list[str] = []
    for raw in candidate_paths:
        relative = checked_relative_path(raw)
        if relative.name != ".gitattributes":
            continue
        candidate = path / relative
        if candidate.is_file() and _has_filter_attribute_declaration(candidate.read_bytes()):
            sources.append(f"candidate:{raw}")
        index_blob = subprocess.run(
            ("git", "show", f":{raw}"),
            cwd=path,
            check=False,
            capture_output=True,
        )
        if index_blob.returncode == 0 and _has_filter_attribute_declaration(
            index_blob.stdout
        ):
            sources.append(f"index:{raw}")
        if index_blob.returncode not in (0, 128):
            raise PreparationFailure(
                f"cannot inspect nested checkout index attributes: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
                details={
                    "stderr": index_blob.stderr.decode(
                        "utf-8", errors="replace"
                    ).strip()
                },
            )
    for raw in tree_paths(path, head):
        relative = checked_relative_path(raw)
        if relative.name != ".gitattributes":
            continue
        if _has_filter_attribute_declaration(git_bytes(path, "show", f"{head}:{raw}")):
            sources.append(f"HEAD:{raw}")
    return tuple(sorted(set(sources)))


def _has_submodule_url(content: bytes, path: Path) -> bool:
    result = subprocess.run(
        (
            "git",
            "config",
            "--file",
            "-",
            "--get-regexp",
            r"^submodule\..*\.url$",
        ),
        cwd=path,
        input=content,
        check=False,
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect nested checkout submodule transport config: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "stderr": result.stderr.decode("utf-8", errors="replace").strip()
            },
        )
    return result.returncode == 0


def _submodule_transport_sources(path: Path, head: str) -> tuple[str, ...]:
    sources: list[str] = []
    candidate = path / ".gitmodules"
    if candidate.is_file() and _has_submodule_url(candidate.read_bytes(), path):
        sources.append("candidate:.gitmodules")
    for label, spec in (("index", ":.gitmodules"), ("HEAD", f"{head}:.gitmodules")):
        blob = subprocess.run(
            ("git", "show", spec),
            cwd=path,
            check=False,
            capture_output=True,
        )
        if blob.returncode == 0 and _has_submodule_url(blob.stdout, path):
            sources.append(f"{label}:.gitmodules")
        if blob.returncode not in (0, 128):
            raise PreparationFailure(
                f"cannot inspect nested checkout submodule config: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
                details={
                    "stderr": blob.stderr.decode("utf-8", errors="replace").strip()
                },
            )
    return tuple(sources)


def _index_version(
    path: Path,
    *,
    env: Mapping[str, str] | None = None,
) -> int:
    raw = git_bytes(
        path,
        "update-index",
        "--show-index-version",
        env=env,
    ).decode("utf-8", errors="strict").strip()
    try:
        version = int(raw)
    except ValueError as exc:
        raise PreparationFailure(
            f"cannot inspect nested checkout index version: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"index_version": raw},
        ) from exc
    if version not in (2, 3, 4):
        raise PreparationFailure(
            f"nested checkout has unsupported index version: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"index_version": version},
        )
    return version


def _git_index_state(path: Path) -> tuple[int, bytes]:
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    raw_index_path = Path(git_text(path, "rev-parse", "--git-path", "index"))
    if not raw_index_path.is_absolute():
        raw_index_path = path / raw_index_path
    index_path = Path(os.path.abspath(raw_index_path))
    try:
        index_path.relative_to(git_dir)
    except ValueError as exc:
        raise PreparationFailure(
            f"nested checkout index is outside its Git directory: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"index_path": index_path.as_posix()},
        ) from exc
    try:
        metadata = index_path.lstat()
    except FileNotFoundError as exc:
        raise PreparationFailure(
            f"nested checkout index is missing: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        ) from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise PreparationFailure(
            f"nested checkout index is not a regular file: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"index_path": index_path.as_posix()},
        )
    return stat.S_IMODE(metadata.st_mode), index_path.read_bytes()


def _restore_git_index_state(
    path: Path,
    expected_mode: int,
    expected_bytes: bytes,
) -> None:
    index_path = Path(git_text(path, "rev-parse", "--git-path", "index"))
    if not index_path.is_absolute():
        index_path = path / index_path
    index_path.write_bytes(expected_bytes)
    index_path.chmod(expected_mode)
    observed = _git_index_state(path)
    if observed != (expected_mode, expected_bytes):
        raise PreparationFailure(
            "nested checkout index state differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )


def _git_object_inventory(path: Path) -> tuple[int, str]:
    output = git_text(
        path,
        "cat-file",
        "--batch-all-objects",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
    )
    rows: list[tuple[str, str, int]] = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) != 3:
            raise PreparationFailure(
                f"cannot inspect nested checkout object inventory: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        object_name, object_type, raw_size = fields
        if (
            len(object_name) not in (40, 64)
            or any(character not in "0123456789abcdef" for character in object_name)
            or object_type not in {"blob", "commit", "tag", "tree"}
        ):
            raise PreparationFailure(
                f"cannot parse nested checkout object inventory: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        try:
            size = int(raw_size)
        except ValueError as exc:
            raise PreparationFailure(
                f"cannot parse nested checkout object size: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            ) from exc
        rows.append((object_name, object_type, size))
    ordered = tuple(sorted(rows))
    return len(ordered), sha256_bytes(canonical_json(ordered))


def _git_object_storage_state(
    path: Path,
) -> tuple[tuple[str, str, int, int, str], ...]:
    objects_raw = git_text(path, "rev-parse", "--git-path", "objects")
    objects = Path(objects_raw)
    if not objects.is_absolute():
        objects = path / objects
    rows: list[tuple[str, str, int, int, str]] = []
    for current, dirnames, filenames in os.walk(objects, topdown=True):
        directory = Path(current)
        relative_directory = directory.relative_to(objects)
        directory_metadata = directory.lstat()
        if not stat.S_ISDIR(directory_metadata.st_mode):
            raise PreparationFailure(
                f"nested checkout object storage has unsupported directory: {directory}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        directory_label = "." if relative_directory == Path(".") else relative_directory.as_posix()
        rows.append(
            (
                "directory",
                directory_label,
                stat.S_IMODE(directory_metadata.st_mode),
                0,
                "",
            )
        )
        dirnames[:] = sorted(dirnames, key=os.fsencode)
        for name in sorted(filenames, key=os.fsencode):
            candidate = directory / name
            metadata = candidate.lstat()
            relative = candidate.relative_to(objects).as_posix()
            if not stat.S_ISREG(metadata.st_mode):
                raise PreparationFailure(
                    f"nested checkout object storage has unsupported file: {candidate}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                    details={"path": relative},
                )
            if metadata.st_nlink != 1:
                raise PreparationFailure(
                    f"nested checkout object storage has external hardlinks: {candidate}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                    details={"path": relative, "link_count": metadata.st_nlink},
                )
            content = candidate.read_bytes()
            rows.append(
                (
                    "file",
                    relative,
                    stat.S_IMODE(metadata.st_mode),
                    len(content),
                    sha256_bytes(content),
                )
            )
    return tuple(rows)


def _require_git_object_inventory_match(
    path: Path,
    expected_count: int,
    expected_digest: str,
) -> None:
    observed_count, observed_digest = _git_object_inventory(path)
    if (observed_count, observed_digest) != (expected_count, expected_digest):
        raise PreparationFailure(
            f"nested checkout object inventory differs after isolation: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "expected_count": expected_count,
                "actual_count": observed_count,
                "expected_digest": expected_digest,
                "actual_digest": observed_digest,
            },
        )


def _require_git_object_storage_match(
    path: Path,
    expected_state: Sequence[tuple[str, str, int, int, str]],
) -> None:
    observed_state = _git_object_storage_state(path)
    if tuple(observed_state) != tuple(expected_state):
        expected_only = sorted(set(expected_state) - set(observed_state))[:20]
        observed_only = sorted(set(observed_state) - set(expected_state))[:20]
        raise PreparationFailure(
            f"nested checkout physical object storage differs after isolation: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "expected_digest": sha256_bytes(canonical_json(tuple(expected_state))),
                "actual_digest": sha256_bytes(canonical_json(observed_state)),
                "expected_only": [list(row) for row in expected_only],
                "observed_only": [list(row) for row in observed_only],
            },
        )


def _restore_git_object_storage_modes(
    path: Path,
    expected_state: Sequence[tuple[str, str, int, int, str]],
) -> None:
    objects_raw = git_text(path, "rev-parse", "--git-path", "objects")
    objects = Path(objects_raw)
    if not objects.is_absolute():
        objects = path / objects
    for kind, raw, mode, _size, _digest in sorted(
        expected_state,
        key=lambda row: (row[1].count("/"), row[1]),
        reverse=True,
    ):
        candidate = objects if raw == "." else objects / checked_relative_path(raw)
        try:
            metadata = candidate.lstat()
        except FileNotFoundError as exc:
            raise PreparationFailure(
                f"nested checkout physical object storage path is absent: {candidate}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            ) from exc
        expected_type = stat.S_IFDIR if kind == "directory" else stat.S_IFREG
        if stat.S_IFMT(metadata.st_mode) != expected_type:
            raise PreparationFailure(
                f"nested checkout physical object storage path changed type: {candidate}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        candidate.chmod(mode)


def _restrictive_git_admin_directory_modes(path: Path) -> tuple[str, ...]:
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    restrictive: list[str] = []

    def visit(directory: Path, relative: Path) -> None:
        metadata = directory.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if mode & stat.S_IRWXU != stat.S_IRWXU:
            label = "." if relative == Path(".") else relative.as_posix()
            restrictive.append(f"{label} mode={mode:04o}")
        for child in sorted(directory.iterdir(), key=lambda item: os.fsencode(item.name)):
            child_relative = child.relative_to(git_dir)
            child_metadata = child.lstat()
            if not stat.S_ISDIR(child_metadata.st_mode) or stat.S_ISLNK(
                child_metadata.st_mode
            ):
                continue
            if child_relative.parts[0] == "logs":
                # Reflog directory modes are captured and restored explicitly.
                continue
            visit(child, child_relative)

    visit(git_dir, Path("."))
    return tuple(restrictive)


def _restrictive_git_admin_file_modes(path: Path) -> tuple[str, ...]:
    """Reject mutable administration files whose owner-write posture clone loses."""
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    restrictive: list[str] = []
    for candidate in sorted(
        git_dir.rglob("*"),
        key=lambda item: os.fsencode(item.relative_to(git_dir).as_posix()),
    ):
        relative = candidate.relative_to(git_dir)
        if "objects" in relative.parts:
            # Git object files are immutable storage and are normally read-only.
            continue
        metadata = candidate.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            continue
        mode = stat.S_IMODE(metadata.st_mode)
        if mode & (stat.S_IRUSR | stat.S_IWUSR) != (stat.S_IRUSR | stat.S_IWUSR):
            restrictive.append(f"{relative.as_posix()} mode={mode:04o}")
    return tuple(restrictive)


def _git_admin_portability_issues(
    path: Path,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    bytes | None,
]:
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    expected_uid = os.geteuid()
    expected_gid = os.getegid()
    ownership: list[str] = []
    symlinks: list[str] = []
    xattrs: list[str] = []
    security_label_issues: list[str] = []
    root_security_label: bytes | None = None
    pending = [git_dir]
    while pending:
        candidate = pending.pop()
        metadata = candidate.lstat()
        relative = candidate.relative_to(git_dir)
        label = "." if relative == Path(".") else relative.as_posix()
        if metadata.st_uid != expected_uid or metadata.st_gid != expected_gid:
            ownership.append(
                f"{label} uid={metadata.st_uid} gid={metadata.st_gid} "
                f"expected_uid={expected_uid} expected_gid={expected_gid}"
            )
        if stat.S_ISLNK(metadata.st_mode):
            symlinks.append(label)
            continue
        try:
            attribute_names = sorted(
                os.listxattr(candidate, follow_symlinks=False),
                key=os.fsencode,
            )
        except OSError as exc:
            raise PreparationFailure(
                f"cannot inspect nested Git administration attributes: {candidate}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
                details={"git_admin_path": label, "error": str(exc)},
            ) from exc
        xattrs.extend(
            f"{label} attribute={name}"
            for name in attribute_names
            if name != "security.selinux"
        )
        security_label = None
        if "security.selinux" in attribute_names:
            try:
                security_label = os.getxattr(
                    candidate,
                    "security.selinux",
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise PreparationFailure(
                    f"cannot read nested Git administration security label: {candidate}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                    details={"git_admin_path": label, "error": str(exc)},
                ) from exc
        if label == ".":
            root_security_label = security_label
        elif security_label != root_security_label:
            security_label_issues.append(label)
        if stat.S_ISDIR(metadata.st_mode):
            pending.extend(
                reversed(
                    sorted(
                        candidate.iterdir(),
                        key=lambda item: os.fsencode(item.name),
                    )
                )
            )
    return (
        tuple(ownership),
        tuple(symlinks),
        tuple(xattrs),
        tuple(security_label_issues),
        root_security_label,
    )


def _require_git_admin_portability_match(
    path: Path,
    expected_security_label: bytes | None,
) -> None:
    (
        ownership,
        symlinks,
        xattrs,
        security_label_issues,
        security_label,
    ) = _git_admin_portability_issues(path)
    if ownership or symlinks or xattrs or security_label_issues:
        raise PreparationFailure(
            "nested Git administration metadata differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "git_admin_ownership": list(ownership),
                "git_admin_symlinks": list(symlinks),
                "git_admin_xattrs": list(xattrs),
                "git_admin_security_label_issues": list(security_label_issues),
            },
        )
    if security_label != expected_security_label:
        raise PreparationFailure(
            "nested Git administration security label differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )


def _git_admin_state(
    path: Path,
) -> tuple[
    tuple[tuple[str, int], ...],
    tuple[tuple[str, int, int, bytes], ...],
]:
    """Capture all Git-admin state not intentionally isolated elsewhere."""
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    directories: list[tuple[str, int]] = []
    files: list[tuple[str, int, int, bytes]] = []
    for current, dirnames, filenames in os.walk(git_dir, topdown=True):
        directory = Path(current)
        relative_directory = directory.relative_to(git_dir)
        if relative_directory == Path("."):
            dirnames[:] = [name for name in dirnames if name != "objects"]
            filenames = [name for name in filenames if name != "config"]
        dirnames[:] = sorted(dirnames, key=os.fsencode)
        metadata = directory.lstat()
        if not stat.S_ISDIR(metadata.st_mode):
            raise PreparationFailure(
                f"nested Git administration has unsupported directory: {directory}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        label = "." if relative_directory == Path(".") else relative_directory.as_posix()
        directories.append((label, stat.S_IMODE(metadata.st_mode)))
        for name in sorted(filenames, key=os.fsencode):
            candidate = directory / name
            file_metadata = candidate.lstat()
            relative = candidate.relative_to(git_dir).as_posix()
            if not stat.S_ISREG(file_metadata.st_mode):
                raise PreparationFailure(
                    f"nested Git administration has unsupported file: {candidate}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                    details={"git_admin_path": relative},
                )
            if file_metadata.st_nlink != 1:
                raise PreparationFailure(
                    f"nested Git administration has external hardlinks: {candidate}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                    details={
                        "git_admin_path": relative,
                        "link_count": file_metadata.st_nlink,
                    },
                )
            files.append(
                (
                    relative,
                    stat.S_IMODE(file_metadata.st_mode),
                    file_metadata.st_mtime_ns,
                    candidate.read_bytes(),
                )
            )
    return tuple(directories), tuple(files)


def _restore_git_admin_state(
    path: Path,
    expected_directories: Sequence[tuple[str, int]],
    expected_files: Sequence[tuple[str, int, int, bytes]],
) -> None:
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    existing_files: list[Path] = []
    existing_directories: list[Path] = []
    for current, dirnames, filenames in os.walk(git_dir, topdown=True):
        directory = Path(current)
        if directory == git_dir:
            dirnames[:] = [name for name in dirnames if name != "objects"]
            filenames = [name for name in filenames if name != "config"]
        dirnames[:] = sorted(dirnames, key=os.fsencode)
        for name in filenames:
            existing_files.append(directory / name)
        for name in dirnames:
            existing_directories.append(directory / name)
    for candidate in existing_directories:
        if not candidate.is_symlink():
            candidate.chmod(stat.S_IMODE(candidate.lstat().st_mode) | stat.S_IRWXU)
    for candidate in existing_files:
        candidate.unlink()
    for candidate in sorted(
        existing_directories,
        key=lambda item: len(item.relative_to(git_dir).parts),
        reverse=True,
    ):
        if candidate.is_symlink():
            candidate.unlink()
        else:
            candidate.rmdir()

    for relative, _mode in expected_directories:
        if relative != ".":
            (git_dir / checked_relative_path(relative)).mkdir(parents=True, exist_ok=True)
    for relative, mode, mtime_ns, content in expected_files:
        destination = git_dir / checked_relative_path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        destination.chmod(mode)
        os.utime(
            destination,
            ns=(destination.stat().st_atime_ns, mtime_ns),
            follow_symlinks=False,
        )
    for relative, mode in reversed(tuple(expected_directories)):
        destination = git_dir if relative == "." else git_dir / checked_relative_path(relative)
        destination.chmod(mode)

    observed = _git_admin_state(path)
    expected = (tuple(expected_directories), tuple(expected_files))
    if observed != expected:
        def state_digest(
            state: tuple[
                tuple[tuple[str, int], ...],
                tuple[tuple[str, int, int, bytes], ...],
            ],
        ) -> str:
            directories, files_state = state
            return sha256_bytes(
                canonical_json(
                    {
                        "directories": [list(row) for row in directories],
                        "files": [
                            [
                                name,
                                mode,
                                mtime_ns,
                                len(content),
                                sha256_bytes(content),
                            ]
                            for name, mode, mtime_ns, content in files_state
                        ],
                    }
                )
            )

        raise PreparationFailure(
            "nested Git administration state differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "expected_digest": state_digest(expected),
                "actual_digest": state_digest(observed),
            },
        )


def _git_admin_lock_paths(path: Path) -> tuple[str, ...]:
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    locks: list[str] = []
    for candidate in sorted(
        git_dir.rglob("*"),
        key=lambda item: os.fsencode(item.relative_to(git_dir).as_posix()),
    ):
        if candidate.name.endswith(".lock"):
            locks.append(candidate.relative_to(git_dir).as_posix())
    return tuple(locks)


def _file_has_sparse_extents(path: Path, metadata: os.stat_result) -> bool:
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size == 0:
        return False
    if metadata.st_blocks * 512 < metadata.st_size:
        return True
    if not hasattr(os, "SEEK_DATA") or not hasattr(os, "SEEK_HOLE"):
        return False
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        try:
            first_data = os.lseek(descriptor, 0, os.SEEK_DATA)
        except OSError as exc:
            if exc.errno == errno.ENXIO:
                return True
            if exc.errno in (errno.EINVAL, errno.ENOTSUP, errno.ENOSYS, errno.ENODEV):
                return False
            raise
        try:
            first_hole = os.lseek(descriptor, 0, os.SEEK_HOLE)
        except OSError as exc:
            if exc.errno in (errno.EINVAL, errno.ENOTSUP, errno.ENOSYS, errno.ENODEV):
                return False
            raise
        return first_data > 0 or first_hole < metadata.st_size
    finally:
        os.close(descriptor)


def _sparse_worktree_paths(
    path: Path,
    candidate_paths: Sequence[str],
) -> tuple[str, ...]:
    sparse: list[str] = []
    for raw in sorted(set(candidate_paths)):
        candidate = path / checked_relative_path(raw)
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        if _file_has_sparse_extents(candidate, metadata):
            sparse.append(raw)
    return tuple(sparse)


def _worktree_hardlink_groups(
    path: Path,
    candidate_paths: Sequence[str],
) -> tuple[tuple[str, ...], ...]:
    inode_paths: dict[tuple[int, int], list[str]] = {}
    inode_links: dict[tuple[int, int], int] = {}
    for raw in sorted(set(candidate_paths)):
        candidate = path / checked_relative_path(raw)
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(metadata.st_mode):
            continue
        inode = (metadata.st_dev, metadata.st_ino)
        inode_paths.setdefault(inode, []).append(raw)
        inode_links[inode] = metadata.st_nlink
    external: list[str] = []
    groups: list[tuple[str, ...]] = []
    for inode, paths in inode_paths.items():
        ordered = tuple(sorted(paths))
        if inode_links[inode] != len(ordered):
            external.extend(ordered)
        elif len(ordered) > 1:
            groups.append(ordered)
    if external:
        raise PreparationFailure(
            f"candidate contains worktree hardlinks outside its identity: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"external_hardlink_paths": sorted(external)},
        )
    return tuple(sorted(groups))


def _regular_worktree_mode_state(
    path: Path,
    candidate_paths: Sequence[str],
) -> tuple[tuple[str, int], ...]:
    state: list[tuple[str, int]] = []
    for raw in sorted(set(candidate_paths)):
        candidate = path / checked_relative_path(raw)
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISREG(metadata.st_mode):
            state.append((raw, stat.S_IMODE(metadata.st_mode)))
    return tuple(state)


def _nonportable_worktree_ownership(
    path: Path,
    candidate_paths: Sequence[str],
    directory_paths: Sequence[str],
) -> tuple[str, ...]:
    """Reject ownership which a non-privileged isolated clone cannot preserve."""
    expected_uid = os.geteuid()
    expected_gid = os.getegid()
    mismatches: list[str] = []
    for raw in (".", *sorted(set((*candidate_paths, *directory_paths)))):
        candidate = path if raw == "." else path / checked_relative_path(raw)
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        if metadata.st_uid == expected_uid and metadata.st_gid == expected_gid:
            continue
        mismatches.append(
            f"{raw} uid={metadata.st_uid} gid={metadata.st_gid} "
            f"expected_uid={expected_uid} expected_gid={expected_gid}"
        )
    return tuple(mismatches)


def _worktree_xattr_state(
    path: Path,
    candidate_paths: Sequence[str],
    directory_paths: Sequence[str],
) -> tuple[tuple[str, tuple[tuple[str, bytes], ...]], ...]:
    state: list[tuple[str, tuple[tuple[str, bytes], ...]]] = []
    for raw in (".", *sorted(set((*candidate_paths, *directory_paths)))):
        candidate = path if raw == "." else path / checked_relative_path(raw)
        try:
            names = sorted(
                os.listxattr(candidate, follow_symlinks=False),
                key=os.fsencode,
            )
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise PreparationFailure(
                f"cannot inspect candidate extended attributes: {candidate}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
                details={"path": raw, "error": str(exc)},
            ) from exc
        attributes: list[tuple[str, bytes]] = []
        for name in names:
            try:
                value = os.getxattr(
                    candidate,
                    name,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise PreparationFailure(
                    f"cannot read candidate extended attribute: {candidate}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                    details={"path": raw, "attribute": name, "error": str(exc)},
                ) from exc
            attributes.append((name, value))
        if attributes:
            state.append((raw, tuple(attributes)))
    return tuple(state)


def _worktree_mtime_state(
    path: Path,
    candidate_paths: Sequence[str],
    directory_paths: Sequence[str],
) -> tuple[tuple[str, int], ...]:
    state: list[tuple[str, int]] = []
    for raw in (".", *sorted(set((*candidate_paths, *directory_paths)))):
        candidate = path if raw == "." else path / checked_relative_path(raw)
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        state.append((raw, metadata.st_mtime_ns))
    return tuple(state)


def _restore_worktree_mtimes(
    path: Path,
    expected_state: Sequence[tuple[str, int]],
) -> None:
    ordered = sorted(
        expected_state,
        key=lambda row: (row[0].count("/"), row[0]),
        reverse=True,
    )
    for raw, mtime_ns in ordered:
        candidate = path if raw == "." else path / checked_relative_path(raw)
        try:
            metadata = candidate.lstat()
            os.utime(
                candidate,
                ns=(metadata.st_atime_ns, mtime_ns),
                follow_symlinks=False,
            )
        except OSError as exc:
            raise PreparationFailure(
                f"cannot restore candidate modification time: {candidate}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
                details={"path": raw, "error": str(exc)},
            ) from exc


def _restore_worktree_xattrs(
    path: Path,
    candidate_paths: Sequence[str],
    directory_paths: Sequence[str],
    expected_state: Sequence[tuple[str, Sequence[tuple[str, bytes]]]],
) -> None:
    expected_by_path = {
        raw: dict(attributes) for raw, attributes in expected_state
    }
    for raw in (".", *sorted(set((*candidate_paths, *directory_paths)))):
        candidate = path if raw == "." else path / checked_relative_path(raw)
        try:
            candidate.lstat()
        except FileNotFoundError:
            continue
        expected = expected_by_path.get(raw, {})
        try:
            observed_names = set(os.listxattr(candidate, follow_symlinks=False))
            for name in sorted(observed_names - expected.keys(), key=os.fsencode):
                os.removexattr(candidate, name, follow_symlinks=False)
            for name, value in sorted(expected.items(), key=lambda row: os.fsencode(row[0])):
                if (
                    name not in observed_names
                    or os.getxattr(candidate, name, follow_symlinks=False) != value
                ):
                    os.setxattr(candidate, name, value, follow_symlinks=False)
        except OSError as exc:
            raise PreparationFailure(
                f"cannot restore candidate extended attributes: {candidate}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
                details={"path": raw, "error": str(exc)},
            ) from exc


def _make_worktree_owner_writable(
    path: Path,
    candidate_paths: Sequence[str],
    directory_paths: Sequence[str],
) -> tuple[tuple[Path, int], ...]:
    captured: list[tuple[Path, int]] = []
    raw_paths = (
        ".",
        *sorted(
            set(directory_paths),
            key=lambda raw: (raw.count("/"), raw),
        ),
        *sorted(set(candidate_paths)),
    )
    visited: set[Path] = set()
    for raw in raw_paths:
        candidate = path if raw == "." else path / checked_relative_path(raw)
        if candidate in visited:
            continue
        visited.add(candidate)
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        mode = stat.S_IMODE(metadata.st_mode)
        if stat.S_ISDIR(metadata.st_mode):
            writable_mode = mode | stat.S_IWUSR | stat.S_IXUSR
        elif stat.S_ISREG(metadata.st_mode):
            writable_mode = mode | stat.S_IWUSR
        elif stat.S_ISLNK(metadata.st_mode):
            continue
        else:
            raise PreparationFailure(
                f"candidate xattr path has unsupported type: {candidate}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
                details={"path": raw},
            )
        captured.append((candidate, mode))
        if writable_mode != mode:
            candidate.chmod(writable_mode)
    return tuple(captured)


def _restore_worktree_hardlinks(
    path: Path,
    groups: Sequence[Sequence[str]],
) -> None:
    for group in groups:
        anchor = path / checked_relative_path(group[0])
        if not stat.S_ISREG(anchor.lstat().st_mode):
            raise PreparationFailure(
                "candidate hardlink anchor changed type during isolation",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        for raw in group[1:]:
            destination = path / checked_relative_path(raw)
            if not stat.S_ISREG(destination.lstat().st_mode):
                raise PreparationFailure(
                    "candidate hardlink target changed type during isolation",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                )
            destination.unlink()
            os.link(anchor, destination)


def _symbolic_head(path: Path) -> str | None:
    result = subprocess.run(
        ("git", "symbolic-ref", "--quiet", "HEAD"),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise PreparationFailure(
            f"cannot inspect nested checkout symbolic HEAD: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": result.stderr.strip()},
        )
    value = result.stdout.strip()
    if not value.startswith("refs/heads/"):
        raise PreparationFailure(
            f"nested checkout has unsupported symbolic HEAD: {value}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    return value


def _git_ref_state(path: Path) -> tuple[str | None, tuple[tuple[str, str], ...]]:
    output = git_text(
        path,
        "for-each-ref",
        "--format=%(refname)%09%(objectname)%09%(symref)%09.",
        "refs",
    )
    origin_head: str | None = None
    direct_refs: list[tuple[str, str]] = []
    for line in output.splitlines():
        refname, object_name, symbolic, marker = line.split("\t", 3)
        if marker != ".":
            raise PreparationFailure(
                f"cannot parse nested checkout remote ref state: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        if symbolic:
            if refname != "refs/remotes/origin/HEAD":
                raise PreparationFailure(
                    f"nested checkout has unsupported symbolic remote ref: {refname}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                )
            origin_head = symbolic
            continue
        direct_refs.append((refname, object_name))
    if origin_head is not None and not origin_head.startswith("refs/remotes/origin/"):
        raise PreparationFailure(
            f"nested checkout origin/HEAD targets an unsupported ref: {origin_head}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    return origin_head, tuple(sorted(direct_refs))


def _git_ref_storage_paths(path: Path) -> tuple[Path, Path]:
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    raw_refs = Path(git_text(path, "rev-parse", "--git-path", "refs"))
    refs_root = raw_refs if raw_refs.is_absolute() else path / raw_refs
    raw_packed = Path(git_text(path, "rev-parse", "--git-path", "packed-refs"))
    packed_refs = raw_packed if raw_packed.is_absolute() else path / raw_packed
    if refs_root.resolve(strict=False) != git_dir / "refs":
        raise PreparationFailure(
            f"nested checkout ref storage escapes its Git directory: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"refs_root": refs_root.as_posix()},
        )
    if packed_refs.resolve(strict=False) != git_dir / "packed-refs":
        raise PreparationFailure(
            f"nested checkout packed-ref storage escapes its Git directory: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"packed_refs": packed_refs.as_posix()},
        )
    return refs_root, packed_refs


def _git_ref_storage_state(
    path: Path,
) -> tuple[
    int | None,
    tuple[tuple[str, int], ...],
    tuple[tuple[str, int, bytes], ...],
    int | None,
    bytes | None,
]:
    refs_root, packed_refs = _git_ref_storage_paths(path)
    root_mode: int | None = None
    directories: list[tuple[str, int]] = []
    files: list[tuple[str, int, bytes]] = []
    if refs_root.exists() or refs_root.is_symlink():
        root_metadata = refs_root.lstat()
        if not stat.S_ISDIR(root_metadata.st_mode) or stat.S_ISLNK(
            root_metadata.st_mode
        ):
            raise PreparationFailure(
                f"nested checkout has unsupported loose-ref root: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        root_mode = stat.S_IMODE(root_metadata.st_mode)

        def visit(directory: Path) -> None:
            for child in sorted(
                directory.iterdir(),
                key=lambda item: os.fsencode(item.name),
            ):
                relative = child.relative_to(refs_root).as_posix()
                checked_relative_path(relative)
                metadata = child.lstat()
                if stat.S_ISLNK(metadata.st_mode):
                    raise PreparationFailure(
                        f"nested checkout loose-ref tree contains a symlink: {path}",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                        details={"ref_path": relative},
                    )
                mode = stat.S_IMODE(metadata.st_mode)
                if stat.S_ISDIR(metadata.st_mode):
                    directories.append((relative, mode))
                    visit(child)
                elif stat.S_ISREG(metadata.st_mode):
                    files.append((relative, mode, child.read_bytes()))
                else:
                    raise PreparationFailure(
                        f"nested checkout loose-ref tree has an unsupported entry: {path}",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                        details={"ref_path": relative},
                    )

        visit(refs_root)

    packed_mode: int | None = None
    packed_bytes: bytes | None = None
    if packed_refs.exists() or packed_refs.is_symlink():
        packed_metadata = packed_refs.lstat()
        if not stat.S_ISREG(packed_metadata.st_mode) or stat.S_ISLNK(
            packed_metadata.st_mode
        ):
            raise PreparationFailure(
                f"nested checkout has unsupported packed-ref storage: {path}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        packed_mode = stat.S_IMODE(packed_metadata.st_mode)
        packed_bytes = packed_refs.read_bytes()
    return (
        root_mode,
        tuple(directories),
        tuple(files),
        packed_mode,
        packed_bytes,
    )


def _restore_git_ref_state(path: Path, expected: NestedGitSnapshot) -> None:
    observed_head, observed_refs = _git_ref_state(path)
    if observed_head is not None:
        git_bytes(path, "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
    for refname, _object_name in observed_refs:
        git_bytes(path, "update-ref", "-d", refname)
    for refname, object_name in expected.git_refs:
        available = subprocess.run(
            ("git", "cat-file", "-e", f"{object_name}^{{object}}"),
            cwd=path,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if available.returncode != 0:
            raise PreparationFailure(
                f"nested checkout remote ref object is unavailable after isolation: {refname}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
                details={"ref": refname, "object": object_name},
            )
        git_bytes(path, "update-ref", refname, object_name)
    if expected.origin_head is not None:
        git_bytes(
            path,
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            expected.origin_head,
        )
    restored = _git_ref_state(path)
    wanted = (expected.origin_head, expected.git_refs)
    if restored != wanted:
        raise PreparationFailure(
            "nested checkout remote refs differ after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"expected": wanted, "actual": restored},
        )


def _restore_git_ref_storage(path: Path, expected: NestedGitSnapshot) -> None:
    refs_root, packed_refs = _git_ref_storage_paths(path)
    if refs_root.exists() or refs_root.is_symlink():
        metadata = refs_root.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise PreparationFailure(
                "nested checkout loose-ref root changed type during isolation",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        shutil.rmtree(refs_root)
    if expected.ref_root_mode is not None:
        refs_root.mkdir(mode=0o700)
        refs_root.chmod(0o700)
        for relative, _mode in expected.ref_directories:
            directory = refs_root / checked_relative_path(relative)
            directory.mkdir(mode=0o700, parents=True, exist_ok=False)
            directory.chmod(0o700)
        for relative, mode, content in expected.loose_ref_files:
            destination = refs_root / checked_relative_path(relative)
            destination.write_bytes(content)
            destination.chmod(mode)
        for relative, mode in reversed(expected.ref_directories):
            (refs_root / checked_relative_path(relative)).chmod(mode)
        refs_root.chmod(expected.ref_root_mode)

    if packed_refs.exists() or packed_refs.is_symlink():
        metadata = packed_refs.lstat()
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise PreparationFailure(
                "nested checkout packed-ref storage changed type during isolation",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        packed_refs.unlink()
    if expected.packed_refs_mode is not None:
        if expected.packed_refs_bytes is None:
            raise PreparationFailure(
                "nested checkout packed-ref snapshot is internally inconsistent",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        packed_refs.write_bytes(expected.packed_refs_bytes)
        packed_refs.chmod(expected.packed_refs_mode)
    elif expected.packed_refs_bytes is not None:
        raise PreparationFailure(
            "nested checkout packed-ref snapshot is internally inconsistent",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )

    restored = _git_ref_storage_state(path)
    wanted = (
        expected.ref_root_mode,
        expected.ref_directories,
        expected.loose_ref_files,
        expected.packed_refs_mode,
        expected.packed_refs_bytes,
    )
    if restored != wanted:
        raise PreparationFailure(
            "nested checkout ref storage differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    logical = _git_ref_state(path)
    expected_logical = (expected.origin_head, expected.git_refs)
    if logical != expected_logical:
        raise PreparationFailure(
            "nested checkout refs differ after exact storage restoration",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"expected": expected_logical, "actual": logical},
        )


def _shallow_boundaries(path: Path) -> tuple[str, ...]:
    shallow = git_text(path, "rev-parse", "--is-shallow-repository")
    if shallow == "false":
        return ()
    if shallow != "true":
        raise PreparationFailure(
            f"cannot inspect nested checkout shallow state: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    shallow_path = Path(git_text(path, "rev-parse", "--git-path", "shallow"))
    if not shallow_path.is_absolute():
        shallow_path = path / shallow_path
    boundaries = tuple(
        sorted(line.strip() for line in shallow_path.read_text(encoding="ascii").splitlines() if line.strip())
    )
    if not boundaries:
        raise PreparationFailure(
            f"nested checkout reports shallow history without boundaries: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    return boundaries


def _history_storage_overrides(path: Path) -> tuple[str, ...]:
    overrides: list[str] = []
    for raw in ("info/grafts", "objects/info/alternates", "objects/info/http-alternates"):
        candidate = Path(git_text(path, "rev-parse", "--git-path", raw))
        if not candidate.is_absolute():
            candidate = path / candidate
        if candidate.is_file() and candidate.read_bytes().strip():
            overrides.append(raw)
    return tuple(overrides)


def _in_progress_operation_state(path: Path) -> tuple[str, ...]:
    markers = (
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "REBASE_HEAD",
        "rebase-apply",
        "rebase-merge",
        "sequencer",
        "BISECT_START",
    )
    active: list[str] = []
    for marker in markers:
        candidate = Path(git_text(path, "rev-parse", "--git-path", marker))
        if not candidate.is_absolute():
            candidate = path / candidate
        if candidate.exists():
            active.append(marker)
    return tuple(active)


def _rerere_cache_state(path: Path) -> tuple[str, ...]:
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    raw_root = Path(git_text(path, "rev-parse", "--git-path", "rr-cache"))
    root = raw_root if raw_root.is_absolute() else path / raw_root
    if root.resolve(strict=False) != git_dir / "rr-cache":
        raise PreparationFailure(
            f"nested checkout rerere cache escapes its Git directory: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"rerere_cache_root": root.as_posix()},
        )
    if not root.exists() and not root.is_symlink():
        return ()
    paths = ["."]
    if root.is_dir() and not root.is_symlink():
        paths.extend(
            child.relative_to(root).as_posix()
            for child in sorted(
                root.rglob("*"),
                key=lambda item: os.fsencode(item.relative_to(root).as_posix()),
            )
        )
    return tuple(paths)


def _unsupported_pseudo_ref_state(path: Path) -> tuple[str, ...]:
    names = (
        "FETCH_HEAD",
        "ORIG_HEAD",
        "AUTO_MERGE",
        "MERGE_AUTOSTASH",
        "BISECT_HEAD",
    )
    active: list[str] = []
    for name in names:
        candidate = Path(git_text(path, "rev-parse", "--git-path", name))
        if not candidate.is_absolute():
            candidate = path / candidate
        if candidate.is_file() and candidate.read_bytes().strip():
            active.append(name)
    return tuple(active)


def _resolve_undo_entries(path: Path) -> tuple[str, ...]:
    return tuple(
        entry.decode("utf-8", errors="surrogateescape")
        for entry in git_bytes(path, "ls-files", "--resolve-undo", "-z").split(b"\0")
        if entry
    )


def _registered_worktree_paths(path: Path) -> tuple[str, ...]:
    fields = git_bytes(path, "worktree", "list", "--porcelain", "-z").split(b"\0")
    worktrees = tuple(
        field.removeprefix(b"worktree ").decode(
            "utf-8", errors="surrogateescape"
        )
        for field in fields
        if field.startswith(b"worktree ")
    )
    if not worktrees:
        raise PreparationFailure(
            f"cannot inspect nested checkout worktree registrations: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    return worktrees


def _reflog_root(path: Path) -> Path:
    git_dir = Path(git_text(path, "rev-parse", "--absolute-git-dir")).resolve()
    raw_root = Path(git_text(path, "rev-parse", "--git-path", "logs"))
    root = raw_root if raw_root.is_absolute() else path / raw_root
    resolved = root.resolve(strict=False)
    if resolved != git_dir / "logs":
        raise PreparationFailure(
            f"nested checkout reflog storage escapes its Git directory: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"reflog_root": root.as_posix()},
        )
    return root


def _reflog_state(
    path: Path,
) -> tuple[
    int | None,
    tuple[tuple[str, int], ...],
    tuple[tuple[str, int, bytes], ...],
]:
    root = _reflog_root(path)
    if not root.exists() and not root.is_symlink():
        return None, (), ()
    root_metadata = root.lstat()
    if not stat.S_ISDIR(root_metadata.st_mode) or stat.S_ISLNK(root_metadata.st_mode):
        raise PreparationFailure(
            f"nested checkout has unsupported reflog root: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    directories: list[tuple[str, int]] = []
    files: list[tuple[str, int, bytes]] = []

    def visit(directory: Path) -> None:
        for child in sorted(directory.iterdir(), key=lambda item: os.fsencode(item.name)):
            relative = child.relative_to(root).as_posix()
            checked_relative_path(relative)
            metadata = child.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise PreparationFailure(
                    f"nested checkout reflog tree contains a symlink: {path}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                    details={"reflog_path": relative},
                )
            mode = stat.S_IMODE(metadata.st_mode)
            if stat.S_ISDIR(metadata.st_mode):
                directories.append((relative, mode))
                visit(child)
            elif stat.S_ISREG(metadata.st_mode):
                files.append((relative, mode, child.read_bytes()))
            else:
                raise PreparationFailure(
                    f"nested checkout reflog tree has an unsupported entry: {path}",
                    failure_type="candidate_snapshot_invalid",
                    action_class="code_fix",
                    details={"reflog_path": relative},
                )

    visit(root)
    return (
        stat.S_IMODE(root_metadata.st_mode),
        tuple(directories),
        tuple(files),
    )


def _restore_reflog_state(path: Path, expected: NestedGitSnapshot) -> None:
    root = _reflog_root(path)
    if root.exists() or root.is_symlink():
        metadata = root.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise PreparationFailure(
                "nested checkout reflog root changed type during isolation",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        shutil.rmtree(root)
    if expected.reflog_root_mode is not None:
        root.mkdir(mode=0o700)
        root.chmod(0o700)
        for relative, _mode in expected.reflog_directories:
            directory = root / checked_relative_path(relative)
            directory.mkdir(mode=0o700, parents=True, exist_ok=False)
            directory.chmod(0o700)
        for relative, mode, content in expected.reflog_files:
            destination = root / checked_relative_path(relative)
            destination.write_bytes(content)
            destination.chmod(mode)
        for relative, mode in reversed(expected.reflog_directories):
            (root / checked_relative_path(relative)).chmod(mode)
        root.chmod(expected.reflog_root_mode)
    restored = _reflog_state(path)
    wanted = (
        expected.reflog_root_mode,
        expected.reflog_directories,
        expected.reflog_files,
    )
    if restored != wanted:
        raise PreparationFailure(
            "nested checkout reflogs differ after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )


def _require_effective_checkout_settings_match(source: Path, destination: Path) -> None:
    source_settings = _effective_checkout_settings(source)
    destination_settings = _effective_checkout_settings(destination)
    if source_settings != destination_settings:
        raise PreparationFailure(
            f"nested checkout conversion settings change in isolation: {source}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "source_settings_digest": sha256_bytes(canonical_json(source_settings)),
                "destination_settings_digest": sha256_bytes(canonical_json(destination_settings)),
            },
        )


def _nonportable_index_flag_paths(path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    entries = tuple(
        entry.decode("utf-8", errors="surrogateescape")
        for entry in git_bytes(path, "ls-files", "-v", "-z").split(b"\0")
        if entry
    )
    malformed = tuple(entry for entry in entries if len(entry) < 3 or entry[1] != " ")
    if malformed:
        raise PreparationFailure(
            f"cannot parse checkout index flags: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"malformed_index_flag_entries": list(malformed)},
        )
    skip_worktree_paths = tuple(
        entry[2:] for entry in entries if entry[0] in ("S", "s")
    )
    assume_unchanged_paths = tuple(
        entry[2:] for entry in entries if entry[0].islower()
    )
    return skip_worktree_paths, assume_unchanged_paths


def _nonportable_local_checkout_settings(path: Path) -> tuple[str, ...]:
    result = subprocess.run(
        (
            "git",
            "config",
            "--local",
            "--get-regexp",
            CHECKOUT_CONVERSION_CONFIG_PATTERN,
        ),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect nested checkout conversion settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": result.stderr.strip()},
        )
    settings = [line for line in result.stdout.splitlines() if line]
    for info_name in ("attributes", "exclude"):
        info_raw = git_text(path, "rev-parse", "--git-path", f"info/{info_name}")
        info_path = Path(info_raw)
        if not info_path.is_absolute():
            info_path = path / info_path
        if info_path.is_file() and any(
            line.strip() and not line.lstrip().startswith("#")
            for line in info_path.read_text(
                encoding="utf-8",
                errors="surrogateescape",
            ).splitlines()
        ):
            settings.append(f"info.{info_name} {info_path}")
    file_mode = subprocess.run(
        ("git", "config", "--bool", "--get", "core.filemode"),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if file_mode.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect nested checkout file-mode setting: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": file_mode.stderr.strip()},
        )
    if file_mode.returncode == 0 and file_mode.stdout.strip() == "false":
        settings.append("core.filemode false")
    ignore_case = subprocess.run(
        ("git", "config", "--bool", "--get", "core.ignorecase"),
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if ignore_case.returncode not in (0, 1):
        raise PreparationFailure(
            f"cannot inspect nested checkout case-folding setting: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"stderr": ignore_case.stderr.strip()},
        )
    if ignore_case.returncode == 0 and ignore_case.stdout.strip() == "true":
        settings.append("core.ignorecase true")
    skip_worktree_paths, assume_unchanged_paths = _nonportable_index_flag_paths(path)
    if skip_worktree_paths:
        settings.append(f"skip-worktree entries={len(skip_worktree_paths)}")
    if assume_unchanged_paths:
        settings.append(f"assume-unchanged entries={len(assume_unchanged_paths)}")
    shared_index_path = git_text(path, "rev-parse", "--shared-index-path")
    if shared_index_path:
        settings.append(f"split-index {shared_index_path}")
    return tuple(settings)


def _nested_git_snapshot(path: Path) -> NestedGitSnapshot | None:
    if not _is_nested_git_checkout(path):
        return None
    registered_worktrees = _registered_worktree_paths(path)
    source_worktree = path.resolve()
    if len(registered_worktrees) != 1 or Path(registered_worktrees[0]).resolve() != source_worktree:
        raise PreparationFailure(
            f"nested checkout has additional linked worktrees: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"registered_worktrees": list(registered_worktrees)},
        )
    restrictive_git_admin_modes = _restrictive_git_admin_directory_modes(path)
    if restrictive_git_admin_modes:
        raise PreparationFailure(
            f"nested checkout has restrictive Git administration directories: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "restrictive_git_admin_directory_modes": list(
                    restrictive_git_admin_modes
                )
            },
        )
    restrictive_git_admin_files = _restrictive_git_admin_file_modes(path)
    if restrictive_git_admin_files:
        raise PreparationFailure(
            f"nested checkout has restrictive Git administration files: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "restrictive_git_admin_file_modes": list(
                    restrictive_git_admin_files
                )
            },
        )
    (
        git_admin_ownership,
        git_admin_symlinks,
        git_admin_xattrs,
        git_admin_security_label_issues,
        git_admin_security_label,
    ) = _git_admin_portability_issues(path)
    if git_admin_ownership:
        raise PreparationFailure(
            f"nested checkout has nonportable Git administration ownership: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"git_admin_ownership": list(git_admin_ownership)},
        )
    if git_admin_symlinks:
        raise PreparationFailure(
            f"nested checkout has symlinked Git administration state: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"git_admin_symlinks": list(git_admin_symlinks)},
        )
    if git_admin_xattrs:
        raise PreparationFailure(
            f"nested checkout has extended Git administration attributes: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"git_admin_xattrs": list(git_admin_xattrs)},
        )
    if git_admin_security_label_issues:
        raise PreparationFailure(
            f"nested checkout has inconsistent Git administration security labels: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "git_admin_security_label_issues": list(
                    git_admin_security_label_issues
                )
            },
        )
    git_admin_locks = _git_admin_lock_paths(path)
    if git_admin_locks:
        raise PreparationFailure(
            f"nested checkout contains active Git administration locks: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"git_admin_lock_paths": list(git_admin_locks)},
        )
    implicit_rule_sources = _implicit_rule_sources()
    if implicit_rule_sources:
        raise PreparationFailure(
            f"nested checkout is exposed to implicit Git rule sources: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"implicit_rule_sources": list(implicit_rule_sources)},
        )
    url_rewrite_settings = _effective_url_rewrite_settings(path)
    if url_rewrite_settings:
        raise PreparationFailure(
            f"nested checkout is exposed to URL rewrite settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "url_rewrite_settings": [list(row) for row in url_rewrite_settings]
            },
        )
    operation_state = _in_progress_operation_state(path)
    if operation_state:
        raise PreparationFailure(
            f"nested checkout contains an in-progress Git operation: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"operation_state": list(operation_state)},
        )
    rerere_cache_state = _rerere_cache_state(path)
    if rerere_cache_state:
        raise PreparationFailure(
            f"nested checkout contains unsupported rerere cache state: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"rerere_cache_state": list(rerere_cache_state)},
        )
    pseudo_ref_state = _unsupported_pseudo_ref_state(path)
    if pseudo_ref_state:
        raise PreparationFailure(
            f"nested checkout contains unsupported pseudo-ref state: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"pseudo_ref_state": list(pseudo_ref_state)},
        )
    fsmonitor_settings = _effective_fsmonitor_settings(path)
    if fsmonitor_settings:
        raise PreparationFailure(
            f"nested checkout has active fsmonitor settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"fsmonitor_settings": list(fsmonitor_settings)},
        )
    resolve_undo_entries = _resolve_undo_entries(path)
    if resolve_undo_entries:
        raise PreparationFailure(
            f"nested checkout index contains resolve-undo state: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"resolve_undo_entries": list(resolve_undo_entries)},
        )
    external_rule_settings = _effective_external_rule_settings(path)
    if external_rule_settings:
        raise PreparationFailure(
            f"nested checkout has external ignore or attribute rules: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"external_rule_settings": list(external_rule_settings)},
        )
    replacement_refs = _replacement_refs(path)
    if replacement_refs:
        raise PreparationFailure(
            f"nested checkout contains history-rewriting replacement refs: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"replacement_refs": list(replacement_refs)},
        )
    history_storage_overrides = _history_storage_overrides(path)
    if history_storage_overrides:
        raise PreparationFailure(
            f"nested checkout contains external history storage state: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"history_storage_overrides": list(history_storage_overrides)},
        )
    partial_clone_settings = _partial_clone_settings(path)
    if partial_clone_settings:
        raise PreparationFailure(
            f"nested checkout is a partial or promisor clone: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"partial_clone_settings": list(partial_clone_settings)},
        )
    populated_submodules = _populated_submodule_paths(path)
    if populated_submodules:
        raise PreparationFailure(
            f"nested checkout contains populated submodule worktrees: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"populated_submodules": list(populated_submodules)},
        )
    effective_submodule_transport = _effective_submodule_transport_settings(path)
    if effective_submodule_transport:
        raise PreparationFailure(
            f"nested checkout is exposed to effective submodule transport: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "effective_submodule_transport": [
                    list(row) for row in effective_submodule_transport
                ]
            },
        )
    conversion_settings = _nonportable_local_checkout_settings(path)
    if conversion_settings:
        raise PreparationFailure(
            f"nested checkout has nonportable worktree settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"conversion_settings": list(conversion_settings)},
        )
    symlinks = candidate_symlink_paths(path, include_ignored=True)
    if symlinks:
        raise PreparationFailure(
            f"nested checkout contains symlinks with unbound target bytes: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"symlinks": list(symlinks)},
        )
    hook_settings = _effective_hook_settings(path)
    if hook_settings:
        raise PreparationFailure(
            f"nested checkout has ambient hook or template settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"hook_settings": list(hook_settings)},
        )
    default_hooks = _default_hook_paths(path)
    if default_hooks:
        raise PreparationFailure(
            f"nested checkout has custom default-directory hooks: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"default_hooks": list(default_hooks)},
        )
    head = git_text(path, "rev-parse", "HEAD")
    submodule_transport_sources = _submodule_transport_sources(path, head)
    if submodule_transport_sources:
        raise PreparationFailure(
            f"nested checkout declares external submodule transport: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "submodule_transport_sources": list(submodule_transport_sources)
            },
        )
    paths = tracked_paths(path)
    candidate_untracked_paths = untracked_paths(path, include_ignored=True)
    candidate_directories = candidate_directory_paths(path, include_ignored=True)
    nonportable_worktree_ownership = _nonportable_worktree_ownership(
        path,
        (*paths, *candidate_untracked_paths),
        candidate_directories,
    )
    if nonportable_worktree_ownership:
        raise PreparationFailure(
            f"nested checkout has ownership isolation cannot preserve: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "nonportable_worktree_ownership": list(
                    nonportable_worktree_ownership
                )
            },
        )
    sparse_worktree_paths = _sparse_worktree_paths(
        path,
        (*paths, *candidate_untracked_paths),
    )
    if sparse_worktree_paths:
        raise PreparationFailure(
            f"nested checkout contains sparse file extents isolation cannot preserve: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"sparse_worktree_paths": list(sparse_worktree_paths)},
        )
    worktree_hardlink_groups = _worktree_hardlink_groups(
        path,
        (*paths, *candidate_untracked_paths),
    )
    filtered_paths = _active_filter_attribute_paths(
        path,
        (*paths, *candidate_untracked_paths),
    )
    if filtered_paths:
        raise PreparationFailure(
            f"nested checkout has active filter attributes: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"filtered_paths": list(filtered_paths)},
        )
    head_paths = tree_paths(path, head)
    paths_exposed_during_materialization = tuple(
        sorted({*head_paths, *paths, *candidate_untracked_paths})
    )
    head_filtered_paths = _active_filter_attribute_paths(
        path,
        paths_exposed_during_materialization,
        source=head,
    )
    if head_filtered_paths:
        raise PreparationFailure(
            f"nested checkout HEAD has active filter attributes: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"head_filtered_paths": list(head_filtered_paths)},
        )
    filter_attribute_sources = _filter_attribute_sources(
        path,
        (*paths, *candidate_untracked_paths),
        head,
    )
    if filter_attribute_sources:
        raise PreparationFailure(
            f"nested checkout declares Git filter attributes: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"filter_attribute_sources": list(filter_attribute_sources)},
        )
    candidate = capture_candidate_snapshot(path, include_ignored=True)
    if (
        candidate.untracked_paths != candidate_untracked_paths
        or candidate.directories != candidate_directories
    ):
        raise PreparationFailure(
            "nested checkout candidate changed during snapshot capture",
            failure_type="candidate_snapshot_changed",
            action_class="retry_same_candidate",
        )
    worktree_xattrs = _worktree_xattr_state(
        path,
        (*paths, *candidate_untracked_paths),
        candidate_directories,
    )
    worktree_mtimes = _worktree_mtime_state(
        path,
        (*paths, *candidate_untracked_paths),
        candidate_directories,
    )
    origin_head, git_refs = _git_ref_state(path)
    (
        ref_root_mode,
        ref_directories,
        loose_ref_files,
        packed_refs_mode,
        packed_refs_bytes,
    ) = _git_ref_storage_state(path)
    reflog_root_mode, reflog_directories, reflog_files = _reflog_state(path)
    index_version = _index_version(path)
    index_mode, index_bytes = _git_index_state(path)
    object_inventory_count, object_inventory_digest = _git_object_inventory(path)
    object_storage_state = _git_object_storage_state(path)
    local_config_mode, local_config_bytes = _git_local_config_state(path)
    local_config = _portable_local_config(path)
    remote_config = _remote_local_config(path)
    if _git_local_config_state(path) != (local_config_mode, local_config_bytes):
        raise PreparationFailure(
            "nested checkout local config changed during snapshot capture",
            failure_type="candidate_snapshot_changed",
            action_class="retry_same_candidate",
        )
    isolated_config_bytes = _neutralized_local_config_bytes(
        path,
        local_config_bytes,
        remote_config,
    )
    symbolic_head = _symbolic_head(path)
    shallow_boundaries = _shallow_boundaries(path)
    effective_checkout_settings = _effective_checkout_settings(path)
    effective_git_config = _effective_git_config(path)
    tracked_digest = tracked_worktree_digest(path, paths)
    # Capture the residual administration tree only after all Git reads used
    # to form the snapshot. Some Git versions may refresh administrative state
    # while answering those reads; the final bound state must be the one that
    # materialization and the unchanged check are required to reproduce.
    git_admin_directories, git_admin_files = _git_admin_state(path)
    return NestedGitSnapshot(
        candidate=candidate,
        root_mode=stat.S_IMODE(path.lstat().st_mode),
        git_admin_security_label=git_admin_security_label,
        git_admin_directories=git_admin_directories,
        git_admin_files=git_admin_files,
        symbolic_head=symbolic_head,
        origin_head=origin_head,
        git_refs=git_refs,
        ref_root_mode=ref_root_mode,
        ref_directories=ref_directories,
        loose_ref_files=loose_ref_files,
        packed_refs_mode=packed_refs_mode,
        packed_refs_bytes=packed_refs_bytes,
        shallow_boundaries=shallow_boundaries,
        local_config=local_config,
        remote_config=remote_config,
        local_config_mode=local_config_mode,
        local_config_bytes=local_config_bytes,
        isolated_config_bytes=isolated_config_bytes,
        reflog_root_mode=reflog_root_mode,
        reflog_directories=reflog_directories,
        reflog_files=reflog_files,
        index_version=index_version,
        index_mode=index_mode,
        index_bytes=index_bytes,
        object_inventory_count=object_inventory_count,
        object_inventory_digest=object_inventory_digest,
        object_storage_state=object_storage_state,
        worktree_hardlink_groups=worktree_hardlink_groups,
        worktree_mtimes=worktree_mtimes,
        worktree_xattrs=worktree_xattrs,
        tracked_paths=paths,
        tracked_worktree_digest=tracked_digest,
        effective_checkout_settings=effective_checkout_settings,
        effective_git_config=effective_git_config,
    )


def tracked_paths(repo_root: Path) -> tuple[str, ...]:
    decoded = git_bytes(repo_root, "ls-files", "-z").decode(
        "utf-8", errors="surrogateescape"
    )
    paths = tuple(item for item in decoded.split("\0") if item)
    for item in paths:
        checked_relative_path(item)
    return paths


def intent_to_add_paths(
    repo_root: Path,
    *,
    env: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    common = ("diff", "--cached", "--name-only", "-z", "--diff-filter=A")
    visible = set(
        item
        for item in git_bytes(
            repo_root,
            *common,
            "--ita-visible-in-index",
            env=env,
        ).decode(
            "utf-8", errors="surrogateescape"
        ).split("\0")
        if item
    )
    ordinary = set(
        item
        for item in git_bytes(
            repo_root,
            *common,
            "--ita-invisible-in-index",
            env=env,
        ).decode(
            "utf-8", errors="surrogateescape"
        ).split("\0")
        if item
    )
    paths = tuple(sorted(visible - ordinary))
    for raw in paths:
        relative = checked_relative_path(raw)
        if not (repo_root / relative).is_file():
            raise PreparationFailure(
                f"intent-to-add path is not a regular candidate file: {raw}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
    return paths


def tree_paths(repo_root: Path, treeish: str) -> tuple[str, ...]:
    decoded = git_bytes(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        "-z",
        treeish,
    ).decode("utf-8", errors="surrogateescape")
    paths = tuple(item for item in decoded.split("\0") if item)
    for item in paths:
        checked_relative_path(item)
    return paths


def candidate_symlink_paths(
    repo_root: Path,
    *,
    include_ignored: bool = False,
) -> tuple[str, ...]:
    paths = (
        *tracked_paths(repo_root),
        *untracked_paths(repo_root, include_ignored=include_ignored),
    )
    return tuple(
        raw
        for raw in paths
        if (repo_root / checked_relative_path(raw)).is_symlink()
    )


def tracked_worktree_digest(repo_root: Path, paths: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for raw in paths:
        relative = checked_relative_path(raw)
        source = repo_root / relative
        digest.update(raw.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        try:
            metadata = source.lstat()
        except FileNotFoundError:
            digest.update(b"missing\0")
            continue
        digest.update(str(stat.S_IFMT(metadata.st_mode)).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(stat.S_IMODE(metadata.st_mode)).encode("ascii"))
        digest.update(b"\0")
        if stat.S_ISLNK(metadata.st_mode):
            digest.update(os.readlink(source).encode("utf-8", errors="surrogateescape"))
        elif stat.S_ISREG(metadata.st_mode):
            digest.update(source.read_bytes())
        elif stat.S_ISDIR(metadata.st_mode):
            digest.update(b"directory")
        else:
            raise PreparationFailure(
                f"tracked nested checkout path has unsupported type: {raw}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def require_nested_git_snapshot_unchanged(
    repo_root: Path,
    expected: NestedGitSnapshot,
) -> None:
    observed = _nested_git_snapshot(repo_root)
    if observed != expected:
        changed_components = (
            [
                field.name
                for field in fields(expected)
                if observed is None
                or getattr(observed, field.name) != getattr(expected, field.name)
            ]
        )
        expected_git_admin = {row[0]: row[1:] for row in expected.git_admin_files}
        observed_git_admin = (
            {}
            if observed is None
            else {row[0]: row[1:] for row in observed.git_admin_files}
        )
        changed_git_admin_paths = sorted(
            path
            for path in expected_git_admin.keys() | observed_git_admin.keys()
            if expected_git_admin.get(path) != observed_git_admin.get(path)
        )
        raise PreparationFailure(
            "nested checkout candidate changed during isolated preparation: "
            + ", ".join(changed_components)
            + (
                " (Git administration: " + ", ".join(changed_git_admin_paths) + ")"
                if changed_git_admin_paths
                else ""
            ),
            failure_type="candidate_snapshot_changed",
            action_class="retry_same_candidate",
            details={
                "expected_identity": expected.identity(),
                "actual_identity": observed.identity() if observed is not None else None,
                "changed_components": changed_components,
                "changed_git_admin_paths": changed_git_admin_paths,
            },
        )


def _update_untracked_path_digest(
    digest: Any,
    repo_root: Path,
    rel: Path,
) -> None:
    source = repo_root / rel
    metadata = source.lstat()
    raw = rel.as_posix()
    digest.update(raw.encode("utf-8", errors="surrogateescape"))
    digest.update(b"\0")
    digest.update(str(stat.S_IFMT(metadata.st_mode)).encode("ascii"))
    digest.update(b"\0")
    digest.update(str(stat.S_IMODE(metadata.st_mode)).encode("ascii"))
    digest.update(b"\0")
    if stat.S_ISLNK(metadata.st_mode):
        digest.update(os.readlink(source).encode("utf-8", errors="surrogateescape"))
    elif stat.S_ISREG(metadata.st_mode):
        digest.update(source.read_bytes())
    elif stat.S_ISDIR(metadata.st_mode):
        nested = _nested_git_snapshot(source)
        if nested is not None:
            digest.update(b"nested-git-candidate\0")
            digest.update(nested.identity().encode("ascii"))
        else:
            for child in sorted(source.iterdir(), key=lambda item: os.fsencode(item.name)):
                _update_untracked_path_digest(digest, repo_root, rel / child.name)
    else:
        raise PreparationFailure(
            f"untracked candidate path has unsupported type: {raw}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    digest.update(b"\0")


def capture_candidate_snapshot(
    repo_root: Path,
    *,
    include_ignored: bool = False,
) -> CandidateSnapshot:
    # Reject routing before the first Git subprocess. Otherwise an exported
    # GIT_DIR/GIT_WORK_TREE pair can make the temporary validation lane inspect
    # or mutate the source repository rather than the isolated candidate.
    _require_isolated_git_environment(repo_root, subject="candidate checkout")
    if git_text(repo_root, "rev-parse", "--show-toplevel") != repo_root.resolve().as_posix():
        raise PreparationFailure(
            "prepare-landing must run at the Git top level",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    fsmonitor_settings = _effective_fsmonitor_settings(repo_root)
    if fsmonitor_settings:
        raise PreparationFailure(
            f"candidate checkout has active fsmonitor settings: {repo_root}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"fsmonitor_settings": list(fsmonitor_settings)},
        )
    if git_bytes(repo_root, "ls-files", "-u", "-z"):
        raise PreparationFailure(
            "candidate contains unmerged Git index entries",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    skip_worktree_paths, assume_unchanged_paths = _nonportable_index_flag_paths(
        repo_root
    )
    if skip_worktree_paths or assume_unchanged_paths:
        raise PreparationFailure(
            "candidate index contains worktree-hiding path flags",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "skip_worktree_paths": list(skip_worktree_paths),
                "assume_unchanged_paths": list(assume_unchanged_paths),
            },
        )
    shared_index_path = git_text(repo_root, "rev-parse", "--shared-index-path")
    if shared_index_path:
        raise PreparationFailure(
            "candidate index uses external split-index storage",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"shared_index_path": shared_index_path},
        )
    outer_tracked_paths = tracked_paths(repo_root)
    nested_tracked_roots = _nested_checkout_roots_with_tracked_content(
        repo_root,
        outer_tracked_paths,
    )
    if nested_tracked_roots:
        raise PreparationFailure(
            "candidate contains a nested Git checkout overlapping outer tracked source",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"nested_tracked_roots": list(nested_tracked_roots)},
        )
    paths = untracked_paths(repo_root, include_ignored=include_ignored)
    if not include_ignored:
        paths = tuple(
            sorted({*paths, *_ignored_nested_checkout_paths(repo_root)})
        )
    directories = candidate_directory_paths(
        repo_root,
        include_ignored=include_ignored,
    )
    # Resolve nested candidate identity before outer topology checks so a
    # nested violation retains its precise path and typed failure details.
    untracked_digest = untracked_content_digest(repo_root, paths)
    directory_digest = candidate_directory_digest(repo_root, directories)
    worktree_paths = (*outer_tracked_paths, *paths)
    nonportable_worktree_ownership = _nonportable_worktree_ownership(
        repo_root,
        worktree_paths,
        directories,
    )
    if nonportable_worktree_ownership:
        raise PreparationFailure(
            f"candidate contains worktree ownership isolation cannot preserve: {repo_root}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "nonportable_worktree_ownership": list(
                    nonportable_worktree_ownership
                )
            },
        )
    sparse_worktree_paths = _sparse_worktree_paths(repo_root, worktree_paths)
    if sparse_worktree_paths:
        raise PreparationFailure(
            f"candidate contains sparse file extents isolation cannot preserve: {repo_root}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"sparse_worktree_paths": list(sparse_worktree_paths)},
        )
    worktree_hardlink_groups = _worktree_hardlink_groups(
        repo_root,
        worktree_paths,
    )
    tracked_file_modes = _regular_worktree_mode_state(
        repo_root,
        outer_tracked_paths,
    )
    directory_mtimes = _worktree_mtime_state(
        repo_root,
        worktree_paths,
        directories,
    )
    worktree_xattrs = _worktree_xattr_state(
        repo_root,
        worktree_paths,
        directories,
    )
    head = git_text(repo_root, "rev-parse", "HEAD")
    index_mode, index_bytes = _git_index_state(repo_root)
    with tempfile.TemporaryDirectory(
        prefix=".aoa-kag-candidate-index-",
        dir=repo_root.parent,
    ) as temp_dir:
        isolated_index = Path(temp_dir) / "index"
        isolated_index.write_bytes(index_bytes)
        isolated_index.chmod(index_mode)
        isolated_index_env = os.environ.copy()
        isolated_index_env["GIT_INDEX_FILE"] = isolated_index.as_posix()
        index_tree = git_bytes(
            repo_root,
            "write-tree",
            env=isolated_index_env,
        ).decode("utf-8", errors="strict").strip()
        cached_patch_bytes = candidate_cached_patch(
            repo_root,
            env=isolated_index_env,
        )
        unstaged_patch_bytes = candidate_unstaged_patch(
            repo_root,
            env=isolated_index_env,
        )
        candidate_patch_bytes = candidate_patch(
            repo_root,
            env=isolated_index_env,
        )
        candidate_intent_to_add_paths = intent_to_add_paths(
            repo_root,
            env=isolated_index_env,
        )
        index_version = _index_version(repo_root, env=isolated_index_env)
    if _git_index_state(repo_root) != (index_mode, index_bytes):
        raise PreparationFailure(
            "candidate index changed during snapshot capture",
            failure_type="candidate_snapshot_changed",
            action_class="retry_same_candidate",
        )
    return CandidateSnapshot(
        head=head,
        root_mode=stat.S_IMODE(repo_root.lstat().st_mode),
        index_tree=index_tree,
        index_version=index_version,
        index_mode=index_mode,
        index_bytes=index_bytes,
        cached_patch_bytes=cached_patch_bytes,
        unstaged_patch_bytes=unstaged_patch_bytes,
        candidate_patch_bytes=candidate_patch_bytes,
        cached_diff_digest=sha256_bytes(cached_patch_bytes),
        worktree_diff_digest=sha256_bytes(candidate_patch_bytes),
        untracked_digest=untracked_digest,
        untracked_paths=paths,
        directory_digest=directory_digest,
        directories=directories,
        worktree_hardlink_groups=worktree_hardlink_groups,
        tracked_file_modes=tracked_file_modes,
        directory_mtimes=directory_mtimes,
        worktree_xattrs=worktree_xattrs,
        intent_to_add_paths=candidate_intent_to_add_paths,
    )


def require_candidate_unchanged(
    repo_root: Path,
    expected: CandidateSnapshot,
) -> None:
    observed = capture_candidate_snapshot(repo_root)
    if observed != expected:
        raise PreparationFailure(
            "source candidate changed while isolated preparation was running",
            failure_type="candidate_snapshot_changed",
            action_class="retry_same_candidate",
            details={
                "expected_identity": expected.identity(),
                "actual_identity": observed.identity(),
            },
        )


def candidate_patch(
    repo_root: Path,
    *,
    env: Mapping[str, str] | None = None,
) -> bytes:
    return git_bytes(
        repo_root,
        "diff",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        "HEAD",
        env=env,
    )


def candidate_cached_patch(
    repo_root: Path,
    *,
    env: Mapping[str, str] | None = None,
) -> bytes:
    return git_bytes(
        repo_root,
        "diff",
        "--cached",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        "HEAD",
        env=env,
    )


def candidate_unstaged_patch(
    repo_root: Path,
    *,
    env: Mapping[str, str] | None = None,
) -> bytes:
    return git_bytes(
        repo_root,
        "diff",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        env=env,
    )


def copy_untracked_candidate(
    source_root: Path,
    destination_root: Path,
    paths: Sequence[str],
) -> None:
    for raw in paths:
        rel = checked_relative_path(raw)
        source = source_root / rel
        destination = destination_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        metadata = source.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            destination.symlink_to(os.readlink(source))
        elif stat.S_ISREG(metadata.st_mode):
            shutil.copy2(source, destination, follow_symlinks=False)
        elif stat.S_ISDIR(metadata.st_mode):
            nested = _nested_git_snapshot(source)
            if nested is None:
                shutil.copytree(source, destination, symlinks=True)
            else:
                # Rebuild a nested validation checkout from its captured Git
                # candidate. Every worktree byte exposed to validation,
                # including ignored validator state, is represented by the
                # nested CandidateSnapshot identity.
                with tempfile.TemporaryDirectory(
                    prefix=".aoa-kag-empty-git-template-",
                    dir=destination.parent,
                ) as empty_template:
                    subprocess.run(
                        (
                            "git",
                            "-c",
                            "core.hooksPath=/dev/null",
                            "clone",
                            "--quiet",
                            "--no-checkout",
                            "--no-hardlinks",
                            f"--template={empty_template}",
                            "--",
                            source.resolve().as_posix(),
                            destination.as_posix(),
                        ),
                        check=True,
                        capture_output=True,
                    )
                _require_git_object_inventory_match(
                    destination,
                    nested.object_inventory_count,
                    nested.object_inventory_digest,
                )
                _restore_git_object_storage_modes(
                    destination,
                    nested.object_storage_state,
                )
                _require_git_object_storage_match(
                    destination,
                    nested.object_storage_state,
                )
                _restore_local_config_state(destination, nested)
                _restore_git_ref_state(destination, nested)
                if _shallow_boundaries(destination) != nested.shallow_boundaries:
                    raise PreparationFailure(
                        "nested checkout shallow boundary differs after isolation",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                    )
                if _effective_fsmonitor_settings(destination):
                    raise PreparationFailure(
                        "nested checkout fsmonitor remains active after isolation",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                    )
                _require_effective_checkout_settings_match(source, destination)
                _require_effective_git_config_match(destination, nested)
                checkout_args = ["-c", "core.hooksPath=/dev/null", "checkout"]
                if nested.symbolic_head is None:
                    checkout_args.append("--detach")
                else:
                    checkout_args.extend(("-B", nested.symbolic_head.removeprefix("refs/heads/")))
                checkout_args.extend(("-q", nested.candidate.head))
                git_bytes(destination, *checkout_args)
                _require_effective_checkout_settings_match(source, destination)
                _require_effective_git_config_match(destination, nested)
                directory_modes = materialize_nested_candidate(
                    source,
                    destination,
                    nested.candidate,
                    restore_directory_modes=False,
                )
                _restore_worktree_hardlinks(
                    destination,
                    nested.worktree_hardlink_groups,
                )
                observed_hardlinks = _worktree_hardlink_groups(
                    destination,
                    (*nested.tracked_paths, *nested.candidate.untracked_paths),
                )
                if observed_hardlinks != nested.worktree_hardlink_groups:
                    raise PreparationFailure(
                        "nested checkout hardlink topology differs after isolation",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                    )
                git_bytes(
                    destination,
                    "update-index",
                    "--index-version",
                    str(nested.index_version),
                )
                if _index_version(destination) != nested.index_version:
                    raise PreparationFailure(
                        "nested checkout index version differs after isolation",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                    )
                _restore_reflog_state(destination, nested)
                writable_modes = _make_worktree_owner_writable(
                    destination,
                    (*nested.tracked_paths, *nested.candidate.untracked_paths),
                    nested.candidate.directories,
                )
                _restore_worktree_xattrs(
                    destination,
                    (*nested.tracked_paths, *nested.candidate.untracked_paths),
                    nested.candidate.directories,
                    nested.worktree_xattrs,
                )
                restore_candidate_directory_modes(writable_modes)
                restore_tracked_worktree_modes(source, destination, nested.tracked_paths)
                restore_candidate_directory_modes(directory_modes)
                destination.chmod(nested.root_mode)
                observed_xattrs = _worktree_xattr_state(
                    destination,
                    (*nested.tracked_paths, *nested.candidate.untracked_paths),
                    nested.candidate.directories,
                )
                if observed_xattrs != nested.worktree_xattrs:
                    raise PreparationFailure(
                        "nested checkout extended attributes differ after isolation",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                    )
                observed_digest = tracked_worktree_digest(destination, nested.tracked_paths)
                if observed_digest != nested.tracked_worktree_digest:
                    raise PreparationFailure(
                        "nested checkout tracked worktree differs after isolation",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                        details={
                            "expected_digest": nested.tracked_worktree_digest,
                            "actual_digest": observed_digest,
                        },
                    )
                _require_git_admin_portability_match(
                    destination,
                    nested.git_admin_security_label,
                )
                _require_local_config_state_match(destination, nested)
                require_nested_git_snapshot_unchanged(source, nested)
                _require_effective_checkout_settings_match(source, destination)
                _require_effective_git_config_match(destination, nested)
                _restore_worktree_mtimes(destination, nested.worktree_mtimes)
                observed_mtimes = _worktree_mtime_state(
                    destination,
                    (*nested.tracked_paths, *nested.candidate.untracked_paths),
                    nested.candidate.directories,
                )
                if observed_mtimes != nested.worktree_mtimes:
                    raise PreparationFailure(
                        "nested checkout modification times differ after isolation",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                    )
                _restore_git_index_state(
                    destination,
                    nested.index_mode,
                    nested.index_bytes,
                )
                if _index_version(destination) != nested.index_version:
                    raise PreparationFailure(
                        "nested checkout index version differs after exact restoration",
                        failure_type="candidate_snapshot_invalid",
                        action_class="code_fix",
                    )
                _restore_git_ref_storage(destination, nested)
                _restore_git_admin_state(
                    destination,
                    nested.git_admin_directories,
                    nested.git_admin_files,
                )
                _require_git_admin_portability_match(
                    destination,
                    nested.git_admin_security_label,
                )
                _require_local_config_state_match(destination, nested)
                _require_effective_checkout_settings_match(source, destination)
                _require_effective_git_config_match(destination, nested)
        else:  # capture_candidate_snapshot already rejects this; retain fail-closed symmetry.
            raise PreparationFailure(
                f"untracked candidate path changed type during copy: {raw}",
                failure_type="candidate_snapshot_changed",
                action_class="retry_same_candidate",
            )


def create_candidate_directories(
    source_root: Path,
    destination_root: Path,
    paths: Sequence[str],
    *,
    restore_modes: bool = True,
) -> tuple[tuple[Path, int], ...]:
    captured_modes: list[tuple[Path, int]] = []
    for raw in paths:
        relative = checked_relative_path(raw)
        source = source_root / relative
        metadata = source.lstat()
        if not stat.S_ISDIR(metadata.st_mode):
            raise PreparationFailure(
                f"candidate directory changed type during copy: {raw}",
                failure_type="candidate_snapshot_changed",
                action_class="retry_same_candidate",
            )
        destination = destination_root / relative
        destination.mkdir(parents=True, exist_ok=True)
        captured_modes.append((destination, stat.S_IMODE(metadata.st_mode)))
    captured = tuple(captured_modes)
    if restore_modes:
        restore_candidate_directory_modes(captured)
    return captured


def restore_candidate_directory_modes(
    captured_modes: Sequence[tuple[Path, int]],
) -> None:
    for destination, mode in reversed(captured_modes):
        destination.chmod(mode)


def materialize_nested_candidate(
    source_root: Path,
    destination_root: Path,
    snapshot: CandidateSnapshot,
    *,
    restore_directory_modes: bool = True,
) -> tuple[tuple[Path, int], ...]:
    cached_patch = snapshot.cached_patch_bytes
    if cached_patch:
        git_bytes(
            destination_root,
            "apply",
            "--index",
            "--binary",
            "--whitespace=nowarn",
            "-",
            input_bytes=cached_patch,
        )
    unstaged_patch = snapshot.unstaged_patch_bytes
    if unstaged_patch:
        git_bytes(
            destination_root,
            "apply",
            "--binary",
            "--whitespace=nowarn",
            "-",
            input_bytes=unstaged_patch,
        )
    for raw in snapshot.intent_to_add_paths:
        relative = checked_relative_path(raw)
        source = source_root / relative
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=False)
        git_bytes(
            destination_root,
            "--literal-pathspecs",
            "add",
            "--intent-to-add",
            "--",
            relative.as_posix(),
        )
    copy_untracked_candidate(source_root, destination_root, snapshot.untracked_paths)
    directory_modes = create_candidate_directories(
        source_root,
        destination_root,
        snapshot.directories,
        restore_modes=restore_directory_modes,
    )
    observed_tree = git_text(destination_root, "write-tree")
    if observed_tree != snapshot.index_tree:
        raise PreparationFailure(
            "nested checkout index differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "expected_index_tree": snapshot.index_tree,
                "actual_index_tree": observed_tree,
            },
        )
    return directory_modes


def restore_tracked_worktree_modes(
    source_root: Path,
    destination_root: Path,
    paths: Sequence[str],
) -> None:
    for raw in paths:
        relative = checked_relative_path(raw)
        source = source_root / relative
        destination = destination_root / relative
        if not source.exists() and not destination.exists():
            continue
        source_metadata = source.lstat()
        destination_metadata = destination.lstat()
        if stat.S_IFMT(source_metadata.st_mode) != stat.S_IFMT(destination_metadata.st_mode):
            raise PreparationFailure(
                f"tracked nested checkout path changed type during isolation: {raw}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        destination.chmod(stat.S_IMODE(source_metadata.st_mode))


def restore_regular_worktree_modes(
    destination_root: Path,
    expected_modes: Sequence[tuple[str, int]],
) -> None:
    for raw, mode in expected_modes:
        destination = destination_root / checked_relative_path(raw)
        try:
            metadata = destination.lstat()
        except FileNotFoundError as exc:
            raise PreparationFailure(
                f"tracked candidate file disappeared during isolation: {raw}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            ) from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise PreparationFailure(
                f"tracked candidate file changed type during isolation: {raw}",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        destination.chmod(mode)


def materialize_candidate(
    source_root: Path,
    temporary_root: Path,
    snapshot: CandidateSnapshot,
) -> str:
    patch = snapshot.candidate_patch_bytes
    if patch:
        git_bytes(
            temporary_root,
            "apply",
            "--index",
            "--binary",
            "--whitespace=nowarn",
            "-",
            input_bytes=patch,
        )
    copy_untracked_candidate(source_root, temporary_root, snapshot.untracked_paths)
    directory_modes = create_candidate_directories(
        source_root,
        temporary_root,
        snapshot.directories,
        restore_modes=False,
    )
    _restore_worktree_hardlinks(
        temporary_root,
        snapshot.worktree_hardlink_groups,
    )
    restore_candidate_directory_modes(directory_modes)
    git_bytes(temporary_root, "add", "-A", "--", ".")
    for raw in snapshot.untracked_paths:
        rel = checked_relative_path(raw)
        if _is_nested_git_checkout(source_root / rel):
            # Validation checkouts are part of stability identity and must remain
            # available to commands, but they are not owner source.  Remove only
            # the temporary gitlink that `git add -A` creates: path-form reset
            # would restore HEAD entries when a staged deletion was replaced by
            # a nested checkout at the same path.
            git_bytes(
                temporary_root,
                "--literal-pathspecs",
                "update-index",
                "--force-remove",
                "--",
                rel.as_posix(),
            )
    observed_hardlinks = _worktree_hardlink_groups(
        temporary_root,
        (*tracked_paths(temporary_root), *snapshot.untracked_paths),
    )
    if observed_hardlinks != snapshot.worktree_hardlink_groups:
        raise PreparationFailure(
            "candidate hardlink topology differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    worktree_paths = (*tracked_paths(temporary_root), *snapshot.untracked_paths)
    writable_modes = _make_worktree_owner_writable(
        temporary_root,
        worktree_paths,
        snapshot.directories,
    )
    _restore_worktree_xattrs(
        temporary_root,
        worktree_paths,
        snapshot.directories,
        snapshot.worktree_xattrs,
    )
    restore_candidate_directory_modes(writable_modes)
    restore_regular_worktree_modes(
        temporary_root,
        snapshot.tracked_file_modes,
    )
    restore_candidate_directory_modes(directory_modes)
    temporary_root.chmod(snapshot.root_mode)
    observed_modes = _regular_worktree_mode_state(
        temporary_root,
        tuple(raw for raw, _mode in snapshot.tracked_file_modes),
    )
    if observed_modes != snapshot.tracked_file_modes:
        raise PreparationFailure(
            "candidate tracked-file modes differ after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    observed_root_mode = stat.S_IMODE(temporary_root.lstat().st_mode)
    if observed_root_mode != snapshot.root_mode:
        raise PreparationFailure(
            "candidate root mode differs after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    observed_xattrs = _worktree_xattr_state(
        temporary_root,
        worktree_paths,
        snapshot.directories,
    )
    if observed_xattrs != snapshot.worktree_xattrs:
        raise PreparationFailure(
            "candidate extended attributes differ after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    _restore_worktree_mtimes(temporary_root, snapshot.directory_mtimes)
    observed_mtimes = _worktree_mtime_state(
        temporary_root,
        worktree_paths,
        snapshot.directories,
    )
    if observed_mtimes != snapshot.directory_mtimes:
        raise PreparationFailure(
            "candidate modification times differ after isolation",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
        )
    _restore_git_index_state(
        temporary_root,
        snapshot.index_mode,
        snapshot.index_bytes,
    )
    with tempfile.TemporaryDirectory(
        prefix=".aoa-kag-verify-index-",
        dir=temporary_root.parent,
    ) as temp_dir:
        verification_index = Path(temp_dir) / "index"
        verification_index.write_bytes(snapshot.index_bytes)
        verification_index.chmod(snapshot.index_mode)
        verification_env = os.environ.copy()
        verification_env["GIT_INDEX_FILE"] = verification_index.as_posix()
        if _index_version(temporary_root, env=verification_env) != snapshot.index_version:
            raise PreparationFailure(
                "candidate index version differs after isolation",
                failure_type="candidate_snapshot_invalid",
                action_class="code_fix",
            )
        observed_tree = git_bytes(
            temporary_root,
            "write-tree",
            env=verification_env,
        ).decode("utf-8", errors="strict").strip()
    if observed_tree != snapshot.index_tree:
        raise PreparationFailure(
            "candidate index tree differs after exact restoration",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={
                "expected_index_tree": snapshot.index_tree,
                "actual_index_tree": observed_tree,
            },
        )
    return observed_tree


def resolve_ref(repo_root: Path, value: str, label: str) -> str:
    try:
        return git_text(repo_root, "rev-parse", "--verify", f"{value}^{{commit}}")
    except subprocess.CalledProcessError as exc:
        raise PreparationFailure(
            f"{label} is not an available commit: {value}",
            failure_type="history_identity_unavailable",
            action_class="fetch_or_choose_base",
            details={"ref": value, "label": label},
        ) from exc


def default_history_ref(repo_root: Path) -> str:
    candidates: list[str] = []
    symbolic = subprocess.run(
        ("git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"),
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if symbolic.returncode == 0 and symbolic.stdout.strip():
        candidates.append(symbolic.stdout.strip())
    candidates.extend(("refs/remotes/origin/main", "refs/remotes/origin/master"))
    for candidate in candidates:
        if subprocess.run(
            ("git", "rev-parse", "--verify", f"{candidate}^{{commit}}"),
            cwd=repo_root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0:
            try:
                return git_text(repo_root, "merge-base", "HEAD", candidate)
            except subprocess.CalledProcessError:
                continue
    raise PreparationFailure(
        "cannot resolve the local origin default-branch merge base without network access",
        failure_type="history_identity_unavailable",
        action_class="fetch_or_choose_base",
    )


def resolve_refs(
    repo_root: Path,
    *,
    history_ref: str | None,
    event_history_ref: str | None,
    budget_base_ref: str | None,
) -> ResolvedRefs:
    history = resolve_ref(
        repo_root,
        history_ref or default_history_ref(repo_root),
        "history-ref",
    )
    event_history = resolve_ref(
        repo_root,
        event_history_ref or history,
        "event-history-ref",
    )
    budget_base = resolve_ref(
        repo_root,
        budget_base_ref or history,
        "budget-base-ref",
    )
    return ResolvedRefs(history, event_history, budget_base)


def load_provider_entries(repo_root: Path) -> tuple[dict[str, Any], ...]:
    path = repo_root / "manifests" / "provider_registry.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PreparationFailure(
            f"cannot load provider registry: {path}",
            failure_type="provider_identity_invalid",
            action_class="code_fix",
        ) from exc
    providers = payload.get("providers") if isinstance(payload, dict) else None
    if not isinstance(providers, list) or not providers:
        raise PreparationFailure(
            "provider registry does not contain a non-empty providers list",
            failure_type="provider_identity_invalid",
            action_class="code_fix",
        )
    if any(not isinstance(item, dict) for item in providers):
        raise PreparationFailure(
            "provider registry contains a non-object provider row",
            failure_type="provider_identity_invalid",
            action_class="code_fix",
        )
    entries = tuple(providers)
    owners = tuple(str(item.get("repo") or "") for item in entries)
    if any(not owner for owner in owners) or len(owners) != len(set(owners)):
        raise PreparationFailure(
            "provider registry contains a missing or duplicate owner identity",
            failure_type="provider_identity_invalid",
            action_class="code_fix",
        )
    return entries


def provider_root(entry: Mapping[str, object], temporary_root: Path) -> Path:
    if entry.get("root_kind") == "self":
        return temporary_root
    env_name = str(entry.get("env") or "")
    if env_name and os.environ.get(env_name):
        return Path(os.environ[env_name]).expanduser().resolve()
    raw_root = Path(str(entry.get("root") or ""))
    if raw_root.is_absolute():
        return raw_root.resolve()
    if entry.get("root_kind") == "runtime_source":
        home_src_root = Path(
            os.environ.get("AOA_HOME_SRC_ROOT", "/home/dionysus/src")
        )
        return (home_src_root / raw_root).resolve()
    return (Path("/srv/AbyssOS") / raw_root).resolve()


def verify_provider_identities(temporary_root: Path) -> tuple[dict[str, str], ...]:
    identities: list[dict[str, str]] = []
    for entry in load_provider_entries(temporary_root):
        repo = str(entry.get("repo") or "")
        root = provider_root(entry, temporary_root)
        if not repo or not root.exists():
            raise PreparationFailure(
                f"provider root is missing: {repo or '<unnamed>'} {root}",
                failure_type="provider_identity_unavailable",
                action_class="materialize_provider_checkouts",
                details={"owner": repo, "root": root.as_posix()},
            )
        observed = git_text(root, "rev-parse", "HEAD")
        observed_tree = git_text(root, "rev-parse", "HEAD^{tree}")
        expected = str(entry.get("pinned_ref") or "")
        if entry.get("checkout_mode") == "pinned" and observed != expected:
            raise PreparationFailure(
                f"provider pin mismatch for {repo}: expected {expected}, observed {observed}",
                failure_type="provider_identity_mismatch",
                action_class="materialize_provider_checkouts",
                details={"owner": repo, "expected": expected, "actual": observed},
            )
        if entry.get("checkout_mode") == "pinned":
            dirty = git_text(
                root,
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--ignored",
            )
            shallow = git_text(root, "rev-parse", "--is-shallow-repository")
            if dirty or shallow != "false":
                raise PreparationFailure(
                    f"provider checkout is not clean complete-history input: {repo}",
                    failure_type="provider_identity_mismatch",
                    action_class="materialize_provider_checkouts",
                    details={
                        "owner": repo,
                        "dirty": bool(dirty),
                        "shallow": shallow,
                    },
                )
        identities.append(
            {
                "owner": repo,
                "head": observed,
                "head_tree": observed_tree,
                "posture": str(entry.get("checkout_mode") or ""),
            }
        )
    return tuple(identities)


def run_command(
    command: Sequence[str],
    *,
    repo_root: Path,
    failure_type: str = "semantic_validation_failure",
    action_class: str = "code_fix",
    allow_failure: bool = False,
) -> CommandResult:
    display = tuple(command)
    print(f"[prepare-landing] {' '.join(display)}", file=sys.stderr, flush=True)
    started = time.perf_counter()
    completed = subprocess.run(
        resolve_command(display),
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    duration_ms = round((time.perf_counter() - started) * 1000)
    if completed.stdout:
        print(completed.stdout, file=sys.stderr, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    result = CommandResult(
        display,
        completed.returncode,
        completed.stdout,
        completed.stderr,
        duration_ms,
    )
    if completed.returncode and not allow_failure:
        output_tail = (completed.stdout + completed.stderr)[-4000:]
        raise PreparationFailure(
            f"command failed with exit code {completed.returncode}: {' '.join(display)}",
            failure_type=failure_type,
            action_class=action_class,
            command=display,
            details={
                "return_code": completed.returncode,
                "duration_ms": duration_ms,
                "output_tail": output_tail,
            },
        )
    return result


def stage_paths(repo_root: Path, paths: Sequence[str]) -> None:
    git_bytes(repo_root, "add", "-A", "--", *paths)


def coverage_generation_module():
    try:
        from scripts import generate_repo_local_kag_coverage as coverage_generation
    except ImportError:  # pragma: no cover - direct script execution
        import generate_repo_local_kag_coverage as coverage_generation  # type: ignore
    return coverage_generation


def load_external_coverage_seed(repo_root: Path, seed_ref: str) -> dict[str, Any]:
    relative = "generated/repo_local_kag_coverage.json"
    try:
        content = git_bytes(repo_root, "show", f"{seed_ref}:{relative}")
        payload = json.loads(content.decode("utf-8", errors="strict"))
    except (subprocess.CalledProcessError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"preparation coverage seed is unavailable or invalid: {seed_ref}:{relative}"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("preparation coverage seed is not a JSON object")
    return payload


def require_seed_compatible_runtime(repo_root: Path, seed_ref: str) -> None:
    coverage_generation = coverage_generation_module()

    ancestry = subprocess.run(
        ("git", "merge-base", "--is-ancestor", seed_ref, "HEAD"),
        cwd=repo_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestry.returncode == 1:
        raise PreparationSeedInapplicable(
            "preparation coverage seed is not an ancestor of the candidate"
        )
    if ancestry.returncode != 0:
        raise RuntimeError("cannot establish preparation coverage seed ancestry")

    paths = tuple(
        relative.as_posix()
        for relative in coverage_generation._coverage_runtime_input_paths()
    )
    completed = subprocess.run(
        ("git", "diff", "--cached", "--quiet", seed_ref, "--", *paths),
        cwd=repo_root,
        check=False,
    )
    if completed.returncode == 1:
        raise PreparationSeedInapplicable(
            "preparation-only external coverage reuse is inapplicable because "
            "canonical coverage runtime inputs differ from the seed ref; run the "
            "full owner build"
        )
    if completed.returncode != 0:
        raise RuntimeError(
            "cannot compare canonical coverage runtime inputs with the seed ref"
        )


def expected_external_portable_family(
    owner: str,
    owner_root: Path,
) -> dict[str, Any]:
    coverage_generation = coverage_generation_module()

    manifest_path = owner_root / coverage_generation.MANIFEST_RELATIVE_PATH
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"preparation coverage cannot read the external manifest for {owner}"
        ) from exc
    if not isinstance(manifest, dict):
        raise RuntimeError(f"external manifest is not an object for {owner}")
    repo = manifest.get("repo")
    family = manifest.get("family_identity")
    summary = manifest.get("summary")
    budgets = manifest.get("budgets")
    if (
        not isinstance(repo, dict)
        or repo.get("name") != owner
        or not isinstance(family, dict)
        or not isinstance(summary, dict)
        or not isinstance(budgets, dict)
    ):
        raise RuntimeError(f"external manifest shape or owner is invalid for {owner}")
    tracked_bytes = summary.get("tracked_bytes")
    tracked_bytes_max = budgets.get("tracked_bytes_max")
    shards = summary.get("shards")
    content_digest = family.get("content_digest")
    if (
        not isinstance(tracked_bytes, int)
        or tracked_bytes < 0
        or not isinstance(tracked_bytes_max, int)
        or tracked_bytes_max < 0
        or not isinstance(shards, int)
        or shards < 0
        or not isinstance(content_digest, str)
        or len(content_digest) != 64
        or any(char not in "0123456789abcdef" for char in content_digest)
    ):
        raise RuntimeError(f"external manifest family identity is invalid for {owner}")
    receipted = tracked_bytes > tracked_bytes_max
    return {
        "manifest_ref": coverage_generation.MANIFEST_RELATIVE_PATH.as_posix(),
        "content_digest": content_digest,
        "digest_state": "published",
        "tracked_bytes": tracked_bytes,
        "tracked_bytes_max": tracked_bytes_max,
        "shards": shards,
        "budget_state": "receipted" if receipted else "passed",
        "receipt_ref": (
            coverage_generation.receipt_path_for(manifest).as_posix()
            if receipted
            else ""
        ),
    }


def build_preparation_coverage(
    repo_root: Path,
    *,
    external_seed_ref: str,
    verify_external_manifests: bool = True,
) -> dict[str, Any]:
    """Rebuild only self while preserving exact, pinned external seed rows.

    This is deliberately not a canonical coverage proof.  It is a bounded SCC
    preparation accelerator whose result must still pass the unchanged full
    owner lane.
    """

    require_seed_compatible_runtime(repo_root, external_seed_ref)
    seed = load_external_coverage_seed(repo_root, external_seed_ref)
    return build_preparation_coverage_from_payload(
        repo_root,
        seed,
        verify_external_manifests=verify_external_manifests,
    )


def build_preparation_coverage_from_payload(
    repo_root: Path,
    seed: dict[str, Any],
    *,
    verify_external_manifests: bool,
) -> dict[str, Any]:
    coverage_generation = coverage_generation_module()

    coverage_generation._validate_coverage_payload_schema(seed)
    if seed.get("root") != coverage_generation.DEFAULT_OS_ROOT.as_posix():
        raise RuntimeError("preparation coverage seed has a non-canonical OS root")
    seed_owners = seed.get("owners")
    if not isinstance(seed_owners, list):
        raise RuntimeError("preparation coverage seed owner list is invalid")
    expected_order = tuple(coverage_generation.provider_repo_order())
    actual_order = tuple(
        row.get("repo") if isinstance(row, dict) else None for row in seed_owners
    )
    if actual_order != expected_order or SELF_OWNER not in expected_order:
        raise RuntimeError(
            "preparation coverage seed owner membership or order differs from the registry"
        )

    provider_entries = coverage_generation.provider_by_repo()
    configured = dict(coverage_generation.configured_owner_roots())
    if tuple(configured) != expected_order:
        raise RuntimeError("configured owner roots differ from the provider registry")

    owners: list[dict[str, Any]] = []
    coverage_generation._portable_bundle_from_disk.cache_clear()
    for row in seed_owners:
        assert isinstance(row, dict)
        owner = str(row["repo"])
        owner_root = configured[owner]
        display_root = coverage_generation.canonical_owner_root(
            coverage_generation.DEFAULT_OS_ROOT,
            owner,
        )
        if owner == SELF_OWNER:
            preparation_family = coverage_generation.load_portable_family(
                repo_root,
                require_budget_receipt=False,
            )
            rebuilt, _timing = coverage_generation._build_owner_coverage(
                owner,
                repo_root,
                display_root=display_root,
                portable_bundle=preparation_family,
            )
            owners.append(rebuilt)
            continue

        if row.get("root") != display_root.as_posix():
            raise RuntimeError(f"preparation coverage external root drift for {owner}")
        if row.get("index_status") != "passed":
            raise RuntimeError(
                f"preparation coverage seed is not all-owner green for {owner}"
            )
        if row.get("family_storage") != "v3-portable-shards":
            raise RuntimeError(
                f"preparation coverage seed is not portable-v3 for {owner}"
            )
        if verify_external_manifests:
            expected_ref = str(provider_entries.get(owner, {}).get("pinned_ref", ""))
            observed_ref = coverage_generation._git_head(owner, owner_root)
            if not expected_ref or observed_ref != expected_ref:
                raise RuntimeError(
                    f"preparation coverage external pin mismatch for {owner}: "
                    f"expected {expected_ref or '<missing>'}, got {observed_ref}"
                )
            if row.get("portable_family") != expected_external_portable_family(
                owner,
                owner_root,
            ):
                raise RuntimeError(
                    f"preparation coverage external manifest identity drift for {owner}"
                )
        owners.append(copy.deepcopy(row))

    payload = coverage_generation._assemble_coverage(
        coverage_generation.DEFAULT_OS_ROOT,
        owners,
    )
    coverage_generation._validate_coverage_payload_schema(payload)
    return payload


def build_full_preparation_coverage(repo_root: Path) -> dict[str, Any]:
    """Rebuild every owner when the pinned coverage runtime cannot be reused.

    The self portable family is admitted structurally here because its final
    digest-bound budget receipt is produced only after the generated SCC is
    stable. All ordinary portable-family loads still require that receipt.
    """
    coverage_generation = coverage_generation_module()
    expected_order = tuple(coverage_generation.provider_repo_order())
    configured = coverage_generation.configured_owner_roots()
    if tuple(owner for owner, _root in configured) != expected_order:
        raise RuntimeError("configured owner roots differ from the provider registry")
    provider_entries = coverage_generation.provider_by_repo()
    owners: list[dict[str, Any]] = []
    coverage_generation._portable_bundle_from_disk.cache_clear()
    for owner, owner_root in configured:
        if owner == SELF_OWNER:
            if owner_root.resolve() != repo_root.resolve():
                raise RuntimeError("full preparation coverage self root drifted")
            portable_bundle = coverage_generation.load_portable_family(
                repo_root,
                require_budget_receipt=False,
            )
        else:
            expected_ref = str(provider_entries.get(owner, {}).get("pinned_ref", ""))
            observed_ref = coverage_generation._git_head(owner, owner_root)
            if not expected_ref or observed_ref != expected_ref:
                raise RuntimeError(
                    f"full preparation coverage external pin mismatch for {owner}: "
                    f"expected {expected_ref or '<missing>'}, got {observed_ref}"
                )
            portable_bundle = None
        rebuilt, _timing = coverage_generation._build_owner_coverage(
            owner,
            owner_root,
            display_root=coverage_generation.canonical_owner_root(
                coverage_generation.DEFAULT_OS_ROOT,
                owner,
            ),
            portable_bundle=portable_bundle,
        )
        owners.append(rebuilt)
    payload = coverage_generation._assemble_coverage(
        coverage_generation.DEFAULT_OS_ROOT,
        owners,
    )
    coverage_generation._validate_coverage_payload_schema(payload)
    return payload


def write_preparation_coverage_cache(
    repo_root: Path,
    path: Path,
    payload: dict[str, Any],
) -> None:
    if path.exists() or path.is_symlink():
        raise RuntimeError("preparation coverage cache path already exists")
    coverage_generation = coverage_generation_module()
    envelope = {
        "schema_version": PREPARATION_COVERAGE_CACHE_SCHEMA,
        "runtime_inputs_digest": coverage_generation._coverage_runtime_inputs_digest(),
        "provider_identity": list(verify_provider_identities(repo_root)),
        "coverage": payload,
    }
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n")


def load_preparation_coverage_cache(
    repo_root: Path,
    path: Path,
) -> dict[str, Any]:
    coverage_generation = coverage_generation_module()
    metadata = path.lstat()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or metadata.st_gid != os.getegid()
        or stat.S_IMODE(metadata.st_mode) != 0o600
    ):
        raise RuntimeError("preparation coverage cache metadata is nonportable")
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("preparation coverage cache is unreadable") from exc
    if not isinstance(envelope, dict):
        raise RuntimeError("preparation coverage cache is not an object")
    if envelope.get("schema_version") != PREPARATION_COVERAGE_CACHE_SCHEMA:
        raise RuntimeError("preparation coverage cache schema drifted")
    if (
        envelope.get("runtime_inputs_digest")
        != coverage_generation._coverage_runtime_inputs_digest()
    ):
        raise RuntimeError("preparation coverage cache runtime identity drifted")
    cached_provider_identity = envelope.get("provider_identity")
    if not isinstance(cached_provider_identity, list):
        raise RuntimeError("preparation coverage cache provider identity is invalid")
    observed_provider_identity = list(verify_provider_identities(repo_root))
    if observed_provider_identity != cached_provider_identity:
        raise RuntimeError("preparation coverage cache provider identity drifted")
    payload = envelope.get("coverage")
    if not isinstance(payload, dict):
        raise RuntimeError("preparation coverage cache payload is invalid")
    return build_preparation_coverage_from_payload(
        repo_root,
        payload,
        verify_external_manifests=True,
    )


def prepare_self_coverage(
    repo_root: Path,
    *,
    external_seed_ref: str,
    check: bool,
    verify_external_manifests: bool,
    full_coverage_cache: Path | None = None,
) -> int:
    coverage_generation = coverage_generation_module()

    try:
        payload = build_preparation_coverage(
            repo_root,
            external_seed_ref=external_seed_ref,
            verify_external_manifests=verify_external_manifests,
        )
        strategy = (
            "verified-external-seed"
            if verify_external_manifests
            else "seed-only-sentinel"
        ) + "+self-rebuild"
    except PreparationSeedInapplicable as exc:
        if full_coverage_cache is not None and full_coverage_cache.is_file():
            payload = load_preparation_coverage_cache(
                repo_root,
                full_coverage_cache,
            )
            strategy = "verified-full-owner-cache+self-rebuild"
        else:
            print(
                "[prepare-landing] pinned coverage reuse inapplicable; "
                f"rebuilding every owner: {exc}",
                file=sys.stderr,
            )
            payload = build_full_preparation_coverage(repo_root)
            if full_coverage_cache is not None:
                write_preparation_coverage_cache(repo_root, full_coverage_cache, payload)
            strategy = "full-owner-rebuild+self-budget-deferred"
    print(
        f"[prepare-landing] coverage strategy={strategy} "
        "proof=preparation-only",
        file=sys.stderr,
    )
    if check:
        return 0 if coverage_generation.check_outputs(
            coverage_generation.DEFAULT_OUTPUT,
            coverage_generation.DEFAULT_MIN_OUTPUT,
            payload,
        ) else 1
    coverage_generation.write_outputs(
        coverage_generation.DEFAULT_OUTPUT,
        coverage_generation.DEFAULT_MIN_OUTPUT,
        payload,
    )
    return 0


def landing_sentinel(
    repo_root: Path,
    *,
    external_seed_ref: str,
    coverage_only: bool = False,
    generated_only: bool = False,
) -> tuple[int, dict[str, object]]:
    """Check likely SCC drift before the expensive OS-wide proof starts."""

    started = time.perf_counter()
    base_receipt: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "mode": "sentinel",
        "seed_ref": external_seed_ref,
        "partial_result_is_green": False,
        "proof_boundary": {
            "claim": "early-self-scc-drift-sentinel",
            "external_rows": "seed-only",
            "fallback": "unchanged-full-owner-proof",
            "does_not_replace": [
                "source-fast",
                "full-owner-proof",
                "release-audit",
                "landing-verdict",
            ],
        },
    }
    try:
        if not generated_only:
            coverage_generation = coverage_generation_module()
            payload = build_preparation_coverage(
                repo_root,
                external_seed_ref=external_seed_ref,
                verify_external_manifests=False,
            )
            if not coverage_generation.check_outputs(
                coverage_generation.DEFAULT_OUTPUT,
                coverage_generation.DEFAULT_MIN_OUTPUT,
                payload,
            ):
                base_receipt.update(
                    {
                        "verdict": "drift",
                        "failure_type": "self_coverage_drift",
                        "action_class": "run_prepare_landing_apply",
                        "fallback_required": False,
                    }
                )
                return 1, base_receipt
        if coverage_only:
            base_receipt.update(
                {
                    "verdict": "passed",
                    "action_class": "continue_checkout_and_full_owner_proof",
                    "fallback_required": True,
                    "checked_components": ["self_coverage"],
                }
            )
            return 0, base_receipt
        generated = run_command(
            generated_command(check=True),
            repo_root=repo_root,
            allow_failure=True,
        )
        if generated.returncode:
            output_tail = (generated.stdout + generated.stderr)[-4000:]
            if "[generate-kag] drift" not in output_tail:
                base_receipt.update(
                    {
                        "verdict": "inapplicable",
                        "failure_type": "generated_sentinel_prerequisite_unavailable",
                        "action_class": "continue_full_owner_proof",
                        "fallback_required": True,
                        "command": list(generated.command),
                        "details": {
                            "return_code": generated.returncode,
                            "duration_ms": generated.duration_ms,
                            "output_tail": output_tail,
                        },
                    }
                )
                return 0, base_receipt
            base_receipt.update(
                {
                    "verdict": "drift",
                    "failure_type": "generated_projection_drift",
                    "action_class": "run_prepare_landing_apply",
                    "fallback_required": False,
                    "command": list(generated.command),
                    "details": {
                        "return_code": generated.returncode,
                        "duration_ms": generated.duration_ms,
                        "output_tail": output_tail,
                    },
                }
            )
            return 1, base_receipt
        base_receipt.update(
            {
                "verdict": "passed",
                "action_class": "continue_full_owner_proof",
                "fallback_required": True,
                "checked_components": (
                    ["generated_projection"]
                    if generated_only
                    else ["self_coverage", "generated_projection"]
                ),
            }
        )
        return 0, base_receipt
    except PreparationSeedInapplicable as exc:
        base_receipt.update(
            {
                "verdict": "inapplicable",
                "failure_type": "preparation_seed_inapplicable",
                "action_class": "continue_full_owner_proof",
                "fallback_required": True,
                "message": str(exc),
            }
        )
        return 0, base_receipt
    except Exception as exc:
        base_receipt.update(
            {
                "verdict": "failed",
                "failure_type": "sentinel_infrastructure_failure",
                "action_class": "code_fix",
                "fallback_required": False,
                "message": str(exc),
            }
        )
        return 1, base_receipt
    finally:
        base_receipt["duration_ms"] = round(
            (time.perf_counter() - started) * 1000
        )


def coverage_command(
    refs: ResolvedRefs,
    *,
    check: bool = False,
    full_coverage_cache: Path | None = None,
) -> tuple[str, ...]:
    command = [
        "python",
        "scripts/prepare_landing.py",
        "--prepare-self-coverage",
        "--external-seed-ref",
        refs.history_ref,
    ]
    if full_coverage_cache is not None:
        command.extend(("--full-coverage-cache", full_coverage_cache.as_posix()))
    if check:
        command.append("--coverage-check")
    return tuple(command)


def generated_command(*, check: bool = False) -> tuple[str, ...]:
    command = ["python", "scripts/generate_kag.py"]
    if check:
        command.append("--check")
    return tuple(command)


def portable_family_command(
    refs: ResolvedRefs,
    *,
    check: bool = False,
    enforce_budget: bool = False,
    write_budget_receipt: bool = False,
    budget_reason: str | None = None,
) -> tuple[str, ...]:
    command = [
        "python",
        "scripts/generate_repo_local_kag_index.py",
        "--repo-root",
        ".",
        "--output",
        "kag/indexes/source_surface_index.json",
        "--portable-family",
        "--history-ref",
        refs.history_ref,
        "--event-history-ref",
        refs.event_history_ref,
    ]
    if enforce_budget or write_budget_receipt:
        command.extend(("--budget-base-ref", refs.budget_base_ref))
    if write_budget_receipt:
        command.append("--write-budget-receipt")
        command.extend(("--budget-reason", budget_reason or ""))
    if check:
        command.append("--check")
    return tuple(command)


def converge_scc(
    repo_root: Path,
    refs: ResolvedRefs,
    *,
    max_iterations: int,
    full_coverage_cache: Path | None = None,
) -> tuple[int, str]:
    for iteration in range(1, max_iterations + 1):
        before_tree = git_text(repo_root, "write-tree")
        run_command(
            coverage_command(refs, full_coverage_cache=full_coverage_cache),
            repo_root=repo_root,
        )
        stage_paths(repo_root, COVERAGE_PATHS)
        run_command(generated_command(), repo_root=repo_root)
        stage_paths(repo_root, GENERATED_PATHS)
        run_command(portable_family_command(refs), repo_root=repo_root)
        stage_paths(repo_root, PORTABLE_FAMILY_PATHS)
        after_tree = git_text(repo_root, "write-tree")
        print(
            f"[prepare-landing] SCC iteration={iteration} "
            f"before={before_tree} after={after_tree}",
            file=sys.stderr,
        )
        if after_tree == before_tree:
            return iteration, after_tree
    raise PreparationFailure(
        f"KAG SCC did not converge within {max_iterations} iterations",
        failure_type="fixed_point_non_convergence",
        action_class="code_fix",
        details={"max_iterations": max_iterations},
    )


def _current_budget_receipt_path(repo_root: Path) -> Path:
    manifest_path = repo_root / PORTABLE_FAMILY_PATHS[0]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        digest = manifest["family_identity"]["content_digest"]
    except (FileNotFoundError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise PreparationFailure(
            "cannot resolve the current portable-family budget receipt path",
            failure_type="budget_receipt_generation_failure",
            action_class="code_fix",
        ) from exc
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
    ):
        raise PreparationFailure(
            "current portable-family digest is invalid for a budget receipt",
            failure_type="budget_receipt_generation_failure",
            action_class="code_fix",
        )
    return Path(BUDGET_RECEIPT_PATHS[0]) / f"{digest}.json"


def prune_obsolete_budget_receipts(
    repo_root: Path,
    refs: ResolvedRefs,
) -> None:
    keep = _current_budget_receipt_path(repo_root)
    root = Path(BUDGET_RECEIPT_PATHS[0])
    base_rows = git_bytes(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        "-z",
        refs.budget_base_ref,
        "--",
        root.as_posix(),
    )
    base_paths = {
        Path(raw.decode("utf-8", errors="surrogateescape"))
        for raw in base_rows.split(b"\0")
        if raw
    }
    receipt_root = repo_root / root
    if not receipt_root.is_dir():
        return
    for candidate in sorted(receipt_root.glob("*.json")):
        relative = candidate.relative_to(repo_root)
        if relative == keep or relative in base_paths:
            continue
        candidate.unlink()


def ensure_budget_receipt(
    repo_root: Path,
    refs: ResolvedRefs,
    *,
    budget_reason: str | None,
) -> str:
    check = run_command(
        portable_family_command(refs, check=True, enforce_budget=True),
        repo_root=repo_root,
        allow_failure=True,
    )
    if check.returncode == 0:
        output = check.stdout + check.stderr
        return "accepted" if "receipt=accepted" in output else "not_required"
    output = check.stdout + check.stderr
    receipt_failure = (
        "no matching receipt exists" in output
        or "receipt field" in output
        or "receipt scope" in output
        or "receipt approval" in output
    )
    if not receipt_failure:
        raise PreparationFailure(
            "final portable-family budget check failed for a non-receipt reason",
            failure_type="semantic_validation_failure",
            action_class="code_fix",
            command=check.command,
            details={"return_code": check.returncode, "duration_ms": check.duration_ms},
        )
    if not budget_reason or not budget_reason.strip():
        raise PreparationFailure(
            "final family requires an owner-reasoned digest-bound budget receipt",
            failure_type="budget_receipt_authority_required",
            action_class="provide_budget_reason",
            command=check.command,
            details={"budget_base_ref": refs.budget_base_ref},
        )
    run_command(
        portable_family_command(
            refs,
            enforce_budget=True,
            write_budget_receipt=True,
            budget_reason=budget_reason,
        ),
        repo_root=repo_root,
        failure_type="budget_receipt_generation_failure",
        action_class="code_fix",
    )
    prune_obsolete_budget_receipts(repo_root, refs)
    stage_paths(repo_root, (*PORTABLE_FAMILY_PATHS, *BUDGET_RECEIPT_PATHS))
    run_command(
        portable_family_command(refs, check=True, enforce_budget=True),
        repo_root=repo_root,
        failure_type="budget_receipt_mismatch",
        action_class="code_fix",
    )
    return "created"


def converge_budgeted_scc(
    repo_root: Path,
    refs: ResolvedRefs,
    *,
    max_iterations: int,
    budget_reason: str | None,
    full_coverage_cache: Path | None = None,
) -> tuple[int, str, str]:
    iterations, fixed_point_tree = converge_scc(
        repo_root,
        refs,
        max_iterations=max_iterations,
        full_coverage_cache=full_coverage_cache,
    )
    budget_receipt = "not_required"
    for receipt_round in range(1, max_iterations + 1):
        before_receipt = git_text(repo_root, "write-tree")
        observed = ensure_budget_receipt(
            repo_root,
            refs,
            budget_reason=budget_reason,
        )
        if observed == "created" or budget_receipt != "created":
            budget_receipt = observed
        after_receipt = git_text(repo_root, "write-tree")
        if after_receipt == before_receipt:
            return iterations, after_receipt, budget_receipt
        print(
            f"[prepare-landing] budget stabilization round={receipt_round} "
            f"before={before_receipt} after={after_receipt}",
            file=sys.stderr,
        )
        added_iterations, fixed_point_tree = converge_scc(
            repo_root,
            refs,
            max_iterations=max_iterations,
            full_coverage_cache=full_coverage_cache,
        )
        iterations += added_iterations
    raise PreparationFailure(
        "KAG budget receipt did not stabilize with the generated SCC",
        failure_type="fixed_point_non_convergence",
        action_class="code_fix",
        details={"max_receipt_rounds": max_iterations},
    )


def final_confirmation(
    repo_root: Path,
    refs: ResolvedRefs,
    *,
    full_coverage_cache: Path | None = None,
) -> None:
    run_command(
        coverage_command(
            refs,
            check=True,
            full_coverage_cache=full_coverage_cache,
        ),
        repo_root=repo_root,
    )
    run_command(
        portable_family_command(refs, check=True, enforce_budget=True),
        repo_root=repo_root,
    )
    run_command(generated_command(check=True), repo_root=repo_root)
    run_command(
        ("python", "scripts/validate_kag.py", "--scope", "local"),
        repo_root=repo_root,
    )
    if git_bytes(repo_root, "diff", "--binary", "--no-ext-diff", "--no-textconv"):
        raise PreparationFailure(
            "final confirmation left unstaged worktree drift in the isolated candidate",
            failure_type="generated_cleanliness_failure",
            action_class="code_fix",
        )


def tree_patch(repo_root: Path, before_tree: str, after_tree: str) -> bytes:
    return git_bytes(
        repo_root,
        "diff",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        before_tree,
        after_tree,
    )


def changed_tree_paths(
    repo_root: Path,
    before_tree: str,
    after_tree: str,
) -> tuple[str, ...]:
    raw = git_bytes(
        repo_root,
        "diff",
        "--no-renames",
        "--name-only",
        "-z",
        before_tree,
        after_tree,
    )
    decoded = raw.decode("utf-8", errors="surrogateescape")
    return tuple(item for item in decoded.split("\0") if item)


def path_is_within(raw: str, allowed: str) -> bool:
    return raw == allowed or raw.startswith(f"{allowed}/")


def require_preparation_output_scope(paths: Sequence[str]) -> None:
    unexpected = sorted(
        raw
        for raw in paths
        if not any(path_is_within(raw, allowed) for allowed in PREPARATION_OUTPUT_PATHS)
    )
    if unexpected:
        raise PreparationFailure(
            "isolated preparation changed paths outside its generated-output authority",
            failure_type="preparation_output_scope_violation",
            action_class="code_fix",
            details={"unexpected_paths": unexpected},
        )


def apply_generated_patch(
    source_root: Path,
    patch: bytes,
    *,
    expected_snapshot: CandidateSnapshot,
) -> None:
    require_candidate_unchanged(source_root, expected_snapshot)
    cached_before = git_bytes(
        source_root,
        "diff",
        "--cached",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
    )
    git_bytes(
        source_root,
        "apply",
        "--check",
        "--binary",
        "--whitespace=nowarn",
        "-",
        input_bytes=patch,
    )
    git_bytes(
        source_root,
        "apply",
        "--binary",
        "--whitespace=nowarn",
        "-",
        input_bytes=patch,
    )
    cached_after = git_bytes(
        source_root,
        "diff",
        "--cached",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
    )
    if cached_after != cached_before:
        raise PreparationFailure(
            "prepare-landing changed the caller Git index",
            failure_type="caller_index_pollution",
            action_class="rollback_generated_patch",
        )


def receipt_base(
    *,
    mode: str,
    snapshot: CandidateSnapshot | None,
    refs: ResolvedRefs | None,
    started: float,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "verdict": "failed",
        "partial_result_is_green": False,
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
        payload["refs"] = {
            "history_ref": refs.history_ref,
            "event_history_ref": refs.event_history_ref,
            "budget_base_ref": refs.budget_base_ref,
        }
    return payload


def prepare_landing(
    source_root: Path,
    *,
    mode: str,
    max_iterations: int,
    history_ref: str | None,
    event_history_ref: str | None,
    budget_base_ref: str | None,
    budget_reason: str | None,
    temp_root: Path | None,
) -> tuple[int, dict[str, object]]:
    started = time.perf_counter()
    snapshot: CandidateSnapshot | None = None
    refs: ResolvedRefs | None = None
    temporary_parent: Path | None = None
    temporary_worktree: Path | None = None
    try:
        snapshot = capture_candidate_snapshot(source_root)
        refs = resolve_refs(
            source_root,
            history_ref=history_ref,
            event_history_ref=event_history_ref,
            budget_base_ref=budget_base_ref,
        )
        if temp_root is not None:
            temp_root.mkdir(parents=True, exist_ok=True)
        temporary_parent = Path(
            tempfile.mkdtemp(
                prefix="aoa-kag-prepare-landing-",
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
        initial_tree = materialize_candidate(
            source_root,
            temporary_worktree,
            snapshot,
        )
        require_candidate_unchanged(source_root, snapshot)
        providers = verify_provider_identities(temporary_worktree)
        full_coverage_cache = temporary_parent / "full-owner-coverage-cache.json"
        iterations, fixed_point_tree, budget_receipt = converge_budgeted_scc(
            temporary_worktree,
            refs,
            max_iterations=max_iterations,
            budget_reason=budget_reason,
            full_coverage_cache=full_coverage_cache,
        )
        final_confirmation(
            temporary_worktree,
            refs,
            full_coverage_cache=full_coverage_cache,
        )
        final_providers = verify_provider_identities(temporary_worktree)
        if final_providers != providers:
            raise PreparationFailure(
                "provider identity changed during landing preparation",
                failure_type="provider_identity_mismatch",
                action_class="materialize_provider_checkouts",
                details={
                    "before": list(providers),
                    "after": list(final_providers),
                },
            )
        require_candidate_unchanged(source_root, snapshot)
        changed_paths = changed_tree_paths(
            temporary_worktree,
            initial_tree,
            fixed_point_tree,
        )
        require_preparation_output_scope(changed_paths)
        patch = tree_patch(temporary_worktree, initial_tree, fixed_point_tree)
        if mode == "apply" and patch:
            apply_generated_patch(
                source_root,
                patch,
                expected_snapshot=snapshot,
            )
        receipt = receipt_base(
            mode=mode,
            snapshot=snapshot,
            refs=refs,
            started=started,
        )
        receipt.update(
            {
                "verdict": "prepared" if mode == "apply" else "clean",
                "action_class": "none" if not patch else (
                    "generated_patch_applied" if mode == "apply" else "run_prepare_landing_apply"
                ),
                "fixed_point": {
                    "iterations": iterations,
                    "initial_tree": initial_tree,
                    "final_tree": fixed_point_tree,
                    "patch_digest": sha256_bytes(patch),
                    "patch_bytes": len(patch),
                    "drift_detected": bool(patch),
                    "changed_paths": list(changed_paths),
                },
                "budget_receipt": budget_receipt,
                "provider_identity": {
                    "verified_count": len(providers),
                    "owners": list(providers),
                },
                "proof_boundary": {
                    "claim": "isolated-local-preparation-and-final-parity",
                    "does_not_replace": [
                        "source-fast",
                        "full-owner-proof",
                        "release-audit",
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
    except PreparationFailure as exc:
        receipt = receipt_base(
            mode=mode,
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
        description="Converge the KAG landing SCC in an isolated staged worktree."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Simulate preparation without changing the caller worktree; fail when drift exists.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Apply only the converged generated patch to the caller worktree without staging it.",
    )
    mode.add_argument(
        "--prepare-self-coverage",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    mode.add_argument(
        "--sentinel",
        action="store_true",
        help="Run the seed-only early SCC drift sentinel; full proof remains required.",
    )
    parser.add_argument("--external-seed-ref", help=argparse.SUPPRESS)
    parser.add_argument("--coverage-check", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--full-coverage-cache",
        type=Path,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--seed-only-external",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--generated-only",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--history-ref")
    parser.add_argument("--event-history-ref")
    parser.add_argument("--budget-base-ref")
    parser.add_argument(
        "--budget-reason",
        help="Explicit repository-owner reason used only if the final digest exceeds its budget.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
    )
    parser.add_argument(
        "--temp-root",
        type=Path,
        help="Optional parent for the isolated temporary worktree.",
    )
    parser.add_argument(
        "--receipt-output",
        type=Path,
        help="Also write the final machine-readable receipt to this path.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.prepare_self_coverage:
        if not args.external_seed_ref:
            raise SystemExit("--prepare-self-coverage requires --external-seed-ref")
        try:
            return prepare_self_coverage(
                REPO_ROOT,
                external_seed_ref=args.external_seed_ref,
                check=args.coverage_check,
                verify_external_manifests=not args.seed_only_external,
                full_coverage_cache=args.full_coverage_cache,
            )
        except PreparationSeedInapplicable as exc:
            print(f"[prepare-landing] preparation coverage inapplicable: {exc}", file=sys.stderr)
            return 2
        except RuntimeError as exc:
            print(f"[prepare-landing] preparation coverage rejected: {exc}", file=sys.stderr)
            return 1
    if args.sentinel:
        if args.coverage_only and args.generated_only:
            raise SystemExit("--coverage-only and --generated-only are mutually exclusive")
        seed_ref = args.external_seed_ref or resolve_ref(
            REPO_ROOT,
            default_history_ref(REPO_ROOT),
            "external-seed-ref",
        )
        code, receipt = landing_sentinel(
            REPO_ROOT,
            external_seed_ref=seed_ref,
            coverage_only=args.coverage_only,
            generated_only=args.generated_only,
        )
        receipt["duration_ms"] = int(receipt.get("duration_ms", 0))
        encoded = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
        if args.receipt_output is not None:
            args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.receipt_output.with_name(
                f".{args.receipt_output.name}.{os.getpid()}.tmp"
            )
            temporary.write_text(encoded + "\n", encoding="utf-8")
            os.replace(temporary, args.receipt_output)
        print(encoded)
        return code
    if args.max_iterations < 1:
        raise SystemExit("--max-iterations must be positive")
    code, receipt = prepare_landing(
        REPO_ROOT,
        mode="apply" if args.apply else "check",
        max_iterations=args.max_iterations,
        history_ref=args.history_ref,
        event_history_ref=args.event_history_ref,
        budget_base_ref=args.budget_base_ref,
        budget_reason=args.budget_reason,
        temp_root=args.temp_root,
    )
    encoded_receipt = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    if args.receipt_output is not None:
        args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.receipt_output.with_name(
            f".{args.receipt_output.name}.{os.getpid()}.tmp"
        )
        temporary.write_text(encoded_receipt + "\n", encoding="utf-8")
        os.replace(temporary, args.receipt_output)
    print(encoded_receipt)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
