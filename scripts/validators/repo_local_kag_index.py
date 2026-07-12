from __future__ import annotations

import copy
import sys

from .common import *
from .schema_surfaces import validate_top_level_schema

try:
    from scripts.generate_repo_local_kag_coverage import build_provider_coverage
    from scripts.generate_repo_local_kag_index import (
        REPOSITORY_INDEX_FILENAMES,
        build_index,
        build_repository_indexes,
        classification_summary,
    )
except ImportError:  # pragma: no cover - direct script import fallback
    from generate_repo_local_kag_coverage import build_provider_coverage  # type: ignore
    from generate_repo_local_kag_index import (  # type: ignore
        REPOSITORY_INDEX_FILENAMES,
        build_index,
        build_repository_indexes,
        classification_summary,
    )


REPOSITORY_INDEX_FAMILY_REFS = {
    "source": "kag/indexes/source_surface_index.json",
    **{
        index_kind: f"kag/indexes/{filename}"
        for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items()
    },
}
DOMAIN_INDEX_CATALOG_REF = "kag/indexes/domain_index_catalog.json"


def _repo_local_index_phase(label: str, *, progress: bool) -> None:
    if progress:
        print(f"[validate-kag:repo-local-index] {label}", file=sys.stderr, flush=True)


def repo_local_kag_validate_payload(payload: object, *, schema_path: Path, label: str) -> None:
    schema = read_json(schema_path)
    if not isinstance(schema, dict):
        fail(f"{label} schema must be a JSON object")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = format_schema_path(first.path)
        suffix = f" at {path}" if path else ""
        fail(f"{label} does not match schema{suffix}: {first.message}")


def repo_local_kag_index_digest_without_self(payload: dict[str, object]) -> str:
    try:
        from scripts.generate_repo_local_kag_index import payload_digest
    except ImportError:  # pragma: no cover
        from generate_repo_local_kag_index import payload_digest  # type: ignore

    return payload_digest(copy.deepcopy(payload))


def validate_repo_local_kag_index_schema_surface() -> None:
    validate_top_level_schema(REPO_LOCAL_KAG_INDEX_SCHEMA_PATH, "repo-local KAG index")
    validate_top_level_schema(
        REPO_LOCAL_KAG_REPOSITORY_INDEX_SCHEMA_PATH,
        "repo-local KAG repository index",
    )
    validate_top_level_schema(REPO_LOCAL_KAG_QUERY_RESULT_SCHEMA_PATH, "repo-local KAG query result")
    validate_top_level_schema(REPO_LOCAL_KAG_FEDERATION_SCHEMA_PATH, "repo-local KAG federation")
    validate_top_level_schema(
        REPO_LOCAL_KAG_RETRIEVAL_PLAN_SCHEMA_PATH,
        "repo-local KAG retrieval plan",
    )
    validate_top_level_schema(
        REPO_LOCAL_KAG_RETRIEVAL_BUNDLE_SCHEMA_PATH,
        "repo-local KAG retrieval bundle",
    )
    validate_top_level_schema(DOMAIN_INDEX_CATALOG_SCHEMA_PATH, "domain index catalog")
    validate_top_level_schema(REPO_LOCAL_KAG_COVERAGE_SCHEMA_PATH, "repo-local KAG coverage")


