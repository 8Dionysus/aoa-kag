"""Shared validation lane loader for aoa-kag.

The executable command authority lives in ``config/validation_lanes.json``.
This module is only the Python loader/API for CI, release, and tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

Command = tuple[str, ...]
LaneDefinition = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_LANES_PATH = REPO_ROOT / "config" / "validation_lanes.json"


def _load_manifest() -> dict[str, Any]:
    payload = json.loads(VALIDATION_LANES_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: unsupported schema_version "
            f"{payload.get('schema_version')!r}"
        )
    return payload


def _command(command: object, where: str) -> Command:
    if not isinstance(command, list) or not command:
        raise ValueError(f"{VALIDATION_LANES_PATH}: {where} must be a non-empty list")
    if any(not isinstance(part, str) or not part for part in command):
        raise ValueError(f"{VALIDATION_LANES_PATH}: {where} must contain strings")
    return tuple(command)


def _command_sequence(manifest: dict[str, Any], name: str) -> tuple[Command, ...]:
    sequences = manifest.get("command_sequences")
    if not isinstance(sequences, dict):
        raise ValueError(f"{VALIDATION_LANES_PATH}: command_sequences must be a mapping")
    sequence = sequences.get(name)
    if not isinstance(sequence, list) or not sequence:
        raise ValueError(f"{VALIDATION_LANES_PATH}: missing command sequence {name!r}")
    return tuple(
        _command(command, f"command_sequences.{name}[{idx}]")
        for idx, command in enumerate(sequence)
    )


def _drift_paths(manifest: dict[str, Any], name: str) -> tuple[str, ...]:
    drift_paths = manifest.get("drift_paths")
    if not isinstance(drift_paths, dict):
        raise ValueError(f"{VALIDATION_LANES_PATH}: drift_paths must be a mapping")
    paths = drift_paths.get(name)
    if not isinstance(paths, list) or not paths:
        raise ValueError(f"{VALIDATION_LANES_PATH}: missing drift path list {name!r}")
    if any(not isinstance(path, str) or not path for path in paths):
        raise ValueError(f"{VALIDATION_LANES_PATH}: drift_paths.{name} must contain strings")
    return tuple(paths)


def _lane_definitions(manifest: dict[str, Any]) -> dict[str, LaneDefinition]:
    lanes = manifest.get("lanes")
    if not isinstance(lanes, dict) or not lanes:
        raise ValueError(f"{VALIDATION_LANES_PATH}: lanes must be a non-empty mapping")

    expected = {
        "source_fast",
        "generated",
        "incremental_federation",
        "release",
        "compatibility_canary",
        "advisory",
    }
    missing = sorted(expected - set(lanes))
    if missing:
        raise ValueError(f"{VALIDATION_LANES_PATH}: missing lane definitions {missing}")

    for lane_id, lane in lanes.items():
        if not isinstance(lane, dict):
            raise ValueError(f"{VALIDATION_LANES_PATH}: lanes.{lane_id} must be an object")
        if not isinstance(lane.get("label"), str) or not lane["label"]:
            raise ValueError(f"{VALIDATION_LANES_PATH}: lanes.{lane_id}.label is required")
        if lane.get("posture") not in {"blocking", "non_blocking"}:
            raise ValueError(f"{VALIDATION_LANES_PATH}: lanes.{lane_id}.posture is invalid")
        if not isinstance(lane.get("owner_surface"), str) or not lane["owner_surface"]:
            raise ValueError(f"{VALIDATION_LANES_PATH}: lanes.{lane_id}.owner_surface is required")
        if lane["posture"] == "blocking" and not isinstance(lane.get("command_sequence"), str):
            raise ValueError(
                f"{VALIDATION_LANES_PATH}: lanes.{lane_id}.command_sequence is required"
            )
    return lanes


_MANIFEST = _load_manifest()
LANE_DEFINITIONS = _lane_definitions(_MANIFEST)


def command_sequence_for_lane(lane_id: str) -> tuple[Command, ...]:
    lane = LANE_DEFINITIONS.get(lane_id)
    if lane is None:
        raise ValueError(f"{VALIDATION_LANES_PATH}: unknown lane {lane_id!r}")
    sequence_name = lane.get("command_sequence")
    if not isinstance(sequence_name, str) or not sequence_name:
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: lanes.{lane_id} does not define a command sequence"
        )
    return _command_sequence(_MANIFEST, sequence_name)


SOURCE_FAST_COMMAND_SEQUENCE = command_sequence_for_lane("source_fast")
GENERATED_CHECK_COMMAND_SEQUENCE = command_sequence_for_lane("generated")
INCREMENTAL_FEDERATION_COMMAND_SEQUENCE = command_sequence_for_lane(
    "incremental_federation"
)
RELEASE_CHECK_COMMAND_SEQUENCE = command_sequence_for_lane("release")
COMPATIBILITY_CANARY_COMMAND_SEQUENCE = command_sequence_for_lane("compatibility_canary")
GENERATED_DRIFT_PATHS = _drift_paths(_MANIFEST, "generated")
GENERATED_DRIFT_SNAPSHOT_COMMAND = (
    "git",
    "diff",
    "--binary",
    "--no-ext-diff",
    "--",
    *GENERATED_DRIFT_PATHS,
)
GENERATED_DRIFT_STATUS_COMMAND = (
    "git",
    "status",
    "--porcelain=v1",
    "--untracked-files=all",
    "--",
    *GENERATED_DRIFT_PATHS,
)
ADVISORY_BOUNDARIES = tuple(LANE_DEFINITIONS["advisory"].get("boundaries", ()))
