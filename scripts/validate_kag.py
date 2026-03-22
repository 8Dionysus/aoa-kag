#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "generated" / "kag_registry.min.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "kag-registry.schema.json"

ALLOWED_STATUS = {"active", "planned", "experimental", "deprecated"}
ALLOWED_SOURCE_CLASS = {"technique_bundle", "skill_bundle", "eval_bundle", "memo_object", "tos_text", "review_surface"}
ALLOWED_DERIVED_KIND = {"section_manifest", "metadata_spine", "relation_view", "provenance_view", "chunk_map", "node_projection", "edge_projection", "retrieval_surface"}
ALLOWED_PROVENANCE = {"strict_source_linked", "bounded_source_linked", "derived_with_handles"}
ALLOWED_FRAMEWORK = {"neutral", "hipporag_ready", "llamaindex_ready", "multi_consumer_ready"}


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(REPO_ROOT).as_posix()}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(REPO_ROOT).as_posix()}: {exc}")


def validate_schema_surface() -> None:
    schema = read_json(SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("schema file must contain a JSON object")
    required_top_level = {"$schema", "$id", "title", "type", "properties", "required"}
    missing = sorted(required_top_level - set(schema))
    if missing:
        fail(f"schema is missing required top-level keys: {', '.join(missing)}")


def validate_registry() -> None:
    payload = read_json(REGISTRY_PATH)
    if not isinstance(payload, dict):
        fail("KAG registry must be a JSON object")

    for key in ("version", "layer", "surfaces"):
        if key not in payload:
            fail(f"KAG registry is missing required key '{key}'")

    if not isinstance(payload["version"], int) or payload["version"] < 1:
        fail("registry 'version' must be an integer >= 1")
    if payload["layer"] != "aoa-kag":
        fail("registry 'layer' must equal 'aoa-kag'")

    surfaces = payload["surfaces"]
    if not isinstance(surfaces, list) or not surfaces:
        fail("registry 'surfaces' must be a non-empty list")

    seen_ids: set[str] = set()
    required_seed = {
        "technique-section-lift",
        "metadata-spine-projection",
        "bounded-relation-view",
        "provenance-note-view",
        "tos-text-chunk-map",
        "cross-source-node-projection",
    }
    seen_names: set[str] = set()

    for index, surface in enumerate(surfaces):
        location = f"surfaces[{index}]"
        if not isinstance(surface, dict):
            fail(f"{location} must be an object")

        for key in (
            "id",
            "name",
            "status",
            "summary",
            "source_class",
            "derived_kind",
            "provenance_mode",
            "normalization_scope",
            "framework_readiness",
            "source_repos",
        ):
            if key not in surface:
                fail(f"{location} is missing required key '{key}'")

        surface_id = surface["id"]
        name = surface["name"]
        status = surface["status"]
        summary = surface["summary"]
        source_class = surface["source_class"]
        derived_kind = surface["derived_kind"]
        provenance_mode = surface["provenance_mode"]
        normalization_scope = surface["normalization_scope"]
        framework_readiness = surface["framework_readiness"]
        source_repos = surface["source_repos"]

        if not isinstance(surface_id, str) or len(surface_id) < 3:
            fail(f"{location}.id must be a string of length >= 3")
        if surface_id in seen_ids:
            fail(f"duplicate KAG surface id in registry: '{surface_id}'")
        seen_ids.add(surface_id)

        if not isinstance(name, str) or len(name) < 3:
            fail(f"{location}.name must be a string of length >= 3")
        seen_names.add(name)
        if status not in ALLOWED_STATUS:
            fail(f"{location}.status '{status}' is not allowed")
        if not isinstance(summary, str) or len(summary) < 10:
            fail(f"{location}.summary must be a string of length >= 10")
        if source_class not in ALLOWED_SOURCE_CLASS:
            fail(f"{location}.source_class '{source_class}' is not allowed")
        if derived_kind not in ALLOWED_DERIVED_KIND:
            fail(f"{location}.derived_kind '{derived_kind}' is not allowed")
        if provenance_mode not in ALLOWED_PROVENANCE:
            fail(f"{location}.provenance_mode '{provenance_mode}' is not allowed")
        if not isinstance(normalization_scope, str) or len(normalization_scope) < 3:
            fail(f"{location}.normalization_scope must be a string of length >= 3")
        if framework_readiness not in ALLOWED_FRAMEWORK:
            fail(f"{location}.framework_readiness '{framework_readiness}' is not allowed")
        if not isinstance(source_repos, list) or not source_repos:
            fail(f"{location}.source_repos must be a non-empty list")
        for repo in source_repos:
            if not isinstance(repo, str) or len(repo) < 2:
                fail(f"{location}.source_repos contains an invalid entry")

    missing_seed = sorted(required_seed - seen_names)
    if missing_seed:
        fail(f"KAG registry is missing required seed surfaces: {', '.join(missing_seed)}")


def main() -> int:
    try:
        validate_schema_surface()
        validate_registry()
    except ValidationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print("[ok] validated KAG registry schema surface")
    print("[ok] validated generated/kag_registry.min.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
