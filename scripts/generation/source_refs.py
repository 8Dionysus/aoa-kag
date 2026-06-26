from __future__ import annotations

from .common import *

def list_family_node_paths(root: Path) -> list[Path]:
    if not root.exists():
        fail(f"missing required family root: {root.as_posix()}")
    if not root.is_dir():
        fail(f"family root must be a directory: {root.as_posix()}")
    node_paths = sorted(root.rglob("node.json"))
    if not node_paths:
        fail(f"family root does not contain any canonical node.json files: {root.as_posix()}")
    return node_paths


def tos_authority_ref_for_path(path: Path) -> str:
    try:
        relative_path = path.resolve().relative_to(TREE_OF_SOPHIA_ROOT.resolve())
    except ValueError:
        fail(f"path must stay inside Tree-of-Sophia: {path.as_posix()}")
    return repo_ref(TOS_REPO, relative_path.as_posix())


def load_tos_route_node_entry(path: Path, *, expected_node_type: str | None = None) -> dict[str, object]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        fail(f"canonical ToS node must be a JSON object: {path.as_posix()}")

    node_id = require_string(payload.get("node_id"), label=f"{path.as_posix()}.node_id")
    node_type = require_string(
        payload.get("node_type"), label=f"{path.as_posix()}.node_type"
    )
    if expected_node_type is not None and node_type != expected_node_type:
        fail(
            f"canonical ToS node {path.as_posix()} must keep node_type "
            f"'{expected_node_type}', got '{node_type}'"
        )

    key_terms = require_string_list(
        payload.get("key_terms"), label=f"{path.as_posix()}.key_terms"
    )
    interpretation_layers = require_string_list(
        payload.get("interpretation_layers"),
        label=f"{path.as_posix()}.interpretation_layers",
    )

    return {
        "node_id": node_id,
        "node_type": node_type,
        "authority_ref": tos_authority_ref_for_path(path),
        "source_anchor": require_string(
            payload.get("source_anchor"), label=f"{path.as_posix()}.source_anchor"
        ),
        "key_terms": key_terms,
        "distilled_thesis": require_string(
            payload.get("distilled_thesis"),
            label=f"{path.as_posix()}.distilled_thesis",
        ),
        "interpretation_layers": interpretation_layers,
    }


def load_tos_route_family_entries(
    root_relative_path: str, *, expected_node_type: str
) -> list[dict[str, object]]:
    root = TREE_OF_SOPHIA_ROOT / root_relative_path
    entries = [
        load_tos_route_node_entry(path, expected_node_type=expected_node_type)
        for path in list_family_node_paths(root)
    ]
    entries.sort(key=lambda entry: require_string(entry.get("node_id"), label="route family node_id"))
    return entries


def load_tos_route_relation_entries(path: Path) -> list[dict[str, object]]:
    rows = read_csv_rows(path)
    if not rows:
        fail(f"canonical ToS route relation pack must not be empty: {path.as_posix()}")

    normalized_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        location = f"{path.as_posix()} row {index + 1}"
        edge_id = require_string(row.get("edge_id"), label=f"{location}.edge_id")
        from_id = require_string(row.get("from_id"), label=f"{location}.from_id")
        to_id = require_string(row.get("to_id"), label=f"{location}.to_id")
        if not from_id.startswith("tos.") or not to_id.startswith("tos."):
            fail(f"{location} must keep canonical tos.* endpoint ids")
        if from_id.startswith("literal.") or to_id.startswith("literal."):
            fail(f"{location} must not include literal residue")

        confidence_text = require_string(
            row.get("confidence"), label=f"{location}.confidence"
        )
        try:
            confidence = int(confidence_text)
        except ValueError as exc:
            fail(f"{location}.confidence must be an integer: {exc}")

        normalized_rows.append(
            {
                "edge_id": edge_id,
                "edge_kind": require_string(
                    row.get("edge_kind"), label=f"{location}.edge_kind"
                ),
                "from_id": from_id,
                "predicate_id": require_string(
                    row.get("predicate_id"), label=f"{location}.predicate_id"
                ),
                "to_id": to_id,
                "layer": require_string(row.get("layer"), label=f"{location}.layer"),
                "anchor_mode": require_string(
                    row.get("anchor_mode"), label=f"{location}.anchor_mode"
                ),
                "anchor_start_secondary": require_optional_string(
                    row.get("anchor_start_secondary"),
                    label=f"{location}.anchor_start_secondary",
                ),
                "anchor_end_secondary": require_optional_string(
                    row.get("anchor_end_secondary"),
                    label=f"{location}.anchor_end_secondary",
                ),
                "anchor_segment_ids": require_string(
                    row.get("anchor_segment_ids"),
                    label=f"{location}.anchor_segment_ids",
                ),
                "witness_scope": require_string(
                    row.get("witness_scope"), label=f"{location}.witness_scope"
                ),
                "connectivity_role": require_string(
                    row.get("connectivity_role"),
                    label=f"{location}.connectivity_role",
                ),
                "confidence": confidence,
                "note": require_optional_string(
                    row.get("note"), label=f"{location}.note"
                ),
            }
        )
    return normalized_rows


