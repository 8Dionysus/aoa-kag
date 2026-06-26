from __future__ import annotations

from .common import *
from .registry import build_registry_payload
from .source_refs import *
from .tos import build_tos_retrieval_axis_pack_payload

def build_federation_spine_payload(
    registry_payload: dict[str, object] | None = None,
    federation_export_registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()
    if federation_export_registry_payload is None:
        federation_export_registry_payload = build_federation_export_registry_payload()

    manifest = read_json(FEDERATION_SPINE_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("federation spine manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    repo_bindings = manifest.get("repo_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("federation spine manifest must declare source_inputs")
    if not isinstance(repo_bindings, list) or not repo_bindings:
        fail("federation spine manifest must declare repo_bindings")

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []

    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("federation spine manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail("federation spine manifest source_inputs must keep name, repo, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate federation spine source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        if not manifest_input_path(normalized_input).exists():
            fail(f"federation spine donor input does not exist: {repo_ref(repo, path)}")

        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    required_manifest_inputs = {
        "kag_registry_manifest": "manifests/kag_registry.json",
        "federation_export_registry_manifest": FEDERATION_EXPORT_REGISTRY_MANIFEST_REF,
    }
    for input_name, expected_ref in required_manifest_inputs.items():
        source_input = inputs_by_name.get(input_name)
        if source_input is None:
            fail(f"federation spine manifest must include {input_name}")
        if manifest_input_ref(source_input) != expected_ref:
            fail(
                f"federation spine manifest {input_name} must point to {expected_ref}"
            )

    registry_exports = federation_export_registry_payload.get("exports")
    if not isinstance(registry_exports, list) or not registry_exports:
        fail("federation export registry payload must declare exports")
    registry_export_by_ref = {
        export["export_ref"]: export
        for export in registry_exports
        if isinstance(export, dict) and isinstance(export.get("export_ref"), str)
    }

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    repos: list[dict[str, object]] = []
    seen_repos: set[str] = set()

    for binding in repo_bindings:
        if not isinstance(binding, dict):
            fail("federation spine manifest repo_bindings entries must be objects")

        surface_id = binding.get("surface_id")
        repo_name = binding.get("repo")
        pilot_posture = binding.get("pilot_posture")
        export_input_name = binding.get("export_input")
        adjunct_surfaces = binding.get("adjunct_surfaces")
        provenance_note = binding.get("provenance_note")
        non_identity_boundary = binding.get("non_identity_boundary")

        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                repo_name,
                pilot_posture,
                export_input_name,
                provenance_note,
                non_identity_boundary,
            )
        ):
            fail("federation spine repo binding must keep required string fields")
        if not isinstance(adjunct_surfaces, list):
            fail("federation spine repo binding adjunct_surfaces must be a list")
        if repo_name in seen_repos:
            fail(f"duplicate federation spine repo binding '{repo_name}'")
        seen_repos.add(repo_name)

        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(f"federation spine binding '{surface_id}' does not exist in the registry manifest")
        if surface.get("status") != "experimental":
            fail(
                f"federation spine binding '{surface_id}' must point to an experimental registry surface"
            )

        export_input = inputs_by_name.get(export_input_name)
        if export_input is None:
            fail(
                f"federation spine repo binding references unknown export input '{export_input_name}'"
            )
        if export_input["repo"] != repo_name:
            fail(
                f"federation spine export input '{export_input_name}' must point to repo '{repo_name}'"
            )

        export_entry = registry_export_by_ref.get(manifest_input_ref(export_input))
        if export_entry is None:
            fail(
                f"federation spine export input '{export_input_name}' must map to a "
                "declared federation export registry entry"
            )
        activation = export_entry.get("activation")
        if not isinstance(activation, dict):
            fail(
                f"federation export registry entry '{manifest_input_ref(export_input)}' "
                "must keep activation"
            )
        if activation.get("spine_visible") is not True:
            fail(
                f"federation spine export input '{export_input_name}' must stay "
                "spine-visible in the donor registry"
            )
        if export_entry.get("owner_repo") != repo_name:
            fail(
                f"federation spine export input '{export_input_name}' must stay aligned "
                f"with registry owner_repo '{repo_name}'"
            )

        entry_surface_ref = require_string(
            export_entry.get("entry_surface_ref"),
            label=f"{manifest_input_ref(export_input)} entry_surface_ref",
        )

        normalized_adjunct_surfaces: list[dict[str, object]] = []
        for adjunct_index, adjunct in enumerate(adjunct_surfaces):
            adjunct_location = (
                f"federation spine repo binding '{repo_name}' "
                f"adjunct_surfaces[{adjunct_index}]"
            )
            if not isinstance(adjunct, dict):
                fail(f"{adjunct_location} must be an object")
            adjunct_surface_id = adjunct.get("surface_id")
            adjunct_surface_name = adjunct.get("surface_name")
            adjunct_surface_ref = adjunct.get("surface_ref")
            adjunct_match_key = adjunct.get("match_key")
            adjunct_target_value = adjunct.get("target_value")
            adjunct_route_id = adjunct.get("route_id")
            adjunct_budget = adjunct.get("adjunct_budget")
            subordinate_posture = adjunct.get("subordinate_posture")
            if not all(
                isinstance(value, str) and value
                for value in (
                    adjunct_surface_id,
                    adjunct_surface_name,
                    adjunct_surface_ref,
                    adjunct_match_key,
                    adjunct_target_value,
                    adjunct_route_id,
                )
            ):
                fail(
                    f"{adjunct_location} must keep surface_id, surface_name, "
                    "surface_ref, match_key, target_value, and route_id"
                )
            if adjunct_budget != TOS_STANDALONE_ADJUNCT_BUDGET:
                fail(
                    f"{adjunct_location}.adjunct_budget must stay aligned with the "
                    "current standalone adjunct budget"
                )
            if subordinate_posture != TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE:
                fail(
                    f"{adjunct_location}.subordinate_posture must stay aligned with "
                    "the current source-first subordinate posture"
                )
            adjunct_surface = registry_by_id.get(adjunct_surface_id)
            if adjunct_surface is None:
                fail(
                    f"{adjunct_location} references unknown registry surface "
                    f"'{adjunct_surface_id}'"
                )
            if adjunct_surface.get("status") != "experimental":
                fail(f"{adjunct_location} must point to an experimental registry surface")
            if adjunct_surface.get("name") != adjunct_surface_name:
                fail(
                    f"{adjunct_location}.surface_name must match registry surface "
                    f"'{adjunct_surface.get('name')}'"
                )
            if repo_name != TOS_REPO:
                fail(
                    f"{adjunct_location} is not allowed because adjunct surfaces "
                    "are only enabled for Tree-of-Sophia in the current scope"
                )
            resolve_path = REPO_ROOT / adjunct_surface_ref
            if not resolve_path.exists():
                fail(
                    f"{adjunct_location}.surface_ref does not exist: "
                    f"{repo_ref(KAG_REPO, adjunct_surface_ref)}"
                )
            normalized_adjunct_surfaces.append(
                {
                    "surface_id": adjunct_surface_id,
                    "surface_name": adjunct_surface_name,
                    "surface_ref": adjunct_surface_ref,
                    "match_key": adjunct_match_key,
                    "target_value": adjunct_target_value,
                    "route_id": adjunct_route_id,
                    "adjunct_budget": adjunct_budget,
                    "subordinate_posture": subordinate_posture,
                }
            )

        repos.append(
            {
                "repo": repo_name,
                "pilot_posture": pilot_posture,
                "export_ref": manifest_input_ref(export_input),
                "kind": export_entry["kind"],
                "object_id": export_entry["object_id"],
                "entry_surface_ref": entry_surface_ref,
                "adjunct_surfaces": normalized_adjunct_surfaces,
                "summary_50": export_entry["summary_50"],
                "provenance_note": provenance_note,
                "non_identity_boundary": non_identity_boundary,
            }
        )

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": FEDERATION_SPINE_MANIFEST_REF,
        "artifact_identity": FEDERATION_SPINE_ARTIFACT_IDENTITY,
        "source_inputs": emitted_source_inputs,
        "repo_count": len(repos),
        "repos": repos,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_federation_export_registry_payload() -> dict[str, object]:
    manifest = read_json(FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("federation export registry manifest must be a JSON object")

    exports = manifest.get("exports")
    if not isinstance(exports, list) or not exports:
        fail("federation export registry manifest must declare exports")

    normalized_exports: list[dict[str, object]] = []
    seen_dependency_ids: set[str] = set()
    seen_export_refs: set[str] = set()
    seen_routing_entry_ids: set[str] = set()

    for index, export in enumerate(exports):
        location = f"federation export registry manifest exports[{index}]"
        if not isinstance(export, dict):
            fail(f"{location} must be an object")

        dependency_id = require_string(
            export.get("dependency_id"),
            label=f"{location}.dependency_id",
        )
        owner_repo = require_string(
            export.get("owner_repo"),
            label=f"{location}.owner_repo",
        )
        export_repo = require_string(
            export.get("export_repo"),
            label=f"{location}.export_repo",
        )
        export_path = ensure_repo_relative_path(
            export.get("export_path"),
            label=f"{location}.export_path",
        )
        package_tier = require_string(
            export.get("package_tier"),
            label=f"{location}.package_tier",
        )
        activation = export.get("activation")
        routing_binding = export.get("routing_binding")
        adjunct_surfaces = export.get("adjunct_surfaces")

        if dependency_id in seen_dependency_ids:
            fail(f"{location}.dependency_id '{dependency_id}' is duplicated")
        seen_dependency_ids.add(dependency_id)

        dependency = dependency_for_export_target(export_repo, export_path)
        if dependency["dependency_id"] != dependency_id:
            fail(
                f"{location}.dependency_id must stay aligned with the source-owned "
                "export dependency contract"
            )
        if dependency["expected_owner_repo"] != owner_repo:
            fail(
                f"{location}.owner_repo must match dependency expected_owner_repo "
                f"'{dependency['expected_owner_repo']}'"
            )

        export_source_input = {
            "repo": export_repo,
            "path": export_path,
        }
        export_payload = load_federation_export_payload(
            export_source_input,
            dependency=dependency,
            consumer_surface_id="federation_export_registry",
        )

        if not isinstance(activation, dict):
            fail(f"{location}.activation must be an object")
        registry_visible = activation.get("registry_visible")
        spine_visible = activation.get("spine_visible")
        routing_visible = activation.get("routing_visible")
        if not all(isinstance(value, bool) for value in (registry_visible, spine_visible, routing_visible)):
            fail(
                f"{location}.activation must keep boolean registry_visible, "
                "spine_visible, and routing_visible"
            )
        if spine_visible and not registry_visible:
            fail(f"{location}.activation.spine_visible requires registry_visible=true")
        if routing_visible and not spine_visible:
            fail(f"{location}.activation.routing_visible requires spine_visible=true")

        dependency_consumed_by = dependency["consumed_by"]
        live_spine_consumed = "AOA-K-0009" in dependency_consumed_by
        if spine_visible != live_spine_consumed:
            fail(
                f"{location}.activation.spine_visible must stay aligned with "
                "AOA-K-0009 presence in consumed_by"
            )

        normalized_routing_binding: dict[str, str] | None
        if routing_visible:
            if not isinstance(routing_binding, dict):
                fail(f"{location}.routing_binding must be an object when routing_visible=true")
            binding_kind = require_string(
                routing_binding.get("kind"),
                label=f"{location}.routing_binding.kind",
            )
            if binding_kind != "kag_view":
                fail(f"{location}.routing_binding.kind must equal 'kag_view'")
            entry_id = require_string(
                routing_binding.get("entry_id"),
                label=f"{location}.routing_binding.entry_id",
            )
            if entry_id in seen_routing_entry_ids:
                fail(f"{location}.routing_binding.entry_id '{entry_id}' is duplicated")
            seen_routing_entry_ids.add(entry_id)
            normalized_routing_binding = {
                "kind": binding_kind,
                "entry_id": entry_id,
            }
        else:
            if routing_binding is not None:
                fail(f"{location}.routing_binding must be null when routing_visible=false")
            normalized_routing_binding = None

        if not isinstance(adjunct_surfaces, list):
            fail(f"{location}.adjunct_surfaces must be a list")
        if adjunct_surfaces and not spine_visible:
            fail(f"{location}.adjunct_surfaces require spine_visible=true")
        normalized_adjunct_surfaces: list[dict[str, str]] = []
        seen_adjunct_refs: set[str] = set()
        for adjunct_index, adjunct in enumerate(adjunct_surfaces):
            adjunct_location = f"{location}.adjunct_surfaces[{adjunct_index}]"
            if not isinstance(adjunct, dict):
                fail(f"{adjunct_location} must be an object")
            if set(adjunct) != {
                "surface_id",
                "surface_ref",
                "match_key",
                "target_value",
            }:
                fail(
                    f"{adjunct_location} must keep exactly surface_id, surface_ref, "
                    "match_key, and target_value"
                )
            surface_id = require_string(
                adjunct.get("surface_id"),
                label=f"{adjunct_location}.surface_id",
            )
            surface_ref = ensure_repo_relative_path(
                adjunct.get("surface_ref"),
                label=f"{adjunct_location}.surface_ref",
            )
            match_key = require_string(
                adjunct.get("match_key"),
                label=f"{adjunct_location}.match_key",
            )
            target_value = require_string(
                adjunct.get("target_value"),
                label=f"{adjunct_location}.target_value",
            )
            if surface_ref in seen_adjunct_refs:
                fail(f"{adjunct_location}.surface_ref '{surface_ref}' is duplicated")
            seen_adjunct_refs.add(surface_ref)
            if not (REPO_ROOT / surface_ref).exists():
                fail(
                    f"{adjunct_location}.surface_ref target is missing: "
                    f"{repo_ref(KAG_REPO, surface_ref)}"
                )
            normalized_adjunct_surfaces.append(
                {
                    "surface_id": surface_id,
                    "surface_ref": surface_ref,
                    "match_key": match_key,
                    "target_value": target_value,
                }
            )

        payload_entry_surface = export_payload.get("entry_surface")
        if not isinstance(payload_entry_surface, dict):
            fail(f"{repo_ref(export_repo, export_path)}.entry_surface must be an object")
        dependency_entry_surface = dependency.get("entry_surface")
        if not isinstance(dependency_entry_surface, dict):
            fail(f"{dependency_id}.entry_surface must be an object")
        entry_surface_ref = repo_ref(
            require_string(
                dependency_entry_surface.get("repo"),
                label=f"{repo_ref(export_repo, export_path)}.entry_surface.repo",
            ),
            require_string(
                dependency_entry_surface.get("path"),
                label=f"{repo_ref(export_repo, export_path)}.entry_surface.path",
            ),
        )
        export_ref = repo_ref(export_repo, export_path)
        if export_ref in seen_export_refs:
            fail(f"{location}.export target '{export_ref}' is duplicated")
        seen_export_refs.add(export_ref)

        normalized_exports.append(
            {
                "dependency_id": dependency_id,
                "owner_repo": owner_repo,
                "export_ref": export_ref,
                "kind": export_payload["kind"],
                "object_id": export_payload["object_id"],
                "package_tier": package_tier,
                "activation": {
                    "registry_visible": registry_visible,
                    "spine_visible": spine_visible,
                    "routing_visible": routing_visible,
                },
                "entry_surface_ref": entry_surface_ref,
                "source_inputs": export_payload["source_inputs"],
                "consumed_by": dependency_consumed_by,
                "routing_binding": normalized_routing_binding,
                "adjunct_surfaces": normalized_adjunct_surfaces,
                "summary_50": export_payload["summary_50"],
                "provenance_note": export_payload["provenance_note"],
                "non_identity_boundary": export_payload["non_identity_boundary"],
            }
        )

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": FEDERATION_EXPORT_REGISTRY_MANIFEST_REF,
        "export_count": len(normalized_exports),
        "exports": normalized_exports,
    }


def build_cross_source_node_projection_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(CROSS_SOURCE_NODE_PROJECTION_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("cross-source node projection manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")
    projection_pairings = manifest.get("projection_pairings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("cross-source node projection manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("cross-source node projection manifest must declare surface_bindings")
    if not isinstance(projection_pairings, list) or not projection_pairings:
        fail("cross-source node projection manifest must declare projection_pairings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("cross-source node projection manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail(
                "cross-source node projection manifest source_inputs must keep name, repo, path, and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate cross-source node projection source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        allow_same_run_generated_input = (
            repo == "aoa-kag"
            and path in {
                "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json",
                FEDERATION_SPINE_MIN_OUTPUT_REF,
            }
        )
        if not input_path.exists() and not allow_same_run_generated_input:
            fail(
                "cross-source node projection donor input does not exist: "
                + repo_ref(repo, path)
            )
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": repo,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    required_input_names = (
        "aoa_techniques_kag_export",
        "tos_kag_export",
        "tos_retrieval_axis_pack",
        "federation_spine",
    )
    missing_inputs = [name for name in required_input_names if name not in inputs_by_name]
    if missing_inputs:
        fail(
            "cross-source node projection manifest is missing required inputs: "
            + ", ".join(sorted(missing_inputs))
        )

    if manifest_input_ref(inputs_by_name["aoa_techniques_kag_export"]) != "aoa-techniques/generated/kag_export.min.json":
        fail(
            "cross-source node projection manifest aoa_techniques_kag_export must point to aoa-techniques/generated/kag_export.min.json"
        )
    if manifest_input_ref(inputs_by_name["tos_kag_export"]) != "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json":
        fail(
            "cross-source node projection manifest tos_kag_export must point to Tree-of-Sophia/ToS/derived-exports/kag_export.min.json"
        )
    if manifest_input_ref(inputs_by_name["tos_retrieval_axis_pack"]) != "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json":
        fail(
            "cross-source node projection manifest tos_retrieval_axis_pack must point to mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/tos_retrieval_axis_pack.min.json"
        )
    if manifest_input_ref(inputs_by_name["federation_spine"]) != FEDERATION_SPINE_MIN_OUTPUT_REF:
        fail(
            "cross-source node projection manifest federation_spine must point to "
            f"{FEDERATION_SPINE_MIN_OUTPUT_REF}"
        )

    seen_surface_ids: set[str] = set()
    binding_surface: dict[str, object] | None = None
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("cross-source node projection manifest surface_bindings entries must be objects")
        surface_id = binding.get("surface_id")
        surface_name = binding.get("surface_name")
        derived_kind = binding.get("derived_kind")
        derived_slot = binding.get("derived_slot")
        source_input = binding.get("source_input")
        if not all(
            isinstance(value, str) and value
            for value in (
                surface_id,
                surface_name,
                derived_kind,
                derived_slot,
                source_input,
            )
        ):
            fail(
                "cross-source node projection manifest surface_bindings must keep id, name, kind, slot, and source input"
            )
        if surface_id in seen_surface_ids:
            fail(f"duplicate cross-source node projection surface binding '{surface_id}'")
        seen_surface_ids.add(surface_id)
        if source_input not in inputs_by_name:
            fail(
                "cross-source node projection binding "
                f"'{surface_id}' references unknown source input '{source_input}'"
            )

        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(
                f"cross-source node projection binding '{surface_id}' does not exist in the registry manifest"
            )
        if surface.get("name") != surface_name:
            fail(
                f"cross-source node projection binding '{surface_id}' does not match registry surface name"
            )
        if surface.get("derived_kind") != derived_kind:
            fail(
                f"cross-source node projection binding '{surface_id}' does not match registry derived_kind"
            )
        if surface.get("status") != "experimental":
            fail(
                f"cross-source node projection binding '{surface_id}' must point to an experimental registry surface"
            )
        binding_surface = surface

    if binding_surface is None:
        fail("cross-source node projection manifest must declare one experimental surface binding")

    consumer_surface_id = require_string(
        binding_surface.get("id"),
        label="cross-source node projection consumer_surface_id",
    )
    technique_dependency = dependency_for_source_input(
        inputs_by_name["aoa_techniques_kag_export"],
        consumer_surface_id=consumer_surface_id,
    )
    tos_dependency = dependency_for_source_input(
        inputs_by_name["tos_kag_export"],
        consumer_surface_id=consumer_surface_id,
    )
    technique_export_payload = load_federation_export_payload(
        inputs_by_name["aoa_techniques_kag_export"],
        dependency=technique_dependency,
        consumer_surface_id=consumer_surface_id,
    )
    tos_export_payload = load_federation_export_payload(
        inputs_by_name["tos_kag_export"],
        dependency=tos_dependency,
        consumer_surface_id=consumer_surface_id,
    )
    export_payloads_by_input = {
        "aoa_techniques_kag_export": technique_export_payload,
        "tos_kag_export": tos_export_payload,
    }
    retrieval_axis_payload = build_tos_retrieval_axis_pack_payload(registry_payload)
    axes = retrieval_axis_payload.get("axes")
    if not isinstance(axes, list) or len(axes) != 1 or not isinstance(axes[0], dict):
        fail("cross-source node projection requires exactly one retrieval axis in the current pilot")
    axis = axes[0]
    axis_id = require_string(axis.get("axis_id"), label="cross-source node projection axis_id")
    if require_string(
        axis.get("source_node_id"),
        label="cross-source node projection source_node_id",
    ) != tos_export_payload["object_id"]:
        fail(
            "cross-source node projection retrieval axis must stay aligned with the Tree-of-Sophia export object_id"
        )

    federation_spine_payload = build_federation_spine_payload(registry_payload)
    federation_repos = federation_spine_payload.get("repos")
    if not isinstance(federation_repos, list) or len(federation_repos) != 2:
        fail("cross-source node projection requires exactly two repo entries in the current federation spine")
    federation_repo_map = {
        repo_entry["repo"]: repo_entry
        for repo_entry in federation_repos
        if isinstance(repo_entry, dict) and isinstance(repo_entry.get("repo"), str)
    }
    if set(federation_repo_map) != {"aoa-techniques", TOS_REPO}:
        fail("cross-source node projection requires aoa-techniques and Tree-of-Sophia federation entries")

    technique_spine_entry = federation_repo_map["aoa-techniques"]
    tos_spine_entry = federation_repo_map[TOS_REPO]
    if technique_spine_entry.get("export_ref") != manifest_input_ref(inputs_by_name["aoa_techniques_kag_export"]):
        fail("cross-source node projection primary export must stay aligned with the federation spine")
    if tos_spine_entry.get("export_ref") != manifest_input_ref(inputs_by_name["tos_kag_export"]):
        fail("cross-source node projection supporting export must stay aligned with the federation spine")

    if len(projection_pairings) != 1:
        fail(
            "cross-source node projection manifest must declare exactly one "
            "projection_pairings entry in the current pilot"
        )
    seen_pairing_ids: set[str] = set()
    projections: list[dict[str, object]] = []
    for index, pairing in enumerate(projection_pairings):
        location = (
            "cross-source node projection manifest "
            f"projection_pairings[{index}]"
        )
        if not isinstance(pairing, dict):
            fail(f"{location} must be an object")
        pairing_id = require_string(
            pairing.get("pairing_id"),
            label=f"{location}.pairing_id",
        )
        primary_export_input = require_string(
            pairing.get("primary_export_input"),
            label=f"{location}.primary_export_input",
        )
        supporting_export_inputs = pairing.get("supporting_export_inputs")
        if not isinstance(supporting_export_inputs, list) or not supporting_export_inputs:
            fail(f"{location}.supporting_export_inputs must be a non-empty list")
        normalized_supporting_inputs: list[str] = []
        for supporting_index, supporting_input in enumerate(supporting_export_inputs):
            normalized_supporting_inputs.append(
                require_string(
                    supporting_input,
                    label=f"{location}.supporting_export_inputs[{supporting_index}]",
                )
            )
        retrieval_axis_input = require_string(
            pairing.get("retrieval_axis_input"),
            label=f"{location}.retrieval_axis_input",
        )
        federation_spine_input = require_string(
            pairing.get("federation_spine_input"),
            label=f"{location}.federation_spine_input",
        )
        projection_summary = require_string(
            pairing.get("projection_summary"),
            label=f"{location}.projection_summary",
        )
        non_identity_boundary = require_string(
            pairing.get("non_identity_boundary"),
            label=f"{location}.non_identity_boundary",
        )
        if pairing_id in seen_pairing_ids:
            fail(f"{location}.pairing_id '{pairing_id}' is duplicated")
        seen_pairing_ids.add(pairing_id)
        if primary_export_input not in inputs_by_name:
            fail(f"{location}.primary_export_input references unknown source input")
        if len(normalized_supporting_inputs) != 1:
            fail(
                f"{location}.supporting_export_inputs must contain exactly one "
                "supporting export in the current pilot"
            )
        if retrieval_axis_input not in inputs_by_name:
            fail(f"{location}.retrieval_axis_input references unknown source input")
        if federation_spine_input not in inputs_by_name:
            fail(f"{location}.federation_spine_input references unknown source input")
        if inputs_by_name[primary_export_input]["role"] != "primary_export":
            fail(f"{location}.primary_export_input must point to a primary_export source input")
        supporting_input_name = normalized_supporting_inputs[0]
        if inputs_by_name[supporting_input_name]["role"] != "supporting_export":
            fail(
                f"{location}.supporting_export_inputs must point only to "
                "supporting_export source inputs"
            )
        if inputs_by_name[retrieval_axis_input]["role"] != "retrieval_axis":
            fail(f"{location}.retrieval_axis_input must point to a retrieval_axis source input")
        if inputs_by_name[federation_spine_input]["role"] != "federation_spine":
            fail(f"{location}.federation_spine_input must point to a federation_spine source input")

        primary_export_payload = export_payloads_by_input.get(primary_export_input)
        supporting_export_payload = export_payloads_by_input.get(supporting_input_name)
        if primary_export_payload is None or supporting_export_payload is None:
            fail(f"{location} must reference known source-owned export inputs")
        if axis.get("source_node_id") != supporting_export_payload["object_id"]:
            fail(
                f"{location}.supporting_export_inputs[0] must stay aligned with the "
                "current retrieval axis source_node_id"
            )
        if (
            technique_spine_entry.get("export_ref")
            != manifest_input_ref(inputs_by_name[primary_export_input])
        ):
            fail(
                f"{location}.primary_export_input must stay aligned with the "
                "aoa-techniques federation spine entry"
            )
        if (
            tos_spine_entry.get("export_ref")
            != manifest_input_ref(inputs_by_name[supporting_input_name])
        ):
            fail(
                f"{location}.supporting_export_inputs[0] must stay aligned with the "
                "Tree-of-Sophia federation spine entry"
            )

        projections.append(
            {
                "projection_id": (
                    "AOA-K-0006::"
                    f"{primary_export_payload['object_id']}::"
                    f"{supporting_export_payload['object_id']}"
                ),
                "primary_input": {
                    "repo": inputs_by_name[primary_export_input]["repo"],
                    "export_ref": manifest_input_ref(inputs_by_name[primary_export_input]),
                    "kind": primary_export_payload["kind"],
                    "object_id": primary_export_payload["object_id"],
                },
                "supporting_inputs": [
                    {
                        "repo": inputs_by_name[supporting_input_name]["repo"],
                        "export_ref": manifest_input_ref(
                            inputs_by_name[supporting_input_name]
                        ),
                        "kind": supporting_export_payload["kind"],
                        "object_id": supporting_export_payload["object_id"],
                    }
                ],
                "retrieval_axis_ref": manifest_input_ref(
                    inputs_by_name[retrieval_axis_input]
                ),
                "axis_id": axis_id,
                "federation_spine_ref": manifest_input_ref(
                    inputs_by_name[federation_spine_input]
                ),
                "projection_summary": projection_summary,
                "non_identity_boundary": non_identity_boundary,
            }
        )

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": CROSS_SOURCE_NODE_PROJECTION_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "surface_bindings": surface_bindings,
        "surface_id": binding_surface["id"],
        "surface_name": binding_surface["name"],
        "projection_count": len(projections),
        "projections": projections,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }
