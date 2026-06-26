from __future__ import annotations

from .common import *
from .registry import build_registry_payload
from .source_refs import *

def build_tos_text_chunk_map_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TOS_TEXT_CHUNK_MAP_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("ToS text chunk map manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")
    if manifest.get("source_repo") != TOS_REPO:
        fail("ToS text chunk map manifest source_repo must equal 'Tree-of-Sophia'")
    if manifest.get("source_root_env") != "TREE_OF_SOPHIA_ROOT":
        fail(
            "ToS text chunk map manifest source_root_env must equal 'TREE_OF_SOPHIA_ROOT'"
        )
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS text chunk map manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS text chunk map manifest must declare surface_bindings")

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
            fail("ToS text chunk map manifest source_inputs entries must be objects")
        name = source_input.get("name")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, path, role)):
            fail("ToS text chunk map manifest source_inputs must keep name, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate ToS text chunk map source input '{name}'")

        donor_path = TREE_OF_SOPHIA_ROOT / path
        if not donor_path.exists():
            fail(f"ToS text chunk map donor input does not exist: {repo_ref(TOS_REPO, path)}")

        normalized_input = {"path": path, "role": role}
        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "role": role,
                "ref": repo_ref(TOS_REPO, path),
            }
        )

    source_node_input = inputs_by_name.get("tos_source_node")
    if source_node_input is None:
        fail("ToS text chunk map manifest must include tos_source_node")
    if source_node_input["path"] != TOS_TINY_ENTRY_AUTHORITY_PATH:
        fail(
            "ToS text chunk map manifest tos_source_node must point to the current source node authority surface"
        )

    route_doc_input = inputs_by_name.get("tos_tiny_entry_route_doc")
    if route_doc_input is None:
        fail("ToS text chunk map manifest must include tos_tiny_entry_route_doc")
    if route_doc_input["path"] != TOS_TINY_ENTRY_DOCTRINE_PATH:
        fail(
            "ToS text chunk map manifest tos_tiny_entry_route_doc must point to the current tiny-entry doctrine"
        )

    capsule_input = inputs_by_name.get("tos_zarathustra_capsule")
    if capsule_input is None:
        fail("ToS text chunk map manifest must include tos_zarathustra_capsule")
    if capsule_input["path"] != TOS_TINY_ENTRY_CAPSULE_PATH:
        fail(
            "ToS text chunk map manifest tos_zarathustra_capsule must point to the current Zarathustra capsule"
        )

    seen_surface_ids: set[str] = set()
    binding_surface: dict[str, object] | None = None
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("ToS text chunk map manifest surface_bindings entries must be objects")
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
                "ToS text chunk map manifest surface_bindings must keep id, name, kind, slot, and source input"
            )
        if surface_id in seen_surface_ids:
            fail(f"duplicate ToS text chunk map surface binding '{surface_id}'")
        seen_surface_ids.add(surface_id)
        if source_input not in inputs_by_name:
            fail(
                f"ToS text chunk map binding '{surface_id}' references unknown source input '{source_input}'"
            )

        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(
                f"ToS text chunk map binding '{surface_id}' does not exist in the registry manifest"
            )
        if surface.get("name") != surface_name:
            fail(f"ToS text chunk map binding '{surface_id}' does not match registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(
                f"ToS text chunk map binding '{surface_id}' does not match registry derived_kind"
            )
        if surface.get("status") != "experimental":
            fail(
                f"ToS text chunk map binding '{surface_id}' must point to an experimental registry surface"
            )
        binding_surface = surface

    if binding_surface is None:
        fail("ToS text chunk map manifest must declare one experimental surface binding")

    route_payload = load_tos_tiny_entry_route_payload()
    source_node_payload = load_tos_source_node_payload()
    if require_string(
        route_payload.get("authority_surface"),
        label=f"{repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)}.authority_surface",
    ) != source_node_input["path"]:
        fail("ToS text chunk map source node must stay aligned with the tiny-entry authority surface")
    if require_string(
        route_payload.get("capsule_surface"),
        label=f"{repo_ref(TOS_REPO, TOS_TINY_ENTRY_ROUTE_PATH)}.capsule_surface",
    ) != capsule_input["path"]:
        fail("ToS text chunk map capsule input must stay aligned with the tiny-entry capsule surface")

    source_label = repo_ref(TOS_REPO, TOS_TINY_ENTRY_AUTHORITY_PATH)
    node_id = require_string(
        source_node_payload.get("node_id"),
        label=f"{source_label}.node_id",
    )
    node_type = require_string(
        source_node_payload.get("node_type"),
        label=f"{source_label}.node_type",
    )
    source_anchor = require_string(
        source_node_payload.get("source_anchor"),
        label=f"{source_label}.source_anchor",
    )
    interpretation_layers = source_node_payload.get("interpretation_layers")
    if not isinstance(interpretation_layers, list) or not interpretation_layers:
        fail(f"{source_label}.interpretation_layers must be a non-empty list")

    raw_language_witnesses = source_node_payload.get("language_witnesses")
    if not isinstance(raw_language_witnesses, list) or not raw_language_witnesses:
        fail(f"{source_label}.language_witnesses must be a non-empty list")

    segment_order: list[str] = []
    expected_segment_order: list[str] | None = None
    seen_languages: set[str] = set()
    witness_entries_by_segment: dict[str, list[dict[str, str]]] = {}

    for witness_index, witness in enumerate(raw_language_witnesses):
        witness_label = f"{source_label}.language_witnesses[{witness_index}]"
        if not isinstance(witness, dict):
            fail(f"{witness_label} must be an object")
        language = require_string(
            witness.get("language"),
            label=f"{witness_label}.language",
        )
        role = require_string(
            witness.get("role"),
            label=f"{witness_label}.role",
        )
        if language in seen_languages:
            fail(f"{witness_label}.language '{language}' is duplicated")
        seen_languages.add(language)

        raw_segments = witness.get("segments")
        if not isinstance(raw_segments, list) or not raw_segments:
            fail(f"{witness_label}.segments must be a non-empty list")

        current_segment_order: list[str] = []
        seen_segment_ids: set[str] = set()
        for segment_index, segment in enumerate(raw_segments):
            segment_label = f"{witness_label}.segments[{segment_index}]"
            if not isinstance(segment, dict):
                fail(f"{segment_label} must be an object")
            segment_id = require_string(
                segment.get("segment_id"),
                label=f"{segment_label}.segment_id",
            )
            text = require_string(
                segment.get("text"),
                label=f"{segment_label}.text",
            )
            if segment_id in seen_segment_ids:
                fail(f"{segment_label}.segment_id '{segment_id}' is duplicated")
            seen_segment_ids.add(segment_id)
            current_segment_order.append(segment_id)
            witness_entries_by_segment.setdefault(segment_id, []).append(
                {
                    "language": language,
                    "role": role,
                    "text": text,
                }
            )

        if expected_segment_order is None:
            expected_segment_order = current_segment_order
            segment_order = list(current_segment_order)
        elif current_segment_order != expected_segment_order:
            fail(
                f"{witness_label}.segments must keep the same segment_id order as the canonical source witness"
            )

    translation_tensions_by_segment: dict[str, dict[str, str]] = {}
    raw_translation_tensions = source_node_payload.get("translation_tensions", [])
    if raw_translation_tensions is not None and not isinstance(raw_translation_tensions, list):
        fail(f"{source_label}.translation_tensions must be a list when present")
    for tension_index, tension in enumerate(raw_translation_tensions or []):
        tension_label = f"{source_label}.translation_tensions[{tension_index}]"
        if not isinstance(tension, dict):
            fail(f"{tension_label} must be an object")
        segment_id = require_string(
            tension.get("segment_id"),
            label=f"{tension_label}.segment_id",
        )
        note = require_string(
            tension.get("note"),
            label=f"{tension_label}.note",
        )
        if segment_id not in witness_entries_by_segment:
            fail(f"{tension_label}.segment_id '{segment_id}' must match a chunked witness segment")
        if segment_id in translation_tensions_by_segment:
            fail(f"{tension_label}.segment_id '{segment_id}' is duplicated")
        translation_tensions_by_segment[segment_id] = {
            "segment_id": segment_id,
            "note": note,
        }

    chunks: list[dict[str, object]] = []
    source_ref = repo_ref(TOS_REPO, source_node_input["path"])
    route_ref = repo_ref(TOS_REPO, route_doc_input["path"])
    capsule_ref = repo_ref(TOS_REPO, capsule_input["path"])
    witness_count = len(raw_language_witnesses)

    for segment_id in segment_order:
        chunk = {
            "chunk_id": f"{node_id}::{segment_id}",
            "node_id": node_id,
            "segment_id": segment_id,
            "source_anchor": source_anchor,
            "source_ref": source_ref,
            "route_ref": route_ref,
            "capsule_ref": capsule_ref,
            "interpretation_layers": interpretation_layers,
            "witness_count": witness_count,
            "witnesses": witness_entries_by_segment[segment_id],
        }
        translation_tension = translation_tensions_by_segment.get(segment_id)
        if translation_tension is not None:
            chunk["translation_tension"] = translation_tension
        chunks.append(chunk)

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_repo": manifest["source_repo"],
        "source_manifest_ref": TOS_TEXT_CHUNK_MAP_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "surface_bindings": surface_bindings,
        "surface_id": binding_surface["id"],
        "surface_name": binding_surface["name"],
        "node_id": node_id,
        "node_type": node_type,
        "source_anchor": source_anchor,
        "authority_surface_ref": source_ref,
        "route_ref": route_ref,
        "capsule_ref": capsule_ref,
        "interpretation_layers": interpretation_layers,
        "chunk_count": len(chunks),
        "chunks": chunks,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }

def build_tos_retrieval_axis_pack_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TOS_RETRIEVAL_AXIS_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("ToS retrieval axis manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS retrieval axis manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS retrieval axis manifest must declare surface_bindings")

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
            fail("ToS retrieval axis manifest source_inputs entries must be objects")
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, repo, path, role)):
            fail("ToS retrieval axis manifest source_inputs must keep name, repo, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate ToS retrieval axis source input '{name}'")

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        if not manifest_input_path(normalized_input).exists():
            fail(f"ToS retrieval axis donor input does not exist: {repo_ref(repo, path)}")
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
        "tos_text_chunk_map",
        "bridge_contract_doc",
        "bridge_surface_example",
        "bridge_envelope_example",
        "memo_chunk_face",
        "memo_graph_face",
        "tos_node_contract",
        "tos_practice_branch",
        "tos_authority_surface",
        "tos_lineage_hop",
    )
    missing_inputs = [name for name in required_input_names if name not in inputs_by_name]
    if missing_inputs:
        fail(
            "ToS retrieval axis manifest is missing required inputs: "
            + ", ".join(sorted(missing_inputs))
        )

    chunk_map_input = inputs_by_name["tos_text_chunk_map"]
    if manifest_input_ref(chunk_map_input) != TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_REF:
        fail(
            "ToS retrieval axis manifest tos_text_chunk_map must point to "
            f"{TOS_TEXT_CHUNK_MAP_MIN_OUTPUT_REF}"
        )
    if manifest_input_ref(inputs_by_name["bridge_contract_doc"]) != "docs/BRIDGE_CONTRACTS.md":
        fail("ToS retrieval axis manifest bridge_contract_doc must point to docs/BRIDGE_CONTRACTS.md")
    if manifest_input_ref(inputs_by_name["bridge_surface_example"]) != "mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_surface.example.json":
        fail(
            "ToS retrieval axis manifest bridge_surface_example must point to mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/tos_retrieval_axis_surface.example.json"
        )
    if manifest_input_ref(inputs_by_name["bridge_envelope_example"]) != "mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/aoa_tos_bridge_envelope.example.json":
        fail(
            "ToS retrieval axis manifest bridge_envelope_example must point to mechanics/boundary-bridge/parts/tos-retrieval-axis/examples/aoa_tos_bridge_envelope.example.json"
        )
    if manifest_input_ref(inputs_by_name["memo_chunk_face"]) != "aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_chunk_face.bridge.example.json":
        fail(
            "ToS retrieval axis manifest memo_chunk_face must point to aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_chunk_face.bridge.example.json"
        )
    if manifest_input_ref(inputs_by_name["memo_graph_face"]) != "aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_graph_face.bridge.example.json":
        fail(
            "ToS retrieval axis manifest memo_graph_face must point to aoa-memo/mechanics/consumer-handoff/parts/kag-tos-bridge-handoff/examples/memory_graph_face.bridge.example.json"
        )
    if manifest_input_ref(inputs_by_name["tos_node_contract"]) != "Tree-of-Sophia/ToS/doctrine/NODE_CONTRACT.md":
        fail("ToS retrieval axis manifest tos_node_contract must point to Tree-of-Sophia/ToS/doctrine/NODE_CONTRACT.md")
    if manifest_input_ref(inputs_by_name["tos_practice_branch"]) != "Tree-of-Sophia/ToS/doctrine/PRACTICE_BRANCH.md":
        fail(
            "ToS retrieval axis manifest tos_practice_branch must point to Tree-of-Sophia/ToS/doctrine/PRACTICE_BRANCH.md"
        )
    if manifest_input_ref(inputs_by_name["tos_authority_surface"]) != "Tree-of-Sophia/ToS/public-compatibility/source_node.example.json":
        fail(
            "ToS retrieval axis manifest tos_authority_surface must point to Tree-of-Sophia/ToS/public-compatibility/source_node.example.json"
        )
    if manifest_input_ref(inputs_by_name["tos_lineage_hop"]) != "Tree-of-Sophia/ToS/public-compatibility/concept_node.example.json":
        fail(
            "ToS retrieval axis manifest tos_lineage_hop must point to Tree-of-Sophia/ToS/public-compatibility/concept_node.example.json"
        )

    seen_surface_ids: set[str] = set()
    binding_surface: dict[str, object] | None = None
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("ToS retrieval axis manifest surface_bindings entries must be objects")
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
                "ToS retrieval axis manifest surface_bindings must keep id, name, kind, slot, and source input"
            )
        if surface_id in seen_surface_ids:
            fail(f"duplicate ToS retrieval axis surface binding '{surface_id}'")
        seen_surface_ids.add(surface_id)
        if source_input not in inputs_by_name:
            fail(
                f"ToS retrieval axis binding '{surface_id}' references unknown source input '{source_input}'"
            )

        surface = registry_by_id.get(surface_id)
        if surface is None:
            fail(
                f"ToS retrieval axis binding '{surface_id}' does not exist in the registry manifest"
            )
        if surface.get("name") != surface_name:
            fail(f"ToS retrieval axis binding '{surface_id}' does not match registry surface name")
        if surface.get("derived_kind") != derived_kind:
            fail(
                f"ToS retrieval axis binding '{surface_id}' does not match registry derived_kind"
            )
        if surface.get("status") != "experimental":
            fail(
                f"ToS retrieval axis binding '{surface_id}' must point to an experimental registry surface"
            )
        binding_surface = surface

    if binding_surface is None:
        fail("ToS retrieval axis manifest must declare one experimental surface binding")

    chunk_map_payload = build_tos_text_chunk_map_payload(registry_payload)
    chunks = chunk_map_payload.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        fail("ToS retrieval axis requires a non-empty ToS text chunk map")
    chunk_ids = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            fail("ToS retrieval axis requires chunk-map chunks to be objects")
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            fail("ToS retrieval axis requires every chunk-map chunk to keep chunk_id")
        chunk_ids.append(chunk_id)

    source_node_id = require_string(
        chunk_map_payload.get("node_id"),
        label="ToS retrieval axis source_node_id",
    )
    axis_summary = (
        "Bundles the current Zarathustra prologue chunk set with bounded source, "
        "lineage, conflict, practice, and memo bridge handles so AoA consumers can "
        "retrieve context without ranking, routing ownership, or graph claims."
    )

    axis = {
        "axis_id": f"AOA-K-0007::{source_node_id}",
        "source_node_id": source_node_id,
        "chunk_map_ref": manifest_input_ref(chunk_map_input),
        "chunk_ids": chunk_ids,
        "source_refs": [
            manifest_input_ref(inputs_by_name["tos_authority_surface"]),
            manifest_input_ref(inputs_by_name["tos_node_contract"]),
            manifest_input_ref(inputs_by_name["tos_practice_branch"]),
        ],
        "lineage_refs": [
            manifest_input_ref(inputs_by_name["tos_lineage_hop"]),
            manifest_input_ref(inputs_by_name["tos_node_contract"]),
        ],
        "conflict_refs": [
            manifest_input_ref(inputs_by_name["tos_node_contract"]),
        ],
        "practice_refs": [
            manifest_input_ref(inputs_by_name["tos_practice_branch"]),
        ],
        "bridge_surface_ref": manifest_input_ref(inputs_by_name["bridge_surface_example"]),
        "bridge_envelope_ref": manifest_input_ref(inputs_by_name["bridge_envelope_example"]),
        "memo_face_refs": [
            manifest_input_ref(inputs_by_name["memo_chunk_face"]),
            manifest_input_ref(inputs_by_name["memo_graph_face"]),
        ],
        "axis_summary": axis_summary,
    }

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": TOS_RETRIEVAL_AXIS_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "surface_bindings": surface_bindings,
        "surface_id": binding_surface["id"],
        "surface_name": binding_surface["name"],
        "axis_count": 1,
        "axes": [axis],
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_tos_zarathustra_route_node_entry(relative_path: str) -> dict[str, object]:
    payload = read_json(TREE_OF_SOPHIA_ROOT / relative_path)
    if not isinstance(payload, dict):
        fail(f"ToS Zarathustra route node surface must be a JSON object: {relative_path}")

    node_id = require_string(payload.get("node_id"), label=f"{relative_path}.node_id")
    node_type = require_string(
        payload.get("node_type"),
        label=f"{relative_path}.node_type",
    )
    if node_type not in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER:
        fail(f"{relative_path}.node_type '{node_type}' is not allowed in the route pack")
    if node_id.startswith("literal."):
        fail(f"{relative_path}.node_id must not carry literal helper residue")

    return {
        "node_id": node_id,
        "node_type": node_type,
        "authority_ref": repo_ref(TOS_REPO, relative_path),
        "source_anchor": require_string(
            payload.get("source_anchor"),
            label=f"{relative_path}.source_anchor",
        ),
        "key_terms": require_string_list(
            payload.get("key_terms"),
            label=f"{relative_path}.key_terms",
        ),
        "distilled_thesis": require_string(
            payload.get("distilled_thesis"),
            label=f"{relative_path}.distilled_thesis",
        ),
        "interpretation_layers": require_string_list(
            payload.get("interpretation_layers"),
            label=f"{relative_path}.interpretation_layers",
        ),
    }