def load_tos_tiny_entry_hop_surface(payload: dict[str, object], *, route_label: str) -> str:
    bounded_hop: str | None = None
    if payload.get(TOS_TINY_ENTRY_PRIMARY_HOP_FIELD) is not None:
        bounded_hop = ensure_tos_relative_surface_path(
            payload.get(TOS_TINY_ENTRY_PRIMARY_HOP_FIELD),
            label=f"{route_label}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD}",
        )

    legacy_hop: str | None = None
    if payload.get(TOS_TINY_ENTRY_LEGACY_HOP_FIELD) is not None:
        legacy_hop = ensure_tos_relative_surface_path(
            payload.get(TOS_TINY_ENTRY_LEGACY_HOP_FIELD),
            label=f"{route_label}.{TOS_TINY_ENTRY_LEGACY_HOP_FIELD}",
        )

    if bounded_hop is None and legacy_hop is None:
        fail(
            f"{route_label} must define '{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD}' or "
            f"'{TOS_TINY_ENTRY_LEGACY_HOP_FIELD}'"
        )
    if bounded_hop is not None and legacy_hop is not None and bounded_hop != legacy_hop:
        fail(
            f"{route_label}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD} and "
            f"{route_label}.{TOS_TINY_ENTRY_LEGACY_HOP_FIELD} must resolve to the "
            "same Tree-of-Sophia surface during transition"
        )

    hop_surface = bounded_hop or legacy_hop
    if hop_surface != TOS_TINY_ENTRY_HOP_PATH:
        fail(
            f"{route_label}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD} must stay "
            f"'{TOS_TINY_ENTRY_HOP_PATH}' in the current KAG route scope"
        )
    return hop_surface


def load_tos_tiny_entry_route_payload() -> dict[str, object]:
    route_path = TREE_OF_SOPHIA_ROOT / TOS_TINY_ENTRY_ROUTE_PATH
    payload = read_json(route_path)
    if not isinstance(payload, dict):
        fail("Tree-of-Sophia tiny-entry route must be a JSON object")

    route_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)
    route_id = require_string(payload.get("route_id"), label=f"{route_label}.route_id")
    if route_id != TOS_TINY_ENTRY_ROUTE_ID:
        fail(f"{route_label}.route_id must stay '{TOS_TINY_ENTRY_ROUTE_ID}' in the current KAG route scope")

    root_surface = ensure_tos_relative_surface_path(
        payload.get("root_surface"),
        label=f"{route_label}.root_surface",
    )
    if root_surface != TOS_ROOT_README_PATH:
        fail(f"{route_label}.root_surface must stay '{TOS_ROOT_README_PATH}'")

    require_string(payload.get("node_kind"), label=f"{route_label}.node_kind")
    require_string(payload.get("node_id"), label=f"{route_label}.node_id")

    capsule_surface = ensure_tos_relative_surface_path(
        payload.get("capsule_surface"),
        label=f"{route_label}.capsule_surface",
    )
    if capsule_surface != TOS_TINY_ENTRY_CAPSULE_PATH:
        fail(f"{route_label}.capsule_surface must stay '{TOS_TINY_ENTRY_CAPSULE_PATH}'")

    authority_surface = ensure_tos_relative_surface_path(
        payload.get("authority_surface"),
        label=f"{route_label}.authority_surface",
    )
    if authority_surface != TOS_TINY_ENTRY_AUTHORITY_PATH:
        fail(f"{route_label}.authority_surface must stay '{TOS_TINY_ENTRY_AUTHORITY_PATH}'")

    load_tos_tiny_entry_hop_surface(payload, route_label=route_label)

    fallback = ensure_tos_relative_surface_path(
        payload.get("fallback"),
        label=f"{route_label}.fallback",
    )
    if fallback != TOS_TINY_ENTRY_FALLBACK_PATH:
        fail(f"{route_label}.fallback must stay '{TOS_TINY_ENTRY_FALLBACK_PATH}'")

    boundary = require_string(
        payload.get("non_identity_boundary"),
        label=f"{route_label}.non_identity_boundary",
    )
    if "aoa-kag" not in boundary or "aoa-routing" not in boundary:
        fail(
            f"{route_label}.non_identity_boundary must explicitly keep aoa-kag and aoa-routing downstream"
        )

    return payload


