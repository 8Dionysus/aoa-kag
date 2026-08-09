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
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoa-kag-prepare-landing-receipt-v1"
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


@dataclass(frozen=True)
class CandidateSnapshot:
    head: str
    index_tree: str
    cached_diff_digest: str
    worktree_diff_digest: str
    untracked_digest: str
    untracked_paths: tuple[str, ...]
    directory_digest: str
    directories: tuple[str, ...]

    def identity(self) -> str:
        payload = {
            "head": self.head,
            "index_tree": self.index_tree,
            "cached_diff_digest": self.cached_diff_digest,
            "worktree_diff_digest": self.worktree_diff_digest,
            "untracked_digest": self.untracked_digest,
            "untracked_paths": list(self.untracked_paths),
            "directory_digest": self.directory_digest,
            "directories": list(self.directories),
        }
        return sha256_bytes(canonical_json(payload))


@dataclass(frozen=True)
class NestedGitSnapshot:
    candidate: CandidateSnapshot
    tracked_paths: tuple[str, ...]
    tracked_worktree_digest: str
    effective_checkout_settings: tuple[str, ...]

    def identity(self) -> str:
        payload = {
            "candidate_identity": self.candidate.identity(),
            "tracked_paths": list(self.tracked_paths),
            "tracked_worktree_digest": self.tracked_worktree_digest,
            "effective_checkout_settings": list(self.effective_checkout_settings),
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
) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        input=input_bytes,
        check=check,
        capture_output=True,
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


def untracked_paths(repo_root: Path) -> tuple[str, ...]:
    raw = git_bytes(
        repo_root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
    )
    decoded = raw.decode("utf-8", errors="surrogateescape")
    paths = tuple(item for item in decoded.split("\0") if item)
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


def candidate_directory_paths(repo_root: Path) -> tuple[str, ...]:
    """Capture every non-ignored directory exposed to candidate validation."""
    ignored_roots = _ignored_directory_roots(repo_root)
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

    ignored = _ignored_directory_paths(repo_root, discovered)
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


def _is_nested_git_checkout(path: Path) -> bool:
    try:
        if not stat.S_ISDIR(path.lstat().st_mode):
            return False
    except FileNotFoundError:
        return False
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
        for parent in relative.parents:
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


