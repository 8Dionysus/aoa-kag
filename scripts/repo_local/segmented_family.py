"""Bounded segmented KAG family for owners whose corpus exceeds v3/v4 hot limits.

The portable v3 family is intentionally a small, fully materialised compatibility
surface.  It must stay bounded, so it cannot be used as an intermediate build
for a larger owner.  This module keeps the same canonical rows and record keys,
but emits independently addressable segments directly from those rows.  A
consumer reads one segment at a time and never has to materialise the complete
corpus to validate or answer a bounded request.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .portable_family import (
    ANCHOR_DEFAULTS,
    CHUNKABLE_FIELDS,
    COMPATIBILITY_ORDER,
    DEFAULT_DELTA_BYTES_MAX,
    GLOBAL_TRACKED_BYTES_MAX,
    MAX_RECORD_BYTES,
    _portable_rows,
    _previous_ranges,
    _split_ranges,
    reconstruct_compatibility_family,
    render_manifest,
    render_row,
    sha256_bytes,
)


SCHEMA_VERSION = "aoa-repo-local-kag-segmented-family-v1"
SCHEMA_REF = "aoa-kag:schemas/repo-local-kag-segmented-family.schema.json"
MANIFEST_RELATIVE_PATH = Path("kag/indexes/index_family.manifest.json")
SEGMENT_ROOT_RELATIVE_PATH = Path("kag/indexes/segments")
SEGMENT_BYTES_MAX = 16 * 1024 * 1024
REQUEST_BYTES_MAX = 4 * 1024 * 1024
LOGICAL_BYTES_MAX = 8 * 1024 * 1024 * 1024
SEGMENT_RECORDS_MAX = 250_000
PRODUCER_IDENTITY_VERSION = "aoa-kag:segmented-family-producer-v1"
CANDIDATE_IDENTITY_VERSION = "aoa-kag:segmented-family-candidate-v1"
MIGRATION_CONTRACT_VERSION = "aoa-kag:segmented-family-migration-v1"
ZERO_DIGEST = "0" * 64


class SegmentedFamilyError(ValueError):
    """Raised when a segmented family is not safe to build or consume."""


@dataclass(frozen=True)
class SegmentedFamilyBuild:
    manifest: dict[str, Any]
    segment_bytes: Mapping[Path, bytes]


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _manifest_digest(payload: Mapping[str, Any]) -> str:
    candidate = copy.deepcopy(dict(payload))
    identity = candidate.get("family_identity")
    if not isinstance(identity, dict):
        raise SegmentedFamilyError("segmented family needs family_identity")
    identity["content_digest"] = ZERO_DIGEST
    return sha256_bytes(_canonical_bytes(candidate))


def _candidate_digest(
    source_digest: str,
    *,
    part_bytes_max: int,
    request_bytes_max: int,
) -> str:
    return sha256_bytes(
        _canonical_bytes(
            {
                "version": CANDIDATE_IDENTITY_VERSION,
                "source_digest": source_digest,
                "part_bytes_max": part_bytes_max,
                "request_bytes_max": request_bytes_max,
                "schema_version": SCHEMA_VERSION,
            }
        )
    )


def _compatibility_files(
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    filenames = {
        "source": "source_surface_index.json",
        "artifact": "repo_artifact_index.json",
        "anchor": "repo_anchor_index.json",
        "entity": "repo_entity_index.json",
        "event": "repo_event_index.json",
        "assertion": "repo_assertion_index.json",
        "relation": "repo_relation_index.json",
    }
    files: list[dict[str, Any]] = []
    for kind in COMPATIBILITY_ORDER:
        payload = source_index if kind == "source" else family[kind]
        identity = payload.get("index_identity")
        collection = payload.get("records" if kind == "source" else "entries")
        if not isinstance(identity, Mapping) or not isinstance(collection, list):
            raise SegmentedFamilyError(
                f"{kind} compatibility view is incomplete"
            )
        digest = identity.get("content_digest")
        if not isinstance(digest, str) or not digest:
            raise SegmentedFamilyError(f"{kind} compatibility digest is missing")
        files.append(
            {
                "kind": kind,
                "path": (Path("kag/indexes") / filenames[kind]).as_posix(),
                "schema_version": payload.get("schema_version"),
                "content_digest": digest,
                "records": len(collection),
            }
        )
    return files


def _source_header(source_index: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    source_records = source_index.get("records")
    repo = source_index.get("repo")
    identity = source_index.get("index_identity")
    if not isinstance(source_records, list):
        raise SegmentedFamilyError("source index records are required")
    if not isinstance(repo, Mapping) or not isinstance(identity, Mapping):
        raise SegmentedFamilyError("source index repo and identity are required")
    source_digest = identity.get("content_digest")
    if not isinstance(source_digest, str) or not source_digest:
        raise SegmentedFamilyError("source index content digest is required")
    header = copy.deepcopy(dict(source_index))
    header.pop("records", None)
    return header, source_digest


def _validate_limits(
    *,
    part_bytes_max: int,
    request_bytes_max: int,
) -> None:
    if isinstance(part_bytes_max, bool) or not isinstance(part_bytes_max, int) or not (
        MAX_RECORD_BYTES <= part_bytes_max <= GLOBAL_TRACKED_BYTES_MAX
    ):
        raise SegmentedFamilyError(
            "part_bytes_max must be between max record bytes and the owner hard ceiling"
        )
    if isinstance(request_bytes_max, bool) or not isinstance(request_bytes_max, int) or not (
        MAX_RECORD_BYTES <= request_bytes_max <= part_bytes_max
    ):
        raise SegmentedFamilyError(
            "request_bytes_max must be between max record bytes and part_bytes_max"
        )


def build_segmented_family(
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
    *,
    previous_manifest: Mapping[str, Any] | None = None,
    part_bytes_max: int = SEGMENT_BYTES_MAX,
    request_bytes_max: int = REQUEST_BYTES_MAX,
    migration_from: Mapping[str, Any] | None = None,
) -> SegmentedFamilyBuild:
    """Build a bounded, directly segmented family without a v3/v4 full build.

    Rows are still canonical v3 rows; the new ABI changes only delivery and
    admission.  Every part has its own digest, record count, byte budget, and
    deterministic hash range.  Existing ranges are retained where supplied so
    a small source change does not move every unrelated part.
    """
    _validate_limits(
        part_bytes_max=part_bytes_max,
        request_bytes_max=request_bytes_max,
    )
    rows = _portable_rows(source_index, family)
    rows_by_kind: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_kind.setdefault(str(row["_kind"]), []).append(row)

    source_header, source_digest = _source_header(source_index)
    segment_bytes: dict[Path, bytes] = {}
    segment_descriptors: list[dict[str, Any]] = []
    ranges_by_kind: dict[str, list[str]] = {}
    for kind, kind_rows in sorted(rows_by_kind.items()):
        previous_ranges = _previous_ranges(previous_manifest, kind)
        ranges, buckets = _split_ranges(
            kind_rows,
            ranges=previous_ranges or list("0123456789abcdef"),
            # The bounded reader consumes one JSONL segment per request.  Do
            # not let a part be larger than the authoritative request cap
            # unless a streaming reader is added as a separately versioned ABI.
            threshold=request_bytes_max,
        )
        ranges_by_kind[kind] = ranges
        for prefix in ranges:
            bucket = sorted(buckets[prefix], key=lambda row: str(row["_key"]))
            if not bucket:
                continue
            if len(bucket) > SEGMENT_RECORDS_MAX:
                raise SegmentedFamilyError(
                    f"segment {kind}/{prefix} exceeds record budget: "
                    f"{len(bucket)} > {SEGMENT_RECORDS_MAX}"
                )
            content = b"".join(render_row(row) for row in bucket)
            if len(content) > request_bytes_max:
                raise SegmentedFamilyError(
                    f"segment {kind}/{prefix} exceeds byte budget: "
                    f"{len(content)} > {request_bytes_max}"
                )
            path = (
                SEGMENT_ROOT_RELATIVE_PATH
                / kind
                / f"{prefix}.jsonl"
            )
            segment_bytes[path] = content
            segment_descriptors.append(
                {
                    "kind": kind,
                    "range": prefix,
                    "path": path.as_posix(),
                    "digest": f"sha256:{sha256_bytes(content)}",
                    "bytes": len(content),
                    "records": len(bucket),
                    "request_bytes_max": request_bytes_max,
                }
            )

    migration = {
        "contract_version": MIGRATION_CONTRACT_VERSION,
        "from_schemas": [
            "aoa-repo-local-kag-family-manifest-v3",
            "aoa-repo-local-kag-distribution-manifest-v1",
        ],
        "from_family_digest": (
            migration_from.get("content_digest")
            if isinstance(migration_from, Mapping)
            else None
        ),
        "mode": "explicit-provider-pin-dual-read",
        "rollback": "retain-last-good-manifest-and-select-by-digest",
        "decision_ref": (
            "aoa-kag:docs/decisions/"
            "AOA-KAG-D-0051-bounded-segmented-kag-family.md"
        ),
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "repo": copy.deepcopy(dict(source_index["repo"])),
        "family_identity": {
            "local_id": "family:repo-local:segmented-record-corpus",
            "artifact_kind": "repo_local_kag_segmented_family",
            "content_digest": ZERO_DIGEST,
            "schema_ref": SCHEMA_REF,
            "source_snapshot": f"sha256:{source_digest}",
        },
        "producer_identity": {
            "version": PRODUCER_IDENTITY_VERSION,
            "route": "aoa-kag:scripts/repo_local/segmented_family.py",
            "canonical_rows": "portable-record-normalization-v3",
            "identity_inputs": [
                "source_index_content_digest",
                "producer_version",
                "partition_parameters",
            ],
        },
        "candidate_identity": {
            "version": CANDIDATE_IDENTITY_VERSION,
            "content_digest": _candidate_digest(
                source_digest,
                part_bytes_max=part_bytes_max,
                request_bytes_max=request_bytes_max,
            ),
            "source_index_content_digest": source_digest,
        },
        "migration": migration,
        "partitioning": {
            "algorithm": "sha256-record-key-adaptive-prefix",
            "target_part_bytes": min(part_bytes_max, 1 * 1024 * 1024),
            "part_bytes_max": part_bytes_max,
            "max_record_bytes": MAX_RECORD_BYTES,
            "split_policy": "prefix-split-only",
            "merge_policy": "never-automatic",
            "ranges": ranges_by_kind,
        },
        "normalization": {
            "canonical_record_classes": ["source", "anchor", "event"],
            "derived_compatibility_classes": [
                "artifact",
                "entity",
                "assertion",
                "relation",
            ],
            "anchor_defaults": copy.deepcopy(ANCHOR_DEFAULTS),
            "chunking": {
                "strategy": "oversize-list-content-chunks",
                "chunk_target_bytes": 64 * 1024,
                "chunkable_fields": {
                    kind: list(fields)
                    for kind, fields in CHUNKABLE_FIELDS.items()
                },
            },
        },
        "source_index_header": source_header,
        "compatibility": {
            "view": "aoa-repo-local-kag-v2",
            "assembly": "deterministic-on-demand-from-segments",
            "requires_explicit_provider_pin": True,
            "files": _compatibility_files(source_index, family),
        },
        "budgets": {
            "part_bytes_max": part_bytes_max,
            "request_bytes_max": request_bytes_max,
            "max_record_bytes": MAX_RECORD_BYTES,
            "logical_bytes_max": LOGICAL_BYTES_MAX,
            "changed_generated_bytes_max": DEFAULT_DELTA_BYTES_MAX,
            "legacy_owner_hard_bytes_max": GLOBAL_TRACKED_BYTES_MAX,
            "tracked_bytes_max": GLOBAL_TRACKED_BYTES_MAX,
            "fail_closed": True,
        },
        "summary": {
            "source_records": len(source_index["records"]),
            "canonical_records": len(rows),
            "segments": len(segment_descriptors),
            "logical_bytes": sum(len(content) for content in segment_bytes.values()),
            "max_segment_bytes": max(
                (len(content) for content in segment_bytes.values()),
                default=0,
            ),
            "control_bytes": 0,
            "tracked_bytes": 0,
        },
        "segments": sorted(
            segment_descriptors,
            key=lambda item: (item["kind"], len(item["range"]), item["range"]),
        ),
    }
    for _ in range(12):
        control_bytes = len(render_manifest(manifest))
        if (
            manifest["summary"]["control_bytes"] == control_bytes
            and manifest["summary"]["tracked_bytes"] == control_bytes
        ):
            break
        manifest["summary"]["control_bytes"] = control_bytes
        manifest["summary"]["tracked_bytes"] = control_bytes
    else:  # pragma: no cover
        raise SegmentedFamilyError("segmented control byte count did not converge")
    if manifest["summary"]["logical_bytes"] > LOGICAL_BYTES_MAX:
        raise SegmentedFamilyError(
            "segmented logical corpus exceeds declared logical byte budget"
        )
    manifest["family_identity"]["content_digest"] = _manifest_digest(manifest)
    if manifest["summary"]["control_bytes"] != len(render_manifest(manifest)):
        raise SegmentedFamilyError("segmented control bytes changed after digest")
    return SegmentedFamilyBuild(manifest=manifest, segment_bytes=segment_bytes)


def _descriptor_map(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    segments = manifest.get("segments")
    if not isinstance(segments, list) or not segments:
        raise SegmentedFamilyError("segmented family needs segments")
    result: dict[str, dict[str, Any]] = {}
    for descriptor in segments:
        if not isinstance(descriptor, dict):
            raise SegmentedFamilyError("segment descriptors must be objects")
        path = descriptor.get("path")
        if not isinstance(path, str) or not path.startswith(
            f"{SEGMENT_ROOT_RELATIVE_PATH.as_posix()}/"
        ):
            raise SegmentedFamilyError("segment path escapes segmented root")
        if path in result:
            raise SegmentedFamilyError("segment paths must be unique")
        result[path] = descriptor
    return result


def validate_segmented_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate the fail-closed control-plane invariants without reading data."""
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise SegmentedFamilyError(f"segmented family schema must be {SCHEMA_VERSION}")
    identity = manifest.get("family_identity")
    if not isinstance(identity, Mapping):
        raise SegmentedFamilyError("segmented family needs family_identity")
    if identity.get("content_digest") != _manifest_digest(manifest):
        raise SegmentedFamilyError("segmented family manifest digest does not match")
    budgets = manifest.get("budgets")
    if not isinstance(budgets, Mapping) or budgets.get("fail_closed") is not True:
        raise SegmentedFamilyError("segmented family budgets must fail closed")
    part_limit = budgets.get("part_bytes_max")
    request_limit = budgets.get("request_bytes_max")
    _validate_limits(
        part_bytes_max=part_limit,
        request_bytes_max=request_limit,
    )
    summary = manifest.get("summary")
    if not isinstance(summary, Mapping):
        raise SegmentedFamilyError("segmented family needs summary")
    descriptors = _descriptor_map(manifest)
    if summary.get("segments") != len(descriptors):
        raise SegmentedFamilyError("segmented segment count does not match")
    if summary.get("max_segment_bytes", 0) > part_limit:
        raise SegmentedFamilyError("segmented max segment exceeds part budget")
    if summary.get("max_segment_bytes", 0) > request_limit:
        raise SegmentedFamilyError("segmented max segment exceeds request budget")
    if summary.get("logical_bytes", 0) > budgets.get("logical_bytes_max", -1):
        raise SegmentedFamilyError("segmented logical bytes exceed budget")