def load_tos_zarathustra_route_family(
    root_path: str,
    *,
    expected_type: str,
) -> list[dict[str, object]]:
    root = TREE_OF_SOPHIA_ROOT / root_path
    if not root.is_dir():
        fail(f"ToS Zarathustra route family root is missing: {root_path}")

    entries: list[dict[str, object]] = []
    for node_path in sorted(root.glob("**/node.json")):
        relative_path = node_path.relative_to(TREE_OF_SOPHIA_ROOT).as_posix()
        entry = build_tos_zarathustra_route_node_entry(relative_path)
        if entry["node_type"] != expected_type:
            fail(
                f"{relative_path}.node_type must stay '{expected_type}' under "
                f"{root_path}"
            )
        entries.append(entry)

    entries.sort(key=lambda record: str(record["node_id"]))
    return entries


def load_tos_zarathustra_route_edges(relative_path: str) -> list[dict[str, object]]:
    rows = read_csv_rows(TREE_OF_SOPHIA_ROOT / relative_path)
    if not rows:
        fail("ToS Zarathustra route relation pack must keep at least one edge row")

    required_columns = {
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
    }

    edges: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        missing = required_columns.difference(row)
        if missing:
            fail(
                "ToS Zarathustra route relation pack row is missing required columns: "
                + ", ".join(sorted(missing))
            )
        edge_id = require_string(row.get("edge_id"), label=f"{relative_path} row {index}.edge_id")
        from_id = require_string(row.get("from_id"), label=f"{relative_path} row {index}.from_id")
        to_id = require_string(row.get("to_id"), label=f"{relative_path} row {index}.to_id")
        if not from_id.startswith("tos.") or not to_id.startswith("tos."):
            fail(f"{relative_path} row {index} must keep canonical tos.* endpoints")
        if from_id.startswith("literal.") or to_id.startswith("literal."):
            fail(f"{relative_path} row {index} must not carry literal helper residue")

        confidence = require_string(
            row.get("confidence"),
            label=f"{relative_path} row {index}.confidence",
        )
        if not confidence.isdigit():
            fail(f"{relative_path} row {index}.confidence must stay integer-like")

        edges.append(
            {
                "edge_id": edge_id,
                "edge_kind": require_string(
                    row.get("edge_kind"),
                    label=f"{relative_path} row {index}.edge_kind",
                ),
                "from_id": from_id,
                "predicate_id": require_string(
                    row.get("predicate_id"),
                    label=f"{relative_path} row {index}.predicate_id",
                ),
                "to_id": to_id,
                "layer": require_string(
                    row.get("layer"),
                    label=f"{relative_path} row {index}.layer",
                ),
                "anchor_mode": require_string(
                    row.get("anchor_mode"),
                    label=f"{relative_path} row {index}.anchor_mode",
                ),
                "anchor_start_secondary": row.get("anchor_start_secondary", ""),
                "anchor_end_secondary": row.get("anchor_end_secondary", ""),
                "anchor_segment_ids": require_string(
                    row.get("anchor_segment_ids"),
                    label=f"{relative_path} row {index}.anchor_segment_ids",
                ),
                "witness_scope": require_string(
                    row.get("witness_scope"),
                    label=f"{relative_path} row {index}.witness_scope",
                ),
                "connectivity_role": require_string(
                    row.get("connectivity_role"),
                    label=f"{relative_path} row {index}.connectivity_role",
                ),
                "confidence": int(confidence),
                "note": row.get("note", ""),
            }
        )

    return edges