def _effective_fsmonitor_settings(path: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ("git", "config", "--null", "--get-all", "core.fsmonitor"),
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
    index_entries = tuple(
        entry.decode("utf-8", errors="surrogateescape")
        for entry in git_bytes(path, "ls-files", "-v", "-z").split(b"\0")
        if entry
    )
    skip_worktree_entries = tuple(entry for entry in index_entries if entry.startswith(("S ", "s ")))
    if skip_worktree_entries:
        settings.append(f"skip-worktree entries={len(skip_worktree_entries)}")
    assume_unchanged_entries = tuple(
        entry for entry in index_entries if entry[0].islower()
    )
    if assume_unchanged_entries:
        settings.append(f"assume-unchanged entries={len(assume_unchanged_entries)}")
    return tuple(settings)


def _nested_git_snapshot(path: Path) -> NestedGitSnapshot | None:
    if not _is_nested_git_checkout(path):
        return None
    fsmonitor_settings = _effective_fsmonitor_settings(path)
    if fsmonitor_settings:
        raise PreparationFailure(
            f"nested checkout has active fsmonitor settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"fsmonitor_settings": list(fsmonitor_settings)},
        )
    populated_submodules = _populated_submodule_paths(path)
    if populated_submodules:
        raise PreparationFailure(
            f"nested checkout contains populated submodule worktrees: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"populated_submodules": list(populated_submodules)},
        )
    conversion_settings = _nonportable_local_checkout_settings(path)
    if conversion_settings:
        raise PreparationFailure(
            f"nested checkout has nonportable worktree settings: {path}",
            failure_type="candidate_snapshot_invalid",
            action_class="code_fix",
            details={"conversion_settings": list(conversion_settings)},
        )
    symlinks = candidate_symlink_paths(path)
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
    head = git_text(path, "rev-parse", "HEAD")
    paths = tracked_paths(path)
    candidate_untracked_paths = untracked_paths(path)
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
    candidate = capture_candidate_snapshot(path)
    return NestedGitSnapshot(
        candidate=candidate,
        tracked_paths=paths,
        tracked_worktree_digest=tracked_worktree_digest(path, paths),
        effective_checkout_settings=_effective_checkout_settings(path),
    )


def tracked_paths(repo_root: Path) -> tuple[str, ...]:
    decoded = git_bytes(repo_root, "ls-files", "-z").decode(
        "utf-8", errors="surrogateescape"
    )
    paths = tuple(item for item in decoded.split("\0") if item)
    for item in paths:
        checked_relative_path(item)
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


def candidate_symlink_paths(repo_root: Path) -> tuple[str, ...]:
    paths = (*tracked_paths(repo_root), *untracked_paths(repo_root))
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
        raise PreparationFailure(
            "nested checkout candidate changed during isolated preparation",
            failure_type="candidate_snapshot_changed",
            action_class="retry_same_candidate",
            details={
                "expected_identity": expected.identity(),
                "actual_identity": observed.identity() if observed is not None else None,
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


def capture_candidate_snapshot(repo_root: Path) -> CandidateSnapshot:
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
    paths = untracked_paths(repo_root)
    directories = candidate_directory_paths(repo_root)
    return CandidateSnapshot(
        head=git_text(repo_root, "rev-parse", "HEAD"),
        index_tree=git_text(repo_root, "write-tree"),
        cached_diff_digest=sha256_bytes(
            git_bytes(
                repo_root,
                "diff",
                "--cached",
                "--binary",
                "--full-index",
                "--no-ext-diff",
                "--no-textconv",
            )
        ),
        worktree_diff_digest=sha256_bytes(
            git_bytes(
                repo_root,
                "diff",
                "--binary",
                "--full-index",
                "--no-ext-diff",
                "--no-textconv",
                "HEAD",
            )
        ),
        untracked_digest=untracked_content_digest(repo_root, paths),
        untracked_paths=paths,
        directory_digest=candidate_directory_digest(repo_root, directories),
        directories=directories,
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


def candidate_patch(repo_root: Path) -> bytes:
    return git_bytes(
        repo_root,
        "diff",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        "HEAD",
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
                # candidate instead of copying repository-local ignored state.
                # Every worktree byte exposed to validation is therefore
                # represented by the nested CandidateSnapshot identity.
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
                git_bytes(
                    destination,
                    "config",
                    "--local",
                    "core.hooksPath",
                    "/dev/null",
                )
                _require_effective_checkout_settings_match(source, destination)
                git_bytes(
                    destination,
                    "-c",
                    "core.hooksPath=/dev/null",
                    "checkout",
                    "--detach",
                    "-q",
                    nested.candidate.head,
                )
                _require_effective_checkout_settings_match(source, destination)
                materialize_candidate(source, destination, nested.candidate)
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
                require_nested_git_snapshot_unchanged(source, nested)
                _require_effective_checkout_settings_match(source, destination)
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
) -> None:
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
        destination.chmod(stat.S_IMODE(metadata.st_mode))


def materialize_candidate(
    source_root: Path,
    temporary_root: Path,
    snapshot: CandidateSnapshot,
) -> str:
    patch = candidate_patch(source_root)
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
    create_candidate_directories(
        source_root,
        temporary_root,
        snapshot.directories,
    )
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
    return git_text(temporary_root, "write-tree")


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

    coverage_generation = coverage_generation_module()

    require_seed_compatible_runtime(repo_root, external_seed_ref)
    seed = load_external_coverage_seed(repo_root, external_seed_ref)
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
            rebuilt, _timing = coverage_generation._build_owner_coverage(
                owner,
                repo_root,
                display_root=display_root,
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


def prepare_self_coverage(
    repo_root: Path,
    *,
    external_seed_ref: str,
    check: bool,
    verify_external_manifests: bool,
) -> int:
    coverage_generation = coverage_generation_module()

    payload = build_preparation_coverage(
        repo_root,
        external_seed_ref=external_seed_ref,
        verify_external_manifests=verify_external_manifests,
    )
    print(
        "[prepare-landing] coverage strategy="
        f"{'verified-external-seed' if verify_external_manifests else 'seed-only-sentinel'}"
        "+self-rebuild "
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
) -> tuple[str, ...]:
    command = [
        "python",
        "scripts/prepare_landing.py",
        "--prepare-self-coverage",
        "--external-seed-ref",
        refs.history_ref,
    ]
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
) -> tuple[int, str]:
    for iteration in range(1, max_iterations + 1):
        before_tree = git_text(repo_root, "write-tree")
        run_command(coverage_command(refs), repo_root=repo_root)
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
    stage_paths(repo_root, (*PORTABLE_FAMILY_PATHS, *BUDGET_RECEIPT_PATHS))
    run_command(
        portable_family_command(refs, check=True, enforce_budget=True),
        repo_root=repo_root,
        failure_type="budget_receipt_mismatch",
        action_class="code_fix",
    )
    return "created"


def final_confirmation(repo_root: Path, refs: ResolvedRefs) -> None:
    run_command(coverage_command(refs, check=True), repo_root=repo_root)
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
        iterations, fixed_point_tree = converge_scc(
            temporary_worktree,
            refs,
            max_iterations=max_iterations,
        )
        budget_receipt = ensure_budget_receipt(
            temporary_worktree,
            refs,
            budget_reason=budget_reason,
        )
        fixed_point_tree = git_text(temporary_worktree, "write-tree")
        final_confirmation(temporary_worktree, refs)
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
