from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "aoa-repo-local-kag-family-manifest-v3"
SCHEMA_REF = "aoa-kag:schemas/repo-local-kag-family-manifest.schema.json"
MANIFEST_RELATIVE_PATH = Path("kag/indexes/index_family.manifest.json")
SHARD_ROOT_RELATIVE_PATH = Path("kag/indexes/shards")
BUDGET_RECEIPT_ROOT_RELATIVE_PATH = Path(
    "kag/receipts/index_family_budget"
)
BUDGET_RECEIPT_SCHEMA_VERSION = "aoa-repo-local-kag-budget-receipt-v1"
DECISION_REF = (
    "aoa-kag:docs/decisions/"
    "AOA-KAG-D-0017-portable-content-addressed-repository-family.md"
)

TARGET_SHARD_BYTES = 128 * 1024
HARD_MAX_SHARD_BYTES = 192 * 1024
MAX_RECORD_BYTES = 128 * 1024
CHUNK_TARGET_BYTES = 64 * 1024
DEFAULT_DELTA_BYTES_MAX = 1024 * 1024
GLOBAL_TRACKED_BYTES_MAX = 48 * 1024 * 1024
OS_AGGREGATE_TRACKED_BYTES_MAX = 320 * 1024 * 1024
MIN_BASELINE_BYTES = 4 * 1024 * 1024
BASELINE_HEADROOM = 1.10
HEX_DIGITS = "0123456789abcdef"
ZERO_DIGEST = "0" * 64

LEGACY_INDEX_FILENAMES = {
    "source": "source_surface_index.json",
    "artifact": "repo_artifact_index.json",
    "anchor": "repo_anchor_index.json",
    "entity": "repo_entity_index.json",
    "event": "repo_event_index.json",
    "assertion": "repo_assertion_index.json",
    "relation": "repo_relation_index.json",
}
COMPATIBILITY_ORDER = (
    "source",
    "artifact",
    "anchor",
    "entity",
    "event",
    "assertion",
    "relation",
)
ANCHOR_DEFAULTS = {
    "evidence_class": "deterministic",
    "provenance_ref": "deterministic",
    "temporal_ref": "current",
    "trust_ref": "deterministic",
}
CHUNKABLE_FIELDS = {
    "anchor": ("outbound_refs",),
    "event": (
        "anchor_ids",
        "changes",
        "evidence_refs",
        "object_ids",
        "source_record_ids",
    ),
}


