#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Sequence

from jsonschema import Draft202012Validator
import yaml

REPO_ROOT = Path(__file__).resolve().parents[5]

QUESTBOOK_PATH = Path("QUESTBOOK.md")
QUEST_STORE_PART_ROOT = (
    Path("mechanics") / "questbook" / "parts" / "quest-store"
)
QUESTBOOK_INTEGRATION_PATH = QUEST_STORE_PART_ROOT / "docs" / "questbook-kag-integration.md"
QUEST_SCHEMA_PATH = QUEST_STORE_PART_ROOT / "schemas" / "quest.schema.json"
QUEST_DISPATCH_SCHEMA_PATH = QUEST_STORE_PART_ROOT / "schemas" / "quest_dispatch.schema.json"
QUEST_CATALOG_EXAMPLE_PATH = QUEST_STORE_PART_ROOT / "examples" / "quest_catalog.min.example.json"
QUEST_DISPATCH_EXAMPLE_PATH = QUEST_STORE_PART_ROOT / "examples" / "quest_dispatch.min.example.json"
QUEST_ROOT = Path("quests")
QUEST_SOURCE_LANE = "kag"
QUEST_ID_RE = re.compile(r"^AOA-KAG-Q-\d{4}$")
QUESTBOOK_REQUIRED_INDEX_TOKENS = (
    "source-owned export dependency gaps",
    "primary truth",
    "quests/kag/<state>/AOA-KAG-Q-*.yaml",
    "mechanics/questbook/parts/quest-store/examples/quest_catalog.min.example.json",
    "mechanics/questbook/parts/quest-store/examples/quest_dispatch.min.example.json",
)
LIFECYCLE_STATES = {
    "captured",
    "triaged",
    "ready",
    "active",
    "blocked",
    "reanchor",
    "done",
    "dropped",
}
CLOSED_QUEST_STATES = {"done", "dropped"}
QUESTBOOK_REQUIRED_INTEGRATION_TOKENS = (
    "source repos remain the owners of meaning",
    "`aoa-kag` remains the owner of derived, provenance-aware structures and bounded export contracts",
    "CHARTER.md",
    "docs/KAG_MODEL.md",
    "mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md",
    "mechanics/boundary-bridge/parts/source-owned-export/docs/federation-kag-readiness.md",
    "docs/BRIDGE_CONTRACTS.md",
    "mechanics/recurrence/parts/return-regrounding/docs/recurrence-regrounding.md",
    "mechanics/boundary-bridge/parts/cross-source-projection/docs/cross-source-node-projection.md",
)
QUESTBOOK_FORBIDDEN_TOKENS = (
    "ATM10-Agent",
    "aoa-sdk",
)
QUEST_SCHEMA_REQUIRED_FIELDS = (
    "schema_version",
    "id",
    "title",
    "repo",
    "owner_surface",
    "kind",
    "state",
    "band",
    "difficulty",
    "risk",
    "control_mode",
    "delegate_tier",
    "write_scope",
    "activation",
    "anchor_ref",
    "evidence",
    "opened_at",
    "touched_at",
    "public_safe",
)
QUEST_DISPATCH_REQUIRED_FIELDS = (
    "schema_version",
    "id",
    "repo",
    "state",
    "band",
    "difficulty",
    "risk",
    "control_mode",
    "delegate_tier",
    "split_required",
    "write_scope",
    "activation_mode",
    "public_safe",
)


class QuestStoreValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise QuestStoreValidationError(message)


def display_path(path: Path, repo_root: Path = REPO_ROOT) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {display_path(path)}: {exc}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")


def read_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {display_path(path)}")
    except yaml.YAMLError as exc:
        fail(f"invalid YAML in {display_path(path)}: {exc}")


def format_schema_path(parts: Sequence[object]) -> str:
    return ".".join(str(part) for part in parts)


