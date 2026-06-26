from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_source_owned_export_dependency_manifest(
    surfaces_by_id: dict[str, dict[str, object]],
) -> dict[tuple[str, str], dict[str, object]]:
    payload = read_json(SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("source-owned export dependency manifest must be a JSON object")

    for key in ("manifest_version", "contract_type", "dependencies"):
        if key not in payload:
            fail(f"source-owned export dependency manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("source-owned export dependency manifest manifest_version must equal 1")
    if payload["contract_type"] != "source_owned_export_dependencies":
        fail(
            "source-owned export dependency manifest contract_type must equal "
            "'source_owned_export_dependencies'"
        )

    dependencies = payload["dependencies"]
    if not isinstance(dependencies, list) or not dependencies:
        fail("source-owned export dependency manifest dependencies must be a non-empty list")

    dependencies_by_source: dict[tuple[str, str], dict[str, object]] = {}
    seen_dependency_ids: set[str] = set()
    for index, dependency in enumerate(dependencies):
        location = f"source-owned export dependency manifest dependencies[{index}]"
        if not isinstance(dependency, dict):
            fail(f"{location} must be an object")

        dependency_id = dependency.get("dependency_id")
        repo = dependency.get("repo")
        path = dependency.get("path")
        expected_owner_repo = dependency.get("expected_owner_repo")
        expected_kind = dependency.get("expected_kind")
        expected_object_id = dependency.get("expected_object_id")
        required_fields = dependency.get("required_fields")
        entry_surface = dependency.get("entry_surface")
        consumed_by = dependency.get("consumed_by")
        if not all(
            isinstance(value, str) and value
            for value in (
                dependency_id,
                repo,
                path,
                expected_owner_repo,
                expected_kind,
                expected_object_id,
            )
        ):
            fail(
                f"{location} must keep dependency_id, repo, path, expected_owner_repo, "
                "expected_kind, and expected_object_id"
            )
        if dependency_id in seen_dependency_ids:
            fail(f"{location}.dependency_id '{dependency_id}' is duplicated")
        seen_dependency_ids.add(dependency_id)
        if repo != expected_owner_repo:
            fail(f"{location}.expected_owner_repo must equal {location}.repo")
        if not isinstance(required_fields, list) or not required_fields:
            fail(f"{location}.required_fields must be a non-empty list")
        normalized_required_fields: list[str] = []
        for field_index, field_name in enumerate(required_fields):
            if not isinstance(field_name, str) or not field_name:
                fail(f"{location}.required_fields[{field_index}] must be a non-empty string")
            normalized_required_fields.append(field_name)
        if len(set(normalized_required_fields)) != len(normalized_required_fields):
            fail(f"{location}.required_fields must not contain duplicates")
        if not isinstance(entry_surface, dict):
            fail(f"{location}.entry_surface must be an object")
        entry_surface_repo = entry_surface.get("repo")
        entry_surface_path = entry_surface.get("path")
        entry_match_key = entry_surface.get("match_key")
        entry_match_value = entry_surface.get("match_value")
        if not all(
            isinstance(value, str) and value
            for value in (
                entry_surface_repo,
                entry_surface_path,
                entry_match_key,
                entry_match_value,
            )
        ):
            fail(
                f"{location}.entry_surface must keep repo, path, match_key, and match_value"
            )
        if entry_surface_repo != expected_owner_repo:
            fail(f"{location}.entry_surface.repo must equal {location}.expected_owner_repo")
        if entry_match_value != expected_object_id:
            fail(
                f"{location}.entry_surface.match_value must equal "
                f"{location}.expected_object_id"
            )
        if not isinstance(consumed_by, list):
            fail(f"{location}.consumed_by must be a list")
        normalized_consumed_by: list[str] = []
        for consumer_index, consumer_surface_id in enumerate(consumed_by):
            if not isinstance(consumer_surface_id, str) or not consumer_surface_id:
                fail(f"{location}.consumed_by[{consumer_index}] must be a non-empty string")
            if consumer_surface_id not in surfaces_by_id:
                fail(
                    f"{location}.consumed_by[{consumer_index}] references unknown "
                    f"registry surface '{consumer_surface_id}'"
                )
            normalized_consumed_by.append(consumer_surface_id)
        if len(set(normalized_consumed_by)) != len(normalized_consumed_by):
            fail(f"{location}.consumed_by must not contain duplicates")

        source_key = (repo, path)
        if source_key in dependencies_by_source:
            fail(f"{location} duplicates repo/path target '{repo_ref(repo, path)}'")

        export_path = resolve_known_ref(repo_ref(repo, path), label=location)
        entry_surface_ref = repo_ref(entry_surface_repo, entry_surface_path)
        resolve_known_ref(entry_surface_ref, label=f"{location}.entry_surface")
        export_payload = read_json(export_path)
        if not isinstance(export_payload, dict):
            fail(f"{location} target export must be a JSON object")
        for field_name in normalized_required_fields:
            if field_name not in export_payload:
                fail(
                    f"{location} requires target export '{repo_ref(repo, path)}' to keep "
                    f"'{field_name}'"
                )
        if export_payload.get("owner_repo") != expected_owner_repo:
            fail(f"{location} target export owner_repo must equal '{expected_owner_repo}'")
        if export_payload.get("kind") != expected_kind:
            fail(f"{location} target export kind must equal '{expected_kind}'")
        if export_payload.get("object_id") != expected_object_id:
            fail(f"{location} target export object_id must equal '{expected_object_id}'")

        export_source_inputs = export_payload.get("source_inputs")
        if not isinstance(export_source_inputs, list) or not export_source_inputs:
            fail(f"{location} target export source_inputs must be a non-empty list")
        primary_count = 0
        for source_input_index, source_input in enumerate(export_source_inputs):
            source_location = f"{location} target export source_inputs[{source_input_index}]"
            if not isinstance(source_input, dict):
                fail(f"{source_location} must be an object")
            source_repo = source_input.get("repo")
            source_role = source_input.get("role")
            source_class = source_input.get("source_class")
            if not all(
                isinstance(value, str) and value
                for value in (source_repo, source_role, source_class)
            ):
                fail(f"{source_location} must keep repo, role, and source_class")
            if source_role == "primary":
                primary_count += 1
                if source_repo != expected_owner_repo:
                    fail(f"{source_location}.repo must equal '{expected_owner_repo}'")
            elif source_role != "supporting":
                fail(f"{source_location}.role must be 'primary' or 'supporting'")
        if primary_count != 1:
            fail(f"{location} target export must contain exactly one primary source input")

        export_entry_surface = export_payload.get("entry_surface")
        if not isinstance(export_entry_surface, dict):
            fail(f"{location} target export entry_surface must be an object")
        if export_entry_surface.get("repo") != entry_surface_repo:
            fail(f"{location} target export entry_surface.repo must equal '{entry_surface_repo}'")
        if not path_matches_current_or_alias(
            entry_surface_repo,
            entry_surface_path,
            export_entry_surface.get("path"),
        ):
            fail(f"{location} target export entry_surface.path must equal '{entry_surface_path}'")
        if export_entry_surface.get("match_key") != entry_match_key:
            fail(
                f"{location} target export entry_surface.match_key must equal "
                f"'{entry_match_key}'"
            )
        if export_entry_surface.get("match_value") != entry_match_value:
            fail(
                f"{location} target export entry_surface.match_value must equal "
                f"'{entry_match_value}'"
            )

        dependencies_by_source[source_key] = {
            "dependency_id": dependency_id,
            "repo": repo,
            "path": path,
            "expected_owner_repo": expected_owner_repo,
            "consumed_by": normalized_consumed_by,
        }

    return dependencies_by_source
