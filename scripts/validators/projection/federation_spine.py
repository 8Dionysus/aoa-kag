from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

def validate_federation_spine_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("federation spine pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "artifact_identity",
        "source_inputs",
        "repo_count",
        "repos",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"federation spine pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("federation spine pack pack_version must equal 1")
    if payload["pack_type"] != "federation_spine":
        fail("federation spine pack pack_type must equal 'federation_spine'")
    if payload["source_manifest_ref"] != FEDERATION_SPINE_MANIFEST_REF:
        fail(
            "federation spine pack source_manifest_ref must point to "
            f"{FEDERATION_SPINE_MANIFEST_REF}"
        )
    if payload["artifact_identity"] != FEDERATION_SPINE_ARTIFACT_IDENTITY:
        fail("federation spine pack artifact_identity must match the published KAG readmodel contract")
    if payload["bounded_output_contract"] != EXPECTED_FEDERATION_SPINE_CONTRACT:
        fail("federation spine pack bounded_output_contract must match the current source-first guardrail")
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("federation spine pack source_inputs must match the manifest-driven donor set")
    forbidden_counterpart_refs = set(EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS) | {
        EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF,
        "AOA-K-0008",
    }
    if any(value in forbidden_counterpart_refs for value in iter_string_values(payload)):
        fail(
            "federation spine pack must not expose counterpart refs or AOA-K-0008 "
            "activation hints in the current review-closed posture"
        )

    for index, source_input in enumerate(payload["source_inputs"]):
        location = f"federation spine pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        ref = source_input.get("ref")
        if not isinstance(ref, str) or not ref:
            fail(f"{location}.ref must be a non-empty string")
        resolve_known_ref(ref, label=location)

    repos = payload["repos"]
    if not isinstance(repos, list) or not repos:
        fail("federation spine pack repos must be a non-empty list")
    repo_count = payload["repo_count"]
    if not isinstance(repo_count, int) or repo_count != len(repos):
        fail("federation spine pack repo_count must equal the number of repos")

    seen_repos: set[str] = set()
    repo_order: list[str] = []
    for index, repo_entry in enumerate(repos):
        location = f"federation spine pack repos[{index}]"
        if not isinstance(repo_entry, dict):
            fail(f"{location} must be an object")
        for key in (
            "repo",
            "pilot_posture",
            "export_ref",
            "kind",
            "object_id",
            "entry_surface_ref",
            "adjunct_surfaces",
            "summary_50",
            "provenance_note",
            "non_identity_boundary",
        ):
            if key not in repo_entry:
                fail(f"{location} is missing required key '{key}'")

        repo_name = repo_entry["repo"]
        pilot_posture = repo_entry["pilot_posture"]
        export_ref = repo_entry["export_ref"]
        kind = repo_entry["kind"]
        object_id = repo_entry["object_id"]
        entry_surface_ref = repo_entry["entry_surface_ref"]
        adjunct_surfaces = repo_entry["adjunct_surfaces"]
        summary_50 = repo_entry["summary_50"]
        provenance_note = repo_entry["provenance_note"]
        non_identity_boundary = repo_entry["non_identity_boundary"]

        if not isinstance(repo_name, str) or not repo_name:
            fail(f"{location}.repo must be a non-empty string")
        if repo_name in seen_repos:
            fail(f"{location}.repo '{repo_name}' is duplicated")
        seen_repos.add(repo_name)
        repo_order.append(repo_name)
        if not isinstance(pilot_posture, str) or not pilot_posture:
            fail(f"{location}.pilot_posture must be a non-empty string")
        if not isinstance(export_ref, str) or not export_ref:
            fail(f"{location}.export_ref must be a non-empty string")
        if not isinstance(kind, str) or not kind:
            fail(f"{location}.kind must be a non-empty string")
        if not isinstance(object_id, str) or not object_id:
            fail(f"{location}.object_id must be a non-empty string")
        if not isinstance(entry_surface_ref, str) or not entry_surface_ref:
            fail(f"{location}.entry_surface_ref must be a non-empty string")
        if not isinstance(adjunct_surfaces, list):
            fail(f"{location}.adjunct_surfaces must be a list")
        if not isinstance(summary_50, str) or len(summary_50) < 10:
            fail(f"{location}.summary_50 must be a string of length >= 10")
        if not isinstance(provenance_note, str) or len(provenance_note) < 20:
            fail(f"{location}.provenance_note must be a string of length >= 20")
        if not isinstance(non_identity_boundary, str) or len(non_identity_boundary) < 20:
            fail(f"{location}.non_identity_boundary must be a string of length >= 20")
        resolve_known_ref(export_ref, label=f"{location}.export_ref")
        resolve_known_ref(entry_surface_ref, label=f"{location}.entry_surface_ref")
        if not export_ref.startswith(f"{repo_name}/"):
            fail(f"{location}.export_ref must point to the same repo as the repo entry")
        if not entry_surface_ref.startswith(f"{repo_name}/"):
            fail(f"{location}.entry_surface_ref must point to the same repo as the repo entry")

        surface_0009 = surfaces_by_id.get("AOA-K-0009")
        if surface_0009 is None or surface_0009.get("status") != "experimental":
            fail("federation spine pack requires AOA-K-0009 to remain experimental in the generated registry")

        normalized_adjunct_surfaces: list[dict[str, object]] = []
        for adjunct_index, adjunct in enumerate(adjunct_surfaces):
            adjunct_location = f"{location}.adjunct_surfaces[{adjunct_index}]"
            if not isinstance(adjunct, dict):
                fail(f"{adjunct_location} must be an object")
            if set(adjunct) != {
                "surface_id",
                "surface_name",
                "surface_ref",
                "match_key",
                "target_value",
                "route_id",
                "adjunct_budget",
                "subordinate_posture",
            }:
                fail(
                    f"{adjunct_location} must keep exactly surface_id, surface_name, "
                    "surface_ref, match_key, target_value, route_id, adjunct_budget, "
                    "and subordinate_posture"
                )
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
            if adjunct_budget != EXPECTED_TOS_STANDALONE_ADJUNCT_BUDGET:
                fail(
                    f"{adjunct_location}.adjunct_budget must match the current "
                    "standalone adjunct budget"
                )
            if (
                subordinate_posture
                != EXPECTED_TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE
            ):
                fail(
                    f"{adjunct_location}.subordinate_posture must match the "
                    "current source-first subordinate posture"
                )
            if adjunct_match_key != "retrieval_id":
                fail(f"{adjunct_location}.match_key must equal 'retrieval_id'")
            if adjunct_target_value != TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID:
                fail(
                    f"{adjunct_location}.target_value must equal "
                    f"'{TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID}'"
                )
            if adjunct_route_id != TOS_ZARATHUSTRA_ROUTE_ID:
                fail(
                    f"{adjunct_location}.route_id must equal "
                    f"'{TOS_ZARATHUSTRA_ROUTE_ID}'"
                )
            resolve_known_ref(
                repo_ref(KAG_REPO, adjunct_surface_ref),
                label=f"{adjunct_location}.surface_ref",
            )
            surface = surfaces_by_id.get(adjunct_surface_id)
            if surface is None or surface.get("status") != "experimental":
                fail(f"{adjunct_location} must point to an experimental registry surface")
            if surface.get("name") != adjunct_surface_name:
                fail(
                    f"{adjunct_location}.surface_name must match registry surface "
                    f"'{surface.get('name')}'"
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
        expected_adjunct_surfaces = EXPECTED_FEDERATION_SPINE_ADJUNCTS_BY_REPO.get(repo_name)
        if expected_adjunct_surfaces is None:
            fail(f"{location}.repo '{repo_name}' is not allowed in the current spine scope")
        if normalized_adjunct_surfaces != expected_adjunct_surfaces:
            fail(
                f"{location}.adjunct_surfaces must match the current bounded adjunct "
                f"contract for '{repo_name}'"
            )

    if repo_order != EXPECTED_FEDERATION_SPINE_REPO_ORDER:
        fail("federation spine pack repos must keep the current stable repo order")
    validate_exact_set(
        seen_repos,
        EXPECTED_FEDERATION_SPINE_REPOS,
        label="federation spine pack repos",
    )
    if payload != expected_payload:
        fail("federation spine pack must match the committed manifest-driven federation payload")
