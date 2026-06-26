from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_federation_export_registry_pack(
    payload: object,
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("federation export registry pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "export_count",
        "exports",
    ):
        if key not in payload:
            fail(f"federation export registry pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("federation export registry pack pack_version must equal 1")
    if payload["pack_type"] != "federation_export_registry":
        fail("federation export registry pack pack_type must equal 'federation_export_registry'")
    if payload["source_manifest_ref"] != FEDERATION_EXPORT_REGISTRY_MANIFEST_REF:
        fail(
            "federation export registry pack source_manifest_ref must point to "
            f"{FEDERATION_EXPORT_REGISTRY_MANIFEST_REF}"
        )

    exports = payload["exports"]
    if not isinstance(exports, list) or not exports:
        fail("federation export registry pack exports must be a non-empty list")
    export_count = payload["export_count"]
    if not isinstance(export_count, int) or export_count != len(exports):
        fail("federation export registry pack export_count must equal the number of exports")

    seen_dependency_ids: set[str] = set()
    seen_export_refs: set[str] = set()
    seen_routing_entry_ids: set[str] = set()
    for index, export in enumerate(exports):
        location = f"federation export registry pack exports[{index}]"
        if not isinstance(export, dict):
            fail(f"{location} must be an object")
        for key in (
            "dependency_id",
            "owner_repo",
            "export_ref",
            "kind",
            "object_id",
            "package_tier",
            "activation",
            "entry_surface_ref",
            "source_inputs",
            "consumed_by",
            "routing_binding",
            "adjunct_surfaces",
            "summary_50",
            "provenance_note",
            "non_identity_boundary",
        ):
            if key not in export:
                fail(f"{location} is missing required key '{key}'")

        dependency_id = export["dependency_id"]
        owner_repo = export["owner_repo"]
        export_ref = export["export_ref"]
        kind = export["kind"]
        object_id = export["object_id"]
        package_tier = export["package_tier"]
        activation = export["activation"]
        entry_surface_ref = export["entry_surface_ref"]
        source_inputs = export["source_inputs"]
        consumed_by = export["consumed_by"]
        routing_binding = export["routing_binding"]
        adjunct_surfaces = export["adjunct_surfaces"]
        summary_50 = export["summary_50"]
        provenance_note = export["provenance_note"]
        non_identity_boundary = export["non_identity_boundary"]
        if not all(
            isinstance(value, str) and value
            for value in (
                dependency_id,
                owner_repo,
                export_ref,
                kind,
                object_id,
                package_tier,
                entry_surface_ref,
                summary_50,
                provenance_note,
                non_identity_boundary,
            )
        ):
            fail(
                f"{location} must keep string dependency_id, owner_repo, export_ref, "
                "kind, object_id, package_tier, entry_surface_ref, summary_50, "
                "provenance_note, and non_identity_boundary"
            )
        if dependency_id in seen_dependency_ids:
            fail(f"{location}.dependency_id '{dependency_id}' is duplicated")
        seen_dependency_ids.add(dependency_id)
        if export_ref in seen_export_refs:
            fail(f"{location}.export_ref '{export_ref}' is duplicated")
        seen_export_refs.add(export_ref)
        resolve_known_ref(export_ref, label=location)
        resolve_known_ref(entry_surface_ref, label=f"{location}.entry_surface_ref")

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

        if not isinstance(source_inputs, list) or not source_inputs:
            fail(f"{location}.source_inputs must be a non-empty list")
        primary_count = 0
        for source_input_index, source_input in enumerate(source_inputs):
            source_location = f"{location}.source_inputs[{source_input_index}]"
            if not isinstance(source_input, dict):
                fail(f"{source_location} must be an object")
            source_repo = source_input.get("repo")
            source_class = source_input.get("source_class")
            source_role = source_input.get("role")
            if not all(
                isinstance(value, str) and value
                for value in (source_repo, source_class, source_role)
            ):
                fail(f"{source_location} must keep repo, source_class, and role")
            if source_role == "primary":
                primary_count += 1
                if source_repo != owner_repo:
                    fail(f"{source_location}.repo must equal owner_repo '{owner_repo}'")
            elif source_role != "supporting":
                fail(f"{source_location}.role must be 'primary' or 'supporting'")
        if primary_count != 1:
            fail(f"{location}.source_inputs must contain exactly one primary input")

        if not isinstance(consumed_by, list):
            fail(f"{location}.consumed_by must be a list")
        for consumer_index, consumer_surface_id in enumerate(consumed_by):
            if not isinstance(consumer_surface_id, str) or not consumer_surface_id:
                fail(f"{location}.consumed_by[{consumer_index}] must be a non-empty string")

        if routing_visible:
            if not isinstance(routing_binding, dict):
                fail(f"{location}.routing_binding must be an object when routing_visible=true")
            binding_kind = routing_binding.get("kind")
            entry_id = routing_binding.get("entry_id")
            if not all(
                isinstance(value, str) and value for value in (binding_kind, entry_id)
            ):
                fail(f"{location}.routing_binding must keep kind and entry_id")
            if binding_kind != "kag_view":
                fail(f"{location}.routing_binding.kind must equal 'kag_view'")
            if entry_id in seen_routing_entry_ids:
                fail(f"{location}.routing_binding.entry_id '{entry_id}' is duplicated")
            seen_routing_entry_ids.add(entry_id)
        else:
            if routing_binding is not None:
                fail(f"{location}.routing_binding must be null when routing_visible=false")

        if not isinstance(adjunct_surfaces, list):
            fail(f"{location}.adjunct_surfaces must be a list")
        if adjunct_surfaces and not spine_visible:
            fail(f"{location}.adjunct_surfaces require spine_visible=true")
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
            resolve_known_ref(repo_ref(KAG_REPO, surface_ref), label=adjunct_location)

    if payload != expected_payload:
        fail(
            "federation export registry pack must match the committed manifest-driven "
            "donor registry payload"
        )