def validate_quest_schema_envelope(
    path: Path,
    *,
    title: str,
    schema_version: str,
    required_fields: Sequence[str],
) -> None:
    schema = read_json(path)
    if not isinstance(schema, dict):
        fail(f"{display_path(path)} must contain a JSON object")
    required_top_level = {"$schema", "$id", "title", "type", "properties", "required"}
    missing_top_level = sorted(required_top_level - set(schema))
    if missing_top_level:
        fail(
            f"{display_path(path)} is missing required top-level keys: {', '.join(missing_top_level)}"
        )
    if schema.get("title") != title:
        fail(f"{display_path(path)} title must equal '{title}'")
    required = schema.get("required")
    if not isinstance(required, list):
        fail(f"{display_path(path)} required must be a list")
    missing_required = [field for field in required_fields if field not in required]
    if missing_required:
        fail(f"{display_path(path)} required must include: {', '.join(missing_required)}")
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        fail(f"{display_path(path)} properties must be an object")
    schema_version_entry = properties.get("schema_version")
    if (
        not isinstance(schema_version_entry, dict)
        or schema_version_entry.get("const") != schema_version
    ):
        fail(f"{display_path(path)} schema_version must stay pinned to '{schema_version}'")


def discover_quest_paths(repo_root: Path) -> list[Path]:
    quest_root = repo_root / QUEST_ROOT
    if not quest_root.is_dir():
        fail(f"missing required directory: {display_path(quest_root, repo_root)}")

    root_aliases = sorted(quest_root.glob("AOA-KAG-Q-*.yaml"))
    if root_aliases:
        paths = ", ".join(display_path(path, repo_root) for path in root_aliases)
        fail(f"root quest aliases are not active source paths: {paths}")

    all_yaml = sorted(quest_root.rglob("*.yaml"))
    if not all_yaml:
        fail("no quest source records found under quests/<lane>/<state>/")

    quest_paths: list[Path] = []
    for path in all_yaml:
        relative_parts = path.relative_to(quest_root).parts
        if len(relative_parts) != 3:
            fail(
                f"{display_path(path, repo_root)} must live at quests/<lane>/<state>/<quest-file>.yaml"
            )
        lane, state, filename = relative_parts
        if lane != QUEST_SOURCE_LANE:
            fail(
                f"{display_path(path, repo_root)} lane must be '{QUEST_SOURCE_LANE}' for aoa-kag source quest records"
            )
        if state not in LIFECYCLE_STATES:
            fail(f"{display_path(path, repo_root)} has unknown lifecycle state directory '{state}'")
        if not filename.startswith("AOA-KAG-Q-") or not filename.endswith(".yaml"):
            fail(f"{display_path(path, repo_root)} must use AOA-KAG-Q-####.yaml naming")
        quest_paths.append(path)

    return sorted(quest_paths, key=lambda path: path.name)


def build_expected_quest_catalog_entry(
    quest_id: str,
    payload: dict[str, Any],
    source_path: str,
) -> dict[str, Any]:
    return {
        "id": quest_id,
        "title": payload["title"],
        "repo": payload["repo"],
        "theme_ref": payload.get("theme_ref", ""),
        "milestone_ref": payload.get("milestone_ref", ""),
        "state": payload["state"],
        "band": payload["band"],
        "kind": payload["kind"],
        "difficulty": payload["difficulty"],
        "risk": payload["risk"],
        "owner_surface": payload["owner_surface"],
        "source_path": source_path,
        "public_safe": payload["public_safe"],
    }


def build_expected_quest_dispatch_entry(
    quest_id: str,
    payload: dict[str, Any],
    actual: dict[str, Any],
    source_path: str,
) -> dict[str, Any]:
    expected = {
        "schema_version": "quest_dispatch_v1",
        "id": quest_id,
        "repo": payload["repo"],
        "state": payload["state"],
        "band": payload["band"],
        "difficulty": payload["difficulty"],
        "risk": payload["risk"],
        "control_mode": payload["control_mode"],
        "delegate_tier": payload["delegate_tier"],
        "split_required": payload.get("split_required", False),
        "write_scope": payload["write_scope"],
        "activation_mode": payload["activation"]["mode"],
        "source_path": source_path,
        "public_safe": payload["public_safe"],
    }
    if "fallback_tier" in actual:
        expected["fallback_tier"] = payload.get("fallback_tier")
    if "wrapper_class" in actual:
        expected["wrapper_class"] = payload.get("wrapper_class")
    return expected


