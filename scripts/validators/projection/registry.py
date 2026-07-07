from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

EXPECTED_MCP_RESOURCE_TEMPLATES = {
    "aoa-kag://providers/{repo}/manifest": {
        "source": "{repo}/kag/manifest.json",
    },
    "aoa-kag://providers/{repo}/records/{record_class}": {
        "source": "{repo}/kag/{record_class_directory}/",
        "record_class_directory_map": {
            "node": "nodes",
            "edge": "edges",
            "index": "indexes",
            "projection": "projections",
            "receipt": "receipts",
        },
    },
    "aoa-kag://providers/{repo}/generation": {
        "source": (
            "aoa-kag/generated/local_kag_provider_map.min.json"
            "#/provider_generation_profiles/{repo}"
        ),
    },
    "aoa-kag://providers/{repo}/source-index": {
        "source": (
            "aoa-kag/generated/local_kag_provider_map.min.json"
            "#/provider_repo_local_indexes/{repo}/source_index_ref"
        ),
        "fallback_source": (
            "aoa-kag/generated/local_kag_provider_map.min.json"
            "#/provider_repo_local_indexes/{repo}/index_files"
        ),
    },
    "aoa-kag://providers/{repo}/repo-local-index": {
        "source": (
            "aoa-kag/generated/local_kag_provider_map.min.json"
            "#/provider_repo_local_indexes/{repo}"
        ),
    },
    "aoa-kag://registry/provider-map": {
        "source": "aoa-kag/generated/local_kag_provider_map.min.json",
    },
    "aoa-kag://coverage/repo-local-source-indexes": {
        "source": "aoa-kag/generated/repo_local_kag_coverage.min.json",
    },
    "aoa-kag://readiness/os-surfaces": {
        "source": "aoa-kag/manifests/local_kag_readiness.json",
    },
}

REQUIRED_MCP_TOOLS = {
    "provider_lookup",
    "provider_status",
    "generation_route_lookup",
    "source_index_lookup",
    "repo_local_coverage_status",
    "freshness_check",
    "source_return_lookup",
    "registry_slice",
    "composition_slice",
    "validation_status",
}

REQUIRED_MCP_PROMPTS = {
    "bounded_provider_query",
    "source_return_summary",
    "repo_source_surface_brief",
    "cross_repo_relation_preview",
    "runtime_handoff_brief",
}

REQUIRED_ROOT_BOUNDARY_KINDS = {
    "provider_home",
    "source_return",
    "runtime_owner",
}


def validate_local_kag_provider_map_payload(
    payload: object,
    *,
    label: str,
) -> dict[str, object]:
    schema = read_json(LOCAL_KAG_PROVIDER_MAP_SCHEMA_PATH)
    if not isinstance(schema, dict):
        fail("local KAG provider map schema must be a JSON object")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = format_schema_path(first.path)
        suffix = f" at {path}" if path else ""
        fail(f"{label} does not match local KAG provider map schema{suffix}: {first.message}")
    if not isinstance(payload, dict):
        fail(f"{label} must be a JSON object")
    _validate_provider_map_semantics(payload, label=label)
    return payload