def validate_repo_local_kag_index_example() -> None:
    payload = read_json(REPO_LOCAL_KAG_INDEX_EXAMPLE_PATH)
    repo_local_kag_validate_payload(
        payload,
        schema_path=REPO_LOCAL_KAG_INDEX_SCHEMA_PATH,
        label="repo-local KAG index example",
    )
    domain_catalog = read_json(DOMAIN_INDEX_CATALOG_EXAMPLE_PATH)
    repo_local_kag_validate_payload(
        domain_catalog,
        schema_path=DOMAIN_INDEX_CATALOG_SCHEMA_PATH,
        label="domain index catalog example",
    )
    query_result = read_json(REPO_LOCAL_KAG_QUERY_RESULT_EXAMPLE_PATH)
    repo_local_kag_validate_payload(
        query_result,
        schema_path=REPO_LOCAL_KAG_QUERY_RESULT_SCHEMA_PATH,
        label="repo-local KAG query result example",
    )
    federation = read_json(REPO_LOCAL_KAG_FEDERATION_EXAMPLE_PATH)
    repo_local_kag_validate_payload(
        federation,
        schema_path=REPO_LOCAL_KAG_FEDERATION_SCHEMA_PATH,
        label="repo-local KAG federation example",
    )
    retrieval_plan = read_json(REPO_LOCAL_KAG_RETRIEVAL_PLAN_EXAMPLE_PATH)
    repo_local_kag_validate_payload(
        retrieval_plan,
        schema_path=REPO_LOCAL_KAG_RETRIEVAL_PLAN_SCHEMA_PATH,
        label="repo-local KAG retrieval plan example",
    )
    retrieval_bundle = read_json(REPO_LOCAL_KAG_RETRIEVAL_BUNDLE_EXAMPLE_PATH)
    repo_local_kag_validate_payload(
        retrieval_bundle,
        schema_path=REPO_LOCAL_KAG_RETRIEVAL_BUNDLE_SCHEMA_PATH,
        label="repo-local KAG retrieval bundle example",
    )


def validate_repo_local_kag_index_payload(payload: object, *, label: str) -> dict[str, object]:
    repo_local_kag_validate_payload(
        payload,
        schema_path=REPO_LOCAL_KAG_INDEX_SCHEMA_PATH,
        label=label,
    )
    if not isinstance(payload, dict):
        fail(f"{label} must be a JSON object")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        fail(f"{label} must contain records")

    ids = []
    paths = []
    for record in records:
        if not isinstance(record, dict):
            fail(f"{label} records must contain objects")
        identity = record.get("identity")
        if not isinstance(identity, dict):
            fail(f"{label} record identity must be an object")
        ids.append(identity.get("id"))
        paths.append(identity.get("path"))
        if record.get("document_role") != "none":
            refs = record.get("refs")
            heading_refs = refs.get("heading_refs") if isinstance(refs, dict) else None
            if not isinstance(heading_refs, list):
                fail(f"{label} document record {identity.get('path')} must keep heading_refs")
        if record.get("mechanics_role") != "none" and "mechanics" not in str(identity.get("path")):
            fail(f"{label} mechanics record {identity.get('path')} must point into mechanics")
        if record.get("command_role") in {"script", "validator", "test", "builder", "lane_entrypoint"}:
            toolchain = record.get("toolchain")
            if not isinstance(toolchain, dict) or not toolchain.get("owner_commands"):
                fail(f"{label} command record {identity.get('path')} must keep owner_commands")

    if len(ids) != len(set(ids)):
        fail(f"{label} record ids must be unique")
    if len(paths) != len(set(paths)):
        fail(f"{label} record paths must be unique")

    summary = payload.get("coverage_summary")
    if not isinstance(summary, dict):
        fail(f"{label} coverage_summary must be an object")
    if summary.get("record_count") != len(records):
        fail(f"{label} coverage_summary.record_count must match records")
    if summary.get("document_count", 0) <= 0:
        fail(f"{label} must cover documents")
    if summary.get("heading_count", 0) <= 0:
        fail(f"{label} must cover document headings")

    classification = payload.get("classification_summary")
    if classification is not None:
        if classification != classification_summary(records):
            fail(f"{label} classification_summary must match records")

    identity = payload.get("index_identity")
    if not isinstance(identity, dict):
        fail(f"{label} index_identity must be an object")
    if identity.get("content_digest") != repo_local_kag_index_digest_without_self(payload):
        fail(f"{label} content_digest must match stable payload digest")
    return payload


