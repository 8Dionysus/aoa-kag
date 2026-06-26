from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

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
