from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence


def _slug(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9_.:/#-]", "-", lowered)
    return re.sub(r"-+", "-", lowered).strip("-") or "root"


def repository_namespace(repo: str) -> str:
    return f"aoa:{_slug(repo)}"


def qualified_id(repo: str, record_class: str, semantic_key: str) -> str:
    normalized_key = semantic_key.replace("\\", "/")
    digest = hashlib.sha256(normalized_key.encode("utf-8")).hexdigest()[:24]
    return f"{repository_namespace(repo)}:{_slug(record_class)}:{digest}"


def _name_status(command: Sequence[str], repo_root: Path) -> Iterable[tuple[str, ...]]:
    try:
        output = subprocess.run(
            command,
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ()

    rows: list[tuple[str, ...]] = []
    for line in output.splitlines():
        columns = tuple(line.split("\t"))
        if len(columns) >= 2 and re.fullmatch(r"[A-Z][0-9]*", columns[0]):
            rows.append(columns)
    return rows


@dataclass
class GitLineageState:
    active: dict[str, str] = field(default_factory=dict)
    generations: dict[str, int] = field(default_factory=dict)

    @staticmethod
    def generation_key(path: str, generation: int) -> str:
        return path if generation == 1 else f"{path}#generation-{generation}"

    def occupy(self, path: str) -> str:
        generation = self.generations.get(path, 0) + 1
        self.generations[path] = generation
        lineage = self.generation_key(path, generation)
        self.active[path] = lineage
        return lineage

    def apply(self, columns: Sequence[str]) -> str:
        status = columns[0]
        operation = status[0]
        path = columns[-1]
        if operation == "R" and len(columns) >= 3:
            old_path, new_path = columns[1], columns[2]
            lineage = self.active.pop(old_path, old_path)
            self.generations[new_path] = self.generations.get(new_path, 0) + 1
            self.active[new_path] = lineage
            return lineage
        if operation == "C" and len(columns) >= 3:
            return self.occupy(columns[2])
        if operation == "A":
            return self.occupy(path)
        if operation == "D":
            generation = self.generations.get(path, 1)
            return self.active.pop(path, self.generation_key(path, generation))
        if path not in self.active:
            self.generations.setdefault(path, 1)
            self.active[path] = self.generation_key(path, self.generations[path])
        return self.active[path]


def _apply_name_status(state: GitLineageState, rows: Iterable[tuple[str, ...]]) -> None:
    for columns in rows:
        state.apply(columns)


def git_lineage_paths(
    repo_root: Path,
    tracked_paths: Iterable[Path],
    *,
    history_ref: str | None = None,
) -> dict[Path, Path]:
    state = GitLineageState()
    history_command = [
        "git",
        "-c",
        "core.quotepath=false",
        "log",
        "--reverse",
        "--format=commit:%H",
        "--name-status",
        "--find-renames=50%",
    ]
    if history_ref:
        history_command.append(history_ref)
    history_command.append("--")
    history = _name_status(
        history_command,
        repo_root,
    )
    _apply_name_status(state, history)
    staged = _name_status(
        (
            "git",
            "-c",
            "core.quotepath=false",
            "diff",
            "--cached",
            "--name-status",
            "--find-renames=50%",
            "--",
        ),
        repo_root,
    )
    _apply_name_status(state, staged)
    return {
        path: Path(state.active.get(path.as_posix(), path.as_posix()))
        for path in tracked_paths
    }


def artifact_identity(
    repo: str,
    path: Path,
    *,
    lineage_path: Path,
    content_hash: str,
) -> dict[str, str]:
    logical_id = qualified_id(repo, "artifact", lineage_path.as_posix())
    return {
        "id": logical_id,
        "logical_id": logical_id,
        "version_id": qualified_id(repo, "artifact-version", f"{logical_id}:{content_hash}"),
        "lineage_path": lineage_path.as_posix(),
    }