def validate_repo_local_kag_repository_index_payload(
    payload: object,
    *,
    source_payload: object,
    label: str,
    expected_index_kind: str | None = None,
) -> dict[str, object]:
    source_index = validate_repo_local_kag_index_payload(
        source_payload,
        label=f"{label} source index",
    )
    return validate_repo_local_kag_repository_index_against_source(
        payload,
        source_index=source_index,
        label=label,
        expected_index_kind=expected_index_kind,
    )


def validate_repo_local_kag_repository_index_against_source(
    payload: object,
    *,
    source_index: dict[str, object],
    label: str,
    expected_index_kind: str | None = None,
) -> dict[str, object]:
    repo_local_kag_validate_payload(
        payload,
        schema_path=REPO_LOCAL_KAG_REPOSITORY_INDEX_SCHEMA_PATH,
        label=label,
    )
    if not isinstance(payload, dict):
        fail(f"{label} must be a JSON object")

    identity = payload.get("index_identity")
    if not isinstance(identity, dict):
        fail(f"{label} index_identity must be an object")
    index_kind = identity.get("index_kind")
    if expected_index_kind is not None and index_kind != expected_index_kind:
        fail(f"{label} must keep index kind {expected_index_kind}")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        fail(f"{label} must keep entries")
    summary = payload.get("summary")
    if not isinstance(summary, dict) or summary.get("entry_count") != len(entries):
        fail(f"{label} summary must match entries")

    source_identity = source_index.get("index_identity")
    if not isinstance(source_identity, dict):
        fail(f"{label} source index identity must be an object")
    source_ref = payload.get("source_index")
    if not isinstance(source_ref, dict):
        fail(f"{label} source_index must be an object")
    if source_ref.get("local_id") != source_identity.get("local_id"):
        fail(f"{label} must pin the source index local id")
    if source_ref.get("content_digest") != source_identity.get("content_digest"):
        fail(f"{label} must pin the source index digest")
    if payload.get("repo") != source_index.get("repo"):
        fail(f"{label} repo identity must match the source index")

    source_records = source_index.get("records")
    if not isinstance(source_records, list):
        fail(f"{label} source index must keep records")
    source_ids = {
        record["identity"]["id"]
        for record in source_records
        if isinstance(record, dict) and isinstance(record.get("identity"), dict)
    }
    for entry in entries:
        if not isinstance(entry, dict):
            fail(f"{label} entries must be objects")
        if index_kind == "artifact":
            referenced_source_ids = [entry.get("id")]
        elif index_kind in {"entity", "event", "assertion"}:
            referenced_source_ids = entry.get("source_record_ids")
        elif index_kind == "relation":
            referenced_source_ids = []
        else:
            referenced_source_ids = [entry.get("source_record_id")]
        if not isinstance(referenced_source_ids, list) or any(
            source_id not in source_ids for source_id in referenced_source_ids
        ):
            fail(f"{label} must return to current source records")
    if identity.get("content_digest") != repo_local_kag_index_digest_without_self(payload):
        fail(f"{label} content_digest must match stable payload digest")
    return payload


