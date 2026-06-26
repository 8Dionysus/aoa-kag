from __future__ import annotations

from .core import *

EXPECTED_TECHNIQUE_LIFT_INPUTS = {
    ("technique_section_manifest", "generated/technique_section_manifest.min.json", "section_manifest"),
    ("technique_catalog", "generated/technique_catalog.json", "metadata_spine"),
    ("technique_evidence_note_manifest", "generated/technique_evidence_note_manifest.min.json", "provenance_handles"),
}

EXPECTED_TECHNIQUE_LIFT_BINDINGS = {
    (
        "AOA-K-0001",
        "technique-section-lift",
        "section_manifest",
        "section_lift",
        "technique_section_manifest",
    ),
    (
        "AOA-K-0002",
        "metadata-spine-projection",
        "metadata_spine",
        "metadata_spine",
        "technique_catalog",
    ),
    (
        "AOA-K-0003",
        "bounded-relation-view",
        "relation_view",
        "relation_view",
        "technique_catalog",
    ),
    (
        "AOA-K-0004",
        "provenance-note-view",
        "provenance_view",
        "provenance_view",
        "technique_evidence_note_manifest",
    ),
}

EXPECTED_TECHNIQUE_LIFT_OUTPUT_PATHS = {
    "full": TECHNIQUE_LIFT_OUTPUT_REF,
    "min": TECHNIQUE_LIFT_MIN_OUTPUT_REF,
}

EXPECTED_TECHNIQUE_LIFT_CONTRACT = {
    "source_trace_required": True,
    "source_replacement": "forbidden",
    "graph_sovereignty": "forbidden",
}
