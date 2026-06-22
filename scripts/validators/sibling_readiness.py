from __future__ import annotations

from .common import *
from .source_refs import *

def validate_optional_memo_source_owned_export_readiness() -> None:
    if not AOA_MEMO_ROOT.exists():
        return
    if not (AOA_MEMO_ROOT / EXPECTED_MEMO_KAG_EXPORT_PATH).exists():
        return

    export_ref = repo_ref("aoa-memo", EXPECTED_MEMO_KAG_EXPORT_PATH)
    export_path = resolve_known_ref(
        export_ref,
        label="optional aoa-memo source-owned export readiness export_ref",
    )
    payload = read_json(export_path)
    if not isinstance(payload, dict):
        fail("optional aoa-memo source-owned export readiness target export must be a JSON object")

    missing_fields = sorted(EXPECTED_MEMO_KAG_EXPORT_REQUIRED_FIELDS - set(payload))
    if missing_fields:
        fail(
            "optional aoa-memo source-owned export readiness target export is missing "
            + ", ".join(missing_fields)
        )

    if payload.get("owner_repo") != "aoa-memo":
        fail("optional aoa-memo source-owned export readiness owner_repo must equal 'aoa-memo'")
    if payload.get("kind") != "bridge":
        fail("optional aoa-memo source-owned export readiness kind must equal 'bridge'")
    if (
        payload.get("object_id")
        != EXPECTED_MEMO_KAG_EXPORT_ENTRY_SURFACE["match_value"]
    ):
        fail(
            "optional aoa-memo source-owned export readiness object_id must equal "
            f"'{EXPECTED_MEMO_KAG_EXPORT_ENTRY_SURFACE['match_value']}'"
        )

    source_inputs = payload.get("source_inputs")
    if source_inputs != EXPECTED_MEMO_KAG_EXPORT_SOURCE_INPUTS:
        fail(
            "optional aoa-memo source-owned export readiness source_inputs must keep "
            "the memo-primary / Tree-of-Sophia-supporting split"
        )

    entry_surface = payload.get("entry_surface")
    if entry_surface != EXPECTED_MEMO_KAG_EXPORT_ENTRY_SURFACE:
        fail(
            "optional aoa-memo source-owned export readiness entry_surface must stay "
            "aligned with the memo bridge capsule surface"
        )
    resolve_known_ref(
        repo_ref("aoa-memo", EXPECTED_MEMO_KAG_EXPORT_ENTRY_SURFACE["path"]),
        label="optional aoa-memo source-owned export readiness entry_surface",
    )

    section_handles = validate_unique_string_list(
        payload.get("section_handles"),
        label="optional aoa-memo source-owned export readiness section_handles",
    )
    if section_handles != EXPECTED_MEMO_KAG_EXPORT_SECTION_HANDLES:
        fail(
            "optional aoa-memo source-owned export readiness section_handles must "
            "match the canonical memo bridge handles"
        )

    direct_relations = payload.get("direct_relations")
    if direct_relations != EXPECTED_MEMO_KAG_EXPORT_DIRECT_RELATIONS:
        fail(
            "optional aoa-memo source-owned export readiness direct_relations must "
            "keep the source/claim/episode/ToS/provenance set"
        )
    for index, relation in enumerate(direct_relations):
        resolve_source_owned_export_ref(
            relation["target_ref"],
            owner_repo="aoa-memo",
            label=f"optional aoa-memo source-owned export readiness direct_relations[{index}]",
        )

def validate_memo_source_owned_export_consumer_boundary_doc() -> None:
    text = read_text(SOURCE_OWNED_EXPORT_DEPENDENCIES_DOC_PATH)
    for snippet in REQUIRED_MEMO_SOURCE_OWNED_EXPORT_CONSUMER_BOUNDARY_SNIPPETS:
        if snippet not in text:
            fail(
                "mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md is missing "
                f"memo consumer boundary guidance: {snippet}"
            )
