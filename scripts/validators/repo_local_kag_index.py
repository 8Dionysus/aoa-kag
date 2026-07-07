from __future__ import annotations

import copy
import sys

from .common import *
from .schema_surfaces import validate_top_level_schema

try:
    from scripts.generate_repo_local_kag_coverage import build_provider_coverage
    from scripts.generate_repo_local_kag_index import build_index, classification_summary
except ImportError:  # pragma: no cover - direct script import fallback
    from generate_repo_local_kag_coverage import build_provider_coverage  # type: ignore
    from generate_repo_local_kag_index import build_index, classification_summary  # type: ignore


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
    validate_top_level_schema(REPO_LOCAL_KAG_COVERAGE_SCHEMA_PATH, "repo-local KAG coverage")


def validate_repo_local_kag_index_example() -> None:
    payload = read_json(REPO_LOCAL_KAG_INDEX_EXAMPLE_PATH)
    repo_local_kag_validate_payload(
        payload,
        schema_path=REPO_LOCAL_KAG_INDEX_SCHEMA_PATH,
        label="repo-local KAG index example",
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