def load_tos_source_node_payload() -> dict[str, object]:
    source_node_path = TREE_OF_SOPHIA_ROOT / TOS_TINY_ENTRY_AUTHORITY_PATH
    payload = read_json(source_node_path)
    if not isinstance(payload, dict):
        fail("Tree-of-Sophia source node authority surface must be a JSON object")

    source_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_AUTHORITY_PATH)
    route_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)
    route_payload = load_tos_tiny_entry_route_payload()
    expected_node_id = require_string(
        route_payload.get("node_id"),
        label=f"{route_label}.node_id",
    )

    node_id = require_string(payload.get("node_id"), label=f"{source_label}.node_id")
    if node_id != expected_node_id:
        fail(f"{source_label}.node_id must stay aligned with {route_label}.node_id")

    node_type = require_string(
        payload.get("node_type"),
        label=f"{source_label}.node_type",
    )
    if node_type != "source":
        fail(f"{source_label}.node_type must stay 'source' in the current KAG route scope")

    require_string(
        payload.get("source_anchor"),
        label=f"{source_label}.source_anchor",
    )

    interpretation_layers = payload.get("interpretation_layers")
    if not isinstance(interpretation_layers, list) or not interpretation_layers:
        fail(f"{source_label}.interpretation_layers must be a non-empty list")
    for index, interpretation_layer in enumerate(interpretation_layers):
        if not isinstance(interpretation_layer, str) or not interpretation_layer:
            fail(
                f"{source_label}.interpretation_layers[{index}] must be a non-empty string"
            )

    language_witnesses = payload.get("language_witnesses")
    if not isinstance(language_witnesses, list) or not language_witnesses:
        fail(f"{source_label}.language_witnesses must be a non-empty list")

    translation_tensions = payload.get("translation_tensions", [])
    if translation_tensions is not None and not isinstance(translation_tensions, list):
        fail(f"{source_label}.translation_tensions must be a list when present")

    return payload