def validate_questbook_surface(repo_root: Path = REPO_ROOT) -> None:
    for path in (
        repo_root / QUESTBOOK_PATH,
        repo_root / QUESTBOOK_INTEGRATION_PATH,
        repo_root / QUEST_SCHEMA_PATH,
        repo_root / QUEST_DISPATCH_SCHEMA_PATH,
        repo_root / QUEST_CATALOG_EXAMPLE_PATH,
        repo_root / QUEST_DISPATCH_EXAMPLE_PATH,
    ):
        if not path.is_file():
            fail(f"missing required file: {display_path(path, repo_root)}")

    validate_quest_schema_envelope(
        repo_root / QUEST_SCHEMA_PATH,
        title="aoa-kag work_quest_v1",
        schema_version="work_quest_v1",
        required_fields=QUEST_SCHEMA_REQUIRED_FIELDS,
    )
    validate_quest_schema_envelope(
        repo_root / QUEST_DISPATCH_SCHEMA_PATH,
        title="aoa-kag quest_dispatch_v1",
        schema_version="quest_dispatch_v1",
        required_fields=QUEST_DISPATCH_REQUIRED_FIELDS,
    )
    quest_schema = read_json(repo_root / QUEST_SCHEMA_PATH)
    if not isinstance(quest_schema, dict):
        fail(f"{display_path(repo_root / QUEST_SCHEMA_PATH, repo_root)} must contain a JSON object")
    Draft202012Validator.check_schema(quest_schema)
    quest_validator = Draft202012Validator(quest_schema)

    integration_text = read_text(repo_root / QUESTBOOK_INTEGRATION_PATH)
    for token in QUESTBOOK_REQUIRED_INTEGRATION_TOKENS:
        if token not in integration_text:
            fail(
                f"{display_path(repo_root / QUESTBOOK_INTEGRATION_PATH, repo_root)} must mention '{token}' explicitly"
            )
    for token in QUESTBOOK_FORBIDDEN_TOKENS:
        if token in integration_text:
            fail(
                f"{display_path(repo_root / QUESTBOOK_INTEGRATION_PATH, repo_root)} must not mention out-of-scope surface '{token}'"
            )

    quest_payloads: dict[str, dict[str, Any]] = {}
    quest_source_paths: dict[str, str] = {}
    active_quest_ids: list[str] = []
    closed_quest_ids: list[str] = []
    for quest_path in discover_quest_paths(repo_root):
        quest_id = quest_path.stem
        source_path = display_path(quest_path, repo_root)
        state_dir = quest_path.parent.name
        if not QUEST_ID_RE.match(quest_id):
            fail(f"{source_path} id must match AOA-KAG-Q-####")
        payload = read_yaml(quest_path)
        if not isinstance(payload, dict):
            fail(f"{display_path(quest_path, repo_root)} must contain a YAML mapping")
        schema_errors = sorted(
            quest_validator.iter_errors(payload),
            key=lambda error: (list(error.absolute_path), error.message),
        )
        if schema_errors:
            first = schema_errors[0]
            error_path = format_schema_path(list(first.absolute_path))
            if error_path:
                fail(
                    f"{display_path(quest_path, repo_root)} schema violation at '{error_path}': {first.message}"
                )
            fail(f"{display_path(quest_path, repo_root)} schema violation: {first.message}")
        if payload.get("schema_version") != "work_quest_v1":
            fail(f"{display_path(quest_path, repo_root)} schema_version must equal 'work_quest_v1'")
        if payload.get("id") != quest_id:
            fail(f"{display_path(quest_path, repo_root)} id must equal '{quest_id}'")
        if payload.get("state") != state_dir:
            fail(
                f"{display_path(quest_path, repo_root)} state must match lifecycle directory '{state_dir}'"
            )
        if payload.get("repo") != "aoa-kag":
            fail(f"{display_path(quest_path, repo_root)} repo must equal 'aoa-kag'")
        if payload.get("public_safe") is not True:
            fail(f"{display_path(quest_path, repo_root)} public_safe must be true")
        quest_payloads[quest_id] = payload
        quest_source_paths[quest_id] = source_path
        if payload.get("state") in CLOSED_QUEST_STATES:
            closed_quest_ids.append(quest_id)
        else:
            active_quest_ids.append(quest_id)

    questbook_text = read_text(repo_root / QUESTBOOK_PATH)
    for token in QUESTBOOK_REQUIRED_INDEX_TOKENS:
        if token not in questbook_text:
            fail(f"{display_path(repo_root / QUESTBOOK_PATH, repo_root)} must mention '{token}' explicitly")
    for quest_id in active_quest_ids:
        if quest_id not in questbook_text:
            fail(f"{display_path(repo_root / QUESTBOOK_PATH, repo_root)} must reference active quest id '{quest_id}'")
    for quest_id in closed_quest_ids:
        if quest_id in questbook_text:
            fail(f"{display_path(repo_root / QUESTBOOK_PATH, repo_root)} must not list closed quest id '{quest_id}'")
    for token in QUESTBOOK_FORBIDDEN_TOKENS:
        if token in questbook_text:
            fail(
                f"{display_path(repo_root / QUESTBOOK_PATH, repo_root)} must not mention out-of-scope surface '{token}'"
            )

    catalog_payload = read_json(repo_root / QUEST_CATALOG_EXAMPLE_PATH)
    if not isinstance(catalog_payload, list):
        fail(f"{display_path(repo_root / QUEST_CATALOG_EXAMPLE_PATH, repo_root)} must contain a JSON array")
    expected_catalog = [
        build_expected_quest_catalog_entry(
            quest_id,
            quest_payloads[quest_id],
            quest_source_paths[quest_id],
        )
        for quest_id in sorted(quest_payloads)
    ]
    if catalog_payload != expected_catalog:
        fail(
            f"{display_path(repo_root / QUEST_CATALOG_EXAMPLE_PATH, repo_root)} must stay aligned with quests/<lane>/<state>/*.yaml"
        )

    dispatch_payload = read_json(repo_root / QUEST_DISPATCH_EXAMPLE_PATH)
    if not isinstance(dispatch_payload, list):
        fail(f"{display_path(repo_root / QUEST_DISPATCH_EXAMPLE_PATH, repo_root)} must contain a JSON array")
    quest_ids = sorted(quest_payloads)
    if len(dispatch_payload) != len(quest_ids):
        fail(
            f"{display_path(repo_root / QUEST_DISPATCH_EXAMPLE_PATH, repo_root)} must contain {len(quest_ids)} entries"
        )
    for entry, quest_id in zip(dispatch_payload, quest_ids, strict=True):
        if not isinstance(entry, dict):
            fail(
                f"{display_path(repo_root / QUEST_DISPATCH_EXAMPLE_PATH, repo_root)} entries must be JSON objects"
            )
        requires_artifacts = entry.get("requires_artifacts")
        if not isinstance(requires_artifacts, list) or not requires_artifacts or not all(
            isinstance(item, str) and item for item in requires_artifacts
        ):
            fail(
                f"{display_path(repo_root / QUEST_DISPATCH_EXAMPLE_PATH, repo_root)} entry '{quest_id}' must keep a non-empty requires_artifacts list"
            )
        expected_entry = build_expected_quest_dispatch_entry(
            quest_id,
            quest_payloads[quest_id],
            entry,
            quest_source_paths[quest_id],
        )
        comparable_entry = {key: entry.get(key) for key in expected_entry}
        if comparable_entry != expected_entry:
            fail(
                f"{display_path(repo_root / QUEST_DISPATCH_EXAMPLE_PATH, repo_root)} entry '{quest_id}' must stay aligned with quests/<lane>/<state>/*.yaml"
            )


def main() -> int:
    try:
        validate_questbook_surface(REPO_ROOT)
    except QuestStoreValidationError as exc:
        print(f"[error] {exc}")
        return 1
    print("[ok] validated quest-store surfaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
