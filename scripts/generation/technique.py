from __future__ import annotations

from .common import *
from .registry import build_registry_payload

def build_technique_lift_pack_payload(
    registry_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if registry_payload is None:
        registry_payload = build_registry_payload()

    manifest = read_json(TECHNIQUE_LIFT_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        fail("technique lift manifest must be a JSON object")

    source_inputs = manifest.get("source_inputs")
    surface_bindings = manifest.get("surface_bindings")

    if not isinstance(source_inputs, list) or not source_inputs:
        fail("technique lift manifest must declare source_inputs")
    if not isinstance(surface_bindings, list) or not surface_bindings:
        fail("technique lift manifest must declare surface_bindings")

    registry_surfaces = registry_payload.get("surfaces")
    if not isinstance(registry_surfaces, list):
        fail("registry manifest must declare surfaces")

    registry_by_id = {
        surface["id"]: surface
        for surface in registry_surfaces
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }

    inputs_by_name: dict[str, dict[str, str]] = {}
    for source_input in source_inputs:
        if not isinstance(source_input, dict):
            fail("technique lift manifest source_inputs entries must be objects")
        name = source_input.get("name")
        path = source_input.get("path")
        role = source_input.get("role")
        if not all(isinstance(value, str) and value for value in (name, path, role)):
            fail("technique lift manifest source_inputs must keep name, path, and role")
        if name in inputs_by_name:
            fail(f"duplicate technique lift source input '{name}'")
        inputs_by_name[name] = {"path": path, "role": role}

    seen_surface_ids: set[str] = set()
    seen_slots: set[str] = set()
    for binding in surface_bindings:
        if not isinstance(binding, dict):
            fail("technique lift manifest surface_bindings entries must be objects")
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
            fail("technique lift manifest surface_bindings must keep id, name, kind, slot, and source input")
        if surface_id in seen_surface_ids:
            fail(f"duplicate technique lift surface binding '{surface_id}'")
        if derived_slot in seen_slots:
            fail(f"duplicate technique lift derived slot '{derived_slot}'")
        seen_surface_ids.add(surface_id)
        seen_slots.add(derived_slot)
        if source_input not in inputs_by_name:
            fail(f"technique lift binding '{surface_id}' references unknown source input '{source_input}'")

        registry_surface = registry_by_id.get(surface_id)
        if registry_surface is None:
            fail(f"technique lift binding '{surface_id}' does not exist in the registry manifest")
        if registry_surface.get("name") != surface_name:
            fail(f"technique lift binding '{surface_id}' does not match registry surface name")
        if registry_surface.get("derived_kind") != derived_kind:
            fail(f"technique lift binding '{surface_id}' does not match registry derived_kind")
        if registry_surface.get("status") != "active":
            fail(f"technique lift binding '{surface_id}' must point to an active registry surface")

    section_manifest = read_json(
        AOA_TECHNIQUES_ROOT / inputs_by_name["technique_section_manifest"]["path"]
    )
    catalog = read_json(AOA_TECHNIQUES_ROOT / inputs_by_name["technique_catalog"]["path"])
    evidence_manifest = read_json(
        AOA_TECHNIQUES_ROOT / inputs_by_name["technique_evidence_note_manifest"]["path"]
    )

    if not all(
        isinstance(payload, dict)
        for payload in (section_manifest, catalog, evidence_manifest)
    ):
        fail("aoa-techniques donor manifests must be JSON objects")

    catalog_techniques = catalog.get("techniques")
    section_techniques = section_manifest.get("techniques")
    evidence_techniques = evidence_manifest.get("techniques")
    section_scope = section_manifest.get("section_scope")

    if not isinstance(catalog_techniques, list) or not catalog_techniques:
        fail("technique catalog must declare techniques")
    if not isinstance(section_techniques, list) or not section_techniques:
        fail("technique section manifest must declare techniques")
    if not isinstance(evidence_techniques, list) or not evidence_techniques:
        fail("technique evidence note manifest must declare techniques")
    if not isinstance(section_scope, list) or not section_scope:
        fail("technique section manifest must declare section_scope")

    section_by_id = {
        technique["id"]: technique
        for technique in section_techniques
        if isinstance(technique, dict) and isinstance(technique.get("id"), str)
    }
    evidence_by_id = {
        technique["id"]: technique
        for technique in evidence_techniques
        if isinstance(technique, dict) and isinstance(technique.get("id"), str)
    }

    techniques: list[dict[str, object]] = []

    for technique in catalog_techniques:
        if not isinstance(technique, dict):
            fail("technique catalog entries must be objects")

        technique_id = technique.get("id")
        technique_name = technique.get("name")
        technique_path = technique.get("technique_path")

        if not all(
            isinstance(value, str) and value
            for value in (technique_id, technique_name, technique_path)
        ):
            fail("technique catalog entries must keep id, name, and technique_path")

        section_entry = section_by_id.get(technique_id)
        evidence_entry = evidence_by_id.get(technique_id)
        if section_entry is None:
            fail(f"technique section manifest is missing '{technique_id}'")
        if evidence_entry is None:
            fail(f"technique evidence note manifest is missing '{technique_id}'")

        raw_sections = section_entry.get("sections")
        raw_relations = technique.get("relations", [])
        raw_notes = evidence_entry.get("notes", [])

        if not isinstance(raw_sections, list) or not raw_sections:
            fail(f"technique section manifest entry '{technique_id}' must keep sections")
        if not isinstance(raw_relations, list):
            fail(f"technique catalog entry '{technique_id}' relations must be a list")
        if not isinstance(raw_notes, list):
            fail(f"technique evidence note manifest entry '{technique_id}' notes must be a list")

        sections: list[dict[str, object]] = []
        for section in raw_sections:
            if not isinstance(section, dict):
                fail(f"technique section manifest entry '{technique_id}' contains an invalid section")
            heading = section.get("heading")
            order = section.get("order")
            if not isinstance(heading, str) or not heading:
                fail(f"technique section manifest entry '{technique_id}' contains a section without heading")
            if not isinstance(order, int) or order < 1:
                fail(f"technique section manifest entry '{technique_id}' contains a section without positive order")
            sections.append({"heading": heading, "order": order})

        relations: list[dict[str, str]] = []
        for relation in raw_relations:
            if not isinstance(relation, dict):
                fail(f"technique catalog entry '{technique_id}' contains an invalid relation")
            relation_type = relation.get("type")
            target = relation.get("target")
            if not isinstance(relation_type, str) or not relation_type:
                fail(f"technique catalog entry '{technique_id}' contains a relation without type")
            if not isinstance(target, str) or not target:
                fail(f"technique catalog entry '{technique_id}' contains a relation without target")
            relations.append(
                {
                    "relation_type": relation_type,
                    "target_ref": f"aoa-techniques/{target}",
                }
            )

        note_handles: list[dict[str, str]] = []
        for note in raw_notes:
            if not isinstance(note, dict):
                fail(f"technique evidence note manifest entry '{technique_id}' contains an invalid note")
            kind = note.get("kind")
            title = note.get("title")
            note_path = note.get("note_path")
            if not all(isinstance(value, str) and value for value in (kind, title, note_path)):
                fail(f"technique evidence note manifest entry '{technique_id}' contains an incomplete note handle")
            note_handles.append(
                {
                    "kind": kind,
                    "title": title,
                    "note_ref": f"aoa-techniques/{note_path}",
                }
            )

        public_safety_reviewed_at = technique.get("public_safety_reviewed_at")
        if not isinstance(public_safety_reviewed_at, str) or not public_safety_reviewed_at:
            fail(f"technique catalog entry '{technique_id}' must keep public_safety_reviewed_at")

        metadata_spine = {
            "domain": technique["domain"],
            "status": technique["status"],
            "summary": technique["summary"],
            "maturity_score": technique["maturity_score"],
            "rigor_level": technique["rigor_level"],
            "reversibility": technique["reversibility"],
            "review_required": technique["review_required"],
            "validation_strength": technique["validation_strength"],
            "export_ready": technique["export_ready"],
        }

        techniques.append(
            {
                "technique_id": technique_id,
                "technique_name": technique_name,
                "source_ref": f"aoa-techniques/{technique_path}",
                "section_lift": {
                    "section_count": len(sections),
                    "sections": sections,
                },
                "metadata_spine": metadata_spine,
                "relation_view": {
                    "relation_count": len(relations),
                    "relations": relations,
                },
                "provenance_view": {
                    "public_safety_reviewed_at": public_safety_reviewed_at,
                    "note_count": len(note_handles),
                    "note_handles": note_handles,
                },
            }
        )

    return {
        "pack_version": manifest["manifest_version"],
        "pack_type": manifest["pack_type"],
        "source_repo": manifest["source_repo"],
        "source_manifest_ref": TECHNIQUE_LIFT_MANIFEST_REF,
        "source_inputs": [
            {
                "name": source_input["name"],
                "role": source_input["role"],
                "ref": f"aoa-techniques/{source_input['path']}",
            }
            for source_input in source_inputs
        ],
        "surface_bindings": surface_bindings,
        "section_scope": section_scope,
        "technique_count": len(techniques),
        "techniques": techniques,
    }