def validate_repo_local_kag_repository_index_family(
    family: object,
    *,
    source_payload: object,
    label: str,
) -> dict[str, dict[str, object]]:
    source_index = validate_repo_local_kag_index_payload(
        source_payload,
        label=f"{label} source index",
    )
    if not isinstance(family, dict):
        fail(f"{label} must be an object keyed by index kind")
    expected_kinds = set(REPOSITORY_INDEX_FILENAMES)
    if set(family) != expected_kinds:
        fail(f"{label} must contain the complete repository index family")

    validated: dict[str, dict[str, object]] = {}
    for index_kind in REPOSITORY_INDEX_FILENAMES:
        validated[index_kind] = validate_repo_local_kag_repository_index_against_source(
            family[index_kind],
            source_index=source_index,
            label=f"{label} {index_kind} index",
            expected_index_kind=index_kind,
        )
        profiles = validated[index_kind].get("profiles")
        if not isinstance(profiles, dict):
            fail(f"{label} {index_kind} index must keep profiles")
        extractors = profiles.get("extractors")
        parsers = profiles.get("parsers")
        provenance_profiles = profiles.get("provenance")
        temporal_profiles = profiles.get("temporal")
        trust_profiles = profiles.get("trust")
        if not all(
            isinstance(item, dict)
            for item in (
                extractors,
                parsers,
                provenance_profiles,
                temporal_profiles,
                trust_profiles,
            )
        ):
            fail(f"{label} {index_kind} index profiles must be maps")
        for profile in provenance_profiles.values():
            if not isinstance(profile, dict) or profile.get("extractor_ref") not in extractors:
                fail(f"{label} {index_kind} provenance profiles must resolve extractors")
        for entry in validated[index_kind].get("entries", []):
            if not isinstance(entry, dict):
                continue
            if "parser_ref" in entry and entry.get("parser_ref") not in parsers:
                fail(f"{label} {index_kind} entries must resolve parser profiles")
            if "provenance_ref" in entry and entry.get("provenance_ref") not in provenance_profiles:
                fail(f"{label} {index_kind} entries must resolve provenance profiles")
            if "temporal_ref" in entry and entry.get("temporal_ref") not in temporal_profiles:
                fail(f"{label} {index_kind} entries must resolve temporal profiles")
            if "trust_ref" in entry and entry.get("trust_ref") not in trust_profiles:
                fail(f"{label} {index_kind} entries must resolve trust profiles")

    entries = {
        kind: payload.get("entries", [])
        for kind, payload in validated.items()
    }
    ids_by_kind: dict[str, set[str]] = {}
    for kind, kind_entries in entries.items():
        ids = {
            str(entry.get("id"))
            for entry in kind_entries
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)
        }
        if len(ids) != len(kind_entries):
            fail(f"{label} {kind} index ids must be present and unique")
        ids_by_kind[kind] = ids

    source_records = source_index.get("records")
    source_ids = {
        str(record["identity"]["id"])
        for record in source_records if isinstance(record, dict) and isinstance(record.get("identity"), dict)
    }
    if ids_by_kind["artifact"] != source_ids:
        fail(f"{label} artifact ids must exactly cover current source records")

    anchor_ids = ids_by_kind["anchor"]
    for kind in ("artifact", "entity", "event", "assertion"):
        for entry in entries[kind]:
            if not isinstance(entry, dict):
                continue
            referenced = (
                [entry.get("anchor_id")]
                if kind == "artifact"
                else (
                    entry.get("evidence_anchor_ids")
                    if kind == "assertion"
                    else entry.get("anchor_ids")
                )
            )
            if not isinstance(referenced, list) or (kind != "event" and not referenced):
                fail(f"{label} {kind} entries must keep current anchors")
            if any(anchor_id not in anchor_ids for anchor_id in referenced):
                fail(f"{label} {kind} entries must return to current anchors")
            source_record_ids = (
                [entry.get("id")]
                if kind == "artifact"
                else entry.get("source_record_ids")
            )
            if not isinstance(source_record_ids, list) or any(
                source_id not in source_ids for source_id in source_record_ids
            ):
                fail(f"{label} {kind} entries must return to current source records")

    node_ids = set().union(
        ids_by_kind["artifact"],
        ids_by_kind["anchor"],
        ids_by_kind["entity"],
        ids_by_kind["event"],
        ids_by_kind["assertion"],
    )
    assertion_subject_ids = set().union(
        ids_by_kind["artifact"],
        ids_by_kind["anchor"],
        ids_by_kind["entity"],
        ids_by_kind["event"],
    )
    for assertion in entries["assertion"]:
        if not isinstance(assertion, dict):
            continue
        if assertion.get("subject_id") not in assertion_subject_ids:
            fail(f"{label} assertion subjects must resolve to current nodes")
        object_value = assertion.get("object")
        if (
            isinstance(object_value, dict)
            and object_value.get("kind") == "node"
            and object_value.get("value") not in assertion_subject_ids
        ):
            fail(f"{label} assertion node objects must resolve to current nodes")
        if assertion.get("quality_state") != "accepted":
            fail(f"{label} canonical assertions must pass the quality gate")
    for relation in entries["relation"]:
        if not isinstance(relation, dict):
            continue
        if relation.get("from_id") not in node_ids or relation.get("to_id") not in node_ids:
            fail(f"{label} relation endpoints must resolve to current nodes")
        evidence = relation.get("evidence_anchor_ids")
        if not isinstance(evidence, list) or not evidence or any(
            anchor_id not in anchor_ids for anchor_id in evidence
        ):
            fail(f"{label} relations must return to current evidence anchors")
    return validated


