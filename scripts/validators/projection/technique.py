from __future__ import annotations

from ..common import *
from ..local_contracts import *
from ..source_refs import *

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
