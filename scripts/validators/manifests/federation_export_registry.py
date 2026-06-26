from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_federation_export_registry_manifest(
    source_owned_export_dependencies: dict[tuple[str, str], dict[str, object]],
) -> dict[tuple[str, str], dict[str, object]]:
    payload = read_json(FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH)
    if not isinstance(payload, dict):
        fail("federation export registry manifest must be a JSON object")

    for key in (
        "manifest_version",
        "pack_type",
        "exports",
        "output_paths",
    ):
        if key not in payload:
            fail(f"federation export registry manifest is missing required key '{key}'")

    if payload["manifest_version"] != 1:
        fail("federation export registry manifest manifest_version must equal 1")
    if payload["pack_type"] != "federation_export_registry":
        fail("federation export registry manifest pack_type must equal 'federation_export_registry'")

    exports = payload["exports"]
    if not isinstance(exports, list) or not exports:
        fail("federation export registry manifest exports must be a non-empty list")

    exports_by_source: dict[tuple[str, str], dict[str, object]] = {}
    seen_dependency_ids: set[str] = set()
    seen_routing_entry_ids: set[str] = set()
    for index, export in enumerate(exports):
        location = f"federation export registry manifest exports[{index}]"
        if not isinstance(export, dict):
            fail(f"{location} must be an object")
        if set(export) != {
            "dependency_id",
            "owner_repo",
            "export_repo",
            "export_path",
            "package_tier",
            "activation",
            "routing_binding",
            "adjunct_surfaces",
        }:
            fail(
                f"{location} must keep exactly dependency_id, owner_repo, export_repo, "
                "export_path, package_tier, activation, routing_binding, and adjunct_surfaces"
            )

        dependency_id = export.get("dependency_id")
        owner_repo = export.get("owner_repo")
        export_repo = export.get("export_repo")
        export_path = export.get("export_path")
        package_tier = export.get("package_tier")
        activation = export.get("activation")
        routing_binding = export.get("routing_binding")
        adjunct_surfaces = export.get("adjunct_surfaces")
        if not all(
            isinstance(value, str) and value
            for value in (
                dependency_id,
                owner_repo,
                export_repo,
                export_path,
                package_tier,
            )
        ):
            fail(
                f"{location} must keep dependency_id, owner_repo, export_repo, "
                "export_path, and package_tier"
            )
        if dependency_id in seen_dependency_ids:
            fail(f"{location}.dependency_id '{dependency_id}' is duplicated")
        seen_dependency_ids.add(dependency_id)
        resolve_known_ref(repo_ref(export_repo, export_path), label=location)

        dependency = source_owned_export_dependencies.get((export_repo, export_path))
        if dependency is None:
            fail(
                f"{location} must map to a declared source-owned export dependency"
            )
        if dependency["dependency_id"] != dependency_id:
            fail(
                f"{location}.dependency_id must match dependency '{dependency['dependency_id']}'"
            )
        if dependency["expected_owner_repo"] != owner_repo:
            fail(
                f"{location}.owner_repo must match dependency expected_owner_repo "
                f"'{dependency['expected_owner_repo']}'"
            )

        if not isinstance(activation, dict):
            fail(f"{location}.activation must be an object")
        if set(activation) != {
            "registry_visible",
            "spine_visible",
            "routing_visible",
        }:
            fail(
                f"{location}.activation must keep exactly registry_visible, "
                "spine_visible, and routing_visible"
            )
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
        live_spine_consumed = "AOA-K-0009" in dependency["consumed_by"]
        if spine_visible != live_spine_consumed:
            fail(
                f"{location}.activation.spine_visible must stay aligned with "
                "AOA-K-0009 presence in consumed_by"
            )

        normalized_routing_binding: dict[str, str] | None
        if routing_visible:
            if not isinstance(routing_binding, dict):
                fail(f"{location}.routing_binding must be an object when routing_visible=true")
            binding_kind = routing_binding.get("kind")
            entry_id = routing_binding.get("entry_id")
            if not all(
                isinstance(value, str) and value for value in (binding_kind, entry_id)
            ):
                fail(
                    f"{location}.routing_binding must keep kind and entry_id"
                )
            if binding_kind != "kag_view":
                fail(f"{location}.routing_binding.kind must equal 'kag_view'")
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
            surface_id = adjunct.get("surface_id")
            surface_ref = adjunct.get("surface_ref")
            match_key = adjunct.get("match_key")
            target_value = adjunct.get("target_value")
            if not all(
                isinstance(value, str) and value
                for value in (surface_id, surface_ref, match_key, target_value)
            ):
                fail(
                    f"{adjunct_location} must keep surface_id, surface_ref, "
                    "match_key, and target_value"
                )
            if surface_ref in seen_adjunct_refs:
                fail(f"{adjunct_location}.surface_ref '{surface_ref}' is duplicated")
            seen_adjunct_refs.add(surface_ref)
            resolve_known_ref(repo_ref(KAG_REPO, surface_ref), label=adjunct_location)
            normalized_adjunct_surfaces.append(
                {
                    "surface_id": surface_id,
                    "surface_ref": surface_ref,
                    "match_key": match_key,
                    "target_value": target_value,
                }
            )

        source_key = (export_repo, export_path)
        if source_key in exports_by_source:
            fail(f"{location} duplicates export target '{repo_ref(export_repo, export_path)}'")
        exports_by_source[source_key] = {
            "dependency_id": dependency_id,
            "owner_repo": owner_repo,
            "activation": {
                "registry_visible": registry_visible,
                "spine_visible": spine_visible,
                "routing_visible": routing_visible,
            },
            "routing_binding": normalized_routing_binding,
            "adjunct_surfaces": normalized_adjunct_surfaces,
        }

    if payload["output_paths"] != EXPECTED_FEDERATION_EXPORT_REGISTRY_OUTPUT_PATHS:
        fail(
            "federation export registry manifest output_paths must match the committed "
            "generated output paths"
        )

    return exports_by_source