def build_tos_zarathustra_route_pack_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("ToS Zarathustra route pack manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS Zarathustra route pack manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS Zarathustra route pack manifest must declare surface_bindings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    surface_0010 = registry_by_id.get("AOA-K-0010")
    if surface_0010 is None:
        fail("registry manifest must declare AOA-K-0010 before building the route pack")
    if surface_0010.get("status") != "experimental":
        fail("AOA-K-0010 must remain experimental in the current route-pack scope")

    expected_inputs = {
        "tos_route_source_node": (
            TOS_ZARATHUSTRA_ROUTE_SOURCE_NODE_PATH,
            "authority_surface",
        ),
        "tos_becoming_concept": (
            TOS_ZARATHUSTRA_ROUTE_BECOMING_CONCEPT_PATH,
            "concept_surface",
        ),
        "tos_overcoming_concept": (
            TOS_ZARATHUSTRA_ROUTE_OVERCOMING_CONCEPT_PATH,
            "concept_surface",
        ),
        "tos_route_lineage_node": (
            TOS_ZARATHUSTRA_ROUTE_LINEAGE_NODE_PATH,
            "lineage_surface",
        ),
        "tos_route_principle_family_root": (
            TOS_ZARATHUSTRA_ROUTE_PRINCIPLE_ROOT,
            "family_root",
        ),
        "tos_route_event_family_root": (
            TOS_ZARATHUSTRA_ROUTE_EVENT_ROOT,
            "family_root",
        ),
        "tos_route_state_family_root": (
            TOS_ZARATHUSTRA_ROUTE_STATE_ROOT,
            "family_root",
        ),
        "tos_route_support_family_root": (
            TOS_ZARATHUSTRA_ROUTE_SUPPORT_ROOT,
            "family_root",
        ),
        "tos_route_analogy_family_root": (
            TOS_ZARATHUSTRA_ROUTE_ANALOGY_ROOT,
            "family_root",
        ),
        "tos_route_synthesis_family_root": (
            TOS_ZARATHUSTRA_ROUTE_SYNTHESIS_ROOT,
            "family_root",
        ),
        "tos_route_relation_pack": (
            TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH,
            "relation_pack",
        ),
        "tos_zarathustra_capsule": (
            TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH,
            "capsule_surface",
        ),
    }

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("ToS Zarathustra route pack manifest source_inputs entries must be objects")
        name = source_input.get("name")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, path, role)):
            fail(
                "ToS Zarathustra route pack manifest source_inputs must keep name, path, "
                "and role"
            )
        if name in inputs_by_name:
            fail(f"duplicate ToS Zarathustra route pack source input '{name}'")
        expected = expected_inputs.get(name)
        if expected is None:
            fail(f"unexpected ToS Zarathustra route pack source input '{name}'")
        expected_path, expected_role = expected
        if path != expected_path or role != expected_role:
            fail(
                "ToS Zarathustra route pack manifest source_inputs must stay aligned "
                f"for '{name}'"
            )

        normalized_input = {
            "name": name,
            "repo": TOS_REPO,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        if role == "family_root":
            if not input_path.is_dir():
                fail(f"ToS Zarathustra route family root is missing: {repo_ref(TOS_REPO, path)}")
        elif not input_path.exists():
            fail(f"ToS Zarathustra route donor input does not exist: {repo_ref(TOS_REPO, path)}")

        inputs_by_name[name] = normalized_input
        emitted_source_inputs.append(
            {
                "name": name,
                "repo": TOS_REPO,
                "role": role,
                "ref": manifest_input_ref(normalized_input),
            }
        )

    if set(inputs_by_name) != set(expected_inputs):
        fail("ToS Zarathustra route pack manifest source_inputs must match the current canonical donor set")

    binding_surface: dict[str, object] | None = None
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("ToS Zarathustra route pack manifest surface_bindings entries must be objects")
        if (
            binding.get("surface_id") == "AOA-K-0010"
            and binding.get("surface_name") == "tos-zarathustra-route-pack"
        ):
            binding_surface = surface_0010
            break
    if binding_surface is None:
        fail("ToS Zarathustra route pack manifest must bind AOA-K-0010")

    nodes_by_type: dict[str, list[dict[str, object]]] = {
        "source": [
            build_tos_zarathustra_route_node_entry(TOS_ZARATHUSTRA_ROUTE_SOURCE_NODE_PATH)
        ],
        "concept": sorted(
            [
                build_tos_zarathustra_route_node_entry(
                    TOS_ZARATHUSTRA_ROUTE_BECOMING_CONCEPT_PATH
                ),
                build_tos_zarathustra_route_node_entry(
                    TOS_ZARATHUSTRA_ROUTE_OVERCOMING_CONCEPT_PATH
                ),
            ],
            key=lambda record: str(record["node_id"]),
        ),
        "principle": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_PRINCIPLE_ROOT,
            expected_type="principle",
        ),
        "lineage": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_LINEAGE_NODE_PATH.rsplit("/", 1)[0],
            expected_type="lineage",
        ),
        "event": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_EVENT_ROOT,
            expected_type="event",
        ),
        "state": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_STATE_ROOT,
            expected_type="state",
        ),
        "support": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_SUPPORT_ROOT,
            expected_type="support",
        ),
        "analogy": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_ANALOGY_ROOT,
            expected_type="analogy",
        ),
        "synthesis": load_tos_zarathustra_route_family(
            TOS_ZARATHUSTRA_ROUTE_SYNTHESIS_ROOT,
            expected_type="synthesis",
        ),
    }

    node_type_counts = {
        node_type: len(nodes_by_type[node_type])
        for node_type in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER
    }
    if node_type_counts != TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS:
        fail("ToS Zarathustra route pack node_type_counts must match the current canonical route")

    nodes: list[dict[str, object]] = []
    for node_type in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER:
        nodes.extend(nodes_by_type[node_type])

    edges = load_tos_zarathustra_route_edges(TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH)
    edge_kind_counts: dict[str, int] = {}
    for edge_kind in ("source_edge", "bridge_edge", "principle_edge"):
        edge_kind_counts[edge_kind] = len(
            [edge for edge in edges if edge["edge_kind"] == edge_kind]
        )
    if edge_kind_counts != TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS:
        fail("ToS Zarathustra route pack edge_kind_counts must match the canonical relation pack")

    if len(nodes) != sum(TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS.values()):
        fail("ToS Zarathustra route pack node_count drifted from the current canonical route")
    if len(edges) != sum(TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS.values()):
        fail("ToS Zarathustra route pack edge_count drifted from the canonical relation pack")

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_repo": manifest["source_repo"],
        "source_manifest_ref": TOS_ZARATHUSTRA_ROUTE_PACK_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "surface_bindings": surface_bindings,
        "surface_id": binding_surface["id"],
        "surface_name": binding_surface["name"],
        "route_id": TOS_ZARATHUSTRA_ROUTE_ID,
        "route_capsule_ref": repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH),
        "relation_pack_ref": repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": node_type_counts,
        "edge_kind_counts": edge_kind_counts,
        "nodes": nodes,
        "edges": edges,
        "bounded_output_contract": manifest["bounded_output_contract"],
    }