def read_segment(
    repo_root: Path,
    manifest: Mapping[str, Any],
    descriptor: Mapping[str, Any],
    *,
    request_bytes_max: int | None = None,
) -> list[dict[str, Any]]:
    """Read exactly one verified segment under the request byte budget."""
    validate_segmented_manifest(manifest)
    path_text = descriptor.get("path")
    if not isinstance(path_text, str):
        raise SegmentedFamilyError("segment path is required")
    known = _descriptor_map(manifest).get(path_text)
    if known is None or dict(known) != dict(descriptor):
        raise SegmentedFamilyError("segment is not described by the manifest")
    declared_request_limit = manifest["budgets"]["request_bytes_max"]
    if request_bytes_max is None:
        budget = declared_request_limit
    else:
        budget = request_bytes_max
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < MAX_RECORD_BYTES:
        raise SegmentedFamilyError("request byte budget is invalid")
    if budget > declared_request_limit:
        raise SegmentedFamilyError(
            "caller request byte budget exceeds the manifest authority"
        )
    if descriptor.get("request_bytes_max") != declared_request_limit:
        raise SegmentedFamilyError("segment request budget is not manifest-bound")
    declared_bytes = descriptor.get("bytes")
    if not isinstance(declared_bytes, int) or declared_bytes > budget:
        raise SegmentedFamilyError("segment exceeds request byte budget")
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        raise SegmentedFamilyError("segment path must stay in repository")
    content = (repo_root / path).read_bytes()
    if len(content) != declared_bytes:
        raise SegmentedFamilyError("segment byte count does not match")
    if descriptor.get("digest") != f"sha256:{sha256_bytes(content)}":
        raise SegmentedFamilyError("segment digest does not match")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        if len(line) + 1 > MAX_RECORD_BYTES:
            raise SegmentedFamilyError(
                f"{path}:{line_number} exceeds record budget"
            )
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SegmentedFamilyError(f"{path}:{line_number} is not JSON") from exc
        if not isinstance(row, dict):
            raise SegmentedFamilyError(f"{path}:{line_number} must be an object")
        if row.get("_kind") != descriptor.get("kind"):
            raise SegmentedFamilyError(f"{path}:{line_number} kind mismatch")
        rows.append(row)
    if descriptor.get("records") != len(rows):
        raise SegmentedFamilyError("segment record count does not match")
    return rows


