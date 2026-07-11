from __future__ import annotations

import hashlib
import re
import subprocess
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


def _apply_name_status(
    lineages: dict[str, str],
    rows: Iterable[tuple[str, ...]],
) -> None:
    for columns in rows:
        status = columns[0]
        operation = status[0]
        if operation == "R" and len(columns) >= 3:
            old_path, new_path = columns[1], columns[2]
            lineages[new_path] = lineages.pop(old_path, old_path)
        elif operation == "C" and len(columns) >= 3:
            lineages.setdefault(columns[2], columns[2])
        elif operation == "D":
            lineages.pop(columns[1], None)
        else:
            lineages.setdefault(columns[1], columns[1])


def git_lineage_paths(repo_root: Path, tracked_paths: Iterable[Path]) -> dict[Path, Path]:
    lineages: dict[str, str] = {}
    history = _name_status(
        (
            "git",
            "-c",
            "core.quotepath=false",
            "log",
            "--reverse",
            "--format=commit:%H",
            "--name-status",
            "--find-renames=50%",
            "--",
        ),
        repo_root,
    )
    _apply_name_status(lineages, history)
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
    _apply_name_status(lineages, staged)
    return {
        path: Path(lineages.get(path.as_posix(), path.as_posix()))
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