class PortableFamilyError(ValueError):
    pass


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def render_manifest(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def render_row(payload: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(payload) + b"\n"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def manifest_digest(payload: Mapping[str, Any]) -> str:
    candidate = copy.deepcopy(dict(payload))
    identity = candidate.get("family_identity")
    if not isinstance(identity, dict):
        raise PortableFamilyError("portable family manifest needs family_identity")
    identity["content_digest"] = ZERO_DIGEST
    return sha256_bytes(canonical_json_bytes(candidate))


def is_portable_control_path(path: Path) -> bool:
    return (
        path == MANIFEST_RELATIVE_PATH
        or SHARD_ROOT_RELATIVE_PATH in (path, *path.parents)
        or BUDGET_RECEIPT_ROOT_RELATIVE_PATH in (path, *path.parents)
    )


def _row_key(row: Mapping[str, Any]) -> str:
    value = row.get("_key")
    if not isinstance(value, str) or not value:
        raise PortableFamilyError("portable record needs a non-empty _key")
    return value


def _row_kind(row: Mapping[str, Any]) -> str:
    value = row.get("_kind")
    if not isinstance(value, str) or not value:
        raise PortableFamilyError("portable record needs a non-empty _kind")
    return value


def _chunk_large_row(
    row: dict[str, Any],
    *,
    parent_kind: str,
    chunkable_fields: Sequence[str],
) -> list[dict[str, Any]]:
    if len(render_row(row)) <= MAX_RECORD_BYTES:
        return [row]
    parent_key = _row_key(row)
    core = copy.deepcopy(row)
    chunked_fields: list[str] = []
    chunks: list[dict[str, Any]] = []
    for field in chunkable_fields:
        values = core.get(field)
        if not isinstance(values, list) or not values:
            continue
        core[field] = []
        chunked_fields.append(field)
        batch: list[Any] = []
        position = 0
        for value in values:
            candidate = [*batch, copy.deepcopy(value)]
            probe = {
                "_kind": f"{parent_kind}_chunk",
                "_key": f"{parent_key}:{field}:{position}",
                "parent": parent_key,
                "field": field,
                "position": position,
                "values": candidate,
            }
            if batch and len(render_row(probe)) > CHUNK_TARGET_BYTES:
                chunks.append(
                    {
                        "_kind": f"{parent_kind}_chunk",
                        "_key": f"{parent_key}:{field}:{position}",
                        "parent": parent_key,
                        "field": field,
                        "position": position,
                        "values": batch,
                    }
                )
                position += 1
                batch = [copy.deepcopy(value)]
            else:
                batch = candidate
        if batch:
            chunks.append(
                {
                    "_kind": f"{parent_kind}_chunk",
                    "_key": f"{parent_key}:{field}:{position}",
                    "parent": parent_key,
                    "field": field,
                    "position": position,
                    "values": batch,
                }
            )
    core["_chunked"] = chunked_fields
    expanded = [core, *chunks]
    oversized = [
        (_row_key(candidate), len(render_row(candidate)))
        for candidate in expanded
        if len(render_row(candidate)) > MAX_RECORD_BYTES
    ]
    if oversized:
        key, size = oversized[0]
        raise PortableFamilyError(
            f"portable record {key} is {size} bytes; maximum is "
            f"{MAX_RECORD_BYTES}"
        )
    return expanded


def _portable_rows(
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_records = source_index.get("records")
    if not isinstance(source_records, list):
        raise PortableFamilyError("source index must carry records")
    for source in source_records:
        if not isinstance(source, dict):
            raise PortableFamilyError("source records must be objects")
        identity = source.get("identity")
        if not isinstance(identity, dict) or not isinstance(identity.get("id"), str):
            raise PortableFamilyError("source record needs identity.id")
        key = f"source:{identity['id']}"
        rows.extend(
            _chunk_large_row(
                {"_kind": "source", "_key": key, **copy.deepcopy(source)},
                parent_kind="source",
                chunkable_fields=(),
            )
        )

    anchor_payload = family.get("anchor")
    anchor_entries = (
        anchor_payload.get("entries") if isinstance(anchor_payload, Mapping) else None
    )
    if not isinstance(anchor_entries, list):
        raise PortableFamilyError("repository family must carry anchor entries")
    for source_anchor in anchor_entries:
        if not isinstance(source_anchor, dict):
            raise PortableFamilyError("anchor entries must be objects")
        anchor = copy.deepcopy(source_anchor)
        source_id = anchor.pop("source_record_id", None)
        anchor_id = anchor.get("id")
        if not isinstance(source_id, str) or not isinstance(anchor_id, str):
            raise PortableFamilyError("anchor needs id and source_record_id")
        for field, expected in ANCHOR_DEFAULTS.items():
            if anchor.pop(field, None) != expected:
                raise PortableFamilyError(
                    f"anchor {anchor_id} has non-canonical {field}"
                )
        key = f"anchor:{source_id}:{anchor_id}"
        rows.extend(
            _chunk_large_row(
                {
                    "_kind": "anchor",
                    "_key": key,
                    "source_id": source_id,
                    **anchor,
                },
                parent_kind="anchor",
                chunkable_fields=CHUNKABLE_FIELDS["anchor"],
            )
        )

    event_payload = family.get("event")
    event_entries = (
        event_payload.get("entries") if isinstance(event_payload, Mapping) else None
    )
    if not isinstance(event_entries, list):
        raise PortableFamilyError("repository family must carry event entries")
    for source_event in event_entries:
        if not isinstance(source_event, dict) or not isinstance(
            source_event.get("id"), str
        ):
            raise PortableFamilyError("event entries must carry id")
        key = f"event:{source_event['id']}"
        rows.extend(
            _chunk_large_row(
                {"_kind": "event", "_key": key, **copy.deepcopy(source_event)},
                parent_kind="event",
                chunkable_fields=CHUNKABLE_FIELDS["event"],
            )
        )

    keys = [_row_key(row) for row in rows]
    if len(keys) != len(set(keys)):
        raise PortableFamilyError("portable record keys must be unique")
    return sorted(rows, key=lambda row: (_row_kind(row), _row_key(row)))


def _initial_ranges() -> list[str]:
    return list(HEX_DIGITS)


def _previous_ranges(
    previous_manifest: Mapping[str, Any] | None,
    kind: str,
) -> list[str]:
    if previous_manifest is None:
        return []
    partitioning = previous_manifest.get("partitioning")
    ranges = (
        partitioning.get("ranges")
        if isinstance(partitioning, Mapping)
        else None
    )
    values = ranges.get(kind) if isinstance(ranges, Mapping) else None
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value for value in values
    ):
        return []
    return sorted(set(values), key=lambda value: (len(value), value))


def _range_for_hash(digest: str, ranges: Sequence[str]) -> str:
    matches = [prefix for prefix in ranges if digest.startswith(prefix)]
    if not matches:
        raise PortableFamilyError(
            f"partition ranges do not cover digest {digest}"
        )
    return max(matches, key=len)


def _split_ranges(
    rows: Sequence[dict[str, Any]],
    *,
    ranges: Sequence[str],
    threshold: int,
) -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
    leaves = set(ranges or _initial_ranges())
    encoded = {
        _row_key(row): render_row(row)
        for row in rows
    }
    hashes = {
        key: sha256_bytes(key.encode("utf-8"))
        for key in encoded
    }
    while True:
        buckets: dict[str, list[dict[str, Any]]] = {
            prefix: [] for prefix in leaves
        }
        for row in rows:
            key = _row_key(row)
            buckets[_range_for_hash(hashes[key], tuple(leaves))].append(row)
        oversized = [
            prefix
            for prefix, bucket in buckets.items()
            if sum(len(encoded[_row_key(row)]) for row in bucket) > threshold
        ]
        if not oversized:
            return (
                sorted(leaves, key=lambda value: (len(value), value)),
                buckets,
            )
        for prefix in oversized:
            if len(prefix) >= 64:
                raise PortableFamilyError(
                    f"cannot split oversized portable shard {prefix}"
                )
            leaves.remove(prefix)
            leaves.update(f"{prefix}{digit}" for digit in HEX_DIGITS)


def _compatibility_files(
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for kind in COMPATIBILITY_ORDER:
        payload = source_index if kind == "source" else family[kind]
        identity = payload.get("index_identity")
        if not isinstance(identity, Mapping):
            raise PortableFamilyError(f"{kind} compatibility view needs identity")
        collection = payload.get("records" if kind == "source" else "entries")
        if not isinstance(collection, list):
            raise PortableFamilyError(f"{kind} compatibility view needs records")
        content_digest = identity.get("content_digest")
        if not isinstance(content_digest, str):
            raise PortableFamilyError(
                f"{kind} compatibility view needs content digest"
            )
        files.append(
            {
                "kind": kind,
                "path": (
                    Path("kag/indexes") / LEGACY_INDEX_FILENAMES[kind]
                ).as_posix(),
                "schema_version": payload.get("schema_version"),
                "content_digest": content_digest,
                "records": len(collection),
            }
        )
    return files


def _baseline_cap(tracked_bytes: int) -> int:
    rounded = math.ceil(
        (tracked_bytes * BASELINE_HEADROOM) / (1024 * 1024)
    ) * 1024 * 1024
    return min(
        GLOBAL_TRACKED_BYTES_MAX,
        max(MIN_BASELINE_BYTES, rounded),
    )


def _preserved_tracked_cap(
    previous_manifest: Mapping[str, Any] | None,
) -> int | None:
    budgets = (
        previous_manifest.get("budgets")
        if isinstance(previous_manifest, Mapping)
        else None
    )
    value = (
        budgets.get("tracked_bytes_max")
        if isinstance(budgets, Mapping)
        else None
    )
    if isinstance(value, int) and 0 < value <= GLOBAL_TRACKED_BYTES_MAX:
        return value
    return None


def build_portable_family(
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
    *,
    previous_manifest: Mapping[str, Any] | None = None,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
) -> tuple[dict[str, Any], dict[Path, bytes]]:
    rows = _portable_rows(source_index, family)
    rows_by_kind: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_kind.setdefault(_row_kind(row), []).append(row)

    ranges_by_kind: dict[str, list[str]] = {}
    shard_bytes: dict[Path, bytes] = {}
    shard_descriptors: list[dict[str, Any]] = []
    for kind, kind_rows in sorted(rows_by_kind.items()):
        previous_ranges = _previous_ranges(previous_manifest, kind)
        ranges, buckets = _split_ranges(
            kind_rows,
            ranges=previous_ranges or _initial_ranges(),
            threshold=(
                HARD_MAX_SHARD_BYTES
                if previous_ranges
                else TARGET_SHARD_BYTES
            ),
        )
        ranges_by_kind[kind] = ranges
        for prefix in ranges:
            bucket = sorted(buckets[prefix], key=_row_key)
            if not bucket:
                continue
            content = b"".join(render_row(row) for row in bucket)
            if len(content) > HARD_MAX_SHARD_BYTES:
                raise PortableFamilyError(
                    f"portable shard {kind}/{prefix} is {len(content)} bytes"
                )
            path = (
                manifest_path.parent
                / "shards"
                / kind
                / f"{prefix}.jsonl"
            )
            shard_bytes[path] = content
            shard_descriptors.append(
                {
                    "kind": kind,
                    "range": prefix,
                    "path": path.as_posix(),
                    "digest": f"sha256:{sha256_bytes(content)}",
                    "bytes": len(content),
                    "records": len(bucket),
                }
            )

    source_header = copy.deepcopy(dict(source_index))
    source_records = source_header.pop("records", None)
    if not isinstance(source_records, list):
        raise PortableFamilyError("source index records are required")
    repo = source_index.get("repo")
    source_identity = source_index.get("index_identity")
    if not isinstance(repo, Mapping) or not isinstance(source_identity, Mapping):
        raise PortableFamilyError("source index repo and identity are required")
    source_digest = source_identity.get("content_digest")
    if not isinstance(source_digest, str):
        raise PortableFamilyError("source index content digest is required")

    preserved_cap = _preserved_tracked_cap(previous_manifest)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "repo": copy.deepcopy(dict(repo)),
        "family_identity": {
            "local_id": "family:repo-local:portable-record-corpus",
            "artifact_kind": "repo_local_kag_portable_family",
            "content_digest": ZERO_DIGEST,
            "schema_ref": SCHEMA_REF,
            "source_snapshot": f"sha256:{source_digest}",
        },
        "partitioning": {
            "algorithm": "sha256-record-key-adaptive-prefix",
            "target_shard_bytes": TARGET_SHARD_BYTES,
            "hard_max_shard_bytes": HARD_MAX_SHARD_BYTES,
            "max_record_bytes": MAX_RECORD_BYTES,
            "split_policy": "prefix-split-only",
            "merge_policy": "never-automatic",
            "ranges": ranges_by_kind,
        },
        "normalization": {
            "canonical_record_classes": [
                "source",
                "anchor",
                "event",
            ],
            "derived_compatibility_classes": [
                "artifact",
                "entity",
                "assertion",
                "relation",
            ],
            "anchor_defaults": copy.deepcopy(ANCHOR_DEFAULTS),
            "chunking": {
                "strategy": "oversize-list-content-chunks",
                "chunk_target_bytes": CHUNK_TARGET_BYTES,
                "chunkable_fields": {
                    kind: list(fields)
                    for kind, fields in CHUNKABLE_FIELDS.items()
                },
            },
        },
        "source_index_header": source_header,
        "compatibility": {
            "view": "aoa-repo-local-kag-v2",
            "assembly": "deterministic-on-demand",
            "files": _compatibility_files(source_index, family),
        },
        "budgets": {
            "tracked_bytes_max": (
                preserved_cap
                if preserved_cap is not None
                else GLOBAL_TRACKED_BYTES_MAX
            ),
            "changed_generated_bytes_max": DEFAULT_DELTA_BYTES_MAX,
            "global_tracked_bytes_max": GLOBAL_TRACKED_BYTES_MAX,
            "exceedance_route": (
                BUDGET_RECEIPT_ROOT_RELATIVE_PATH.as_posix()
                + "/<family-digest>.json"
            ),
        },
        "summary": {
            "source_records": len(source_records),
            "anchor_records": len(family["anchor"]["entries"]),
            "event_records": len(family["event"]["entries"]),
            "canonical_records": len(rows),
            "shards": len(shard_descriptors),
            "shard_bytes": sum(len(content) for content in shard_bytes.values()),
            "tracked_bytes": 0,
        },
        "shards": sorted(
            shard_descriptors,
            key=lambda item: (item["kind"], len(item["range"]), item["range"]),
        ),
    }

    for _ in range(12):
        tracked = len(render_manifest(manifest)) + manifest["summary"]["shard_bytes"]
        if manifest["summary"]["tracked_bytes"] == tracked:
            break
        manifest["summary"]["tracked_bytes"] = tracked
    else:  # pragma: no cover - integer-width convergence guard
        raise PortableFamilyError("portable tracked byte count did not converge")

    if preserved_cap is None:
        manifest["budgets"]["tracked_bytes_max"] = _baseline_cap(
            manifest["summary"]["tracked_bytes"]
        )
        for _ in range(12):
            tracked = (
                len(render_manifest(manifest))
                + manifest["summary"]["shard_bytes"]
            )
            if manifest["summary"]["tracked_bytes"] == tracked:
                break
            manifest["summary"]["tracked_bytes"] = tracked
        else:  # pragma: no cover
            raise PortableFamilyError(
                "portable tracked byte count did not converge after baseline"
            )

    if (
        manifest["summary"]["tracked_bytes"]
        > manifest["budgets"]["global_tracked_bytes_max"]
    ):
        raise PortableFamilyError(
            "portable family tracked bytes exceed the global owner ceiling: "
            f"{manifest['summary']['tracked_bytes']} > "
            f"{manifest['budgets']['global_tracked_bytes_max']}"
        )
    manifest["family_identity"]["content_digest"] = manifest_digest(manifest)
    final_tracked = (
        len(render_manifest(manifest))
        + manifest["summary"]["shard_bytes"]
    )
    if final_tracked != manifest["summary"]["tracked_bytes"]:
        raise PortableFamilyError("portable tracked byte count changed after digest")
    return manifest, shard_bytes


def _validate_manifest_shape(manifest: object) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise PortableFamilyError("portable family manifest must be an object")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise PortableFamilyError(
            f"portable family schema must be {SCHEMA_VERSION}"
        )
    identity = manifest.get("family_identity")
    if not isinstance(identity, dict):
        raise PortableFamilyError("portable family needs family_identity")
    if identity.get("content_digest") != manifest_digest(manifest):
        raise PortableFamilyError("portable family manifest digest does not match")
    summary = manifest.get("summary")
    shards = manifest.get("shards")
    if not isinstance(summary, dict) or not isinstance(shards, list):
        raise PortableFamilyError("portable family needs summary and shards")
    return manifest


def _load_rows(
    repo_root: Path,
    manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    shards = manifest.get("shards")
    if not isinstance(shards, list):
        raise PortableFamilyError("portable family shards must be a list")
    shard_bytes = 0
    for descriptor in shards:
        if not isinstance(descriptor, dict):
            raise PortableFamilyError("portable shard descriptors must be objects")
        relative = descriptor.get("path")
        if not isinstance(relative, str):
            raise PortableFamilyError("portable shard path must be a string")
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise PortableFamilyError("portable shard path must stay in repository")
        content = (repo_root / path).read_bytes()
        digest = descriptor.get("digest")
        if digest != f"sha256:{sha256_bytes(content)}":
            raise PortableFamilyError(
                f"portable shard digest does not match: {relative}"
            )
        if descriptor.get("bytes") != len(content):
            raise PortableFamilyError(
                f"portable shard byte count does not match: {relative}"
            )
        shard_rows: list[dict[str, Any]] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PortableFamilyError(
                    f"{relative}:{line_number} is not valid JSON"
                ) from exc
            if not isinstance(row, dict):
                raise PortableFamilyError(
                    f"{relative}:{line_number} must be an object"
                )
            if _row_kind(row) != descriptor.get("kind"):
                raise PortableFamilyError(
                    f"{relative}:{line_number} record kind does not match shard"
                )
            if len(line) + 1 > MAX_RECORD_BYTES:
                raise PortableFamilyError(
                    f"{relative}:{line_number} exceeds record budget"
                )
            shard_rows.append(row)
        if descriptor.get("records") != len(shard_rows):
            raise PortableFamilyError(
                f"portable shard record count does not match: {relative}"
            )
        rows.extend(shard_rows)
        shard_bytes += len(content)
    keys = [_row_key(row) for row in rows]
    if len(keys) != len(set(keys)):
        raise PortableFamilyError("portable record keys must be unique")
    summary = manifest["summary"]
    if summary.get("canonical_records") != len(rows):
        raise PortableFamilyError("portable canonical record count does not match")
    if summary.get("shard_bytes") != shard_bytes:
        raise PortableFamilyError("portable shard byte total does not match")
    manifest_bytes = render_manifest(manifest)
    if summary.get("tracked_bytes") != len(manifest_bytes) + shard_bytes:
        raise PortableFamilyError("portable tracked byte total does not match")
    budgets = manifest.get("budgets")
    if not isinstance(budgets, dict):
        raise PortableFamilyError("portable family needs budgets")
    if budgets.get("global_tracked_bytes_max") != GLOBAL_TRACKED_BYTES_MAX:
        raise PortableFamilyError("portable global tracked byte budget drifted")
    if summary["tracked_bytes"] > budgets.get("tracked_bytes_max", -1):
        _validate_tracked_size_receipt(repo_root, manifest)
    return rows


def _expanded_parents(
    rows: Sequence[dict[str, Any]],
    *,
    parent_kind: str,
) -> list[dict[str, Any]]:
    chunk_kind = f"{parent_kind}_chunk"
    parents = {
        _row_key(row): copy.deepcopy(row)
        for row in rows
        if _row_kind(row) == parent_kind
    }
    chunks_by_parent: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in rows:
        if _row_kind(row) != chunk_kind:
            continue
        parent = row.get("parent")
        field = row.get("field")
        position = row.get("position")
        values = row.get("values")
        if (
            not isinstance(parent, str)
            or not isinstance(field, str)
            or not isinstance(position, int)
            or not isinstance(values, list)
        ):
            raise PortableFamilyError(f"{chunk_kind} record is malformed")
        chunks_by_parent.setdefault(parent, {}).setdefault(field, []).append(row)
    for parent_key, fields in chunks_by_parent.items():
        parent = parents.get(parent_key)
        if parent is None:
            raise PortableFamilyError(
                f"portable chunk has no parent: {parent_key}"
            )
        declared = parent.get("_chunked")
        if not isinstance(declared, list):
            raise PortableFamilyError(
                f"portable parent does not declare chunks: {parent_key}"
            )
        for field, chunks in fields.items():
            if field not in declared:
                raise PortableFamilyError(
                    f"portable parent does not declare chunk field {field}"
                )
            positions = sorted(int(chunk["position"]) for chunk in chunks)
            if positions != list(range(len(positions))):
                raise PortableFamilyError(
                    f"portable chunks are not contiguous for {parent_key}:{field}"
                )
            parent[field] = [
                copy.deepcopy(value)
                for chunk in sorted(chunks, key=lambda item: item["position"])
                for value in chunk["values"]
            ]
        missing = set(declared) - set(fields)
        if missing:
            raise PortableFamilyError(
                f"portable parent is missing chunks for {sorted(missing)}"
            )
    return sorted(parents.values(), key=_row_key)


def _strip_portable_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(dict(row))
    payload.pop("_kind", None)
    payload.pop("_key", None)
    payload.pop("_chunked", None)
    return payload


def reconstruct_compatibility_family(
    manifest: Mapping[str, Any],
    rows: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    source_rows = [
        _strip_portable_fields(row)
        for row in rows
        if _row_kind(row) == "source"
    ]
    source_rows.sort(key=lambda record: record["identity"]["path"])
    source_header = manifest.get("source_index_header")
    if not isinstance(source_header, dict):
        raise PortableFamilyError("portable family needs source_index_header")
    source_index = copy.deepcopy(source_header)
    source_index["records"] = source_rows

    structure_records = copy.deepcopy(source_rows)
    anchor_rows = _expanded_parents(rows, parent_kind="anchor")
    anchors: list[dict[str, Any]] = []
    records_by_id = {
        str(record["identity"]["id"]): record
        for record in structure_records
    }
    for row in anchor_rows:
        anchor = _strip_portable_fields(row)
        source_id = anchor.pop("source_id", None)
        if not isinstance(source_id, str) or source_id not in records_by_id:
            raise PortableFamilyError("portable anchor source does not resolve")
        anchor["source_record_id"] = source_id
        anchor.update(ANCHOR_DEFAULTS)
        anchors.append(anchor)
        raw_anchor = copy.deepcopy(anchor)
        parser_ref = raw_anchor.pop("parser_ref", None)
        if not isinstance(parser_ref, str) or "@" not in parser_ref:
            raise PortableFamilyError("portable anchor parser_ref is invalid")
        parser_name, parser_version = parser_ref.rsplit("@", 1)
        raw_anchor["parser"] = {
            "name": parser_name,
            "version": parser_version,
        }
        raw_anchor.pop("source_record_id", None)
        for field in ANCHOR_DEFAULTS:
            raw_anchor.pop(field, None)
        outbound = raw_anchor.pop("outbound_refs", [])
        refs = records_by_id[source_id].get("refs")
        if not isinstance(refs, dict):
            raise PortableFamilyError("portable source refs must be an object")
        refs.setdefault("anchor_refs", []).append(raw_anchor)
        refs.setdefault("outbound_refs", []).extend(
            {
                **copy.deepcopy(reference),
                "source_anchor_id": str(raw_anchor["id"]),
            }
            for reference in outbound
        )
    anchors.sort(
        key=lambda item: (
            item["source_record_id"],
            item["locator"]["start_line"],
            item["id"],
        )
    )
    for record in structure_records:
        refs = record["refs"]
        refs.setdefault("anchor_refs", [])
        refs.setdefault("outbound_refs", [])
        refs["anchor_refs"].sort(
            key=lambda item: (
                item["locator"]["start_line"],
                item["id"],
            )
        )
        refs["outbound_refs"].sort(
            key=lambda item: (
                item["source_anchor_id"],
                item["relation_kind"],
                item["target_ref"],
            )
        )

    event_rows = _expanded_parents(rows, parent_kind="event")
    events = [_strip_portable_fields(row) for row in event_rows]
    events.sort(key=lambda entry: (entry["event_kind"], entry["id"]))

    try:
        from scripts.generate_repo_local_kag_index import (
            DEFAULT_OUTPUT,
            repository_index_payload,
        )
        from scripts.repo_local.indexes import (
            artifact_entries,
            assertion_entries,
            entity_entries,
            relation_entries,
        )
    except ImportError:  # pragma: no cover - direct script execution
        from generate_repo_local_kag_index import (  # type: ignore
            DEFAULT_OUTPUT,
            repository_index_payload,
        )
        from repo_local.indexes import (  # type: ignore
            artifact_entries,
            assertion_entries,
            entity_entries,
            relation_entries,
        )

    repo = str(source_index["repo"]["name"])
    artifacts = artifact_entries(structure_records)
    entities = entity_entries(repo, structure_records)
    assertions = assertion_entries(
        repo,
        structure_records,
        artifacts=artifacts,
    )
    relations = relation_entries(
        repo,
        structure_records,
        artifacts=artifacts,
        anchors=anchors,
        entities=entities,
    )
    entries = {
        "artifact": artifacts,
        "anchor": anchors,
        "entity": entities,
        "event": events,
        "assertion": assertions,
        "relation": relations,
    }
    family = {
        kind: repository_index_payload(
            source_index,
            index_kind=kind,
            entries=entries[kind],
            source_index_path=DEFAULT_OUTPUT,
        )
        for kind in (
            "entity",
            "artifact",
            "anchor",
            "event",
            "assertion",
            "relation",
        )
    }
    compatibility = manifest.get("compatibility")
    files = (
        compatibility.get("files")
        if isinstance(compatibility, Mapping)
        else None
    )
    expected_digests = {
        item["kind"]: item["content_digest"]
        for item in files or []
        if isinstance(item, dict)
        and isinstance(item.get("kind"), str)
        and isinstance(item.get("content_digest"), str)
    }
    actual_payloads = {"source": source_index, **family}
    for kind in COMPATIBILITY_ORDER:
        identity = actual_payloads[kind]["index_identity"]
        if identity["content_digest"] != expected_digests.get(kind):
            raise PortableFamilyError(
                f"portable {kind} compatibility digest does not match"
            )
    return source_index, family


def load_portable_family(
    repo_root: Path,
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    root = repo_root.resolve()
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise PortableFamilyError(
            f"cannot read portable family manifest {path}"
        ) from exc
    validated = _validate_manifest_shape(manifest)
    rows = _load_rows(root, validated)
    source, family = reconstruct_compatibility_family(validated, rows)
    return source, family, validated


def expected_portable_paths(
    manifest: Mapping[str, Any],
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
) -> set[Path]:
    paths = {manifest_path}
    for descriptor in manifest.get("shards", []):
        if isinstance(descriptor, dict) and isinstance(
            descriptor.get("path"), str
        ):
            paths.add(Path(descriptor["path"]))
    return paths


def check_portable_output(
    repo_root: Path,
    manifest: Mapping[str, Any],
    shards: Mapping[Path, bytes],
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
    require_legacy_absent: bool = True,
) -> bool:
    root = repo_root.resolve()
    ok = True
    expected_manifest = render_manifest(manifest)
    actual_manifest_path = root / manifest_path
    if (
        not actual_manifest_path.is_file()
        or actual_manifest_path.read_bytes() != expected_manifest
    ):
        ok = False
    for path, expected in shards.items():
        actual = root / path
        if not actual.is_file() or actual.read_bytes() != expected:
            ok = False
    actual_shards = {
        path.relative_to(root)
        for path in (root / manifest_path.parent / "shards").glob("*/*.jsonl")
        if path.is_file()
    }
    if actual_shards != set(shards):
        ok = False
    if require_legacy_absent:
        legacy_root = root / manifest_path.parent
        if any(
            (legacy_root / filename).exists()
            for filename in LEGACY_INDEX_FILENAMES.values()
        ):
            ok = False
    return ok


def write_portable_output(
    repo_root: Path,
    manifest: Mapping[str, Any],
    shards: Mapping[Path, bytes],
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
    remove_legacy: bool = True,
) -> None:
    root = repo_root.resolve()
    expected = set(shards)
    shard_root = root / manifest_path.parent / "shards"
    for existing in shard_root.glob("*/*.jsonl"):
        relative = existing.relative_to(root)
        if relative not in expected:
            existing.unlink()
    for path, content in shards.items():
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.is_file() or destination.read_bytes() != content:
            destination.write_bytes(content)
    manifest_destination = root / manifest_path
    manifest_destination.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_manifest(manifest)
    if (
        not manifest_destination.is_file()
        or manifest_destination.read_bytes() != rendered
    ):
        manifest_destination.write_bytes(rendered)
    if remove_legacy:
        for filename in LEGACY_INDEX_FILENAMES.values():
            (root / manifest_path.parent / filename).unlink(missing_ok=True)


def _git_bytes(repo_root: Path, ref: str, path: Path) -> bytes | None:
    result = subprocess.run(
        ("git", "show", f"{ref}:{path.as_posix()}"),
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _base_portable_paths(repo_root: Path, base_ref: str) -> set[Path]:
    manifest_bytes = _git_bytes(repo_root, base_ref, MANIFEST_RELATIVE_PATH)
    if manifest_bytes is None:
        return {
            Path("kag/indexes") / filename
            for filename in LEGACY_INDEX_FILENAMES.values()
            if _git_bytes(
                repo_root,
                base_ref,
                Path("kag/indexes") / filename,
            )
            is not None
        }
    try:
        manifest = json.loads(manifest_bytes)
    except json.JSONDecodeError as exc:
        raise PortableFamilyError(
            f"{base_ref} portable family manifest is invalid"
        ) from exc
    return expected_portable_paths(manifest)


def _base_manifest(
    repo_root: Path,
    base_ref: str,
) -> dict[str, Any] | None:
    content = _git_bytes(repo_root, base_ref, MANIFEST_RELATIVE_PATH)
    if content is None:
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise PortableFamilyError(
            f"{base_ref} portable family manifest is invalid"
        ) from exc
    if not isinstance(payload, dict):
        raise PortableFamilyError(
            f"{base_ref} portable family manifest must be an object"
        )
    return payload


def _budget_receipt_scope(
    *,
    base_has_v3: bool,
    generated_delta_exceeded: bool,
    tracked_size_exceeded: bool,
) -> str:
    if not base_has_v3:
        return "v2_to_v3_migration"
    if generated_delta_exceeded and tracked_size_exceeded:
        return "generated_delta_and_tracked_size"
    if tracked_size_exceeded:
        return "tracked_size"
    return "generated_delta"


def _validate_standing_budget(
    manifest: Mapping[str, Any],
    base_manifest: Mapping[str, Any] | None,
) -> None:
    if base_manifest is None:
        return
    head_budgets = manifest.get("budgets")
    base_budgets = base_manifest.get("budgets")
    if not isinstance(head_budgets, Mapping) or not isinstance(
        base_budgets,
        Mapping,
    ):
        raise PortableFamilyError("portable family budgets are malformed")
    for field in ("tracked_bytes_max", "changed_generated_bytes_max"):
        head_value = head_budgets.get(field)
        base_value = base_budgets.get(field)
        if (
            not isinstance(head_value, int)
            or not isinstance(base_value, int)
        ):
            raise PortableFamilyError(
                f"portable family budget {field} is malformed"
            )
        if head_value > base_value:
            raise PortableFamilyError(
                f"standing budget {field} cannot be raised by generated output "
                "or a one-change receipt"
            )


def changed_generated_bytes(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
) -> tuple[int, int, str]:
    root = repo_root.resolve()
    resolved = subprocess.run(
        ("git", "rev-parse", base_ref),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    head_paths = expected_portable_paths(manifest)
    base_paths = _base_portable_paths(root, resolved)
    changed_bytes = 0
    changed_files = 0
    for path in sorted(head_paths | base_paths):
        old = _git_bytes(root, resolved, path)
        new_path = root / path
        new = new_path.read_bytes() if new_path.is_file() else None
        if old == new:
            continue
        changed_files += 1
        changed_bytes += max(len(old or b""), len(new or b""))
    return changed_bytes, changed_files, resolved


def receipt_path_for(manifest: Mapping[str, Any]) -> Path:
    digest = manifest["family_identity"]["content_digest"]
    return (
        BUDGET_RECEIPT_ROOT_RELATIVE_PATH
        / f"{digest}.json"
    )


def build_budget_receipt(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
    reason: str,
    approved_by: str = "repository-owner",
) -> tuple[Path, dict[str, Any]]:
    if not reason.strip():
        raise PortableFamilyError("budget receipt reason must not be empty")
    changed_bytes, changed_files, resolved = changed_generated_bytes(
        repo_root,
        base_ref=base_ref,
        manifest=manifest,
    )
    base_manifest = _base_manifest(repo_root, resolved)
    _validate_standing_budget(manifest, base_manifest)
    budgets = manifest["budgets"]
    summary = manifest["summary"]
    delta_exceeded = (
        changed_bytes > budgets["changed_generated_bytes_max"]
    )
    tracked_exceeded = (
        summary["tracked_bytes"] > budgets["tracked_bytes_max"]
    )
    scope = _budget_receipt_scope(
        base_has_v3=base_manifest is not None,
        generated_delta_exceeded=delta_exceeded,
        tracked_size_exceeded=tracked_exceeded,
    )
    receipt = {
        "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "scope": scope,
        "base_ref": resolved,
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "changed_generated_bytes": changed_bytes,
        "changed_generated_files": changed_files,
        "default_limit_bytes": DEFAULT_DELTA_BYTES_MAX,
        "allowed_bytes": changed_bytes,
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "allowed_tracked_bytes": summary["tracked_bytes"],
        "reason": reason.strip(),
        "approved_by": approved_by,
        "decision_ref": DECISION_REF,
    }
    return receipt_path_for(manifest), receipt


def write_budget_receipt(
    repo_root: Path,
    path: Path,
    receipt: Mapping[str, Any],
) -> None:
    destination = repo_root.resolve() / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = render_manifest(receipt)
    if not destination.is_file() or destination.read_bytes() != content:
        destination.write_bytes(content)


def validate_changed_generated_budget(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
) -> tuple[int, int, bool]:
    changed_bytes, changed_files, resolved = changed_generated_bytes(
        repo_root,
        base_ref=base_ref,
        manifest=manifest,
    )
    base_manifest = _base_manifest(repo_root, resolved)
    _validate_standing_budget(manifest, base_manifest)
    budgets = manifest["budgets"]
    summary = manifest["summary"]
    limit = budgets["changed_generated_bytes_max"]
    delta_exceeded = changed_bytes > limit
    tracked_exceeded = (
        summary["tracked_bytes"] > budgets["tracked_bytes_max"]
    )
    if not delta_exceeded and not tracked_exceeded:
        return changed_bytes, changed_files, False
    path = repo_root.resolve() / receipt_path_for(manifest)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise PortableFamilyError(
            "portable family budget is exceeded and no matching receipt exists: "
            f"changed={changed_bytes}/{limit}, "
            f"tracked={summary['tracked_bytes']}/"
            f"{budgets['tracked_bytes_max']}"
        ) from exc
    expected_scope = _budget_receipt_scope(
        base_has_v3=base_manifest is not None,
        generated_delta_exceeded=delta_exceeded,
        tracked_size_exceeded=tracked_exceeded,
    )
    expected = {
        "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "base_ref": resolved,
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "changed_generated_bytes": changed_bytes,
        "changed_generated_files": changed_files,
        "default_limit_bytes": limit,
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "decision_ref": DECISION_REF,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise PortableFamilyError(
                f"budget receipt field {field} does not match current delta"
            )
    if receipt.get("scope") != expected_scope:
        raise PortableFamilyError(
            "budget receipt scope does not match the current exceedance"
        )
    if (
        not isinstance(receipt.get("reason"), str)
        or not receipt["reason"].strip()
        or not isinstance(receipt.get("approved_by"), str)
        or not receipt["approved_by"].strip()
        or receipt.get("allowed_bytes", -1) < changed_bytes
        or receipt.get("allowed_tracked_bytes", -1)
        < summary["tracked_bytes"]
    ):
        raise PortableFamilyError("budget receipt approval is incomplete")
    return changed_bytes, changed_files, True


def _validate_tracked_size_receipt(
    repo_root: Path,
    manifest: Mapping[str, Any],
) -> None:
    path = repo_root.resolve() / receipt_path_for(manifest)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise PortableFamilyError(
            "portable tracked byte budget is exceeded without a matching "
            "digest-bound receipt"
        ) from exc
    summary = manifest["summary"]
    budgets = manifest["budgets"]
    expected = {
        "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "decision_ref": DECISION_REF,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise PortableFamilyError(
                f"tracked-size receipt field {field} does not match family"
            )
    if receipt.get("scope") not in {
        "tracked_size",
        "generated_delta_and_tracked_size",
    }:
        raise PortableFamilyError(
            "tracked-size receipt scope does not authorize this exceedance"
        )
    if receipt.get("allowed_tracked_bytes", -1) < summary["tracked_bytes"]:
        raise PortableFamilyError(
            "tracked-size receipt allowance is below the family size"
        )


def write_compatibility_view(
    output_root: Path,
    source_index: Mapping[str, Any],
    family: Mapping[str, Mapping[str, Any]],
    *,
    normalized_json: Any,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    payloads = {"source": source_index, **family}
    for kind in COMPATIBILITY_ORDER:
        destination = output_root / LEGACY_INDEX_FILENAMES[kind]
        destination.write_text(
            normalized_json(payloads[kind]),
            encoding="utf-8",
        )
