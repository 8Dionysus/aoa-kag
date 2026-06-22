from __future__ import annotations

from .common import *
from .local_contracts import *
from .source_refs import *

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

def validate_tos_text_chunk_map_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("ToS text chunk map pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "node_id",
        "node_type",
        "source_anchor",
        "authority_surface_ref",
        "route_ref",
        "capsule_ref",
        "interpretation_layers",
        "chunk_count",
        "chunks",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS text chunk map pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("ToS text chunk map pack pack_version must equal 1")
    if payload["pack_type"] != "tos_text_chunk_map":
        fail("ToS text chunk map pack pack_type must equal 'tos_text_chunk_map'")
    if payload["source_repo"] != TOS_REPO:
        fail("ToS text chunk map pack source_repo must equal 'Tree-of-Sophia'")
    if payload["source_manifest_ref"] != TOS_TEXT_CHUNK_MAP_MANIFEST_REF:
        fail(
            "ToS text chunk map pack source_manifest_ref must point to "
            f"{TOS_TEXT_CHUNK_MAP_MANIFEST_REF}"
        )
    if payload["bounded_output_contract"] != EXPECTED_TOS_TEXT_CHUNK_MAP_CONTRACT:
        fail("ToS text chunk map pack bounded_output_contract must match the current source-first guardrail")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS text chunk map pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str]] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"ToS text chunk map pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, role, ref)):
            fail(f"{location} must keep name, role, and ref")
        resolve_known_ref(ref, label=location)
        actual_source_inputs.add((name, role, ref))
    expected_source_inputs = {
        (
            source_input["name"],
            source_input["role"],
            source_input["ref"],
        )
        for source_input in expected_payload["source_inputs"]
        if isinstance(source_input, dict)
    }
    if actual_source_inputs != expected_source_inputs:
        fail("ToS text chunk map pack source_inputs must match the manifest-driven donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS text chunk map pack surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"ToS text chunk map pack surface_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
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
            fail(f"{location} must keep id, name, kind, slot, and source input")
        actual_bindings.add(
            (surface_id, surface_name, derived_kind, derived_slot, source_input)
        )
    if actual_bindings != EXPECTED_TOS_TEXT_CHUNK_MAP_BINDINGS:
        fail("ToS text chunk map pack surface_bindings must match the current bounded chunk-map contract")

    surface_id = payload["surface_id"]
    if surface_id != "AOA-K-0005":
        fail("ToS text chunk map pack surface_id must equal 'AOA-K-0005'")
    registry_surface = surfaces_by_id.get(surface_id)
    if registry_surface is None:
        fail("ToS text chunk map pack surface_id must exist in the generated registry")
    if registry_surface.get("status") != "experimental":
        fail("AOA-K-0005 must remain experimental in the generated registry")
    if payload["surface_name"] != "tos-text-chunk-map":
        fail("ToS text chunk map pack surface_name must equal 'tos-text-chunk-map'")
    if payload["node_id"] != expected_payload["node_id"]:
        fail("ToS text chunk map pack node_id must stay aligned with the current ToS authority surface")
    if payload["node_type"] != "source":
        fail("ToS text chunk map pack node_type must stay 'source'")
    if payload["source_anchor"] != expected_payload["source_anchor"]:
        fail("ToS text chunk map pack source_anchor must match the current ToS authority surface")

    for key in ("authority_surface_ref", "route_ref", "capsule_ref"):
        value = payload[key]
        if not isinstance(value, str) or not value:
            fail(f"ToS text chunk map pack {key} must be a non-empty string")
        resolve_known_ref(value, label=f"ToS text chunk map pack {key}")
        if value != expected_payload[key]:
            fail(f"ToS text chunk map pack {key} must stay aligned with the current bounded ToS route")

    interpretation_layers = validate_unique_string_list(
        payload["interpretation_layers"],
        label="ToS text chunk map pack interpretation_layers",
    )
    if interpretation_layers != expected_payload["interpretation_layers"]:
        fail("ToS text chunk map pack interpretation_layers must match the authority surface")

    chunks = payload["chunks"]
    if not isinstance(chunks, list) or not chunks:
        fail("ToS text chunk map pack chunks must be a non-empty list")
    chunk_count = payload["chunk_count"]
    if not isinstance(chunk_count, int) or chunk_count != len(chunks):
        fail("ToS text chunk map pack chunk_count must equal the number of chunks")

    expected_chunks = expected_payload["chunks"]
    if not isinstance(expected_chunks, list):
        fail("expected ToS text chunk map payload must declare chunks")
    expected_chunks_by_segment = {
        chunk["segment_id"]: chunk
        for chunk in expected_chunks
        if isinstance(chunk, dict) and isinstance(chunk.get("segment_id"), str)
    }
    if chunk_count != len(expected_chunks_by_segment):
        fail("ToS text chunk map pack chunk_count must equal the number of unique donor segment_ids")

    seen_segment_ids: set[str] = set()
    for index, chunk in enumerate(chunks):
        location = f"ToS text chunk map pack chunks[{index}]"
        if not isinstance(chunk, dict):
            fail(f"{location} must be an object")
        for key in (
            "chunk_id",
            "node_id",
            "segment_id",
            "source_anchor",
            "source_ref",
            "route_ref",
            "capsule_ref",
            "interpretation_layers",
            "witness_count",
            "witnesses",
        ):
            if key not in chunk:
                fail(f"{location} is missing required key '{key}'")
        segment_id = chunk["segment_id"]
        if not isinstance(segment_id, str) or not segment_id:
            fail(f"{location}.segment_id must be a non-empty string")
        if segment_id in seen_segment_ids:
            fail(f"{location}.segment_id '{segment_id}' is duplicated")
        seen_segment_ids.add(segment_id)
        expected_chunk = expected_chunks_by_segment.get(segment_id)
        if expected_chunk is None:
            fail(f"{location}.segment_id '{segment_id}' is not present in the bounded ToS authority surface")

        witnesses = chunk["witnesses"]
        if not isinstance(witnesses, list) or not witnesses:
            fail(f"{location}.witnesses must be a non-empty list")
        witness_count = chunk["witness_count"]
        if not isinstance(witness_count, int) or witness_count != len(witnesses):
            fail(f"{location}.witness_count must equal the number of witnesses")
        for witness_index, witness in enumerate(witnesses):
            witness_location = f"{location}.witnesses[{witness_index}]"
            if not isinstance(witness, dict):
                fail(f"{witness_location} must be an object")
            for key in ("language", "role", "text"):
                if key not in witness:
                    fail(f"{witness_location} is missing required key '{key}'")
                if not isinstance(witness[key], str) or not witness[key]:
                    fail(f"{witness_location}.{key} must be a non-empty string")

        translation_tension = chunk.get("translation_tension")
        if translation_tension is not None:
            if not isinstance(translation_tension, dict):
                fail(f"{location}.translation_tension must be an object when present")
            if translation_tension.get("segment_id") != segment_id:
                fail(f"{location}.translation_tension.segment_id must match the chunk segment_id")
            if not isinstance(translation_tension.get("note"), str) or not translation_tension["note"]:
                fail(f"{location}.translation_tension.note must be a non-empty string")

        if chunk != expected_chunk:
            fail(f"{location} must match the committed source-linked chunk payload for segment '{segment_id}'")

    if seen_segment_ids != set(expected_chunks_by_segment):
        fail("ToS text chunk map pack must cover every unique donor segment_id exactly once")

def validate_tos_retrieval_axis_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("ToS retrieval axis pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "axis_count",
        "axes",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS retrieval axis pack is missing required key '{key}'")

    if payload["pack_type"] != "tos_retrieval_axis_pack":
        fail("ToS retrieval axis pack pack_type must equal 'tos_retrieval_axis_pack'")
    if payload["bounded_output_contract"] != EXPECTED_TOS_RETRIEVAL_AXIS_CONTRACT:
        fail("ToS retrieval axis pack bounded_output_contract must match the current source-first guardrail")
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("ToS retrieval axis pack source_inputs must match the manifest-driven donor set")
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail("ToS retrieval axis pack surface_bindings must match the current bounded retrieval binding")

    surface_0007 = surfaces_by_id.get("AOA-K-0007")
    if surface_0007 is None or surface_0007.get("status") != "experimental":
        fail("ToS retrieval axis pack requires AOA-K-0007 to remain experimental in the generated registry")

    axes = payload["axes"]
    if not isinstance(axes, list) or len(axes) != 1:
        fail("ToS retrieval axis pack must contain exactly one axis in the current pilot")
    if payload["axis_count"] != 1:
        fail("ToS retrieval axis pack axis_count must equal 1 in the current pilot")
    axis = axes[0]
    if not isinstance(axis, dict):
        fail("ToS retrieval axis pack axis must be an object")
    for key in (
        "chunk_map_ref",
        "source_refs",
        "lineage_refs",
        "conflict_refs",
        "practice_refs",
        "bridge_surface_ref",
        "bridge_envelope_ref",
        "memo_face_refs",
    ):
        value = axis.get(key)
        if value is None:
            fail(f"ToS retrieval axis pack axis is missing required key '{key}'")
    resolve_known_ref(axis["chunk_map_ref"], label="ToS retrieval axis pack chunk_map_ref")
    resolve_known_ref(axis["bridge_surface_ref"], label="ToS retrieval axis pack bridge_surface_ref")
    resolve_known_ref(axis["bridge_envelope_ref"], label="ToS retrieval axis pack bridge_envelope_ref")
    for ref_list_key in ("source_refs", "lineage_refs", "conflict_refs", "practice_refs", "memo_face_refs"):
        refs = validate_unique_string_list(axis[ref_list_key], label=f"ToS retrieval axis pack {ref_list_key}")
        for ref in refs:
            resolve_known_ref(ref, label=f"ToS retrieval axis pack {ref_list_key}")

    if payload != expected_payload:
        fail("ToS retrieval axis pack must match the committed manifest-driven retrieval-axis payload")

def validate_tos_zarathustra_route_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("ToS Zarathustra route pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "route_id",
        "route_capsule_ref",
        "relation_pack_ref",
        "node_count",
        "edge_count",
        "node_type_counts",
        "edge_kind_counts",
        "nodes",
        "edges",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"ToS Zarathustra route pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("ToS Zarathustra route pack pack_version must equal 1")
    if payload["pack_type"] != "tos_zarathustra_route_pack":
        fail("ToS Zarathustra route pack pack_type must equal 'tos_zarathustra_route_pack'")
    if payload["source_repo"] != TOS_REPO:
        fail("ToS Zarathustra route pack source_repo must equal 'Tree-of-Sophia'")
    if payload["source_manifest_ref"] != TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_REF:
        fail(
            "ToS Zarathustra route pack source_manifest_ref must point to "
            f"{TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_REF}"
        )
    if payload["route_id"] != TOS_ZARATHUSTRA_ROUTE_ID:
        fail(
            "ToS Zarathustra route pack route_id must equal "
            f"'{TOS_ZARATHUSTRA_ROUTE_ID}'"
        )
    if payload["bounded_output_contract"] != EXPECTED_TOS_ZARATHUSTRA_ROUTE_PACK_CONTRACT:
        fail(
            "ToS Zarathustra route pack bounded_output_contract must match the current "
            "source-first guardrail"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail(
            "ToS Zarathustra route pack source_inputs must match the manifest-driven "
            "canonical donor set"
        )
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail(
            "ToS Zarathustra route pack surface_bindings must match the current "
            "bounded route-pack binding"
        )

    surface_0010 = surfaces_by_id.get("AOA-K-0010")
    if surface_0010 is None or surface_0010.get("status") != "experimental":
        fail(
            "ToS Zarathustra route pack requires AOA-K-0010 to remain experimental in "
            "the generated registry"
        )

    route_capsule_ref = payload["route_capsule_ref"]
    relation_pack_ref = payload["relation_pack_ref"]
    if not isinstance(route_capsule_ref, str) or not route_capsule_ref:
        fail("ToS Zarathustra route pack route_capsule_ref must be a non-empty string")
    if not isinstance(relation_pack_ref, str) or not relation_pack_ref:
        fail("ToS Zarathustra route pack relation_pack_ref must be a non-empty string")
    resolve_known_ref(route_capsule_ref, label="ToS Zarathustra route pack route_capsule_ref")
    resolve_known_ref(relation_pack_ref, label="ToS Zarathustra route pack relation_pack_ref")
    if route_capsule_ref != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH):
        fail(
            "ToS Zarathustra route pack route_capsule_ref must stay aligned with the "
            "canonical Zarathustra route capsule"
        )
    if relation_pack_ref != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH):
        fail(
            "ToS Zarathustra route pack relation_pack_ref must stay aligned with the "
            "canonical ToS relation pack"
        )

    nodes = payload["nodes"]
    if not isinstance(nodes, list) or len(nodes) != sum(TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS.values()):
        fail("ToS Zarathustra route pack must contain exactly 92 nodes")
    if payload["node_count"] != len(nodes):
        fail("ToS Zarathustra route pack node_count must equal the number of nodes")
    if payload["node_type_counts"] != TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS:
        fail("ToS Zarathustra route pack node_type_counts must match the current canonical route")

    actual_node_type_counts = {key: 0 for key in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS}
    seen_node_ids: set[str] = set()
    seen_authority_refs: set[str] = set()
    actual_node_type_order: list[str] = []
    for index, node in enumerate(nodes):
        location = f"ToS Zarathustra route pack nodes[{index}]"
        if not isinstance(node, dict):
            fail(f"{location} must be an object")
        for key in (
            "node_id",
            "node_type",
            "authority_ref",
            "source_anchor",
            "key_terms",
            "distilled_thesis",
            "interpretation_layers",
        ):
            if key not in node:
                fail(f"{location} is missing required key '{key}'")
        node_id = node["node_id"]
        node_type = node["node_type"]
        authority_ref = node["authority_ref"]
        if not isinstance(node_id, str) or not node_id.startswith("tos."):
            fail(f"{location}.node_id must be a canonical tos.* id")
        if node_id.startswith("literal."):
            fail(f"{location}.node_id must not carry literal residue")
        if node_id in seen_node_ids:
            fail(f"{location}.node_id '{node_id}' is duplicated")
        seen_node_ids.add(node_id)
        if node_type not in actual_node_type_counts:
            fail(f"{location}.node_type '{node_type}' is not allowed in the route pack")
        actual_node_type_counts[node_type] += 1
        actual_node_type_order.append(node_type)
        if not isinstance(authority_ref, str) or not authority_ref.startswith("Tree-of-Sophia/ToS/canon/"):
            fail(f"{location}.authority_ref must point into Tree-of-Sophia/ToS/canon/**/node.json")
        if not authority_ref.endswith("/node.json"):
            fail(f"{location}.authority_ref must resolve to a canonical node.json file")
        if "/intake/" in authority_ref or authority_ref.startswith("Tree-of-Sophia/intake/"):
            fail(f"{location}.authority_ref must not point at Tree-of-Sophia/intake")
        if authority_ref in seen_authority_refs:
            fail(
                f"{location}.authority_ref '{authority_ref}' is duplicated and would "
                "collapse distinct canonical nodes into one projection handle"
            )
        seen_authority_refs.add(authority_ref)
        resolve_known_ref(authority_ref, label=f"{location}.authority_ref")
        validate_unique_string_list(node["key_terms"], label=f"{location}.key_terms")
        validate_unique_string_list(
            node["interpretation_layers"],
            label=f"{location}.interpretation_layers",
        )
        if not isinstance(node["source_anchor"], str) or not node["source_anchor"]:
            fail(f"{location}.source_anchor must be a non-empty string")
        if not isinstance(node["distilled_thesis"], str) or not node["distilled_thesis"]:
            fail(f"{location}.distilled_thesis must be a non-empty string")

    if actual_node_type_counts != TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS:
        fail(
            "ToS Zarathustra route pack nodes must preserve the current family counts "
            "across the canonical route"
        )
    expected_node_type_order = [
        node_type
        for node_type in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER
        for _ in range(TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS[node_type])
    ]
    if actual_node_type_order != expected_node_type_order:
        fail(
            "ToS Zarathustra route pack nodes must preserve the current family order "
            "source -> concept -> principle -> lineage -> event -> state -> support "
            "-> analogy -> synthesis"
        )

    edges = payload["edges"]
    if not isinstance(edges, list) or len(edges) != sum(TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS.values()):
        fail("ToS Zarathustra route pack must contain exactly 125 edges")
    if payload["edge_count"] != len(edges):
        fail("ToS Zarathustra route pack edge_count must equal the number of edges")
    if payload["edge_kind_counts"] != TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS:
        fail("ToS Zarathustra route pack edge_kind_counts must match the canonical relation pack")

    actual_edge_kind_counts = {key: 0 for key in TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS}
    actual_edge_ids: list[str] = []
    expected_edge_ids = [
        edge["edge_id"]
        for edge in expected_payload["edges"]
        if isinstance(edge, dict) and isinstance(edge.get("edge_id"), str)
    ]
    for index, edge in enumerate(edges):
        location = f"ToS Zarathustra route pack edges[{index}]"
        if not isinstance(edge, dict):
            fail(f"{location} must be an object")
        for key in (
            "edge_id",
            "edge_kind",
            "from_id",
            "predicate_id",
            "to_id",
            "layer",
            "anchor_mode",
            "anchor_start_secondary",
            "anchor_end_secondary",
            "anchor_segment_ids",
            "witness_scope",
            "connectivity_role",
            "confidence",
            "note",
        ):
            if key not in edge:
                fail(f"{location} is missing required key '{key}'")
        edge_id = edge["edge_id"]
        if not isinstance(edge_id, str) or not edge_id:
            fail(f"{location}.edge_id must be a non-empty string")
        actual_edge_ids.append(edge_id)
        edge_kind = edge["edge_kind"]
        if edge_kind not in actual_edge_kind_counts:
            fail(f"{location}.edge_kind '{edge_kind}' is not allowed in the route pack")
        actual_edge_kind_counts[edge_kind] += 1
        for endpoint_key in ("from_id", "to_id"):
            endpoint = edge[endpoint_key]
            if not isinstance(endpoint, str) or not endpoint.startswith("tos."):
                fail(f"{location}.{endpoint_key} must keep canonical tos.* ids")
            if endpoint.startswith("literal."):
                fail(f"{location}.{endpoint_key} must not carry literal residue")
            if endpoint not in seen_node_ids:
                fail(
                    f"{location}.{endpoint_key} '{endpoint}' must resolve to a node_id "
                    "projected into the same route pack"
                )
        if not isinstance(edge["predicate_id"], str) or not edge["predicate_id"]:
            fail(f"{location}.predicate_id must be a non-empty string")
        if not isinstance(edge["confidence"], int):
            fail(f"{location}.confidence must remain integer-valued")
    if actual_edge_kind_counts != TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS:
        fail(
            "ToS Zarathustra route pack edges must preserve the current canonical "
            "edge-kind counts"
        )
    if actual_edge_ids != expected_edge_ids:
        fail(
            "ToS Zarathustra route pack edges must preserve the canonical relation "
            "pack row order"
        )

    if payload != expected_payload:
        fail(
            "ToS Zarathustra route pack must match the committed manifest-driven "
            "canonical route payload"
        )

def validate_tos_zarathustra_route_retrieval_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
    route_pack_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("ToS Zarathustra route retrieval pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "adjunct_budget",
        "subordinate_posture",
        "route_count",
        "routes",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(
                "ToS Zarathustra route retrieval pack is missing required key "
                f"'{key}'"
            )

    if payload["pack_version"] != 1:
        fail("ToS Zarathustra route retrieval pack pack_version must equal 1")
    if payload["pack_type"] != "tos_zarathustra_route_retrieval_pack":
        fail(
            "ToS Zarathustra route retrieval pack pack_type must equal "
            "'tos_zarathustra_route_retrieval_pack'"
        )
    if (
        payload["source_manifest_ref"]
        != TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_REF
    ):
        fail(
            "ToS Zarathustra route retrieval pack source_manifest_ref must point to "
            f"{TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_REF}"
        )
    if (
        payload["bounded_output_contract"]
        != EXPECTED_TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_CONTRACT
    ):
        fail(
            "ToS Zarathustra route retrieval pack bounded_output_contract must "
            "match the current source-first guardrail"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail(
            "ToS Zarathustra route retrieval pack source_inputs must match the "
            "single-donor route-pack contract"
        )
    if payload["adjunct_budget"] != EXPECTED_TOS_STANDALONE_ADJUNCT_BUDGET:
        fail(
            "ToS Zarathustra route retrieval pack adjunct_budget must match the "
            "current standalone adjunct budget"
        )
    if (
        payload["subordinate_posture"]
        != EXPECTED_TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE
    ):
        fail(
            "ToS Zarathustra route retrieval pack subordinate_posture must match "
            "the current source-first subordinate posture"
        )
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail(
            "ToS Zarathustra route retrieval pack surface_bindings must match the "
            "current bounded retrieval binding"
        )

    surface_0011 = surfaces_by_id.get("AOA-K-0011")
    if surface_0011 is None or surface_0011.get("status") != "experimental":
        fail(
            "ToS Zarathustra route retrieval pack requires AOA-K-0011 to remain "
            "experimental in the generated registry"
        )

    if payload["route_count"] != 1:
        fail("ToS Zarathustra route retrieval pack route_count must equal 1")
    routes = payload["routes"]
    if not isinstance(routes, list) or len(routes) != 1:
        fail(
            "ToS Zarathustra route retrieval pack must contain exactly one route in "
            "the current pilot"
        )
    route = routes[0]
    if not isinstance(route, dict):
        fail("ToS Zarathustra route retrieval pack route must be an object")

    for key in (
        "retrieval_id",
        "route_id",
        "route_pack_ref",
        "route_capsule_ref",
        "relation_pack_ref",
        "node_type_counts",
        "edge_kind_counts",
        "source_handles",
        "concept_handles",
        "principle_handles",
        "lineage_handles",
        "event_handles",
        "state_handles",
        "support_handles",
        "analogy_handles",
        "synthesis_handles",
        "retrieval_summary",
    ):
        if key not in route:
            fail(
                "ToS Zarathustra route retrieval pack route is missing required key "
                f"'{key}'"
            )

    if route["retrieval_id"] != TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID:
        fail(
            "ToS Zarathustra route retrieval pack retrieval_id must stay aligned "
            "with AOA-K-0011"
        )
    if route["route_id"] != TOS_ZARATHUSTRA_ROUTE_ID:
        fail(
            "ToS Zarathustra route retrieval pack route_id must equal "
            f"'{TOS_ZARATHUSTRA_ROUTE_ID}'"
        )
    if route["route_pack_ref"] != TOS_ZARATHUSTRA_ROUTE_PACK_INPUT_REF:
        fail(
            "ToS Zarathustra route retrieval pack route_pack_ref must point to "
            f"{TOS_ZARATHUSTRA_ROUTE_PACK_INPUT_REF}"
        )
    if "/intake/" in route["route_pack_ref"] or route["route_pack_ref"].startswith("Tree-of-Sophia/intake/"):
        fail("ToS Zarathustra route retrieval pack route_pack_ref must not point at intake")
    resolve_known_ref(
        route["route_pack_ref"],
        label="ToS Zarathustra route retrieval pack route_pack_ref",
    )
    resolve_known_ref(
        route["route_capsule_ref"],
        label="ToS Zarathustra route retrieval pack route_capsule_ref",
    )
    resolve_known_ref(
        route["relation_pack_ref"],
        label="ToS Zarathustra route retrieval pack relation_pack_ref",
    )
    if route["route_capsule_ref"] != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH):
        fail(
            "ToS Zarathustra route retrieval pack route_capsule_ref must stay "
            "aligned with the canonical Zarathustra capsule"
        )
    if (
        route["relation_pack_ref"]
        != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH)
    ):
        fail(
            "ToS Zarathustra route retrieval pack relation_pack_ref must stay "
            "aligned with the canonical ToS relation pack"
        )
    route_pack_nodes = route_pack_payload.get("nodes")
    if not isinstance(route_pack_nodes, list):
        fail("ToS Zarathustra route retrieval pack validation requires AOA-K-0010 nodes[]")
    if route["route_capsule_ref"] != route_pack_payload.get("route_capsule_ref"):
        fail(
            "ToS Zarathustra route retrieval pack route_capsule_ref must match the "
            "live AOA-K-0010 route_capsule_ref"
        )
    if route["relation_pack_ref"] != route_pack_payload.get("relation_pack_ref"):
        fail(
            "ToS Zarathustra route retrieval pack relation_pack_ref must match the "
            "live AOA-K-0010 relation_pack_ref"
        )
    if route["node_type_counts"] != route_pack_payload.get("node_type_counts"):
        fail(
            "ToS Zarathustra route retrieval pack node_type_counts must match the "
            "live AOA-K-0010 counts"
        )
    if route["edge_kind_counts"] != route_pack_payload.get("edge_kind_counts"):
        fail(
            "ToS Zarathustra route retrieval pack edge_kind_counts must match the "
            "live AOA-K-0010 counts"
        )
    if route["retrieval_summary"] != TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_SUMMARY:
        fail(
            "ToS Zarathustra route retrieval pack retrieval_summary must match the "
            "current bounded adjunct wording"
        )

    route_pack_nodes_by_type = {
        node_type: [
            {
                "node_id": node["node_id"],
                "authority_ref": node["authority_ref"],
            }
            for node in route_pack_nodes
            if isinstance(node, dict) and node.get("node_type") == node_type
        ]
        for node_type in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER
    }
    seen_handle_node_ids: set[str] = set()
    for node_type, expected_count in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS.items():
        handle_key = f"{node_type}_handles"
        handles = route[handle_key]
        if not isinstance(handles, list) or len(handles) != expected_count:
            fail(
                "ToS Zarathustra route retrieval pack must preserve the current "
                f"handle count for '{node_type}'"
            )
        seen_node_ids: set[str] = set()
        normalized_handles: list[dict[str, str]] = []
        for index, handle in enumerate(handles):
            location = (
                "ToS Zarathustra route retrieval pack "
                f"{handle_key}[{index}]"
            )
            if not isinstance(handle, dict):
                fail(f"{location} must be an object")
            if set(handle) != {"node_id", "authority_ref"}:
                fail(
                    f"{location} must keep exactly node_id and authority_ref in the "
                    "handles-only retrieval scope"
                )
            node_id = handle["node_id"]
            authority_ref = handle["authority_ref"]
            if not isinstance(node_id, str) or not node_id.startswith("tos."):
                fail(f"{location}.node_id must keep canonical tos.* ids")
            if node_id.startswith("literal."):
                fail(f"{location}.node_id must not carry literal residue")
            if node_id in seen_node_ids:
                fail(f"{location}.node_id '{node_id}' is duplicated")
            seen_node_ids.add(node_id)
            seen_handle_node_ids.add(node_id)
            if not isinstance(authority_ref, str) or not authority_ref.startswith("Tree-of-Sophia/ToS/canon/"):
                fail(f"{location}.authority_ref must point into Tree-of-Sophia/ToS/canon/**/node.json")
            if not authority_ref.endswith("/node.json"):
                fail(f"{location}.authority_ref must resolve to a canonical node.json file")
            if authority_ref.startswith("Tree-of-Sophia/intake/") or "/intake/" in authority_ref:
                fail(f"{location}.authority_ref must not point at Tree-of-Sophia/intake")
            if authority_ref.startswith("aoa-memo/") or authority_ref.startswith("aoa-routing/"):
                fail(f"{location}.authority_ref must not point at aoa-memo or aoa-routing")
            resolve_known_ref(authority_ref, label=f"{location}.authority_ref")
            normalized_handles.append(
                {
                    "node_id": node_id,
                    "authority_ref": authority_ref,
                }
            )
        if normalized_handles != route_pack_nodes_by_type[node_type]:
            fail(
                "ToS Zarathustra route retrieval pack must preserve family handle "
                f"order and authority parity with AOA-K-0010 for '{node_type}'"
            )

    route_pack_node_ids = {
        node["node_id"]
        for node in route_pack_nodes
        if isinstance(node, dict) and isinstance(node.get("node_id"), str)
    }
    if seen_handle_node_ids != route_pack_node_ids:
        fail(
            "ToS Zarathustra route retrieval pack handles must cover exactly the "
            "node set published by AOA-K-0010"
        )

    if payload != expected_payload:
        fail(
            "ToS Zarathustra route retrieval pack must match the committed "
            "manifest-driven retrieval payload"
        )

def validate_reasoning_handoff_pack(payload: object) -> None:
    if not isinstance(payload, dict):
        fail("reasoning handoff pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "scenario_count",
        "scenarios",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"reasoning handoff pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("reasoning handoff pack pack_version must equal 1")
    if payload["pack_type"] != "reasoning_handoff_pack":
        fail("reasoning handoff pack pack_type must equal 'reasoning_handoff_pack'")
    if payload["source_manifest_ref"] != REASONING_HANDOFF_MANIFEST_REF:
        fail(
            "reasoning handoff pack source_manifest_ref must point to "
            f"{REASONING_HANDOFF_MANIFEST_REF}"
        )
    if payload["bounded_output_contract"] != EXPECTED_REASONING_HANDOFF_CONTRACT:
        fail("reasoning handoff pack bounded_output_contract must match the current source-first guardrail")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("reasoning handoff pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"reasoning handoff pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, repo, role, ref)):
            fail(f"{location} must keep name, repo, role, and ref")
        resolve_known_ref(ref, label=location)
        relative_ref = ref if repo == "aoa-kag" else ref.split("/", 1)[1]
        actual_source_inputs.add((name, repo, relative_ref, role))
    if actual_source_inputs != EXPECTED_REASONING_HANDOFF_INPUTS:
        fail("reasoning handoff pack source_inputs must match the manifest-driven donor set")

    scenarios = payload["scenarios"]
    if not isinstance(scenarios, list) or not scenarios:
        fail("reasoning handoff pack scenarios must be a non-empty list")
    scenario_count = payload["scenario_count"]
    if not isinstance(scenario_count, int) or scenario_count != len(scenarios):
        fail("reasoning handoff pack scenario_count must equal the number of scenarios")

    seen_scenarios: set[str] = set()
    for index, scenario in enumerate(scenarios):
        location = f"reasoning handoff pack scenarios[{index}]"
        if not isinstance(scenario, dict):
            fail(f"{location} must be an object")
        for key in (
            "scenario_ref",
            "playbook_ref",
            "artifact_spine",
            "eval_bridge",
            "memo_bridge",
            "compatible_query_modes",
            "authoritative_refs",
            "return_contract",
            "boundary_guardrails",
        ):
            if key not in scenario:
                fail(f"{location} is missing required key '{key}'")

        scenario_ref = scenario["scenario_ref"]
        playbook_ref = scenario["playbook_ref"]
        if not isinstance(scenario_ref, str) or not re.match(r"^AOA-P-[0-9]{4}$", scenario_ref):
            fail(f"{location}.scenario_ref must be an AOA playbook id")
        if scenario_ref in seen_scenarios:
            fail(f"{location}.scenario_ref '{scenario_ref}' is duplicated")
        seen_scenarios.add(scenario_ref)
        if not isinstance(playbook_ref, str) or not playbook_ref.startswith("aoa-playbooks/"):
            fail(f"{location}.playbook_ref must point to aoa-playbooks")
        resolve_known_ref(playbook_ref, label=f"{location}.playbook_ref")

        query_modes = validate_unique_string_list(
            scenario["compatible_query_modes"],
            label=f"{location}.compatible_query_modes",
        )
        validate_exact_set(
            query_modes,
            ALLOWED_QUERY_MODES,
            label=f"{location}.compatible_query_modes",
        )

        return_contract = scenario["return_contract"]
        if not isinstance(return_contract, dict):
            fail(f"{location}.return_contract must be an object")
        must_include = validate_unique_string_list(
            return_contract.get("must_include"),
            label=f"{location}.return_contract.must_include",
        )
        validate_exact_set(
            must_include,
            EXPECTED_RETURN_MUST_INCLUDE,
            label=f"{location}.return_contract.must_include",
        )
        may_include = validate_unique_string_list(
            return_contract.get("may_include"),
            label=f"{location}.return_contract.may_include",
            allow_empty=True,
        )
        validate_exact_set(
            may_include,
            EXPECTED_RETURN_MAY_INCLUDE,
            label=f"{location}.return_contract.may_include",
        )
        normalized_return_fields = validate_unique_string_list(
            return_contract.get("normalized_return_fields"),
            label=f"{location}.return_contract.normalized_return_fields",
        )
        if normalized_return_fields != ["axis_summary"]:
            fail(f"{location}.return_contract.normalized_return_fields must equal ['axis_summary']")

        if scenario["boundary_guardrails"] != EXPECTED_BOUNDARY_GUARDRAILS:
            fail(f"{location}.boundary_guardrails must match the current handoff guardrail contract")

        authoritative_refs = scenario["authoritative_refs"]
        if not isinstance(authoritative_refs, dict):
            fail(f"{location}.authoritative_refs must be an object")
        for key, prefix in (
            ("playbook_refs", "aoa-playbooks/"),
            ("eval_refs", "aoa-evals/"),
            ("memo_refs", "aoa-memo/"),
        ):
            refs = validate_unique_string_list(
                authoritative_refs.get(key),
                label=f"{location}.authoritative_refs.{key}",
            )
            for ref in refs:
                if not ref.startswith(prefix):
                    fail(f"{location}.authoritative_refs.{key} contains a ref outside {prefix}")
                resolve_known_ref(ref, label=f"{location}.authoritative_refs.{key}")
        guardrail_refs = validate_unique_string_list(
            authoritative_refs.get("kag_guardrail_refs"),
            label=f"{location}.authoritative_refs.kag_guardrail_refs",
        )
        if guardrail_refs != EXPECTED_REASONING_HANDOFF_KAG_GUARDRAIL_REFS:
            fail(f"{location}.authoritative_refs.kag_guardrail_refs must match the local KAG guardrail refs")
        for ref in guardrail_refs:
            resolve_known_ref(ref, label=f"{location}.authoritative_refs.kag_guardrail_refs")
        artifact_schema_refs = validate_unique_string_list(
            authoritative_refs.get("artifact_schema_refs"),
            label=f"{location}.authoritative_refs.artifact_schema_refs",
        )
        for ref in artifact_schema_refs:
            if not ref.endswith(".schema.json"):
                fail(f"{location}.authoritative_refs.artifact_schema_refs must only contain schema refs")
            resolve_known_ref(ref, label=f"{location}.authoritative_refs.artifact_schema_refs")

        artifact_spine = scenario["artifact_spine"]
        if not isinstance(artifact_spine, dict):
            fail(f"{location}.artifact_spine must be an object")
        verification_surface = validate_reasoning_artifact_descriptor(
            artifact_spine.get("verification_surface"),
            label=f"{location}.artifact_spine.verification_surface",
        )
        continuity_surface = artifact_spine.get("continuity_surface")
        if continuity_surface is not None:
            validate_reasoning_artifact_descriptor(
                continuity_surface,
                label=f"{location}.artifact_spine.continuity_surface",
            )
        supporting_artifacts = artifact_spine.get("supporting_artifacts")
        if not isinstance(supporting_artifacts, list):
            fail(f"{location}.artifact_spine.supporting_artifacts must be a list")
        supporting_names: list[str] = []
        for artifact_index, artifact in enumerate(supporting_artifacts):
            descriptor = validate_reasoning_artifact_descriptor(
                artifact,
                label=f"{location}.artifact_spine.supporting_artifacts[{artifact_index}]",
            )
            supporting_names.append(descriptor["artifact_name"])
        optional_trace_sidecars = artifact_spine.get("optional_trace_sidecars")
        if not isinstance(optional_trace_sidecars, list):
            fail(f"{location}.artifact_spine.optional_trace_sidecars must be a list")
        trace_sidecar_names: list[str] = []
        for artifact_index, artifact in enumerate(optional_trace_sidecars):
            descriptor = validate_reasoning_artifact_descriptor(
                artifact,
                label=f"{location}.artifact_spine.optional_trace_sidecars[{artifact_index}]",
            )
            trace_sidecar_names.append(descriptor["artifact_name"])

        eval_bridge = scenario["eval_bridge"]
        if not isinstance(eval_bridge, dict):
            fail(f"{location}.eval_bridge must be an object")
        eval_anchor_refs = validate_unique_string_list(
            eval_bridge.get("eval_anchor_refs"),
            label=f"{location}.eval_bridge.eval_anchor_refs",
        )
        for ref in eval_anchor_refs:
            resolve_known_ref(ref, label=f"{location}.eval_bridge.eval_anchor_refs")
        if eval_bridge.get("verification_surface") != verification_surface["artifact_name"]:
            fail(f"{location}.eval_bridge.verification_surface must match artifact_spine.verification_surface")
        trace_surfaces = validate_unique_string_list(
            eval_bridge.get("trace_surfaces"),
            label=f"{location}.eval_bridge.trace_surfaces",
            allow_empty=True,
        )
        for ref in trace_surfaces:
            resolve_known_ref(ref, label=f"{location}.eval_bridge.trace_surfaces")
        eval_contract_refs = validate_unique_string_list(
            eval_bridge.get("artifact_contract_refs"),
            label=f"{location}.eval_bridge.artifact_contract_refs",
        )
        for ref in eval_contract_refs:
            resolve_known_ref(ref, label=f"{location}.eval_bridge.artifact_contract_refs")
        report_expectation = eval_bridge.get("report_expectation")
        if not isinstance(report_expectation, dict):
            fail(f"{location}.eval_bridge.report_expectation must be an object")
        for key in ("report_format", "verdict_shape", "review_required"):
            if key not in report_expectation:
                fail(f"{location}.eval_bridge.report_expectation is missing '{key}'")

        memo_bridge = scenario["memo_bridge"]
        if not isinstance(memo_bridge, dict):
            fail(f"{location}.memo_bridge must be an object")
        memo_contract_refs = validate_unique_string_list(
            memo_bridge.get("memo_contract_refs"),
            label=f"{location}.memo_bridge.memo_contract_refs",
        )
        for ref in memo_contract_refs:
            resolve_known_ref(ref, label=f"{location}.memo_bridge.memo_contract_refs")
        memo_writeback_targets = validate_unique_string_list(
            memo_bridge.get("memo_writeback_targets"),
            label=f"{location}.memo_bridge.memo_writeback_targets",
        )
        delta_split = memo_bridge.get("delta_split")

        if scenario_ref == "AOA-P-0008":
            if verification_surface["artifact_name"] != "verification_result":
                fail(f"{location} must keep verification_result as the verification surface")
            if continuity_surface is not None:
                fail(f"{location} must not declare a continuity surface")
            if supporting_names != [
                "route_decision",
                "bounded_plan",
                "transition_decision",
                "distillation_pack",
            ]:
                fail(f"{location}.artifact_spine.supporting_artifacts must keep the bounded AOA-P-0008 route artifacts")
            if trace_sidecar_names != ["WitnessTrace"]:
                fail(f"{location}.artifact_spine.optional_trace_sidecars must keep WitnessTrace as the only optional sidecar")
            if trace_surfaces != ["aoa-memo/mechanics/recurrence-support/docs/WITNESS_TRACE_CONTRACT.md"]:
                fail(f"{location}.eval_bridge.trace_surfaces must keep the witness trace contract")
            if memo_writeback_targets != ["decision", "claim", "pattern"]:
                fail(f"{location}.memo_bridge.memo_writeback_targets must keep the bounded AOA-P-0008 writeback targets")
            if delta_split is not None:
                fail(f"{location}.memo_bridge.delta_split must stay null for AOA-P-0008")
            validate_exact_set(
                set(artifact_schema_refs),
                {
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.route_decision.schema.json",
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.bounded_plan.schema.json",
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.verification_result.schema.json",
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.transition_decision.schema.json",
                    "aoa-agents/mechanics/runtime-seam/parts/artifact-contracts/schemas/artifact.distillation_pack.schema.json",
                    "aoa-memo/mechanics/recurrence-support/parts/witness-trace-contract/schemas/witness-trace.schema.json",
                },
                label=f"{location}.authoritative_refs.artifact_schema_refs",
            )
        elif scenario_ref == "AOA-P-0009":
            if verification_surface["artifact_name"] != "inquiry_checkpoint":
                fail(f"{location} must keep inquiry_checkpoint as the verification surface")
            if not isinstance(continuity_surface, dict) or continuity_surface.get("artifact_name") != "inquiry_checkpoint":
                fail(f"{location} must keep inquiry_checkpoint as the continuity surface")
            if supporting_names != [
                "decision_ledger",
                "contradiction_map",
                "memory_delta",
                "canon_delta",
                "next_pass_brief",
            ]:
                fail(f"{location}.artifact_spine.supporting_artifacts must keep the bounded AOA-P-0009 route artifacts")
            if trace_sidecar_names:
                fail(f"{location}.artifact_spine.optional_trace_sidecars must stay empty for AOA-P-0009")
            if trace_surfaces:
                fail(f"{location}.eval_bridge.trace_surfaces must stay empty for AOA-P-0009")
            if memo_writeback_targets != ["state_capsule", "decision"]:
                fail(f"{location}.memo_bridge.memo_writeback_targets must keep the bounded AOA-P-0009 writeback targets")
            if not isinstance(delta_split, dict):
                fail(f"{location}.memo_bridge.delta_split must be an object for AOA-P-0009")
            expected_delta_split = {
                "memory_delta": {
                    "artifact_name": "memory_delta",
                    "checkpoint_field": "memory_delta_refs",
                    "field_contract_ref": "aoa-memo/mechanics/checkpoint/parts/checkpoint-carry-contract/schemas/inquiry_checkpoint.schema.json",
                },
                "canon_delta": {
                    "artifact_name": "canon_delta",
                    "checkpoint_field": "canon_delta_refs",
                    "field_contract_ref": "aoa-memo/mechanics/checkpoint/parts/checkpoint-carry-contract/schemas/inquiry_checkpoint.schema.json",
                },
            }
            if delta_split != expected_delta_split:
                fail(f"{location}.memo_bridge.delta_split must keep the explicit inquiry checkpoint memory/canon split")
            validate_exact_set(
                set(artifact_schema_refs),
                {
                    "aoa-memo/mechanics/checkpoint/parts/checkpoint-carry-contract/schemas/inquiry_checkpoint.schema.json",
                    "aoa-memo/mechanics/checkpoint/parts/checkpoint-to-memory-mapping/schemas/checkpoint-to-memory-contract.schema.json",
                },
                label=f"{location}.authoritative_refs.artifact_schema_refs",
            )
        else:
            fail(f"{location}.scenario_ref '{scenario_ref}' is not supported in this pack")

    validate_exact_set(
        seen_scenarios,
        EXPECTED_REASONING_HANDOFF_SCENARIOS,
        label="reasoning handoff pack scenarios",
    )

def validate_return_regrounding_pack(
    payload: object,
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("return regrounding pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "mode_count",
        "modes",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"return regrounding pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("return regrounding pack pack_version must equal 1")
    if payload["pack_type"] != "return_regrounding_pack":
        fail("return regrounding pack pack_type must equal 'return_regrounding_pack'")
    if payload["source_manifest_ref"] != RETURN_REGROUNDING_MANIFEST_REF:
        fail(
            "return regrounding pack source_manifest_ref must point to "
            f"{RETURN_REGROUNDING_MANIFEST_REF}"
        )
    if payload["bounded_output_contract"] != EXPECTED_RETURN_REGROUNDING_CONTRACT:
        fail("return regrounding pack bounded_output_contract must match the current source-first guardrail")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("return regrounding pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    source_input_order: list[str] = []
    for index, source_input in enumerate(source_inputs):
        location = f"return regrounding pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, repo, role, ref)):
            fail(f"{location} must keep name, repo, role, and ref")
        resolve_known_ref(ref, label=location)
        relative_ref = ref if repo == "aoa-kag" else ref.split("/", 1)[1]
        actual_source_inputs.add((name, repo, relative_ref, role))
        source_input_order.append(name)
    if actual_source_inputs != EXPECTED_RETURN_REGROUNDING_INPUTS:
        fail("return regrounding pack source_inputs must match the manifest-driven donor set")
    if source_input_order != EXPECTED_RETURN_REGROUNDING_INPUT_ORDER:
        fail("return regrounding pack source_inputs must keep the current additive donor order")

    modes = payload["modes"]
    if not isinstance(modes, list) or not modes:
        fail("return regrounding pack modes must be a non-empty list")
    mode_count = payload["mode_count"]
    if not isinstance(mode_count, int) or mode_count != len(modes):
        fail("return regrounding pack mode_count must equal the number of modes")

    seen_modes: set[str] = set()
    mode_order: list[str] = []
    counterpart_forbidden_refs = set(EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS) | {
        EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF,
        COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF,
    }

    for index, mode in enumerate(modes):
        location = f"return regrounding pack modes[{index}]"
        if not isinstance(mode, dict):
            fail(f"{location} must be an object")
        for key in (
            "mode_id",
            "used_when",
            "query_mode_hint",
            "trigger_surface_refs",
            "stronger_refs",
            "supporting_surface_refs",
            "preserved_fields",
            "reentry_note",
            "non_identity_boundary",
            "prohibited_promotions",
        ):
            if key not in mode:
                fail(f"{location} is missing required key '{key}'")

        mode_id = mode["mode_id"]
        used_when = mode["used_when"]
        query_mode_hint = mode["query_mode_hint"]
        reentry_note = mode["reentry_note"]
        non_identity_boundary = mode["non_identity_boundary"]
        if not isinstance(mode_id, str) or not mode_id:
            fail(f"{location}.mode_id must be a non-empty string")
        if mode_id in seen_modes:
            fail(f"{location}.mode_id '{mode_id}' is duplicated")
        seen_modes.add(mode_id)
        mode_order.append(mode_id)
        if not isinstance(used_when, str) or len(used_when) < 20:
            fail(f"{location}.used_when must be a string of length >= 20")
        if query_mode_hint not in {"local_search", "global_search", "drift_search", "consumer_read_path"}:
            fail(f"{location}.query_mode_hint '{query_mode_hint}' is not allowed")
        if not isinstance(reentry_note, str) or len(reentry_note) < 20:
            fail(f"{location}.reentry_note must be a string of length >= 20")
        if not isinstance(non_identity_boundary, str) or len(non_identity_boundary) < 20:
            fail(f"{location}.non_identity_boundary must be a string of length >= 20")

        trigger_surface_refs = validate_unique_string_list(
            mode["trigger_surface_refs"],
            label=f"{location}.trigger_surface_refs",
        )
        stronger_refs = validate_unique_string_list(
            mode["stronger_refs"],
            label=f"{location}.stronger_refs",
        )
        supporting_surface_refs = validate_unique_string_list(
            mode["supporting_surface_refs"],
            label=f"{location}.supporting_surface_refs",
        )
        preserved_fields = validate_unique_string_list(
            mode["preserved_fields"],
            label=f"{location}.preserved_fields",
        )
        prohibited_promotions = validate_unique_string_list(
            mode["prohibited_promotions"],
            label=f"{location}.prohibited_promotions",
        )

        for ref in trigger_surface_refs:
            resolve_known_ref(ref, label=f"{location}.trigger_surface_refs")
        for ref in stronger_refs:
            resolve_known_ref(ref, label=f"{location}.stronger_refs")
        for ref in supporting_surface_refs:
            resolve_known_ref(ref, label=f"{location}.supporting_surface_refs")

        if any(ref in counterpart_forbidden_refs for ref in stronger_refs):
            fail(f"{location}.stronger_refs must not promote counterpart review or contract refs into stronger authority")
        if any(ref.startswith(("generated/", "docs/", "examples/", "manifests/", "schemas/")) for ref in stronger_refs):
            fail(f"{location}.stronger_refs must not point to aoa-kag-local surfaces")

        if mode_id == "source_export_reentry":
            validate_exact_set(
                stronger_refs,
                {
                    "aoa-techniques/generated/kag_export.min.json",
                    "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json",
                },
                label=f"{location}.stronger_refs",
            )
            validate_exact_set(
                set(preserved_fields),
                {"provenance_note", "non_identity_boundary", "entry_surface_ref"},
                label=f"{location}.preserved_fields",
            )
        elif mode_id == "bridge_axis_reentry":
            if not all(ref.startswith("Tree-of-Sophia/") for ref in stronger_refs):
                fail(f"{location}.stronger_refs must stay ToS-owned for bridge axis regrounding")
            validate_exact_set(
                set(preserved_fields),
                {
                    "source_refs",
                    "lineage_refs",
                    "conflict_refs",
                    "practice_refs",
                    "axis_summary",
                },
                label=f"{location}.preserved_fields",
            )
        elif mode_id == "projection_boundary_reentry":
            validate_exact_set(
                stronger_refs,
                {
                    "aoa-techniques/generated/kag_export.min.json",
                    "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json",
                },
                label=f"{location}.stronger_refs",
            )
            if COUNTERPART_FEDERATION_EXPOSURE_REVIEW_DOC_REF not in supporting_surface_refs:
                fail(f"{location}.supporting_surface_refs must keep the counterpart exposure review as a supporting boundary ref")
        elif mode_id == "handoff_guardrail_reentry":
            if not all(
                ref.startswith(("aoa-playbooks/", "aoa-evals/", "aoa-memo/"))
                for ref in stronger_refs
            ):
                fail(f"{location}.stronger_refs must stay playbook/eval/memo-owned for handoff regrounding")
            validate_exact_set(
                set(preserved_fields),
                {
                    "source_refs",
                    "axis_summary",
                    "provenance_note",
                    "boundary_guardrails",
                },
                label=f"{location}.preserved_fields",
            )
        elif mode_id == "owner_boundary_reentry":
            if not all(ref.startswith(("aoa-memo/", "Tree-of-Sophia/")) for ref in stronger_refs):
                fail(f"{location}.stronger_refs must stay memo- or ToS-owned at the owner boundary")
            validate_exact_set(
                set(preserved_fields),
                {"source_refs", "provenance_note", "boundary_guardrails"},
                label=f"{location}.preserved_fields",
            )
        else:
            fail(f"{location}.mode_id '{mode_id}' is not supported")

    if mode_order != EXPECTED_RETURN_REGROUNDING_MODE_ORDER:
        fail("return regrounding pack modes must keep the current stable mode order")

    if payload != expected_payload:
        fail("return regrounding pack must match the committed manifest-driven regrounding payload")

def validate_kag_maturity_governance_pack(
    payload: object,
    expected_payload: dict[str, object],
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    if not isinstance(payload, dict):
        fail("KAG maturity governance pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "stability_tier_count",
        "stability_tiers",
        "surface_count",
        "surfaces",
        "owner_wait_state_count",
        "owner_wait_states",
        "stop_rule",
        "projection_recovery",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"KAG maturity governance pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("KAG maturity governance pack pack_version must equal 1")
    if payload["pack_type"] != "kag_maturity_governance":
        fail("KAG maturity governance pack pack_type must equal 'kag_maturity_governance'")
    if payload["source_manifest_ref"] != KAG_MATURITY_GOVERNANCE_MANIFEST_REF:
        fail(
            "KAG maturity governance pack source_manifest_ref must point to "
            f"{KAG_MATURITY_GOVERNANCE_MANIFEST_REF}"
        )
    if payload["bounded_output_contract"] != EXPECTED_KAG_MATURITY_GOVERNANCE_CONTRACT:
        fail("KAG maturity governance pack bounded_output_contract must match the current source-first stop-rule contract")

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("KAG maturity governance pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str, str]] = set()
    source_input_order: list[str] = []
    for index, source_input in enumerate(source_inputs):
        location = f"KAG maturity governance pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        repo = source_input.get("repo")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, repo, role, ref)):
            fail(f"{location} must keep name, repo, role, and ref")
        resolve_known_ref(ref, label=location)
        relative_ref = ref if repo == "aoa-kag" else ref.split("/", 1)[1]
        actual_source_inputs.add((name, repo, relative_ref, role))
        source_input_order.append(name)
    if actual_source_inputs != EXPECTED_KAG_MATURITY_GOVERNANCE_INPUTS:
        fail("KAG maturity governance pack source_inputs must match the manifest-driven donor set")
    if source_input_order != EXPECTED_KAG_MATURITY_GOVERNANCE_INPUT_ORDER:
        fail("KAG maturity governance pack source_inputs must keep the current donor order")

    stability_tiers = payload["stability_tiers"]
    if not isinstance(stability_tiers, list) or not stability_tiers:
        fail("KAG maturity governance pack stability_tiers must be a non-empty list")
    if payload["stability_tier_count"] != len(stability_tiers):
        fail("KAG maturity governance pack stability_tier_count must equal the number of tiers")
    tier_order: list[str] = []
    tier_status_map: dict[str, list[str]] = {}
    for index, tier in enumerate(stability_tiers):
        location = f"KAG maturity governance pack stability_tiers[{index}]"
        if not isinstance(tier, dict):
            fail(f"{location} must be an object")
        for key in (
            "tier",
            "registry_statuses",
            "consumer_posture",
            "expansion_posture",
            "live_payload_allowed",
        ):
            if key not in tier:
                fail(f"{location} is missing required key '{key}'")
        tier_name = tier["tier"]
        registry_statuses = validate_unique_string_list(
            tier["registry_statuses"],
            label=f"{location}.registry_statuses",
        )
        tier_order.append(tier_name)
        expected_statuses, expected_live_payload_allowed = (
            EXPECTED_KAG_MATURITY_GOVERNANCE_TIER_STATUS_MAP.get(tier_name, (None, None))
        )
        if expected_statuses is None:
            fail(f"{location}.tier '{tier_name}' is not supported")
        if registry_statuses != expected_statuses:
            fail(f"{location}.registry_statuses must match the current tier-to-status mapping")
        if tier["live_payload_allowed"] != expected_live_payload_allowed:
            fail(f"{location}.live_payload_allowed must match the current tier contract")
        tier_status_map[tier_name] = registry_statuses
    if tier_order != EXPECTED_KAG_MATURITY_GOVERNANCE_TIER_ORDER:
        fail("KAG maturity governance pack stability_tiers must keep the current stable order")

    surfaces = payload["surfaces"]
    if not isinstance(surfaces, list) or not surfaces:
        fail("KAG maturity governance pack surfaces must be a non-empty list")
    if payload["surface_count"] != len(surfaces):
        fail("KAG maturity governance pack surface_count must equal the number of surfaces")
    seen_surface_ids: set[str] = set()
    for index, surface in enumerate(surfaces):
        location = f"KAG maturity governance pack surfaces[{index}]"
        if not isinstance(surface, dict):
            fail(f"{location} must be an object")
        required_keys = {
            "surface_id",
            "surface_name",
            "registry_status",
            "source_repos",
            "derived_kind",
            "stability_tier",
            "consumer_posture",
            "proof_expectation_refs",
            "regrounding_mode_refs",
            "quarantine_policy",
            "stop_rule",
        }
        if not required_keys.issubset(surface):
            missing = sorted(required_keys - set(surface))
            fail(f"{location} is missing required keys: {', '.join(missing)}")
        surface_id = surface["surface_id"]
        if not isinstance(surface_id, str) or not surface_id:
            fail(f"{location}.surface_id must be a non-empty string")
        if surface_id in seen_surface_ids:
            fail(f"{location}.surface_id '{surface_id}' is duplicated")
        seen_surface_ids.add(surface_id)
        registry_surface = surfaces_by_id.get(surface_id)
        if registry_surface is None:
            fail(f"{location}.surface_id references unknown registry surface '{surface_id}'")
        if surface["surface_name"] != registry_surface["name"]:
            fail(f"{location}.surface_name must match the generated registry")
        if surface["registry_status"] != registry_surface["status"]:
            fail(f"{location}.registry_status must match the generated registry")
        if surface["derived_kind"] != registry_surface["derived_kind"]:
            fail(f"{location}.derived_kind must match the generated registry")
        source_repos = validate_unique_string_list(
            surface["source_repos"],
            label=f"{location}.source_repos",
        )
        if source_repos != registry_surface["source_repos"]:
            fail(f"{location}.source_repos must match the generated registry")
        stability_tier = surface["stability_tier"]
        if stability_tier not in tier_status_map:
            fail(f"{location}.stability_tier '{stability_tier}' is not supported")
        if registry_surface["status"] not in tier_status_map[stability_tier]:
            fail(f"{location}.stability_tier must match the registry status")
        if not isinstance(surface["consumer_posture"], str) or len(surface["consumer_posture"]) < 3:
            fail(f"{location}.consumer_posture must be a string of length >= 3")
        if not isinstance(surface["quarantine_policy"], str) or len(surface["quarantine_policy"]) < 3:
            fail(f"{location}.quarantine_policy must be a string of length >= 3")
        if not isinstance(surface["stop_rule"], str) or len(surface["stop_rule"]) < 3:
            fail(f"{location}.stop_rule must be a string of length >= 3")
        proof_gap_note = surface.get("proof_gap_note")
        if proof_gap_note is not None and (not isinstance(proof_gap_note, str) or len(proof_gap_note) < 10):
            fail(f"{location}.proof_gap_note must be a string of length >= 10 when present")

        proof_expectation_refs = validate_unique_string_list(
            surface["proof_expectation_refs"],
            label=f"{location}.proof_expectation_refs",
        )
        regrounding_mode_refs = validate_unique_string_list(
            surface["regrounding_mode_refs"],
            label=f"{location}.regrounding_mode_refs",
        )
        for proof_ref in proof_expectation_refs:
            resolve_aoa_evals_ref(
                proof_ref,
                label=f"{location}.proof_expectation_refs",
            )
        for mode_ref in regrounding_mode_refs:
            if mode_ref not in EXPECTED_KAG_MATURITY_GOVERNANCE_MODE_ORDER:
                fail(f"{location}.regrounding_mode_refs contains unsupported mode '{mode_ref}'")
    validate_exact_set(
        seen_surface_ids,
        set(surfaces_by_id),
        label="KAG maturity governance pack surface coverage",
    )

    owner_wait_states = payload["owner_wait_states"]
    if not isinstance(owner_wait_states, list) or not owner_wait_states:
        fail("KAG maturity governance pack owner_wait_states must be a non-empty list")
    if payload["owner_wait_state_count"] != len(owner_wait_states):
        fail("KAG maturity governance pack owner_wait_state_count must equal the number of owner wait states")
    owner_repo_order: list[str] = []
    for index, wait_state in enumerate(owner_wait_states):
        location = f"KAG maturity governance pack owner_wait_states[{index}]"
        if not isinstance(wait_state, dict):
            fail(f"{location} must be an object")
        owner_repo = wait_state.get("owner_repo")
        if not isinstance(owner_repo, str) or not owner_repo:
            fail(f"{location}.owner_repo must be a non-empty string")
        owner_repo_order.append(owner_repo)
        if not isinstance(wait_state.get("current_kag_posture"), str) or len(wait_state["current_kag_posture"]) < 10:
            fail(f"{location}.current_kag_posture must be a string of length >= 10")
        if not isinstance(wait_state.get("forbidden_inference"), str) or len(wait_state["forbidden_inference"]) < 10:
            fail(f"{location}.forbidden_inference must be a string of length >= 10")
        validate_unique_string_list(
            wait_state.get("waits_for"),
            label=f"{location}.waits_for",
        )
    if owner_repo_order != EXPECTED_KAG_MATURITY_GOVERNANCE_OWNER_WAIT_REPO_ORDER:
        fail("KAG maturity governance pack owner_wait_states must keep the current owner wait-state order")

    stop_rule = payload["stop_rule"]
    if not isinstance(stop_rule, dict):
        fail("KAG maturity governance pack stop_rule must be an object")
    blocked_surface_ids = validate_unique_string_list(
        stop_rule.get("blocked_surface_ids"),
        label="KAG maturity governance pack stop_rule.blocked_surface_ids",
    )
    validate_exact_set(
        blocked_surface_ids,
        {"AOA-K-0008"},
        label="KAG maturity governance pack stop_rule.blocked_surface_ids",
    )
    validate_unique_string_list(
        stop_rule.get("resume_when"),
        label="KAG maturity governance pack stop_rule.resume_when",
    )
    if not isinstance(stop_rule.get("new_surface_growth"), str) or len(stop_rule["new_surface_growth"]) < 3:
        fail("KAG maturity governance pack stop_rule.new_surface_growth must be a string of length >= 3")
    if not isinstance(stop_rule.get("current_program"), str) or len(stop_rule["current_program"]) < 3:
        fail("KAG maturity governance pack stop_rule.current_program must be a string of length >= 3")
    if not isinstance(stop_rule.get("pause_threshold"), str) or len(stop_rule["pause_threshold"]) < 10:
        fail("KAG maturity governance pack stop_rule.pause_threshold must be a string of length >= 10")

    projection_recovery = payload["projection_recovery"]
    if not isinstance(projection_recovery, dict):
        fail("KAG maturity governance pack projection_recovery must be an object")
    for field_name in (
        "stress_receipt_schema_ref",
        "regrounding_ticket_schema_ref",
        "stress_doc_ref",
        "quarantine_doc_ref",
        "regrounding_pack_ref",
    ):
        ref = projection_recovery.get(field_name)
        if not isinstance(ref, str) or not ref:
            fail(f"KAG maturity governance pack projection_recovery.{field_name} must be a non-empty string")
        resolve_known_ref(
            ref,
            label=f"KAG maturity governance pack projection_recovery.{field_name}",
        )
    health_states = validate_unique_string_list(
        projection_recovery.get("health_states"),
        label="KAG maturity governance pack projection_recovery.health_states",
    )
    if health_states != EXPECTED_KAG_MATURITY_GOVERNANCE_HEALTH_STATES:
        fail("KAG maturity governance pack projection_recovery.health_states must keep the current health-state order")
    mode_refs = validate_unique_string_list(
        projection_recovery.get("mode_refs"),
        label="KAG maturity governance pack projection_recovery.mode_refs",
    )
    if mode_refs != EXPECTED_KAG_MATURITY_GOVERNANCE_MODE_ORDER:
        fail("KAG maturity governance pack projection_recovery.mode_refs must keep the current regrounding mode order")
    validate_unique_string_list(
        projection_recovery.get("quarantine_triggers"),
        label="KAG maturity governance pack projection_recovery.quarantine_triggers",
    )
    validate_unique_string_list(
        projection_recovery.get("quarantine_exit_requirements"),
        label="KAG maturity governance pack projection_recovery.quarantine_exit_requirements",
    )

    if payload != expected_payload:
        fail("KAG maturity governance pack must match the committed manifest-driven governance payload")

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

def validate_cross_source_node_projection_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
    expected_payload: dict[str, object],
) -> None:
    if not isinstance(payload, dict):
        fail("cross-source node projection pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "surface_id",
        "surface_name",
        "projection_count",
        "projections",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(f"cross-source node projection pack is missing required key '{key}'")

    if payload["pack_type"] != "cross_source_node_projection":
        fail("cross-source node projection pack pack_type must equal 'cross_source_node_projection'")
    if payload["bounded_output_contract"] != EXPECTED_CROSS_SOURCE_NODE_PROJECTION_CONTRACT:
        fail("cross-source node projection pack bounded_output_contract must match the current source-first guardrail")
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("cross-source node projection pack source_inputs must match the manifest-driven donor set")
    if payload["surface_bindings"] != expected_payload["surface_bindings"]:
        fail("cross-source node projection pack surface_bindings must match the current bounded projection binding")
    forbidden_counterpart_refs = set(EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS) | {
        EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_REF,
        "AOA-K-0008",
    }
    if any(value in forbidden_counterpart_refs for value in iter_string_values(payload)):
        fail(
            "cross-source node projection pack must not expose counterpart refs or "
            "AOA-K-0008 activation hints in the current review-closed posture"
        )

    surface_0006 = surfaces_by_id.get("AOA-K-0006")
    if surface_0006 is None or surface_0006.get("status") != "experimental":
        fail("cross-source node projection pack requires AOA-K-0006 to remain experimental in the generated registry")

    projections = payload["projections"]
    if not isinstance(projections, list) or len(projections) != 1:
        fail("cross-source node projection pack must contain exactly one projection in the current pilot")
    if payload["projection_count"] != 1:
        fail("cross-source node projection pack projection_count must equal 1 in the current pilot")
    projection = projections[0]
    if not isinstance(projection, dict):
        fail("cross-source node projection pack projection must be an object")
    for input_key in ("primary_input",):
        input_payload = projection.get(input_key)
        if not isinstance(input_payload, dict):
            fail(f"cross-source node projection pack {input_key} must be an object")
        resolve_known_ref(input_payload["export_ref"], label=f"cross-source node projection pack {input_key}.export_ref")
    supporting_inputs = projection.get("supporting_inputs")
    if not isinstance(supporting_inputs, list) or len(supporting_inputs) != 1:
        fail("cross-source node projection pack supporting_inputs must contain exactly one supporting export in the current pilot")
    resolve_known_ref(
        supporting_inputs[0]["export_ref"],
        label="cross-source node projection pack supporting_inputs[0].export_ref",
    )
    resolve_known_ref(
        projection["retrieval_axis_ref"],
        label="cross-source node projection pack retrieval_axis_ref",
    )
    resolve_known_ref(
        projection["federation_spine_ref"],
        label="cross-source node projection pack federation_spine_ref",
    )
    if payload != expected_payload:
        fail("cross-source node projection pack must match the committed manifest-driven projection payload")

def validate_tiny_consumer_bundle_pack(expected_payload: dict[str, object]) -> None:
    payload = read_json(TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH)
    if not isinstance(payload, dict):
        fail("tiny consumer bundle pack must be a JSON object")

    for key in (
        "bundle_version",
        "bundle_type",
        "source_manifest_ref",
        "source_inputs",
        "bundle_item_count",
        "bundle_items",
        "deferred_counterpart",
    ):
        if key not in payload:
            fail(f"tiny consumer bundle pack is missing required key '{key}'")

    if payload["bundle_version"] != 1:
        fail("tiny consumer bundle pack bundle_version must equal 1")
    if payload["bundle_type"] != "tiny_consumer_bundle":
        fail("tiny consumer bundle pack bundle_type must equal 'tiny_consumer_bundle'")
    if payload["source_manifest_ref"] != TINY_CONSUMER_BUNDLE_MANIFEST_REF:
        fail(
            "tiny consumer bundle pack source_manifest_ref must point to "
            f"{TINY_CONSUMER_BUNDLE_MANIFEST_REF}"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail("tiny consumer bundle pack source_inputs must match the manifest-driven donor set")

    bundle_items = payload["bundle_items"]
    if not isinstance(bundle_items, list) or not bundle_items:
        fail("tiny consumer bundle pack bundle_items must be a non-empty list")
    if payload["bundle_item_count"] != len(bundle_items):
        fail("tiny consumer bundle pack bundle_item_count must equal the number of bundle_items")

    observed_order: list[str] = []
    for index, bundle_item in enumerate(bundle_items):
        location = f"tiny consumer bundle pack bundle_items[{index}]"
        if not isinstance(bundle_item, dict):
            fail(f"{location} must be an object")
        for key in ("order", "name", "role", "ref"):
            if key not in bundle_item:
                fail(f"{location} is missing required key '{key}'")
        if bundle_item["order"] != index + 1:
            fail(f"{location}.order must keep the stable 1-based bundle order")
        if not isinstance(bundle_item["name"], str) or not bundle_item["name"]:
            fail(f"{location}.name must be a non-empty string")
        if not isinstance(bundle_item["role"], str) or not bundle_item["role"]:
            fail(f"{location}.role must be a non-empty string")
        if not isinstance(bundle_item["ref"], str) or not bundle_item["ref"]:
            fail(f"{location}.ref must be a non-empty string")
        resolve_known_ref(bundle_item["ref"], label=f"{location}.ref")
        observed_order.append(bundle_item["name"])

    if observed_order != EXPECTED_TINY_CONSUMER_BUNDLE_ORDER:
        fail("tiny consumer bundle pack bundle_items must keep the current stable bundle order")
    if payload["deferred_counterpart"] != EXPECTED_TINY_CONSUMER_BUNDLE_DEFERRED_COUNTERPART:
        fail("tiny consumer bundle pack deferred_counterpart must match the contract-only posture")
    resolve_known_ref(
        payload["deferred_counterpart"]["federation_exposure_review_ref"],
        label="tiny consumer bundle pack deferred_counterpart.federation_exposure_review_ref",
    )
    if payload != expected_payload:
        fail("tiny consumer bundle pack must match the committed manifest-driven bundle payload")

def validate_counterpart_federation_exposure_review_pack(
    expected_payload: dict[str, object],
) -> None:
    payload = read_json(COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MIN_OUTPUT_PATH)
    if not isinstance(payload, dict):
        fail("counterpart federation exposure review pack must be a JSON object")

    for key in (
        "review_version",
        "review_type",
        "source_manifest_ref",
        "source_inputs",
        "surface_id",
        "surface_status",
        "review_status",
        "reviewed_surface_count",
        "reviewed_surfaces",
        "bounded_output_contract",
    ):
        if key not in payload:
            fail(
                "counterpart federation exposure review pack is missing required key "
                f"'{key}'"
            )

    if payload["review_version"] != 1:
        fail("counterpart federation exposure review pack review_version must equal 1")
    if payload["review_type"] != "counterpart_federation_exposure_review":
        fail(
            "counterpart federation exposure review pack review_type must equal "
            "'counterpart_federation_exposure_review'"
        )
    if payload["source_manifest_ref"] != COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_REF:
        fail(
            "counterpart federation exposure review pack source_manifest_ref must point "
            f"to {COUNTERPART_FEDERATION_EXPOSURE_REVIEW_MANIFEST_REF}"
        )
    if payload["source_inputs"] != expected_payload["source_inputs"]:
        fail(
            "counterpart federation exposure review pack source_inputs must match the "
            "manifest-driven donor set"
        )
    if payload["surface_id"] != "AOA-K-0008":
        fail("counterpart federation exposure review pack surface_id must equal 'AOA-K-0008'")
    if payload["surface_status"] != "planned":
        fail("counterpart federation exposure review pack surface_status must equal 'planned'")
    if payload["review_status"] != "passed_for_planned_posture":
        fail(
            "counterpart federation exposure review pack review_status must equal "
            "'passed_for_planned_posture'"
        )
    if payload["bounded_output_contract"] != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_CONTRACT:
        fail(
            "counterpart federation exposure review pack bounded_output_contract must "
            "match the current review guardrail"
        )

    reviewed_surfaces = payload["reviewed_surfaces"]
    if not isinstance(reviewed_surfaces, list) or not reviewed_surfaces:
        fail("counterpart federation exposure review pack reviewed_surfaces must be a non-empty list")
    if payload["reviewed_surface_count"] != len(reviewed_surfaces):
        fail(
            "counterpart federation exposure review pack reviewed_surface_count must "
            "equal the number of reviewed_surfaces"
        )

    observed_order: list[str] = []
    for index, reviewed_surface in enumerate(reviewed_surfaces):
        location = f"counterpart federation exposure review pack reviewed_surfaces[{index}]"
        if not isinstance(reviewed_surface, dict):
            fail(f"{location} must be an object")
        for key in ("surface_name", "surface_ref", "exposure_posture", "review_note"):
            if key not in reviewed_surface:
                fail(f"{location} is missing required key '{key}'")
        surface_name = reviewed_surface["surface_name"]
        surface_ref = reviewed_surface["surface_ref"]
        exposure_posture = reviewed_surface["exposure_posture"]
        observed_order.append(surface_name)
        resolve_known_ref(surface_ref, label=f"{location}.surface_ref")
        expected_posture = EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_POSTURES.get(surface_name)
        if exposure_posture != expected_posture:
            fail(
                f"{location}.exposure_posture must match the current reviewed posture "
                f"for '{surface_name}'"
            )
        if surface_name in {"reasoning_handoff_pack", "tiny_consumer_bundle"}:
            if reviewed_surface.get("allowed_counterpart_refs") != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.allowed_counterpart_refs must match the current "
                    "contract-only counterpart refs"
                )
        elif surface_name in {"federation_spine", "cross_source_node_projection"}:
            if reviewed_surface.get("forbidden_refs") != EXPECTED_COUNTERPART_CONSUMER_ALLOWED_REFS:
                fail(
                    f"{location}.forbidden_refs must match the current forbidden "
                    "counterpart exposure set"
                )

    if observed_order != EXPECTED_COUNTERPART_FEDERATION_EXPOSURE_REVIEW_ORDER:
        fail(
            "counterpart federation exposure review pack reviewed_surfaces must keep "
            "the current reviewed surface order"
        )
    if payload != expected_payload:
        fail(
            "counterpart federation exposure review pack must match the committed "
            "manifest-driven review payload"
        )

def validate_generated_text(path: Path, expected_text: str, *, label: str) -> None:
    try:
        actual_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"{label} is missing at {display_path(path)}")
    if actual_text != expected_text:
        fail(f"{label} is out of date; run python scripts/generate_kag.py")

def validate_technique_lift_pack(
    payload: object,
    surfaces_by_id: dict[str, dict[str, object]],
) -> None:
    if not isinstance(payload, dict):
        fail("technique lift pack must be a JSON object")

    for key in (
        "pack_version",
        "pack_type",
        "source_repo",
        "source_manifest_ref",
        "source_inputs",
        "surface_bindings",
        "section_scope",
        "technique_count",
        "techniques",
    ):
        if key not in payload:
            fail(f"technique lift pack is missing required key '{key}'")

    if payload["pack_version"] != 1:
        fail("technique lift pack pack_version must equal 1")
    if payload["pack_type"] != "technique_lift_pack":
        fail("technique lift pack pack_type must equal 'technique_lift_pack'")
    if payload["source_repo"] != "aoa-techniques":
        fail("technique lift pack source_repo must equal 'aoa-techniques'")
    if payload["source_manifest_ref"] != TECHNIQUE_LIFT_MANIFEST_REF:
        fail(
            "technique lift pack source_manifest_ref must point to "
            f"{TECHNIQUE_LIFT_MANIFEST_REF}"
        )

    source_inputs = payload["source_inputs"]
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("technique lift pack source_inputs must be a non-empty list")
    actual_source_inputs: set[tuple[str, str, str]] = set()
    for index, source_input in enumerate(source_inputs):
        location = f"technique lift pack source_inputs[{index}]"
        if not isinstance(source_input, dict):
            fail(f"{location} must be an object")
        name = source_input.get("name")
        role = source_input.get("role")
        ref = source_input.get("ref")
        if not all(isinstance(value, str) and value for value in (name, role, ref)):
            fail(f"{location} must keep name, role, and ref")
        resolve_aoa_techniques_ref(ref, label=location)
        actual_source_inputs.add((name, ref.split("/", 1)[1], role))
    if actual_source_inputs != EXPECTED_TECHNIQUE_LIFT_INPUTS:
        fail("technique lift pack source_inputs must match the manifest-driven donor set")

    surface_bindings = payload["surface_bindings"]
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("technique lift pack surface_bindings must be a non-empty list")
    actual_bindings: set[tuple[str, str, str, str, str]] = set()
    for index, binding in enumerate(surface_bindings):
        location = f"technique lift pack surface_bindings[{index}]"
        if not isinstance(binding, dict):
            fail(f"{location} must be an object")
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
            fail(f"{location} must keep id, name, kind, slot, and source input")
        actual_bindings.add(
            (surface_id, surface_name, derived_kind, derived_slot, source_input)
        )
        surface = surfaces_by_id.get(surface_id)
        if surface is None:
            fail(f"{location} references unknown registry surface '{surface_id}'")
        if surface.get("name") != surface_name:
            fail(f"{location} does not match the generated registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(f"{location} does not match the generated registry derived_kind")
        if surface.get("status") != "active":
            fail(f"{location} must only point to active registry surfaces")
    if actual_bindings != EXPECTED_TECHNIQUE_LIFT_BINDINGS:
        fail("technique lift pack surface_bindings must match the current bounded technique lift bindings")

    section_scope = validate_unique_string_list(
        payload["section_scope"],
        label="technique lift pack section_scope",
    )

    techniques = payload["techniques"]
    if not isinstance(techniques, list) or not techniques:
        fail("technique lift pack techniques must be a non-empty list")
    technique_count = payload["technique_count"]
    if not isinstance(technique_count, int) or technique_count != len(techniques):
        fail("technique lift pack technique_count must equal the number of techniques")

    seen_technique_ids: set[str] = set()
    for index, technique in enumerate(techniques):
        location = f"technique lift pack techniques[{index}]"
        if not isinstance(technique, dict):
            fail(f"{location} must be an object")

        for key in (
            "technique_id",
            "technique_name",
            "source_ref",
            "section_lift",
            "metadata_spine",
            "relation_view",
            "provenance_view",
        ):
            if key not in technique:
                fail(f"{location} is missing required key '{key}'")

        technique_id = technique["technique_id"]
        technique_name = technique["technique_name"]
        source_ref = technique["source_ref"]
        if not isinstance(technique_id, str) or not re.match(r"^AOA-T-[0-9]{4}$", technique_id):
            fail(f"{location}.technique_id must be an AOA technique id")
        if technique_id in seen_technique_ids:
            fail(f"{location}.technique_id '{technique_id}' is duplicated")
        seen_technique_ids.add(technique_id)
        if not isinstance(technique_name, str) or not technique_name:
            fail(f"{location}.technique_name must be a non-empty string")
        if not isinstance(source_ref, str) or not source_ref.startswith("aoa-techniques/"):
            fail(f"{location}.source_ref must point to aoa-techniques")
        resolve_aoa_techniques_ref(source_ref, label=f"{location}.source_ref")

        section_lift = technique["section_lift"]
        if not isinstance(section_lift, dict):
            fail(f"{location}.section_lift must be an object")
        section_count = section_lift.get("section_count")
        sections = section_lift.get("sections")
        if not isinstance(sections, list) or not sections:
            fail(f"{location}.section_lift.sections must be a non-empty list")
        if not isinstance(section_count, int) or section_count != len(sections):
            fail(f"{location}.section_lift.section_count must equal the number of sections")
        seen_headings: set[str] = set()
        for section_index, section in enumerate(sections):
            section_location = f"{location}.section_lift.sections[{section_index}]"
            if not isinstance(section, dict):
                fail(f"{section_location} must be an object")
            heading = section.get("heading")
            order = section.get("order")
            if not isinstance(heading, str) or not heading:
                fail(f"{section_location}.heading must be a non-empty string")
            if heading not in section_scope:
                fail(f"{section_location}.heading '{heading}' must appear in section_scope")
            if heading in seen_headings:
                fail(f"{section_location}.heading '{heading}' is duplicated for {technique_id}")
            seen_headings.add(heading)
            if not isinstance(order, int) or order < 1:
                fail(f"{section_location}.order must be a positive integer")

        metadata_spine = technique["metadata_spine"]
        if not isinstance(metadata_spine, dict):
            fail(f"{location}.metadata_spine must be an object")
        for key in (
            "domain",
            "status",
            "summary",
            "maturity_score",
            "rigor_level",
            "reversibility",
            "review_required",
            "validation_strength",
            "export_ready",
        ):
            if key not in metadata_spine:
                fail(f"{location}.metadata_spine is missing '{key}'")
        if not isinstance(metadata_spine["domain"], str) or not metadata_spine["domain"]:
            fail(f"{location}.metadata_spine.domain must be a non-empty string")
        if not isinstance(metadata_spine["status"], str) or not metadata_spine["status"]:
            fail(f"{location}.metadata_spine.status must be a non-empty string")
        if not isinstance(metadata_spine["summary"], str) or len(metadata_spine["summary"]) < 10:
            fail(f"{location}.metadata_spine.summary must be a string of length >= 10")
        if not isinstance(metadata_spine["maturity_score"], int) or metadata_spine["maturity_score"] < 0:
            fail(f"{location}.metadata_spine.maturity_score must be a non-negative integer")
        if not isinstance(metadata_spine["review_required"], bool):
            fail(f"{location}.metadata_spine.review_required must be a boolean")
        if not isinstance(metadata_spine["export_ready"], bool):
            fail(f"{location}.metadata_spine.export_ready must be a boolean")

        relation_view = technique["relation_view"]
        if not isinstance(relation_view, dict):
            fail(f"{location}.relation_view must be an object")
        relation_count = relation_view.get("relation_count")
        relations = relation_view.get("relations")
        if not isinstance(relations, list):
            fail(f"{location}.relation_view.relations must be a list")
        if not isinstance(relation_count, int) or relation_count != len(relations):
            fail(f"{location}.relation_view.relation_count must equal the number of relations")
        for relation_index, relation in enumerate(relations):
            relation_location = f"{location}.relation_view.relations[{relation_index}]"
            if not isinstance(relation, dict):
                fail(f"{relation_location} must be an object")
            relation_type = relation.get("relation_type")
            target_ref = relation.get("target_ref")
            if not isinstance(relation_type, str) or not relation_type:
                fail(f"{relation_location}.relation_type must be a non-empty string")
            if not isinstance(target_ref, str) or not target_ref.startswith("aoa-techniques/AOA-T-"):
                fail(f"{relation_location}.target_ref must be an aoa-techniques technique ref")

        provenance_view = technique["provenance_view"]
        if not isinstance(provenance_view, dict):
            fail(f"{location}.provenance_view must be an object")
        reviewed_at = provenance_view.get("public_safety_reviewed_at")
        note_count = provenance_view.get("note_count")
        note_handles = provenance_view.get("note_handles")
        if not isinstance(reviewed_at, str) or not DATE_RE.match(reviewed_at):
            fail(f"{location}.provenance_view.public_safety_reviewed_at must be a YYYY-MM-DD string")
        if not isinstance(note_handles, list):
            fail(f"{location}.provenance_view.note_handles must be a list")
        if not isinstance(note_count, int) or note_count != len(note_handles):
            fail(f"{location}.provenance_view.note_count must equal the number of note handles")
        seen_note_refs: set[str] = set()
        for note_index, note_handle in enumerate(note_handles):
            note_location = f"{location}.provenance_view.note_handles[{note_index}]"
            if not isinstance(note_handle, dict):
                fail(f"{note_location} must be an object")
            kind = note_handle.get("kind")
            title = note_handle.get("title")
            note_ref = note_handle.get("note_ref")
            if not all(isinstance(value, str) and value for value in (kind, title, note_ref)):
                fail(f"{note_location} must keep kind, title, and note_ref")
            if note_ref in seen_note_refs:
                fail(f"{note_location}.note_ref '{note_ref}' is duplicated for {technique_id}")
            seen_note_refs.add(note_ref)
            resolve_aoa_techniques_ref(note_ref, label=f"{note_location}.note_ref")