def _validate_provider_map_semantics(payload: dict[str, object], *, label: str) -> None:
    providers = _object_list(payload.get("providers"), f"{label}.providers")
    provider_repos = [str(provider.get("repo")) for provider in providers]
    if len(provider_repos) != len(set(provider_repos)):
        fail(f"{label}.providers must keep unique repo entries")

    provider_status_counts = _string_int_map(
        payload.get("provider_status_counts"),
        f"{label}.provider_status_counts",
    )
    actual_provider_status_counts: dict[str, int] = {}
    for provider in providers:
        status = str(provider.get("provider_status"))
        actual_provider_status_counts[status] = actual_provider_status_counts.get(status, 0) + 1
    if provider_status_counts != actual_provider_status_counts:
        fail(f"{label}.provider_status_counts must match provider rows")

    profile_map = _object_map(
        payload.get("provider_generation_profiles"),
        f"{label}.provider_generation_profiles",
    )
    index_map = _object_map(
        payload.get("provider_repo_local_indexes"),
        f"{label}.provider_repo_local_indexes",
    )
    provider_repo_set = set(provider_repos)
    if set(profile_map) != provider_repo_set:
        fail(f"{label}.provider_generation_profiles must cover provider repos exactly")
    if set(index_map) != provider_repo_set:
        fail(f"{label}.provider_repo_local_indexes must cover provider repos exactly")

    for provider in providers:
        repo = str(provider["repo"])
        if provider.get("generation_profile") != profile_map[repo]:
            fail(f"{label}.providers[{repo}].generation_profile must match provider_generation_profiles")
        if provider.get("repo_local_index") != index_map[repo]:
            fail(f"{label}.providers[{repo}].repo_local_index must match provider_repo_local_indexes")

    os_surfaces = _object_list(payload.get("os_surfaces"), f"{label}.os_surfaces")
    readiness = _object_value(payload.get("generation_readiness"), f"{label}.generation_readiness")
    os_surface_status_counts = _string_int_map(
        readiness.get("os_surface_status_counts"),
        f"{label}.generation_readiness.os_surface_status_counts",
    )
    os_surface_ids_by_status = _string_list_map(
        readiness.get("os_surface_ids_by_status"),
        f"{label}.generation_readiness.os_surface_ids_by_status",
    )
    actual_os_counts: dict[str, int] = {}
    actual_os_ids: dict[str, list[str]] = {}
    for surface in os_surfaces:
        surface_id = str(surface.get("surface_id"))
        status = str(surface.get("provider_status"))
        actual_os_counts[status] = actual_os_counts.get(status, 0) + 1
        actual_os_ids.setdefault(status, []).append(surface_id)
    actual_os_ids = {
        status: sorted(surface_ids)
        for status, surface_ids in actual_os_ids.items()
    }
    if os_surface_status_counts != actual_os_counts:
        fail(f"{label}.generation_readiness.os_surface_status_counts must match os_surfaces")
    if os_surface_ids_by_status != actual_os_ids:
        fail(f"{label}.generation_readiness.os_surface_ids_by_status must match os_surfaces")

    _validate_mcp_handoff(
        _object_value(payload.get("mcp_handoff"), f"{label}.mcp_handoff"),
        label=f"{label}.mcp_handoff",
    )


def _validate_mcp_handoff(handoff: dict[str, object], *, label: str) -> None:
    if handoff.get("service_route") != "abyss-stack/mcp/services/aoa-kag-mcp":
        fail(f"{label}.service_route must point to the aoa-kag MCP service route")
    if handoff.get("resource_uri_scheme") != "aoa-kag://{scope}/{identifier}":
        fail(f"{label}.resource_uri_scheme must keep the aoa-kag URI scheme")

    templates = _object_list(handoff.get("resource_templates"), f"{label}.resource_templates")
    by_uri: dict[str, dict[str, object]] = {}
    for template in templates:
        uri_template = str(template.get("uri_template"))
        if uri_template in by_uri:
            fail(f"{label}.resource_templates must keep unique uri_template values")
        by_uri[uri_template] = template

    missing_templates = sorted(set(EXPECTED_MCP_RESOURCE_TEMPLATES) - set(by_uri))
    if missing_templates:
        fail(f"{label} missing required MCP resource templates: {', '.join(missing_templates)}")
    extra_templates = sorted(set(by_uri) - set(EXPECTED_MCP_RESOURCE_TEMPLATES))
    if extra_templates:
        fail(f"{label} carries unknown MCP resource templates: {', '.join(extra_templates)}")

    for uri_template, expected_fields in EXPECTED_MCP_RESOURCE_TEMPLATES.items():
        template = by_uri[uri_template]
        for key, expected_value in expected_fields.items():
            if template.get(key) != expected_value:
                fail(f"{label} template {uri_template} must keep {key}")

    root_boundaries = _object_list(handoff.get("root_boundaries"), f"{label}.root_boundaries")
    root_kinds = {str(boundary.get("root_kind")) for boundary in root_boundaries}
    if root_kinds != REQUIRED_ROOT_BOUNDARY_KINDS:
        fail(f"{label}.root_boundaries must cover provider_home, source_return, and runtime_owner")

    tools = set(_string_list(handoff.get("tools"), f"{label}.tools"))
    if tools != REQUIRED_MCP_TOOLS:
        fail(f"{label}.tools must match the provider-map handoff tool contract")
    prompts = set(_string_list(handoff.get("prompts"), f"{label}.prompts"))
    if prompts != REQUIRED_MCP_PROMPTS:
        fail(f"{label}.prompts must match the provider-map handoff prompt contract")