def build_tos_zarathustra_route_handle(
    node: object,
    *,
    label: str,
) -> dict[str, str]:
    if not isinstance(node, dict):
        fail(f"{label} must be an object")
    node_id = require_string(node.get("node_id"), label=f"{label}.node_id")
    authority_ref = require_string(
        node.get("authority_ref"),
        label=f"{label}.authority_ref",
    )
    if not node_id.startswith("tos."):
        fail(f"{label}.node_id must stay canonical and start with 'tos.'")
    if node_id.startswith("literal."):
        fail(f"{label}.node_id must not carry literal residue")
    if not authority_ref.startswith(f"{TOS_REPO}/ToS/canon/"):
        fail(f"{label}.authority_ref must point into Tree-of-Sophia/ToS/canon/**")
    if not authority_ref.endswith("/node.json"):
        fail(f"{label}.authority_ref must resolve to a canonical node.json file")
    if authority_ref.startswith(f"{TOS_REPO}/intake/") or "/intake/" in authority_ref:
        fail(f"{label}.authority_ref must not point at Tree-of-Sophia/intake")
    return {
        "node_id": node_id,
        "authority_ref": authority_ref,
    }


def build_tos_zarathustra_route_retrieval_pack_payload(
    registry_payload: dict[str, object] | None = None,
    *,
    route_pack_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("ToS Zarathustra route retrieval pack manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")
    adjunct_budget = manifest.get("adjunct_budget")
    subordinate_posture = manifest.get("subordinate_posture")
    if not isinstance(source_inputs, list) or not source_inputs:
        fail("ToS Zarathustra route retrieval pack manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("ToS Zarathustra route retrieval pack manifest must declare surface_bindings")
    if adjunct_budget != TOS_STANDALONE_ADJUNCT_BUDGET:
        fail(
            "ToS Zarathustra route retrieval pack manifest adjunct_budget must stay "
            "aligned with the current standalone adjunct budget"
        )
    if subordinate_posture != TOS_STANDALONE_ADJUNCT_SUBORDINATE_POSTURE:
        fail(
            "ToS Zarathustra route retrieval pack manifest subordinate_posture must "
            "stay aligned with the current source-first subordinate posture"
        )

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")
    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    surface_0011 = registry_by_id.get("AOA-K-0011")
    if surface_0011 is None:
        fail(
            "registry manifest must declare AOA-K-0011 before building the route retrieval pack"
        )
    if surface_0011.get("status") != "experimental":
        fail("AOA-K-0011 must remain experimental in the current route retrieval scope")

    expected_inputs = {
        "tos_zarathustra_route_pack": (
            "aoa-kag",
            TOS_ZARATHUSTRA_ROUTE_PACK_INPUT_REF,
            "route_pack",
        )
    }

    inputs_by_name: dict[str, dict[str, str]] = {}
    emitted_source_inputs: list[dict[str, str]] = []
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail(
                "ToS Zarathustra route retrieval pack manifest source_inputs entries "
                "must be objects"
            )
        name = source_input.get("name")
        repo = source_input.get("repo")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(
            isinstance(value, str) and value for value in (name, repo, path, role)
        ):
            fail(
                "ToS Zarathustra route retrieval pack manifest source_inputs must keep "
                "name, repo, path, and role"
            )
        if name in inputs_by_name:
            fail(
                f"duplicate ToS Zarathustra route retrieval pack source input '{name}'"
            )
        expected = expected_inputs.get(name)
        if expected is None:
            fail(
                f"unexpected ToS Zarathustra route retrieval pack source input '{name}'"
            )
        expected_repo, expected_path, expected_role = expected
        if repo != expected_repo or path != expected_path or role != expected_role:
            fail(
                "ToS Zarathustra route retrieval pack manifest source_inputs must stay "
                f"aligned for '{name}'"
            )

        normalized_input = {
            "name": name,
            "repo": repo,
            "path": path,
            "role": role,
        }
        input_path = manifest_input_path(normalized_input)
        if not input_path.exists() and route_pack_payload is None:
            fail(
                "ToS Zarathustra route retrieval pack donor input does not exist: "
                f"{manifest_input_ref(normalized_input)}"
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

    if set(inputs_by_name) != set(expected_inputs):
        fail(
            "ToS Zarathustra route retrieval pack manifest source_inputs must match "
            "the current single-donor route-pack contract"
        )

    binding_surface: dict[str, object] | None = None
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail(
                "ToS Zarathustra route retrieval pack manifest surface_bindings "
                "entries must be objects"
            )
        if (
            binding.get("surface_id") == "AOA-K-0011"
            and binding.get("surface_name")
            == "tos-zarathustra-route-retrieval-surface"
        ):
            binding_surface = surface_0011
            break
    if binding_surface is None:
        fail("ToS Zarathustra route retrieval pack manifest must bind AOA-K-0011")

    route_pack_input = inputs_by_name["tos_zarathustra_route_pack"]
    if route_pack_payload is None:
        loaded_route_pack = read_json(manifest_input_path(route_pack_input))
        if not isinstance(loaded_route_pack, dict):
            fail("ToS Zarathustra route retrieval pack donor route pack must be a JSON object")
        route_pack_payload = loaded_route_pack

    if route_pack_payload.get("pack_type") != "tos_zarathustra_route_pack":
        fail(
            "ToS Zarathustra route retrieval pack donor must remain the canonical "
            "AOA-K-0010 route pack"
        )
    if route_pack_payload.get("route_id") != TOS_ZARATHUSTRA_ROUTE_ID:
        fail(
            "ToS Zarathustra route retrieval pack donor route_id must stay aligned "
            "with the current canonical route"
        )

    route_capsule_ref = require_string(
        route_pack_payload.get("route_capsule_ref"),
        label="ToS Zarathustra route retrieval pack donor route_capsule_ref",
    )
    relation_pack_ref = require_string(
        route_pack_payload.get("relation_pack_ref"),
        label="ToS Zarathustra route retrieval pack donor relation_pack_ref",
    )
    if route_capsule_ref != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_CAPSULE_PATH):
        fail(
            "ToS Zarathustra route retrieval pack donor route_capsule_ref must stay "
            "aligned with the canonical Zarathustra capsule"
        )
    if relation_pack_ref != repo_ref(TOS_REPO, TOS_ZARATHUSTRA_ROUTE_RELATION_PACK_PATH):
        fail(
            "ToS Zarathustra route retrieval pack donor relation_pack_ref must stay "
            "aligned with the canonical relation pack"
        )
    if route_capsule_ref.startswith("aoa-memo/") or route_capsule_ref.startswith("aoa-routing/"):
        fail(
            "ToS Zarathustra route retrieval pack donor route_capsule_ref must not "
            "point at aoa-memo or aoa-routing"
        )
    if relation_pack_ref.startswith("aoa-memo/") or relation_pack_ref.startswith("aoa-routing/"):
        fail(
            "ToS Zarathustra route retrieval pack donor relation_pack_ref must not "
            "point at aoa-memo or aoa-routing"
        )

    node_type_counts = route_pack_payload.get("node_type_counts")
    edge_kind_counts = route_pack_payload.get("edge_kind_counts")
    if node_type_counts != TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS:
        fail(
            "ToS Zarathustra route retrieval pack donor node_type_counts must match "
            "the canonical AOA-K-0010 route counts"
        )
    if edge_kind_counts != TOS_ZARATHUSTRA_ROUTE_EDGE_KIND_COUNTS:
        fail(
            "ToS Zarathustra route retrieval pack donor edge_kind_counts must match "
            "the canonical AOA-K-0010 route counts"
        )

    route_nodes = route_pack_payload.get("nodes")
    if not isinstance(route_nodes, list) or len(route_nodes) != sum(
        TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS.values()
    ):
        fail(
            "ToS Zarathustra route retrieval pack donor must contain the full "
            "canonical Zarathustra route node set"
        )

    family_handles: dict[str, list[dict[str, str]]] = {
        f"{node_type}_handles": []
        for node_type in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER
    }
    for index, node in enumerate(route_nodes):
        if not isinstance(node, dict):
            fail(
                "ToS Zarathustra route retrieval pack donor nodes entries must be objects"
            )
        node_type = require_string(
            node.get("node_type"),
            label=f"ToS Zarathustra route retrieval pack donor nodes[{index}].node_type",
        )
        if node_type not in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_ORDER:
            fail(
                "ToS Zarathustra route retrieval pack donor node_type "
                f"'{node_type}' is not allowed"
            )
        family_handles[f"{node_type}_handles"].append(
            build_tos_zarathustra_route_handle(
                node,
                label=(
                    "ToS Zarathustra route retrieval pack donor "
                    f"nodes[{index}]"
                ),
            )
        )

    for node_type, expected_count in TOS_ZARATHUSTRA_ROUTE_NODE_TYPE_COUNTS.items():
        handle_key = f"{node_type}_handles"
        if len(family_handles[handle_key]) != expected_count:
            fail(
                "ToS Zarathustra route retrieval pack must preserve the current "
                f"family handle count for '{node_type}'"
            )

    retrieval_route = {
        "retrieval_id": TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_ID,
        "route_id": TOS_ZARATHUSTRA_ROUTE_ID,
        "route_pack_ref": manifest_input_ref(route_pack_input),
        "route_capsule_ref": route_capsule_ref,
        "relation_pack_ref": relation_pack_ref,
        "node_type_counts": node_type_counts,
        "edge_kind_counts": edge_kind_counts,
        "source_handles": family_handles["source_handles"],
        "concept_handles": family_handles["concept_handles"],
        "principle_handles": family_handles["principle_handles"],
        "lineage_handles": family_handles["lineage_handles"],
        "event_handles": family_handles["event_handles"],
        "state_handles": family_handles["state_handles"],
        "support_handles": family_handles["support_handles"],
        "analogy_handles": family_handles["analogy_handles"],
        "synthesis_handles": family_handles["synthesis_handles"],
        "retrieval_summary": TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_SUMMARY,
    }

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_manifest_ref": TOS_ZARATHUSTRA_ROUTE_RETRIEVAL_PACK_MANIFEST_REF,
        "source_inputs": emitted_source_inputs,
        "surface_bindings": surface_bindings,
        "surface_id": binding_surface["id"],
        "surface_name": binding_surface["name"],
        "adjunct_budget": adjunct_budget,
        "subordinate_posture": subordinate_posture,
        "route_count": 1,
        "routes": [retrieval_route],
        "bounded_output_contract": manifest["bounded_output_contract"],
    }