def load_source_owned_export_dependencies(
) -> tuple[dict[str, dict[str, object]], dict[tuple[str, str], dict[str, object]]]:
    payload = read_json(SOURCE_OWNED_EXPORT_DEPENDENCIES_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("source-owned export dependency manifest must be a JSON object")

    manifest_version = payload.get("manifest_version")
    contract_type = payload.get("contract_type")
    dependencies = payload.get("dependencies")
    if manifest_version != 1:
        fail("source-owned export dependency manifest manifest_version must equal 1")
    if contract_type != "source_owned_export_dependencies":
        fail(
            "source-owned export dependency manifest contract_type must equal "
            "'source_owned_export_dependencies'"
        )
    if not isinstance(dependencies, list) or not dependencies:
        fail("source-owned export dependency manifest must declare dependencies")

    dependencies_by_id: dict[str, dict[str, object]] = {}
    dependencies_by_source: dict[tuple[str, str], dict[str, object]] = {}
    for index, dependency in enumerate(dependencies):
        location = f"source-owned export dependency manifest dependencies[{index}]"
        if not isinstance(dependency, dict):
            fail(f"{location} must be an object")

        dependency_id = require_string(
            dependency.get("dependency_id"),
            label=f"{location}.dependency_id",
        )
        repo = require_string(dependency.get("repo"), label=f"{location}.repo")
        path = ensure_repo_relative_path(dependency.get("path"), label=f"{location}.path")
        expected_owner_repo = require_string(
            dependency.get("expected_owner_repo"),
            label=f"{location}.expected_owner_repo",
        )
        expected_kind = require_string(
            dependency.get("expected_kind"),
            label=f"{location}.expected_kind",
        )
        expected_object_id = require_string(
            dependency.get("expected_object_id"),
            label=f"{location}.expected_object_id",
        )
        required_fields = dependency.get("required_fields")
        if not isinstance(required_fields, list) or not required_fields:
            fail(f"{location}.required_fields must be a non-empty list")
        normalized_required_fields: list[str] = []
        for field_index, field_name in enumerate(required_fields):
            normalized_required_fields.append(
                require_string(
                    field_name,
                    label=f"{location}.required_fields[{field_index}]",
                )
            )
        if len(set(normalized_required_fields)) != len(normalized_required_fields):
            fail(f"{location}.required_fields must not contain duplicates")

        entry_surface = dependency.get("entry_surface")
        if not isinstance(entry_surface, dict):
            fail(f"{location}.entry_surface must be an object")
        entry_surface_repo = require_string(
            entry_surface.get("repo"),
            label=f"{location}.entry_surface.repo",
        )
        entry_surface_path = ensure_repo_relative_path(
            entry_surface.get("path"),
            label=f"{location}.entry_surface.path",
        )
        entry_match_key = require_string(
            entry_surface.get("match_key"),
            label=f"{location}.entry_surface.match_key",
        )
        entry_match_value = require_string(
            entry_surface.get("match_value"),
            label=f"{location}.entry_surface.match_value",
        )
        if entry_match_value != expected_object_id:
            fail(
                f"{location}.entry_surface.match_value must equal "
                f"{location}.expected_object_id"
            )

        consumed_by = dependency.get("consumed_by")
        if not isinstance(consumed_by, list):
            fail(f"{location}.consumed_by must be a list")
        normalized_consumed_by: list[str] = []
        for consumer_index, consumer_surface_id in enumerate(consumed_by):
            normalized_consumed_by.append(
                require_string(
                    consumer_surface_id,
                    label=f"{location}.consumed_by[{consumer_index}]",
                )
            )
        if len(set(normalized_consumed_by)) != len(normalized_consumed_by):
            fail(f"{location}.consumed_by must not contain duplicates")

        if expected_owner_repo != repo:
            fail(
                f"{location}.expected_owner_repo must equal {location}.repo in the "
                "current source-owned export contract"
            )
        if entry_surface_repo != expected_owner_repo:
            fail(
                f"{location}.entry_surface.repo must equal {location}.expected_owner_repo"
            )

        if dependency_id in dependencies_by_id:
            fail(f"{location}.dependency_id '{dependency_id}' is duplicated")
        source_key = (repo, path)
        if source_key in dependencies_by_source:
            fail(
                f"{location} duplicates repo/path dependency target "
                f"'{repo_ref(repo, path)}'"
            )

        if not resolve_repo_path(repo, path).exists():
            fail(f"{location}.path target is missing: {repo_ref(repo, path)}")
        if not resolve_repo_path(entry_surface_repo, entry_surface_path).exists():
            fail(
                f"{location}.entry_surface.path target is missing: "
                f"{repo_ref(entry_surface_repo, entry_surface_path)}"
            )

        normalized_dependency = {
            "dependency_id": dependency_id,
            "repo": repo,
            "path": path,
            "expected_owner_repo": expected_owner_repo,
            "expected_kind": expected_kind,
            "expected_object_id": expected_object_id,
            "required_fields": normalized_required_fields,
            "entry_surface": {
                "repo": entry_surface_repo,
                "path": entry_surface_path,
                "match_key": entry_match_key,
                "match_value": entry_match_value,
            },
            "consumed_by": normalized_consumed_by,
        }
        dependencies_by_id[dependency_id] = normalized_dependency
        dependencies_by_source[source_key] = normalized_dependency

    return dependencies_by_id, dependencies_by_source


def dependency_for_export_target(
    repo: str,
    path: str,
    *,
    consumer_surface_id: str | None = None,
) -> dict[str, object]:
    _, dependencies_by_source = load_source_owned_export_dependencies()
    source_key = (repo, path)
    dependency = dependencies_by_source.get(source_key)
    if dependency is None:
        label = (
            f"{consumer_surface_id} source input" if consumer_surface_id else "export target"
        )
        fail(
            f"{label} '{repo_ref(repo, path)}' "
            "must map to a declared source-owned export dependency"
        )

    if consumer_surface_id is None:
        return dependency

    dependency_id = require_string(
        dependency.get("dependency_id"),
        label=f"{consumer_surface_id} dependency_id",
    )
    consumed_by = dependency.get("consumed_by")
    if not isinstance(consumed_by, list) or consumer_surface_id not in consumed_by:
        fail(
            f"source-owned export dependency '{dependency_id}' must declare "
            f"'{consumer_surface_id}' in consumed_by"
        )
    return dependency


def dependency_for_source_input(
    source_input: dict[str, str],
    *,
    consumer_surface_id: str,
) -> dict[str, object]:
    return dependency_for_export_target(
        source_input["repo"],
        source_input["path"],
        consumer_surface_id=consumer_surface_id,
    )


def load_federation_export_payload(
    source_input: dict[str, str],
    *,
    dependency: dict[str, object],
    consumer_surface_id: str,
) -> dict[str, object]:
    dependency_id = require_string(
        dependency.get("dependency_id"),
        label=f"{consumer_surface_id} dependency_id",
    )
    expected_repo = require_string(
        dependency.get("expected_owner_repo"),
        label=f"{dependency_id}.expected_owner_repo",
    )
    expected_kind = require_string(
        dependency.get("expected_kind"),
        label=f"{dependency_id}.expected_kind",
    )
    expected_object_id = require_string(
        dependency.get("expected_object_id"),
        label=f"{dependency_id}.expected_object_id",
    )
    dependency_repo = require_string(dependency.get("repo"), label=f"{dependency_id}.repo")
    dependency_path = ensure_repo_relative_path(
        dependency.get("path"),
        label=f"{dependency_id}.path",
    )
    required_fields = dependency.get("required_fields")
    dependency_entry_surface = dependency.get("entry_surface")
    if not isinstance(required_fields, list) or not required_fields:
        fail(f"source-owned export dependency '{dependency_id}' must keep required_fields")
    if not isinstance(dependency_entry_surface, dict):
        fail(f"source-owned export dependency '{dependency_id}' must keep entry_surface")

    if (
        source_input["repo"] != dependency_repo
        or source_input["path"] != dependency_path
    ):
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"must stay aligned with '{manifest_input_ref(source_input)}'"
        )

    payload = read_json(manifest_input_path(source_input))
    if not isinstance(payload, dict):
        fail(f"{manifest_input_ref(source_input)} must be a JSON object")

    for index, key in enumerate(required_fields):
        field_name = require_string(
            key,
            label=f"{dependency_id}.required_fields[{index}]",
        )
        if field_name not in payload:
            fail(
                f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
                f"is missing required key '{field_name}' in {manifest_input_ref(source_input)}"
            )

    owner_repo = require_string(
        payload.get("owner_repo"),
        label=f"{manifest_input_ref(source_input)}.owner_repo",
    )
    kind = require_string(
        payload.get("kind"),
        label=f"{manifest_input_ref(source_input)}.kind",
    )
    object_id = require_string(
        payload.get("object_id"),
        label=f"{manifest_input_ref(source_input)}.object_id",
    )
    if owner_repo != expected_repo:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.owner_repo to equal "
            f"'{expected_repo}'"
        )
    if kind != expected_kind:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.kind to equal '{expected_kind}'"
        )
    if object_id != expected_object_id:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.object_id to equal "
            f"'{expected_object_id}'"
        )

    source_inputs = payload.get("source_inputs")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail(f"{manifest_input_ref(source_input)}.source_inputs must be a non-empty list")
    primary_count = 0
    primary_repo: str | None = None
    for index, export_source_input in enumerate(source_inputs):
        location = f"{manifest_input_ref(source_input)}.source_inputs[{index}]"
        if not isinstance(export_source_input, dict):
            fail(f"{location} must be an object")
        repo = require_string(export_source_input.get("repo"), label=f"{location}.repo")
        require_string(
            export_source_input.get("source_class"),
            label=f"{location}.source_class",
        )
        role = require_string(export_source_input.get("role"), label=f"{location}.role")
        if role == "primary":
            primary_count += 1
            primary_repo = repo
        if role not in {"primary", "supporting"}:
            fail(f"{location}.role must be 'primary' or 'supporting'")
    if primary_count != 1:
        fail(f"{manifest_input_ref(source_input)}.source_inputs must contain exactly one primary input")
    if primary_repo != expected_repo:
        fail(
            f"{manifest_input_ref(source_input)}.source_inputs primary repo must equal "
            f"'{expected_repo}'"
        )

    payload_entry_surface = payload.get("entry_surface")
    if not isinstance(payload_entry_surface, dict):
        fail(f"{manifest_input_ref(source_input)}.entry_surface must be an object")
    entry_repo = require_string(
        payload_entry_surface.get("repo"),
        label=f"{manifest_input_ref(source_input)}.entry_surface.repo",
    )
    entry_path = require_string(
        payload_entry_surface.get("path"),
        label=f"{manifest_input_ref(source_input)}.entry_surface.path",
    )
    match_key = require_string(
        payload_entry_surface.get("match_key"),
        label=f"{manifest_input_ref(source_input)}.entry_surface.match_key",
    )
    match_value = require_string(
        payload_entry_surface.get("match_value"),
        label=f"{manifest_input_ref(source_input)}.entry_surface.match_value",
    )
    dependency_entry_repo = require_string(
        dependency_entry_surface.get("repo"),
        label=f"{dependency_id}.entry_surface.repo",
    )
    dependency_entry_path = ensure_repo_relative_path(
        dependency_entry_surface.get("path"),
        label=f"{dependency_id}.entry_surface.path",
    )
    dependency_match_key = require_string(
        dependency_entry_surface.get("match_key"),
        label=f"{dependency_id}.entry_surface.match_key",
    )
    dependency_match_value = require_string(
        dependency_entry_surface.get("match_value"),
        label=f"{dependency_id}.entry_surface.match_value",
    )
    if entry_repo != dependency_entry_repo:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.entry_surface.repo to equal "
            f"'{dependency_entry_repo}'"
        )
    if not path_matches_current_or_alias(entry_repo, dependency_entry_path, entry_path):
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.entry_surface.path to equal "
            f"'{dependency_entry_path}'"
        )
    if match_key != dependency_match_key:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.entry_surface.match_key to "
            f"equal '{dependency_match_key}'"
        )
    if match_value != dependency_match_value:
        fail(
            f"source-owned export dependency '{dependency_id}' for {consumer_surface_id} "
            f"requires {manifest_input_ref(source_input)}.entry_surface.match_value to "
            f"equal '{dependency_match_value}'"
        )
    resolve_repo_path(entry_repo, entry_path)

    section_handles = payload.get("section_handles")
    if not isinstance(section_handles, list) or not section_handles:
        fail(f"{manifest_input_ref(source_input)}.section_handles must be a non-empty list")
    direct_relations = payload.get("direct_relations")
    if not isinstance(direct_relations, list):
        fail(f"{manifest_input_ref(source_input)}.direct_relations must be a list")

    require_string(
        payload.get("summary_50"),
        label=f"{manifest_input_ref(source_input)}.summary_50",
    )
    require_string(
        payload.get("summary_200"),
        label=f"{manifest_input_ref(source_input)}.summary_200",
    )
    require_string(
        payload.get("primary_question"),
        label=f"{manifest_input_ref(source_input)}.primary_question",
    )
    require_string(
        payload.get("provenance_note"),
        label=f"{manifest_input_ref(source_input)}.provenance_note",
    )
    require_string(
        payload.get("non_identity_boundary"),
        label=f"{manifest_input_ref(source_input)}.non_identity_boundary",
    )

    return payload
