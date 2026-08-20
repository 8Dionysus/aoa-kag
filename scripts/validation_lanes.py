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
ImpactRoutingDefinition = dict[str, Any]

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
        "release",
        "release_continuation",
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


def _string_list(value: object, where: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{VALIDATION_LANES_PATH}: {where} must be a list")
    if not allow_empty and not value:
        raise ValueError(f"{VALIDATION_LANES_PATH}: {where} must not be empty")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{VALIDATION_LANES_PATH}: {where} must contain strings")
    return tuple(value)


def _impact_rules(value: object, where: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{VALIDATION_LANES_PATH}: {where} must be a non-empty list")
    rules: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    match_fields = ("exact_paths", "prefixes", "segments", "suffixes")
    for index, rule in enumerate(value):
        rule_where = f"{where}[{index}]"
        if not isinstance(rule, dict):
            raise ValueError(f"{VALIDATION_LANES_PATH}: {rule_where} must be an object")
        rule_id = rule.get("id")
        reason = rule.get("reason")
        if not isinstance(rule_id, str) or not rule_id:
            raise ValueError(f"{VALIDATION_LANES_PATH}: {rule_where}.id is required")
        if rule_id in seen_ids:
            raise ValueError(
                f"{VALIDATION_LANES_PATH}: duplicate impact rule id {rule_id!r}"
            )
        seen_ids.add(rule_id)
        if not isinstance(reason, str) or not reason:
            raise ValueError(f"{VALIDATION_LANES_PATH}: {rule_where}.reason is required")
        normalized_rule: dict[str, Any] = {"id": rule_id, "reason": reason}
        matched = False
        for field in match_fields:
            if field not in rule:
                normalized_rule[field] = ()
                continue
            values = _string_list(
                rule[field],
                f"{rule_where}.{field}",
                allow_empty=True,
            )
            normalized_rule[field] = values
            matched = matched or bool(values)
        if not matched:
            raise ValueError(
                f"{VALIDATION_LANES_PATH}: {rule_where} must define a path matcher"
            )
        rules.append(normalized_rule)
    return tuple(rules)


def _impact_routing(manifest: dict[str, Any]) -> ImpactRoutingDefinition:
    routing = manifest.get("impact_routing")
    if not isinstance(routing, dict):
        raise ValueError(f"{VALIDATION_LANES_PATH}: impact_routing must be an object")
    if routing.get("schema_version") != 1:
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: unsupported impact_routing schema_version "
            f"{routing.get('schema_version')!r}"
        )
    if routing.get("default_route") != "full-audit":
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: impact_routing.default_route must be "
            "'full-audit'"
        )
    default_reason = routing.get("default_reason")
    if not isinstance(default_reason, str) or not default_reason:
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: impact_routing.default_reason is required"
        )
    always_required = _string_list(
        routing.get("always_required_proofs"),
        "impact_routing.always_required_proofs",
    )
    if set(always_required) != {"source-fast", "owner-family"}:
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: impact routing must always require "
            "source-fast and owner-family proofs"
        )
    return {
        "schema_version": 1,
        "default_route": "full-audit",
        "default_reason": default_reason,
        "always_required_proofs": always_required,
        "full_audit_rules": _impact_rules(
            routing.get("full_audit_rules"),
            "impact_routing.full_audit_rules",
        ),
        "owner_local_rules": _impact_rules(
            routing.get("owner_local_rules"),
            "impact_routing.owner_local_rules",
        ),
    }


_MANIFEST = _load_manifest()
LANE_DEFINITIONS = _lane_definitions(_MANIFEST)
IMPACT_ROUTING = _impact_routing(_MANIFEST)


def _source_fast_handoff(manifest: dict[str, Any]) -> dict[str, Any]:
    handoff = manifest.get("source_fast_handoff")
    if not isinstance(handoff, dict):
        raise ValueError(f"{VALIDATION_LANES_PATH}: source_fast_handoff must be an object")
    if handoff.get("schema_version") != "aoa_kag_source_fast_handoff_v1":
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: source_fast_handoff schema is unsupported"
        )
    if handoff.get("producer_job") != "source_fast":
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: source_fast_handoff producer must be source_fast"
        )
    if handoff.get("consumer_job") != "release_audit":
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: source_fast_handoff consumer must be release_audit"
        )
    if handoff.get("invalid_receipt_posture") != "fallback-full-release":
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: invalid source-fast handoff must fall back"
        )
    donors = _string_list(handoff.get("donors"), "source_fast_handoff.donors")
    if len(donors) != len(set(donors)):
        raise ValueError(
            f"{VALIDATION_LANES_PATH}: source_fast_handoff donors must be unique"
        )
    return {**handoff, "donors": donors}


SOURCE_FAST_HANDOFF = _source_fast_handoff(_MANIFEST)


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
RELEASE_CHECK_COMMAND_SEQUENCE = command_sequence_for_lane("release")
RELEASE_CONTINUATION_COMMAND_SEQUENCE = command_sequence_for_lane(
    "release_continuation"
)
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
ADVISORY_BOUNDARIES = tuple(LANE_DEFINITIONS["advisory"].get("boundaries", ()))