def load_segmented_family(
    repo_root: Path,
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
    max_materialized_bytes: int = GLOBAL_TRACKED_BYTES_MAX,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    """Load a complete compatibility view under an explicit materialisation cap."""
    if (
        isinstance(max_materialized_bytes, bool)
        or not isinstance(max_materialized_bytes, int)
        or max_materialized_bytes <= 0
    ):
        raise SegmentedFamilyError("materialisation budget is invalid")
    manifest_payload = json.loads(
        (repo_root / manifest_path).read_text(encoding="utf-8")
    )
    if not isinstance(manifest_payload, dict):
        raise SegmentedFamilyError("segmented manifest must be an object")
    validate_segmented_manifest(manifest_payload)
    logical_bytes = manifest_payload["summary"]["logical_bytes"]
    if logical_bytes > max_materialized_bytes:
        raise SegmentedFamilyError(
            "complete compatibility assembly exceeds materialisation budget; "
            "use read_segment for bounded access"
        )
    rows: list[dict[str, Any]] = []
    for descriptor in manifest_payload["segments"]:
        rows.extend(read_segment(repo_root, manifest_payload, descriptor))
    keys = [row.get("_key") for row in rows]
    if len(keys) != len(set(keys)):
        raise SegmentedFamilyError("segmented record keys must be unique")
    source, family = reconstruct_compatibility_family(manifest_payload, rows)
    return source, family, manifest_payload


def validate_segmented_segments(
    repo_root: Path,
    manifest: Mapping[str, Any],
) -> dict[str, int]:
    """Verify every bounded segment without assembling a compatibility view."""
    validate_segmented_manifest(manifest)
    seen: set[str] = set()
    total_rows = 0
    total_bytes = 0
    for descriptor in manifest["segments"]:
        rows = read_segment(repo_root, manifest, descriptor)
        for row in rows:
            key = row.get("_key")
            if not isinstance(key, str) or key in seen:
                raise SegmentedFamilyError("segmented record keys must be unique")
            seen.add(key)
        total_rows += len(rows)
        total_bytes += int(descriptor["bytes"])
    if total_rows != manifest["summary"]["canonical_records"]:
        raise SegmentedFamilyError("segmented canonical record count does not match")
    if total_bytes != manifest["summary"]["logical_bytes"]:
        raise SegmentedFamilyError("segmented logical byte total does not match")
    return {"segments": len(manifest["segments"]), "records": total_rows, "bytes": total_bytes}


def write_segmented_output(
    repo_root: Path,
    build: SegmentedFamilyBuild,
) -> None:
    """Write only the explicitly-owned manifest and segment files."""
    root = repo_root.resolve()
    expected = set(build.segment_bytes)
    actual = {
        path.relative_to(root)
        for path in (root / SEGMENT_ROOT_RELATIVE_PATH).glob("*/*.jsonl")
        if path.is_file()
    }
    for path in sorted(actual - expected):
        (root / path).unlink()
    for path, content in build.segment_bytes.items():
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.is_file() or destination.read_bytes() != content:
            destination.write_bytes(content)
    destination = root / MANIFEST_RELATIVE_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.is_file() or destination.read_bytes() != render_manifest(build.manifest):
        destination.write_bytes(render_manifest(build.manifest))


def check_segmented_output(repo_root: Path, build: SegmentedFamilyBuild) -> bool:
    root = repo_root.resolve()
    manifest_path = root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file() or manifest_path.read_bytes() != render_manifest(build.manifest):
        return False
    for path, content in build.segment_bytes.items():
        destination = root / path
        if not destination.is_file() or destination.read_bytes() != content:
            return False
    actual = {
        path.relative_to(root)
        for path in (root / SEGMENT_ROOT_RELATIVE_PATH).glob("*/*.jsonl")
        if path.is_file()
    }
    return actual == set(build.segment_bytes)


def segment_for_key(manifest: Mapping[str, Any], key: str) -> dict[str, Any]:
    """Return the unique segment descriptor for one portable record key."""
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    kind, _, _ = key.partition(":")
    candidates = [
        descriptor
        for descriptor in manifest.get("segments", [])
        if isinstance(descriptor, Mapping) and descriptor.get("kind") == kind
    ]
    matches = [
        descriptor
        for descriptor in candidates
        if isinstance(descriptor.get("range"), str)
        and digest.startswith(descriptor["range"])
    ]
    if not matches:
        raise SegmentedFamilyError(f"no segment covers record key {key}")
    return max(matches, key=lambda descriptor: len(str(descriptor["range"])))


__all__ = [
    "CANDIDATE_IDENTITY_VERSION",
    "GLOBAL_TRACKED_BYTES_MAX",
    "MANIFEST_RELATIVE_PATH",
    "REQUEST_BYTES_MAX",
    "SCHEMA_REF",
    "SCHEMA_VERSION",
    "SEGMENT_BYTES_MAX",
    "SEGMENT_ROOT_RELATIVE_PATH",
    "SegmentedFamilyBuild",
    "SegmentedFamilyError",
    "build_segmented_family",
    "check_segmented_output",
    "load_segmented_family",
    "read_segment",
    "segment_for_key",
    "validate_segmented_segments",
    "validate_segmented_manifest",
    "write_segmented_output",
]
