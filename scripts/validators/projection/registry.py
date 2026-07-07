from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *


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
    return payload


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
