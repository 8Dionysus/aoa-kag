from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .identity import GitLineageState, qualified_id


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
    lineage_state: GitLineageState,
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
    lineage_path = lineage_state.apply(columns)
    object_id = qualified_id(repo, "artifact", lineage_path)
    return {
        "change_kind": change_kind,
        "path": path,
        "old_path": old_path,
        "object_id": object_id,
    }


def _repository_snapshot_event(
    *,
    repo: str,
    changes: list[dict[str, str]],
    current_ids: dict[str, str],
    artifact_anchor_ids: dict[str, str],
) -> dict[str, Any]:
    current_object_ids = set(current_ids.values())
    changes = [
        {
            **item,
            "object_id": current_ids.get(item["path"], item["object_id"]),
        }
        for item in changes
    ]
    ordered_changes = sorted(
        changes,
        key=lambda item: (
            item["path"],
            item["old_path"],
            item["change_kind"],
            item["object_id"],
        ),
    )
    signature = json.dumps(
        ordered_changes,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    source_ids = sorted({
        item["object_id"]
        for item in ordered_changes
        if item["object_id"] in current_object_ids
    })
    return {
        "id": qualified_id(repo, "event", f"repository-snapshot:{signature}"),
        "event_kind": "repository_snapshot_change_set",
        "event_role": "observation",
        "observation_state": "observed",
        "label": "Repository source snapshot change set",
        "source_record_ids": source_ids,
        "anchor_ids": [
            artifact_anchor_ids[item]
            for item in source_ids
            if item in artifact_anchor_ids
        ],
        "object_ids": source_ids,
        "changes": ordered_changes,
        "occurred_at": "",
        "actor": {"name": "repository-snapshot", "email": ""},
        "evidence_refs": [
            {"kind": "repository_snapshot", "ref": "source-tree-snapshot"}
        ],
        "temporal_ref": "current",
        "provenance_ref": "observed",
        "trust_ref": "observed",
    }


def git_commit_events(
    repo_root: Path,
    *,
    repo: str,
    current_ids: dict[str, str],
    artifact_anchor_ids: dict[str, str],
    excluded_paths: set[str] | None = None,
    history_ref: str | None = None,
) -> list[dict[str, Any]]:
    excluded = excluded_paths or set()
    current_object_ids = set(current_ids.values())
    history_command = [
        "git",
        "-c",
        "core.quotepath=false",
        "log",
        "--reverse",
        "--format=@@@%H%x09%aI%x09%an%x09%ae%x09%s",
        "--name-status",
        "--find-renames=50%",
    ]
    if history_ref:
        history_command.append(history_ref)
    history_command.append("--")
    output = _git_text(
        repo_root,
        history_command,
    )
    events: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    lineage_state = GitLineageState()
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
            lineage_state=lineage_state,
        )
        if change["path"] in excluded or change["old_path"] in excluded:
            continue
        change["object_id"] = current_ids.get(change["path"], change["object_id"])
        current["changes"].append(change)
        object_id = change["object_id"]
        if object_id in current_object_ids:
            current["object_ids"].append(object_id)
            current["source_record_ids"].append(object_id)
            anchor_id = artifact_anchor_ids.get(object_id)
            if anchor_id:
                current["anchor_ids"].append(anchor_id)
    if current is not None and current["changes"]:
        events.append(current)

    snapshot_command = [
        "git",
        "-c",
        "core.quotepath=false",
        "diff",
        "--cached",
        "--name-status",
        "--find-renames=50%",
    ]
    if history_ref:
        snapshot_command.append(history_ref)
    snapshot_command.append("--")
    staged = _git_text(repo_root, snapshot_command)
    staged_changes = [
        _change(
            line.split("\t"),
            repo=repo,
            lineage_state=lineage_state,
        )
        for line in staged.splitlines()
        if "\t" in line
    ]
    staged_changes = [
        item
        for item in staged_changes
        if item["path"] not in excluded and item["old_path"] not in excluded
    ]
    snapshot_changes: list[dict[str, str]] = staged_changes
    if not snapshot_changes and events:
        # The latest source change is the current snapshot until another source change appears.
        snapshot_changes = events.pop()["changes"]
    if snapshot_changes:
        events.append(
            _repository_snapshot_event(
                repo=repo,
                changes=snapshot_changes,
                current_ids=current_ids,
                artifact_anchor_ids=artifact_anchor_ids,
            )
        )

    for event in events:
        event["source_record_ids"] = sorted(set(event["source_record_ids"]))
        event["anchor_ids"] = sorted(set(event["anchor_ids"]))
        event["object_ids"] = sorted(set(event["object_ids"]))
    return events
