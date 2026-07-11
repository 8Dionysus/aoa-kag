from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Sequence

from .identity import qualified_id


def _git_text(repo_root: Path, command: Sequence[str]) -> str:
    try:
        return subprocess.run(
            command,
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def _change(
    columns: list[str],
    *,
    repo: str,
    current_ids: dict[str, str],
    lineage_paths: dict[str, str],
) -> dict[str, str]:
    status = columns[0]
    operation = status[0]
    old_path = ""
    path = columns[-1]
    if operation in {"R", "C"} and len(columns) >= 3:
        old_path = columns[1]
    change_kind = {
        "A": "add",
        "C": "copy",
        "D": "delete",
        "M": "modify",
        "R": "rename",
        "T": "type_change",
    }.get(operation, "change")
    if operation == "R":
        lineage_path = lineage_paths.pop(old_path, old_path)
        lineage_paths[path] = lineage_path
    elif operation == "C":
        lineage_path = path
        lineage_paths[path] = lineage_path
    elif operation == "D":
        lineage_path = lineage_paths.pop(path, path)
    else:
        lineage_path = lineage_paths.setdefault(path, path)
    object_id = current_ids.get(path) or qualified_id(repo, "artifact", lineage_path)
    return {
        "change_kind": change_kind,
        "path": path,
        "old_path": old_path,
        "object_id": object_id,
    }


def git_commit_events(
    repo_root: Path,
    *,
    repo: str,
    current_ids: dict[str, str],
    artifact_anchor_ids: dict[str, str],
    excluded_paths: set[str] | None = None,
) -> list[dict[str, Any]]:
    excluded = excluded_paths or set()
    output = _git_text(
        repo_root,
        (
            "git",
            "-c",
            "core.quotepath=false",
            "log",
            "--reverse",
            "--format=@@@%H%x09%aI%x09%an%x09%ae%x09%s",
            "--name-status",
            "--find-renames=50%",
            "--",
        ),
    )
    events: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    lineage_paths: dict[str, str] = {}
    for line in output.splitlines():
        if line.startswith("@@@"):
            if current is not None and current["changes"]:
                events.append(current)
            fields = line[3:].split("\t", 4)
            if len(fields) < 5:
                current = None
                continue
            commit, occurred_at, actor_name, actor_email, subject = fields
            current = {
                "id": qualified_id(repo, "event", f"git-commit:{commit}"),
                "event_kind": "git_commit",
                "event_role": "observation",
                "observation_state": "observed",
                "label": subject or commit[:12],
                "source_record_ids": [],
                "anchor_ids": [],
                "object_ids": [],
                "changes": [],
                "occurred_at": occurred_at,
                "actor": {"name": actor_name, "email": actor_email},
                "evidence_refs": [{"kind": "git_commit", "ref": commit}],
                "temporal_ref": "historical",
                "provenance_ref": "observed",
                "trust_ref": "observed",
            }
            continue
        if current is None or "\t" not in line:
            continue
        columns = line.split("\t")
        change = _change(
            columns,
            repo=repo,
            current_ids=current_ids,
            lineage_paths=lineage_paths,
        )
        if change["path"] in excluded or change["old_path"] in excluded:
            continue
        current["changes"].append(change)
        object_id = change["object_id"]
        current["object_ids"].append(object_id)
        path = change["path"]
        source_id = current_ids.get(path)
        if source_id:
            current["source_record_ids"].append(source_id)
            anchor_id = artifact_anchor_ids.get(source_id)
            if anchor_id:
                current["anchor_ids"].append(anchor_id)
    if current is not None and current["changes"]:
        events.append(current)

    staged = _git_text(
        repo_root,
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
    )
    staged_changes = [
        _change(
            line.split("\t"),
            repo=repo,
            current_ids=current_ids,
            lineage_paths=lineage_paths,
        )
        for line in staged.splitlines()
        if "\t" in line
    ]
    staged_changes = [
        item
        for item in staged_changes
        if item["path"] not in excluded and item["old_path"] not in excluded
    ]
    if staged_changes:
        signature = "|".join(
            f"{item['change_kind']}:{item['old_path']}:{item['path']}" for item in staged_changes
        )
        source_ids = sorted(
            {
                current_ids[item["path"]]
                for item in staged_changes
                if item["path"] in current_ids
            }
        )
        events.append(
            {
                "id": qualified_id(repo, "event", f"git-index:{signature}"),
                "event_kind": "git_index_change_set",
                "event_role": "observation",
                "observation_state": "observed",
                "label": "Git index change set",
                "source_record_ids": source_ids,
                "anchor_ids": [artifact_anchor_ids[item] for item in source_ids if item in artifact_anchor_ids],
                "object_ids": [item["object_id"] for item in staged_changes],
                "changes": staged_changes,
                "occurred_at": "",
                "actor": {"name": "git-index", "email": ""},
                "evidence_refs": [{"kind": "git_index", "ref": "git-index-source-tree"}],
                "temporal_ref": "current",
                "provenance_ref": "observed",
                "trust_ref": "observed",
            }
        )

    for event in events:
        event["source_record_ids"] = sorted(set(event["source_record_ids"]))
        event["anchor_ids"] = sorted(set(event["anchor_ids"]))
        event["object_ids"] = sorted(set(event["object_ids"]))
    return events