def _object_value(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def _object_list(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, list) or not value:
        fail(f"{label} must be a non-empty list")
    result: list[dict[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            fail(f"{label}[{index}] must be a JSON object")
        result.append(item)
    return result


def _object_map(value: object, label: str) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    result: dict[str, dict[str, object]] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            fail(f"{label} keys must be strings")
        if not isinstance(item, dict):
            fail(f"{label}.{key} must be a JSON object")
        result[key] = item
    return result


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        fail(f"{label} must be a non-empty list")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            fail(f"{label}[{index}] must be a non-empty string")
        result.append(item)
    if len(result) != len(set(result)):
        fail(f"{label} must keep unique entries")
    return result


def _string_int_map(value: object, label: str) -> dict[str, int]:
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    result: dict[str, int] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            fail(f"{label} keys must be strings")
        if not isinstance(item, int):
            fail(f"{label}.{key} must be an integer")
        result[key] = item
    return result


def _string_list_map(value: object, label: str) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    result: dict[str, list[str]] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            fail(f"{label} keys must be strings")
        result[key] = sorted(_string_list(item, f"{label}.{key}"))
    return result


def validate_registry_payload(
    payload: object,
    *,
    label: str,
) -> dict[str, dict[str, object]]:
    if not isinstance(payload, dict):
        fail(f"{label} must be a JSON object")

    for key in ("version", "layer", "artifact_identity", "surfaces"):
        if key not in payload:
            fail(f"{label} is missing required key '{key}'")

    if not isinstance(payload["version"], int) or payload["version"] < 1:
        fail(f"{label} 'version' must be an integer >= 1")
    if payload["layer"] != "aoa-kag":
        fail(f"{label} 'layer' must equal 'aoa-kag'")
    if payload["artifact_identity"] != KAG_REGISTRY_ARTIFACT_IDENTITY:
        fail(f"{label} artifact_identity must match KAG_REGISTRY_ARTIFACT_IDENTITY")

    surfaces = payload["surfaces"]
    if not isinstance(surfaces, list) or not surfaces:
        fail(f"{label} 'surfaces' must be a non-empty list")

    seen_ids: set[str] = set()
    required_surfaces = {
        "technique-section-lift",
        "metadata-spine-projection",
        "bounded-relation-view",
        "provenance-note-view",
        "tos-text-chunk-map",
        "cross-source-node-projection",
        "tos-retrieval-axis-surface",
        "counterpart-edge-view",
        "federation-readiness-spine",
    }
    seen_names: set[str] = set()
    surfaces_by_id: dict[str, dict[str, object]] = {}

    for index, surface in enumerate(surfaces):
        location = f"{label} surfaces[{index}]"
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
        source_inputs = surface.get("source_inputs")

        if not isinstance(surface_id, str) or len(surface_id) < 3:
            fail(f"{location}.id must be a string of length >= 3")
        if surface_id in seen_ids:
            fail(f"duplicate KAG surface id in {label}: '{surface_id}'")
        seen_ids.add(surface_id)
        surfaces_by_id[surface_id] = surface

        if not isinstance(name, str) or len(name) < 3:
            fail(f"{location}.name must be a string of length >= 3")
        if name in seen_names:
            fail(f"duplicate KAG surface name in {label}: '{name}'")
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

        if source_inputs is not None:
            if not isinstance(source_inputs, list) or not source_inputs:
                fail(f"{location}.source_inputs must be a non-empty list when present")

            primary_count = 0
            input_repos: set[str] = set()
            for input_index, source_input in enumerate(source_inputs):
                input_location = f"{location}.source_inputs[{input_index}]"
                if not isinstance(source_input, dict):
                    fail(f"{input_location} must be an object")
                for key in ("repo", "source_class", "role"):
                    if key not in source_input:
                        fail(f"{input_location} is missing required key '{key}'")

                input_repo = source_input["repo"]
                input_source_class = source_input["source_class"]
                input_role = source_input["role"]

                if not isinstance(input_repo, str) or len(input_repo) < 2:
                    fail(f"{input_location}.repo must be a string of length >= 2")
                if input_repo not in source_repos:
                    fail(f"{input_location}.repo '{input_repo}' must also appear in source_repos")
                if input_repo in input_repos:
                    fail(f"{input_location}.repo '{input_repo}' is duplicated")
                input_repos.add(input_repo)

                if input_source_class not in ALLOWED_SOURCE_CLASS:
                    fail(f"{input_location}.source_class '{input_source_class}' is not allowed")
                if input_role not in ALLOWED_SOURCE_INPUT_ROLE:
                    fail(f"{input_location}.role '{input_role}' is not allowed")
                if input_role == "primary":
                    primary_count += 1
                    if input_source_class != source_class:
                        fail(
                            f"{input_location}.source_class must match top-level source_class for the primary input"
                        )

            if primary_count != 1:
                fail(f"{location}.source_inputs must contain exactly one primary input")

        if len(source_repos) > 1 and source_inputs is None:
            fail(f"{location}.source_inputs is required when more than one source repo is declared")

    missing_required_surfaces = sorted(required_surfaces - seen_names)
    if missing_required_surfaces:
        fail(
            f"{label} is missing required registry surfaces: "
            f"{', '.join(missing_required_surfaces)}"
        )
    validate_special_registry_surfaces(surfaces_by_id, label=label)
    return surfaces_by_id

def validate_special_registry_surfaces(
    surfaces_by_id: dict[str, dict[str, object]],
    *,
    label: str,
) -> None:
    surface_0005 = surfaces_by_id.get("AOA-K-0005")
    if surface_0005 is None:
        fail(f"{label} is missing required surface 'AOA-K-0005'")
    if surface_0005.get("name") != "tos-text-chunk-map":
        fail(f"{label} AOA-K-0005 must keep name 'tos-text-chunk-map'")
    if surface_0005.get("status") != "experimental":
        fail(f"{label} AOA-K-0005 must be experimental in the current chunk-map pilot")
    if surface_0005.get("source_class") != "tos_text":
        fail(f"{label} AOA-K-0005 must keep 'tos_text' as its primary source_class")
    if surface_0005.get("derived_kind") != "chunk_map":
        fail(f"{label} AOA-K-0005 must keep 'chunk_map' as its derived_kind")
    if surface_0005.get("provenance_mode") != "strict_source_linked":
        fail(f"{label} AOA-K-0005 must keep 'strict_source_linked' as its provenance_mode")
    if surface_0005.get("normalization_scope") != "text_chunks":
        fail(f"{label} AOA-K-0005 must keep 'text_chunks' as its normalization_scope")
    if surface_0005.get("framework_readiness") != "llamaindex_ready":
        fail(f"{label} AOA-K-0005 must keep 'llamaindex_ready' as its framework_readiness")
    if surface_0005.get("source_repos") != [TOS_REPO]:
        fail(f"{label} AOA-K-0005 must keep source_repos ['{TOS_REPO}']")

    surface_0006 = surfaces_by_id.get("AOA-K-0006")
    if surface_0006 is None:
        fail(f"{label} is missing required surface 'AOA-K-0006'")
    if surface_0006.get("name") != "cross-source-node-projection":
        fail(f"{label} AOA-K-0006 must keep name 'cross-source-node-projection'")
    if surface_0006.get("status") != "experimental":
        fail(f"{label} AOA-K-0006 must be experimental in the current projection pilot")
    if surface_0006.get("source_class") != "technique_bundle":
        fail(f"{label} AOA-K-0006 must keep 'technique_bundle' as its primary source_class")
    if surface_0006.get("derived_kind") != "node_projection":
        fail(f"{label} AOA-K-0006 must keep 'node_projection' as its derived_kind")
    if surface_0006.get("provenance_mode") != "derived_with_handles":
        fail(f"{label} AOA-K-0006 must keep 'derived_with_handles' as its provenance_mode")
    if surface_0006.get("normalization_scope") != "cross_source_nodes":
        fail(f"{label} AOA-K-0006 must keep 'cross_source_nodes' as its normalization_scope")
    if surface_0006.get("framework_readiness") != "multi_consumer_ready":
        fail(f"{label} AOA-K-0006 must keep 'multi_consumer_ready' as its framework_readiness")
    if surface_0006.get("source_repos") != ["aoa-techniques", TOS_REPO]:
        fail(f"{label} AOA-K-0006 must keep source_repos ['aoa-techniques', '{TOS_REPO}']")
    if surface_0006.get("source_inputs") != EXPECTED_AOA_K_0006_SOURCE_INPUTS:
        fail(f"{label} AOA-K-0006 must keep the current primary/supporting source_inputs mapping")

    surface_0007 = surfaces_by_id.get("AOA-K-0007")
    if surface_0007 is None:
        fail(f"{label} is missing required surface 'AOA-K-0007'")
    if surface_0007.get("name") != "tos-retrieval-axis-surface":
        fail(f"{label} AOA-K-0007 must keep name 'tos-retrieval-axis-surface'")
    if surface_0007.get("status") != "experimental":
        fail(f"{label} AOA-K-0007 must be experimental in the current retrieval-axis pilot")
    if surface_0007.get("source_class") != "tos_text":
        fail(f"{label} AOA-K-0007 must keep 'tos_text' as its primary source_class")
    if surface_0007.get("derived_kind") != "retrieval_surface":
        fail(f"{label} AOA-K-0007 must keep 'retrieval_surface' as its derived_kind")
    if surface_0007.get("provenance_mode") != "derived_with_handles":
        fail(f"{label} AOA-K-0007 must keep 'derived_with_handles' as its provenance_mode")
    if surface_0007.get("normalization_scope") != "axis_bundles":
        fail(f"{label} AOA-K-0007 must keep 'axis_bundles' as its normalization_scope")
    if surface_0007.get("framework_readiness") != "hipporag_ready":
        fail(f"{label} AOA-K-0007 must keep 'hipporag_ready' as its framework_readiness")
    if surface_0007.get("source_repos") != [TOS_REPO, "aoa-memo"]:
        fail(f"{label} AOA-K-0007 must keep source_repos ['{TOS_REPO}', 'aoa-memo']")

    surface_0008 = surfaces_by_id.get("AOA-K-0008")
    if surface_0008 is None:
        fail(f"{label} is missing required surface 'AOA-K-0008'")
    if surface_0008.get("name") != "counterpart-edge-view":
        fail(f"{label} AOA-K-0008 must keep name 'counterpart-edge-view'")
    if surface_0008.get("status") != "planned":
        fail(f"{label} AOA-K-0008 must remain planned")
    if surface_0008.get("source_class") != "tos_text":
        fail(f"{label} AOA-K-0008 must keep 'tos_text' as its primary source_class")
    if surface_0008.get("derived_kind") != "edge_projection":
        fail(f"{label} AOA-K-0008 must keep 'edge_projection' as its derived_kind")

    source_inputs = surface_0008.get("source_inputs")
    if not isinstance(source_inputs, list):
        fail(f"{label} AOA-K-0008 must declare source_inputs")
    expected_inputs = {
        ("Tree-of-Sophia", "tos_text", "primary"),
        ("aoa-techniques", "technique_bundle", "supporting"),
        ("aoa-playbooks", "playbook_bundle", "supporting"),
        ("aoa-evals", "eval_bundle", "supporting"),
    }
    actual_inputs = {
        (item.get("repo"), item.get("source_class"), item.get("role"))
        for item in source_inputs
        if isinstance(item, dict)
    }
    if actual_inputs != expected_inputs:
        fail(f"{label} AOA-K-0008 source_inputs must match the current counterpart bridge source contract")

    surface_0009 = surfaces_by_id.get("AOA-K-0009")
    if surface_0009 is None:
        fail(f"{label} is missing required surface 'AOA-K-0009'")
    if surface_0009.get("name") != "federation-readiness-spine":
        fail(f"{label} AOA-K-0009 must keep name 'federation-readiness-spine'")
    if surface_0009.get("status") != "experimental":
        fail(f"{label} AOA-K-0009 must remain experimental")
    if surface_0009.get("source_class") != "review_surface":
        fail(f"{label} AOA-K-0009 must keep 'review_surface' as its primary source_class")
    if surface_0009.get("derived_kind") != "metadata_spine":
        fail(f"{label} AOA-K-0009 must keep 'metadata_spine' as its derived_kind")
    if surface_0009.get("provenance_mode") != "derived_with_handles":
        fail(f"{label} AOA-K-0009 must keep 'derived_with_handles' as its provenance_mode")
    if surface_0009.get("normalization_scope") != "repo_entry_surfaces":
        fail(f"{label} AOA-K-0009 must keep 'repo_entry_surfaces' as its normalization_scope")
    if surface_0009.get("framework_readiness") != "neutral":
        fail(f"{label} AOA-K-0009 must keep 'neutral' as its framework_readiness")
    if surface_0009.get("source_repos") != ["aoa-techniques", TOS_REPO]:
        fail(f"{label} AOA-K-0009 must keep source_repos ['aoa-techniques', '{TOS_REPO}']")
    if surface_0009.get("source_inputs") != EXPECTED_AOA_K_0009_SOURCE_INPUTS:
        fail(f"{label} AOA-K-0009 must keep the current two-repo source_inputs mapping")