def load_repo_local_kag_repository_index_family(
    repo_root: Path,
    *,
    source_index: Path = Path("kag/indexes/source_surface_index.json"),
    label: str | None = None,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    source_path = source_index if source_index.is_absolute() else repo_root / source_index
    source_payload = read_json(source_path)
    family = {
        index_kind: read_json(source_path.parent / filename)
        for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items()
    }
    validated = validate_repo_local_kag_repository_index_family(
        family,
        source_payload=source_payload,
        label=label or f"{repo_root.name} repo-local KAG family",
    )
    if not isinstance(source_payload, dict):
        fail(f"{label or repo_root.name} source index must be an object")
    return source_payload, validated


def validate_repo_local_kag_index_generated_payload(*, progress: bool = False) -> None:
    _repo_local_index_phase("generated-index-read", progress=progress)
    payload = read_json(REPO_LOCAL_KAG_INDEX_PATH)
    _repo_local_index_phase("generated-index-payload", progress=progress)
    validate_repo_local_kag_index_payload(payload, label="repo-local KAG generated index")
    _repo_local_index_phase("generated-index-rebuild", progress=progress)
    expected = build_index(REPO_ROOT, output=Path("kag/indexes/source_surface_index.json"))
    _repo_local_index_phase("generated-index-parity", progress=progress)
    if payload != expected:
        fail("repo-local KAG generated index drifted from generator")

    _repo_local_index_phase("generated-repository-index-family", progress=progress)
    expected_family = build_repository_indexes(expected, repo_root=REPO_ROOT)
    actual_family: dict[str, object] = {}
    for index_kind, filename in REPOSITORY_INDEX_FILENAMES.items():
        path = REPO_ROOT / "kag" / "indexes" / filename
        family_payload = read_json(path)
        actual_family[index_kind] = family_payload
        if family_payload != expected_family[index_kind]:
            fail(f"repo-local KAG {index_kind} index drifted from generator")
    validate_repo_local_kag_repository_index_family(
        actual_family,
        source_payload=payload,
        label="repo-local KAG repository family",
    )


def validate_repo_local_kag_coverage_payload(payload: object, *, label: str) -> dict[str, object]:
    repo_local_kag_validate_payload(
        payload,
        schema_path=REPO_LOCAL_KAG_COVERAGE_SCHEMA_PATH,
        label=label,
    )
    if not isinstance(payload, dict):
        fail(f"{label} must be a JSON object")
    owners = payload.get("owners")
    if not isinstance(owners, list) or not owners:
        fail(f"{label} must contain owners")
    statuses = {owner.get("index_status") for owner in owners if isinstance(owner, dict)}
    if not {"passed", "migration-needed", "missing", "owner-specific"} & statuses:
        fail(f"{label} must contain repo-local KAG status rows")
    repo_names = [owner.get("repo") for owner in owners if isinstance(owner, dict)]
    if "aoa-kag" not in repo_names:
        fail(f"{label} must include aoa-kag")
    for owner in owners:
        if not isinstance(owner, dict):
            continue
        repo = owner.get("repo")
        index_files = owner.get("index_files")
        repository_index_family = owner.get("repository_index_family")
        domain_index_catalog_ref = owner.get("domain_index_catalog_ref")
        if not isinstance(index_files, list) or not isinstance(repository_index_family, dict):
            fail(f"{label} owner {repo} must expose repository index family routes")
        if any(path not in index_files for path in repository_index_family.values()):
            fail(f"{label} owner {repo} repository index family must return to index_files")
        if owner.get("index_status") == "passed" and repository_index_family != REPOSITORY_INDEX_FAMILY_REFS:
            fail(f"{label} owner {repo} passed status requires the complete repository index family")
        expected_domain_ref = (
            DOMAIN_INDEX_CATALOG_REF if DOMAIN_INDEX_CATALOG_REF in index_files else ""
        )
        if domain_index_catalog_ref != expected_domain_ref:
            fail(f"{label} owner {repo} domain index catalog route must match index_files")
        profile = owner.get("common_surface_profile")
        if not isinstance(profile, dict):
            continue
        counts = profile.get("counts")
        quality = profile.get("quality")
        if not isinstance(counts, dict) or not isinstance(quality, dict):
            fail(f"{label} owner {repo} common_surface_profile must keep counts and quality")
        for key in (
            "artifact_kind",
            "primary_kind",
            "surface_state",
            "document_role",
            "mechanics_role",
            "command_role",
        ):
            if not isinstance(counts.get(key), dict):
                fail(f"{label} owner {repo} common_surface_profile.counts.{key} must be a map")
        for key in (
            "has_kag_home",
            "has_record_classes",
            "has_source_index",
            "has_owner_commands",
            "has_generated_readmodels",
            "has_validation_route",
        ):
            if not isinstance(quality.get(key), bool):
                fail(f"{label} owner {repo} common_surface_profile.quality.{key} must be boolean")
        unknown_count = quality.get("unknown_count")
        if not isinstance(unknown_count, int) or unknown_count < 0:
            fail(
                f"{label} owner {repo} common_surface_profile.quality.unknown_count "
                "must be a non-negative integer"
            )
    return payload


def validate_repo_local_kag_coverage_generated_payload(*, progress: bool = False) -> None:
    _repo_local_index_phase("coverage-read", progress=progress)
    payload = read_json(REPO_LOCAL_KAG_COVERAGE_PATH)
    _repo_local_index_phase("coverage-payload", progress=progress)
    validate_repo_local_kag_coverage_payload(payload, label="repo-local KAG coverage")
    _repo_local_index_phase("coverage-rebuild", progress=progress)
    expected = build_provider_coverage(progress=progress)
    _repo_local_index_phase("coverage-parity", progress=progress)
    if payload != expected:
        fail("repo-local KAG coverage drifted from generator")

    _repo_local_index_phase("coverage-min", progress=progress)
    min_payload = read_json(REPO_LOCAL_KAG_COVERAGE_MIN_PATH)
    if min_payload != payload:
        fail("repo-local KAG min coverage must match full coverage")


def validate_repo_local_kag_index_contract_with_progress() -> None:
    validate_repo_local_kag_index_contract(progress=True)


def validate_repo_local_kag_index_contract(*, progress: bool = False) -> None:
    _repo_local_index_phase("schema-surfaces", progress=progress)
    validate_repo_local_kag_index_schema_surface()
    _repo_local_index_phase("example", progress=progress)
    validate_repo_local_kag_index_example()
    _repo_local_index_phase("generated-index", progress=progress)
    validate_repo_local_kag_index_generated_payload(progress=progress)
    _repo_local_index_phase("generated-coverage", progress=progress)
    validate_repo_local_kag_coverage_generated_payload(progress=progress)
