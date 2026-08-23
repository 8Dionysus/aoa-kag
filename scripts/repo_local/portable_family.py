from __future__ import annotations

import copy
import base64
import binascii
import hashlib
import json
import math
import os
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


SCHEMA_VERSION = "aoa-repo-local-kag-family-manifest-v3"
SCHEMA_REF = "aoa-kag:schemas/repo-local-kag-family-manifest.schema.json"
MANIFEST_RELATIVE_PATH = Path("kag/indexes/index_family.manifest.json")
SHARD_ROOT_RELATIVE_PATH = Path("kag/indexes/shards")
BUDGET_RECEIPT_ROOT_RELATIVE_PATH = Path(
    "kag/receipts/index_family_budget"
)
TIERED_CONTROL_PATHS = {
    Path("kag/indexes/corpus.manifest.json"),
    Path("kag/indexes/hot_profile.json"),
    Path("kag/indexes/artifact_locators.json"),
}
BUDGET_RECEIPT_SCHEMA_VERSION = "aoa-repo-local-kag-budget-receipt-v2"
LEGACY_BUDGET_RECEIPT_SCHEMA_VERSION = "aoa-repo-local-kag-budget-receipt-v1"
BUDGET_EVIDENCE_SCHEMA_VERSION = "aoa-repo-local-kag-budget-evidence-v2"
SEMANTIC_BUDGET_DECISION_REF = (
    "aoa-kag:docs/decisions/"
    "AOA-KAG-D-0042-semantic-owner-evidence-for-budget-admission.md"
)
BUDGET_CAUSE_CLASSES = frozenset(
    {
        "deliberate_source_migration",
        "legitimate_bulk_authored_change",
        "schema_builder_migration",
        "accidental_generated_amplification",
        "hot_set_pressure",
        "shard_topology_pressure",
        "artifact_delivery_migration",
    }
)
BUDGET_SEMANTIC_STATES = frozenset(
    {"supported", "unsupported", "unknown", "migration_required"}
)
BUDGET_PROCEDURE_VERSION = "aoa-kag:budget-semantic-admission-v3"
BUDGET_PROCEDURE_PATHS = (
    Path("scripts/repo_local/portable_family.py"),
    Path("scripts/repo_local/tiered_family.py"),
    Path("scripts/generate_repo_local_kag_index.py"),
    Path("scripts/repo_local/history.py"),
    Path("scripts/repo_local/identity.py"),
    Path("scripts/repo_local/indexes.py"),
    Path("scripts/repo_local/structure.py"),
    Path("scripts/prepare_landing.py"),
    Path("schemas/repo-local-kag-budget-evidence.schema.json"),
    Path("schemas/repo-local-kag-budget-receipt.schema.json"),
)
TRANSITION_AUTHORITY_VERSION = "aoa-kag:transition-authority-v1"
TRANSITION_AUTHORITY_ARTIFACT_VERSION = (
    "aoa-kag:detached-transition-authority-v1"
)
TRANSITION_REPLAY_SNAPSHOT_VERSION = (
    "aoa-kag:transition-replay-snapshot-v1"
)
TRANSITION_ACCEPTANCE_RECORD_VERSION = (
    "aoa-kag:transition-acceptance-record-v1"
)
TRANSITION_TRUST_REGISTRY_VERSION = "aoa-kag:transition-trust-registry-v1"
TRANSITION_SIGNATURE_ALGORITHM = "ed25519"
TRANSITION_DECISION_REF = (
    "aoa-kag:docs/decisions/"
    "AOA-KAG-D-0044-detached-transition-authority.md"
)
TRANSITION_CONTRACT_PATHS = (
    Path("scripts/repo_local/portable_family.py"),
    Path("scripts/repo_local/tiered_family.py"),
    Path("scripts/generate_repo_local_kag_index.py"),
    Path("schemas/repo-local-kag-producer-migration.schema.json"),
    Path("schemas/repo-local-kag-projection-transition.schema.json"),
    Path("schemas/repo-local-kag-transition-replay-snapshot.schema.json"),
    Path("schemas/repo-local-kag-transition-trust.schema.json"),
    Path("config/transition_authority_trust.json"),
)
PRODUCER_MIGRATION_SCHEMA_VERSION = (
    "aoa-repo-local-kag-producer-migration-v1"
)
PROJECTION_TRANSITION_SCHEMA_VERSION = (
    "aoa-repo-local-kag-projection-transition-v1"
)
PRODUCER_MIGRATION_SCHEMA_PATH = Path(
    "schemas/repo-local-kag-producer-migration.schema.json"
)
PROJECTION_TRANSITION_SCHEMA_PATH = Path(
    "schemas/repo-local-kag-projection-transition.schema.json"
)
TRANSITION_TRUST_REGISTRY_PATH = Path(
    "config/transition_authority_trust.json"
)
TRANSITION_TRUST_REGISTRY_SCHEMA_PATH = Path(
    "schemas/repo-local-kag-transition-trust.schema.json"
)
BUDGET_EVIDENCE_SCHEMA_PATH = Path(
    "schemas/repo-local-kag-budget-evidence.schema.json"
)
BUDGET_RECEIPT_SCHEMA_PATH = Path(
    "schemas/repo-local-kag-budget-receipt.schema.json"
)
BUDGET_RECEIPT_FAILURE_MARKER = "budget_receipt_validation_failure"
TIERED_CORPUS_MANIFEST_PATH = Path("kag/indexes/corpus.manifest.json")
TIERED_HOT_PROFILE_PATH = Path("kag/indexes/hot_profile.json")
SOURCE_CAUSE_CLASSES = frozenset(
    {
        "deliberate_source_migration",
        "legitimate_bulk_authored_change",
    }
)
TOPOLOGY_CAUSE_CLASSES = frozenset(
    {
        "hot_set_pressure",
        "shard_topology_pressure",
        "artifact_delivery_migration",
    }
)
# A causal receipt is deliberately conservative.  A one-byte edit is not a
# source/procedure witness for a large generated delta; callers can remain in
# the explicit unknown state until the owner procedure produces a real
# transition or source change.
MIN_CAUSAL_DELTA_BYTES = 16
MAX_GENERATED_FILES_PER_CAUSAL_FILE = 128
MAX_GENERATED_BYTES_PER_CAUSAL_BYTE = 4096
MAX_UNRELATED_GENERATED_BYTES = 128 * 1024
SEMANTIC_DERIVED_PATHS = {
    Path("docs/validation/script_inventory.json"),
    Path("docs/testing/test_inventory.json"),
}
SEMANTIC_DERIVED_ROOTS = {
    Path("docs/decisions/indexes"),
}
DECISION_REF = (
    "aoa-kag:docs/decisions/"
    "AOA-KAG-D-0017-portable-content-addressed-repository-family.md"
)
TIERED_DECISION_REF = (
    "aoa-kag:docs/decisions/"
    "AOA-KAG-D-0039-tiered-content-addressed-kag-distribution.md"
)
TIERED_DISTRIBUTION_SCHEMA_VERSION = (
    "aoa-repo-local-kag-distribution-manifest-v1"
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


class BudgetReceiptValidationError(PortableFamilyError):
    """A receipt/evidence failure that the preparation lane may regenerate."""

    def __init__(self, message: str) -> None:
        super().__init__(f"{BUDGET_RECEIPT_FAILURE_MARKER}: {message}")


class BudgetPairPublicationError(PortableFamilyError):
    """A paired receipt/evidence publication failed after semantic preflight."""


class TransitionAuthorityError(PortableFamilyError):
    """A detached transition cannot be admitted by the owner contract."""

    def __init__(self, state: str, message: str) -> None:
        if state not in BUDGET_SEMANTIC_STATES:
            raise ValueError(f"unknown transition authority state: {state}")
        self.state = state
        super().__init__(message)


def effective_index_surface_record(
    manifest: Mapping[str, Any],
    *,
    repo: str,
) -> dict[str, object]:
    """Project a portable-only family manifest as one effective index surface."""
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise PortableFamilyError(
            "effective index surface requires a v3 portable family manifest"
        )
    family_identity = manifest.get("family_identity")
    source_index_header = manifest.get("source_index_header")
    if not isinstance(family_identity, Mapping) or not isinstance(
        source_index_header,
        Mapping,
    ):
        raise PortableFamilyError(
            "portable family manifest needs family and source index identity"
        )
    index_identity = source_index_header.get("index_identity")
    if not isinstance(index_identity, Mapping):
        raise PortableFamilyError(
            "portable family manifest needs source_index_header.index_identity"
        )
    local_id = index_identity.get("local_id")
    content_digest = family_identity.get("content_digest")
    if not isinstance(local_id, str) or not local_id:
        raise PortableFamilyError(
            "portable family source index identity needs local_id"
        )
    if not isinstance(content_digest, str) or not content_digest:
        raise PortableFamilyError(
            "portable family identity needs content_digest"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "repo": repo,
        "local_id": local_id,
        "record_class": "index",
        "generated_or_authored": "generated_from_source",
        "builder": {
            "route": "repo-local KAG portable family",
            "surface": MANIFEST_RELATIVE_PATH.as_posix(),
        },
        "effective_index_surface": "portable_family_manifest",
        "portable_family_content_digest": content_digest,
    }


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
        or path in TIERED_CONTROL_PATHS
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
        if kind != "source":
            payload = copy.deepcopy(dict(payload))
            source_reference = payload.get("source_index")
            if not isinstance(source_reference, Mapping):
                raise PortableFamilyError(
                    f"{kind} compatibility view needs source_index"
                )
            payload["source_index"] = {
                **dict(source_reference),
                "path": (
                    Path("kag/indexes")
                    / LEGACY_INDEX_FILENAMES["source"]
                ).as_posix(),
            }
            canonical_identity = payload.get("index_identity")
            if not isinstance(canonical_identity, Mapping):
                raise PortableFamilyError(
                    f"{kind} compatibility view needs identity"
                )
            payload["index_identity"] = {
                **dict(canonical_identity),
                "content_digest": ZERO_DIGEST,
            }
            payload["index_identity"]["content_digest"] = sha256_bytes(
                canonical_json_bytes(payload)
            )
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
        "producer_identity": _budget_procedure_identity(
            Path(__file__).resolve().parents[2]
        ),
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
    *,
    require_budget_receipt: bool,
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
    if (
        require_budget_receipt
        and summary["tracked_bytes"] > budgets.get("tracked_bytes_max", -1)
    ):
        _validate_tracked_size_receipt(repo_root, manifest)
    return rows


def _expanded_parents(
    rows: Sequence[dict[str, Any]],
    *,
    parent_kind: str,
) -> list[dict[str, Any]]:
    chunk_kind = f"{parent_kind}_chunk"
    parents = {
        _row_key(row): dict(row)
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
    payload = dict(row)
    payload.pop("_kind", None)
    payload.pop("_key", None)
    payload.pop("_chunked", None)
    return payload


def reconstruct_source_index(
    manifest: Mapping[str, Any],
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Reconstruct and verify the Git-hot source compatibility view.

    Tiered externalized checkouts retain every source record while
    artifact-cold anchor and event records may be absent. Source-fast
    consumers can therefore verify authored coverage without pretending that
    the complete seven-view family is hydrated.
    """
    source_rows = [
        _strip_portable_fields(row)
        for row in rows
        if _row_kind(row) == "source"
    ]
    source_rows.sort(key=lambda record: record["identity"]["path"])
    source_header = manifest.get("source_index_header")
    if not isinstance(source_header, dict):
        raise PortableFamilyError("portable family needs source_index_header")
    source_index = dict(source_header)
    source_index["records"] = source_rows

    compatibility = manifest.get("compatibility")
    files = (
        compatibility.get("files")
        if isinstance(compatibility, Mapping)
        else None
    )
    expected_source_digest = next(
        (
            item["content_digest"]
            for item in files or []
            if isinstance(item, dict)
            and item.get("kind") == "source"
            and isinstance(item.get("content_digest"), str)
        ),
        None,
    )
    identity = source_index.get("index_identity")
    if (
        not isinstance(identity, Mapping)
        or identity.get("content_digest") != expected_source_digest
    ):
        raise PortableFamilyError(
            "portable source compatibility digest does not match"
        )
    try:
        from scripts.generate_repo_local_kag_index import payload_digest
    except ImportError:  # pragma: no cover - direct script execution
        from generate_repo_local_kag_index import payload_digest  # type: ignore
    if identity.get("content_digest") != payload_digest(source_index):
        raise PortableFamilyError(
            "portable source compatibility content has drifted"
        )
    return source_index


def reconstruct_compatibility_family(
    manifest: Mapping[str, Any],
    rows: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    source_index = reconstruct_source_index(manifest, rows)
    source_rows = source_index["records"]
    if not isinstance(source_rows, list):
        raise PortableFamilyError("portable source records must be a list")
    structure_records: list[dict[str, Any]] = []
    for source_record in source_rows:
        structure_record = dict(source_record)
        source_refs = source_record.get("refs")
        if not isinstance(source_refs, dict):
            raise PortableFamilyError("portable source refs must be an object")
        structure_refs = dict(source_refs)
        for field in ("anchor_refs", "outbound_refs"):
            value = source_refs.get(field)
            if isinstance(value, list):
                structure_refs[field] = list(value)
        structure_record["refs"] = structure_refs
        structure_records.append(structure_record)
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

    compatibility = manifest.get("compatibility")
    files = (
        compatibility.get("files")
        if isinstance(compatibility, Mapping)
        else None
    )
    source_index_path = DEFAULT_OUTPUT
    for item in files or []:
        if (
            isinstance(item, Mapping)
            and item.get("kind") == "source"
            and isinstance(item.get("path"), str)
        ):
            source_index_path = Path(str(item["path"]))
            break

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
            source_index_path=source_index_path,
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


def load_portable_family_with_state(
    repo_root: Path,
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
    require_budget_receipt: bool = True,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    """Load either v3 or v4 and preserve the observed delivery state.

    The long-standing ``load_portable_family`` triple remains the compatibility
    API. Runtime, query, and MCP adapters use this state-bearing route so a
    missing cold object can never be flattened into a successful full read.
    """
    root = repo_root.resolve()
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise PortableFamilyError(
            f"cannot read portable family manifest {path}"
        ) from exc
    if manifest.get("schema_version") != SCHEMA_VERSION:
        try:
            from scripts.repo_local.tiered_family import (
                DISTRIBUTION_SCHEMA_VERSION,
                load_tiered_family,
            )
        except ImportError:  # pragma: no cover - direct script execution
            from repo_local.tiered_family import (  # type: ignore
                DISTRIBUTION_SCHEMA_VERSION,
                load_tiered_family,
            )
        if manifest.get("schema_version") != DISTRIBUTION_SCHEMA_VERSION:
            raise PortableFamilyError(
                "portable family manifest has an unsupported schema version"
            )
        source, family, distribution, state = load_tiered_family(
            root,
            artifact_root=artifact_root,
            allow_shadow_git=allow_shadow_git,
        )
        return source, family, distribution, state
    validated = _validate_manifest_shape(manifest)
    rows = _load_rows(
        root,
        validated,
        require_budget_receipt=require_budget_receipt,
    )
    source, family = reconstruct_compatibility_family(validated, rows)
    state = {
        "state": "git_hot_complete",
        "complete": True,
        "missing_objects": [],
        "routes": {
            "git_hot": len(validated["shards"]),
            "local_cas": 0,
            "shadow_git": 0,
        },
        "corpus_digest": (
            "sha256:" + validated["family_identity"]["content_digest"]
        ),
        "distribution_digest": "",
    }
    return source, family, validated, state


def load_portable_family(
    repo_root: Path,
    *,
    manifest_path: Path = MANIFEST_RELATIVE_PATH,
    artifact_root: Path | None = None,
    allow_shadow_git: bool = True,
    require_budget_receipt: bool = True,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    source, family, manifest, _ = load_portable_family_with_state(
        repo_root,
        manifest_path=manifest_path,
        artifact_root=artifact_root,
        allow_shadow_git=allow_shadow_git,
        require_budget_receipt=require_budget_receipt,
    )
    return source, family, manifest


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
    if manifest.get("schema_version") == TIERED_DISTRIBUTION_SCHEMA_VERSION:
        corpus_bytes = _git_bytes(
            repo_root,
            base_ref,
            Path("kag/indexes/corpus.manifest.json"),
        )
        hot_profile_bytes = _git_bytes(
            repo_root,
            base_ref,
            Path("kag/indexes/hot_profile.json"),
        )
        if corpus_bytes is None or hot_profile_bytes is None:
            raise PortableFamilyError(
                f"{base_ref} tiered family control manifests are incomplete"
            )
        try:
            corpus = json.loads(corpus_bytes)
            hot_profile = json.loads(hot_profile_bytes)
        except json.JSONDecodeError as exc:
            raise PortableFamilyError(
                f"{base_ref} tiered family control manifest is invalid"
            ) from exc
        objects = corpus.get("objects") if isinstance(corpus, dict) else None
        selection = (
            hot_profile.get("selection")
            if isinstance(hot_profile, dict)
            else None
        )
        hot_kinds = (
            selection.get("include_record_kinds")
            if isinstance(selection, dict)
            else None
        )
        placement = manifest.get("placement")
        placement_state = (
            placement.get("state") if isinstance(placement, dict) else None
        )
        if (
            not isinstance(objects, list)
            or not isinstance(hot_kinds, list)
            or placement_state not in {"shadow", "externalized"}
        ):
            raise PortableFamilyError(
                f"{base_ref} tiered family placement is malformed"
            )
        paths = {
            MANIFEST_RELATIVE_PATH,
            Path("kag/indexes/corpus.manifest.json"),
            Path("kag/indexes/hot_profile.json"),
            Path("kag/indexes/artifact_locators.json"),
        }
        for descriptor in objects:
            if not isinstance(descriptor, dict):
                raise PortableFamilyError(
                    f"{base_ref} tiered object descriptor is malformed"
                )
            kind = descriptor.get("kind")
            range_value = descriptor.get("range")
            if not isinstance(kind, str) or not isinstance(range_value, str):
                raise PortableFamilyError(
                    f"{base_ref} tiered object path is malformed"
                )
            if placement_state == "shadow" or kind in hot_kinds:
                paths.add(
                    Path("kag/indexes/shards")
                    / kind
                    / f"{range_value}.jsonl"
                )
        return paths
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
    if payload.get("schema_version") == TIERED_DISTRIBUTION_SCHEMA_VERSION:
        corpus_content = _git_bytes(
            repo_root,
            base_ref,
            Path("kag/indexes/corpus.manifest.json"),
        )
        if corpus_content is None:
            raise PortableFamilyError(
                f"{base_ref} tiered family corpus manifest is missing"
            )
        try:
            corpus = json.loads(corpus_content)
        except json.JSONDecodeError as exc:
            raise PortableFamilyError(
                f"{base_ref} tiered family corpus manifest is invalid"
            ) from exc
        if not isinstance(corpus, dict):
            raise PortableFamilyError(
                f"{base_ref} tiered family corpus manifest must be an object"
            )
        distribution_identity = payload.get("distribution_identity")
        corpus_identity = corpus.get("corpus_identity")
        if not isinstance(distribution_identity, Mapping) or not isinstance(
            corpus_identity,
            Mapping,
        ):
            raise PortableFamilyError(
                f"{base_ref} tiered family identities are incomplete"
            )
        corpus_digest = distribution_identity.get("corpus_digest")
        if isinstance(corpus_digest, str):
            corpus_digest = corpus_digest.removeprefix("sha256:")
        payload["family_identity"] = {
            "content_digest": corpus_digest,
            "source_snapshot": corpus_identity.get("source_snapshot"),
            "distribution_digest": distribution_identity.get("content_digest"),
        }
        producer_identity = corpus.get("producer_identity")
        if isinstance(producer_identity, Mapping):
            payload["producer_identity"] = copy.deepcopy(dict(producer_identity))
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
        base_field = (
            "owner_git_hot_bytes_max"
            if field == "tracked_bytes_max"
            and base_manifest.get("schema_version")
            == TIERED_DISTRIBUTION_SCHEMA_VERSION
            else field
        )
        base_value = base_budgets.get(base_field)
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


def _budget_decision_ref(manifest: Mapping[str, Any]) -> str:
    del manifest
    return SEMANTIC_BUDGET_DECISION_REF


def _resolve_git_ref(repo_root: Path, ref: str) -> str:
    return subprocess.run(
        ("git", "rev-parse", ref),
        cwd=repo_root.resolve(),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def resolve_exact_git_commit(
    repo_root: Path,
    ref: str,
    *,
    require_clean: bool = False,
) -> str:
    """Resolve one immutable commit through the repository's Git boundary.

    A transition ref is an identity, not a caller-provided label.  Requiring
    Git to resolve a commit and, for target builds, a clean worktree keeps the
    direct Python API and the CLI on the same trusted derivation path.
    """
    root = repo_root.resolve()
    try:
        resolved = _resolve_git_ref(root, f"{ref}^{{commit}}")
    except (FileNotFoundError, OSError, subprocess.CalledProcessError) as exc:
        raise PortableFamilyError(
            f"cannot resolve exact Git commit for transition ref {ref!r}"
        ) from exc
    if (
        len(resolved) != 40
        or any(character not in HEX_DIGITS for character in resolved)
    ):
        raise PortableFamilyError(
            f"Git resolved transition ref {ref!r} to a non-commit identity"
        )
    if require_clean:
        try:
            status = subprocess.run(
                ("git", "status", "--porcelain=v1", "--untracked-files=all", "-z"),
                cwd=root,
                check=True,
                capture_output=True,
            ).stdout
        except (FileNotFoundError, OSError, subprocess.CalledProcessError) as exc:
            raise PortableFamilyError(
                "cannot verify clean Git worktree for transition target"
            ) from exc
        if status:
            raise PortableFamilyError(
                "transition target requires a clean immutable Git worktree"
            )
    return resolved


def trusted_transition_target_ref(
    repo_root: Path,
    target_ref: str | None = None,
) -> str:
    """Derive the only target ref admitted by the current clean worktree."""
    head = resolve_exact_git_commit(repo_root, "HEAD", require_clean=True)
    if target_ref is None:
        return head
    resolved = resolve_exact_git_commit(repo_root, target_ref)
    if resolved != head:
        raise PortableFamilyError(
            "transition target ref does not describe the clean built HEAD"
        )
    return resolved


def _current_bytes(repo_root: Path, path: Path) -> bytes | None:
    candidate = repo_root.resolve() / path
    try:
        if candidate.is_symlink():
            return candidate.readlink().as_posix().encode("utf-8")
        if candidate.is_file():
            return candidate.read_bytes()
    except OSError:
        return None
    return None


def _content_delta_bytes(old: bytes | None, new: bytes | None) -> int:
    """Measure the smallest contiguous content replacement for one path.

    ``changed_bytes`` remains the conservative whole-file budget measure.  The
    causal witness also needs a localized edit measure so that a one-byte edit
    to a large builder file cannot masquerade as a large owner migration.
    """
    old_bytes = old or b""
    new_bytes = new or b""
    if old_bytes == new_bytes:
        return 0
    prefix = 0
    common_prefix = min(len(old_bytes), len(new_bytes))
    while prefix < common_prefix and old_bytes[prefix] == new_bytes[prefix]:
        prefix += 1
    old_end = len(old_bytes)
    new_end = len(new_bytes)
    suffix = 0
    while (
        suffix < old_end - prefix
        and suffix < new_end - prefix
        and old_bytes[old_end - suffix - 1] == new_bytes[new_end - suffix - 1]
    ):
        suffix += 1
    return max(
        old_end - prefix - suffix,
        new_end - prefix - suffix,
    )


def _path_change_records(
    repo_root: Path,
    *,
    base_ref: str,
    paths: Iterable[Path],
) -> list[dict[str, Any]]:
    root = repo_root.resolve()
    records: list[dict[str, Any]] = []
    for path in sorted(set(paths)):
        old = _git_bytes(root, base_ref, path)
        new = _current_bytes(root, path)
        if old == new:
            continue
        records.append(
            {
                "path": path.as_posix(),
                "old_digest": sha256_bytes(old) if old is not None else None,
                "new_digest": sha256_bytes(new) if new is not None else None,
                "old_bytes": len(old) if old is not None else 0,
                "new_bytes": len(new) if new is not None else 0,
                "changed_bytes": max(
                    len(old) if old is not None else 0,
                    len(new) if new is not None else 0,
                ),
                "delta_bytes": _content_delta_bytes(old, new),
            }
        )
    return records


def _measurement_digest(records: Sequence[Mapping[str, Any]]) -> str:
    return sha256_bytes(canonical_json_bytes(list(records)))


def _changed_generated_records(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return _path_change_records(
        repo_root,
        base_ref=base_ref,
        paths=(
            expected_portable_paths(manifest)
            | _base_portable_paths(repo_root.resolve(), base_ref)
        ),
    )


def _git_changed_paths(repo_root: Path, base_ref: str) -> set[Path]:
    root = repo_root.resolve()
    changed = subprocess.run(
        ("git", "diff", "--name-only", "-z", base_ref, "--"),
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    untracked = subprocess.run(
        ("git", "ls-files", "--others", "--exclude-standard", "-z"),
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    paths: set[Path] = set()
    for encoded in (*changed.split(b"\0"), *untracked.split(b"\0")):
        if not encoded:
            continue
        try:
            path = Path(encoded.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise PortableFamilyError(
                "Git changed path is not valid UTF-8"
            ) from exc
        if path.is_absolute() or ".." in path.parts:
            raise PortableFamilyError(f"Git changed path is unsafe: {path}")
        paths.add(path)
    return paths


def _is_semantic_derived_path(path: Path) -> bool:
    return (
        path in SEMANTIC_DERIVED_PATHS
        or any(root in (path, *path.parents) for root in SEMANTIC_DERIVED_ROOTS)
        or "generated" in path.parts
    )


def _changed_source_records(
    repo_root: Path,
    *,
    base_ref: str,
) -> list[dict[str, Any]]:
    paths = {
        path
        for path in _git_changed_paths(repo_root, base_ref)
        if not is_portable_control_path(path)
        and path not in BUDGET_PROCEDURE_PATHS
        and not _is_semantic_derived_path(path)
    }
    return _path_change_records(repo_root, base_ref=base_ref, paths=paths)


def _measurement_payload(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "bytes": sum(int(record["changed_bytes"]) for record in records),
        "delta_bytes": sum(int(record["delta_bytes"]) for record in records),
        "files": len(records),
        "paths_digest": _measurement_digest(records),
    }


def _family_json_rows(
    content: bytes | None,
    *,
    path: Path,
) -> list[dict[str, Any]]:
    if content is None:
        return []
    if path.suffix != ".jsonl":
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in content.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise PortableFamilyError(
                    f"portable family row is not an object: {path}"
                )
            rows.append(row)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PortableFamilyError(
            f"portable family row is malformed: {path}"
        ) from exc
    return rows


def _row_dependency_paths(
    row: Mapping[str, Any],
    source_ids: Mapping[str, str],
    *,
    fallback_source_ids: Mapping[str, str] | None = None,
    ambiguous_source_ids: set[str] | frozenset[str] = frozenset(),
) -> set[str]:
    """Collect declared source lineage without inventing path conventions.

    The primary map belongs to the row's temporal version. A fallback map
    covers rows whose source record exists only in the other version, while
    current-version paths remain preferred when both versions know the ID.
    IDs that resolve to multiple paths inside one version are intentionally
    ignored so an ambiguous identity cannot authorize source-caused output.
    """
    paths: set[str] = set()
    path_keys = {"path", "old_path", "source_path", "lineage_path"}
    id_keys = {
        "object_id",
        "source_id",
        "source_record_id",
        "source_record_ids",
        "object_ids",
    }

    def visit(value: Any, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for child_key, child_value in value.items():
                visit(child_value, str(child_key))
            return
        if isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes, bytearray),
        ):
            for child in value:
                visit(child, key)
            return
        if not isinstance(value, str):
            return
        if key in path_keys:
            paths.add(value)
        if key in id_keys:
            if value in ambiguous_source_ids:
                return
            source_path = source_ids.get(value)
            if source_path is not None:
                paths.add(source_path)
            elif fallback_source_ids is not None:
                source_path = fallback_source_ids.get(value)
                if source_path is not None:
                    paths.add(source_path)

    visit(row)
    return paths


def _family_row_key(row: Mapping[str, Any]) -> str:
    for key in ("_key", "id"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return f"{key}:{value}"
    return f"content:{sha256_bytes(canonical_json_bytes(row))}"


def _source_dependency_measurement(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
    source_records: Sequence[Mapping[str, Any]],
    generated_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind source-caused admission to generated rows that name those inputs.

    The scan is bounded by the existing owner-family read ceiling.  Control
    manifests are excluded from the relation check; every changed shard must
    either carry a changed source path directly or expose one through its
    typed source-id/path lineage.  A small shard-sized tolerance covers
    deterministic source-family movement without allowing a source edit to
    self-authorize unrelated generated churn.
    """
    source_paths = sorted(
        {
            str(record.get("path"))
            for record in source_records
            if isinstance(record.get("path"), str)
        }
    )
    empty_digest = sha256_bytes(canonical_json_bytes([]))
    base_paths = _base_portable_paths(repo_root.resolve(), base_ref)
    current_paths = expected_portable_paths(manifest)
    shard_paths = {
        path
        for path in {*current_paths, *base_paths}
        if SHARD_ROOT_RELATIVE_PATH in (path, *path.parents)
    }
    if not source_paths:
        return {
            "state": "not_applicable",
            "changed_source_paths_digest": empty_digest,
            "related_generated_paths_digest": empty_digest,
            "unrelated_generated_paths_digest": empty_digest,
            "related_generated_rows_digest": empty_digest,
            "unrelated_generated_rows_digest": empty_digest,
            "related_generated_files": 0,
            "unrelated_generated_files": 0,
            "related_generated_rows": 0,
            "unrelated_generated_rows": 0,
            "unrelated_generated_bytes": 0,
        }
    if not base_paths:
        return {
            "state": "unknown",
            "changed_source_paths_digest": sha256_bytes(
                canonical_json_bytes(source_paths)
            ),
            "related_generated_paths_digest": empty_digest,
            "unrelated_generated_paths_digest": empty_digest,
            "related_generated_rows_digest": empty_digest,
            "unrelated_generated_rows_digest": empty_digest,
            "related_generated_files": 0,
            "unrelated_generated_files": 0,
            "related_generated_rows": 0,
            "unrelated_generated_rows": 0,
            "unrelated_generated_bytes": 0,
        }

    rows_by_path: dict[tuple[str, Path], list[dict[str, Any]]] = {}
    source_ids_by_ref: dict[str, dict[str, str]] = {
        "current": {},
        "base": {},
    }
    ambiguous_source_ids: set[str] = set()
    for ref, paths in (("current", current_paths), ("base", base_paths)):
        total_bytes = 0
        for path in sorted(paths):
            if SHARD_ROOT_RELATIVE_PATH not in (path, *path.parents):
                continue
            content = (
                _current_bytes(repo_root, path)
                if ref == "current"
                else _git_bytes(repo_root, base_ref, path)
            )
            total_bytes += len(content or b"")
            if total_bytes > GLOBAL_TRACKED_BYTES_MAX:
                raise PortableFamilyError(
                    "portable source dependency scan exceeds the bounded read ceiling"
                )
            rows = _family_json_rows(content, path=path)
            rows_by_path[(ref, path)] = rows
            for row in rows:
                identity = row.get("identity")
                if not isinstance(identity, Mapping):
                    continue
                source_id = identity.get("id")
                source_path = identity.get("path")
                if isinstance(source_id, str) and isinstance(source_path, str):
                    source_ids = source_ids_by_ref[ref]
                    previous_path = source_ids.get(source_id)
                    if previous_path is None:
                        source_ids[source_id] = source_path
                    elif previous_path != source_path:
                        ambiguous_source_ids.add(source_id)

    changed_generated_paths = {
        Path(str(record["path"]))
        for record in generated_records
        if record.get("old_digest") != record.get("new_digest")
    }
    related_paths: list[str] = []
    unrelated_paths: list[str] = []
    related_rows: list[str] = []
    unrelated_rows: list[str] = []
    unrelated_bytes = 0
    changed_source_paths = set(source_paths)
    for path in sorted(changed_generated_paths & shard_paths):
        current_rows = rows_by_path.get(("current", path), [])
        base_rows = rows_by_path.get(("base", path), [])
        current_by_key = {_family_row_key(row): row for row in current_rows}
        base_by_key = {_family_row_key(row): row for row in base_rows}
        path_has_related = False
        path_has_unrelated = False
        changed_row_keys = sorted(set(current_by_key) | set(base_by_key))
        changed_row_count = 0
        for key in changed_row_keys:
            current_row = current_by_key.get(key)
            base_row = base_by_key.get(key)
            if current_row == base_row:
                continue
            changed_row_count += 1
            dependencies: set[str] = set()
            if current_row is not None:
                dependencies.update(
                    _row_dependency_paths(
                        current_row,
                        source_ids_by_ref["current"],
                        fallback_source_ids=source_ids_by_ref["base"],
                        ambiguous_source_ids=ambiguous_source_ids,
                    )
                )
            if base_row is not None:
                dependencies.update(
                    _row_dependency_paths(
                        base_row,
                        source_ids_by_ref["base"],
                        fallback_source_ids=source_ids_by_ref["current"],
                        ambiguous_source_ids=ambiguous_source_ids,
                    )
                )
            if dependencies & changed_source_paths:
                path_has_related = True
                related_rows.append(f"{path.as_posix()}::{key}")
            else:
                path_has_unrelated = True
                unrelated_rows.append(f"{path.as_posix()}::{key}")
                current_size = len(render_row(current_row)) if current_row is not None else 0
                base_size = len(render_row(base_row)) if base_row is not None else 0
                unrelated_bytes += max(current_size, base_size)
        if changed_row_count == 0:
            path_has_unrelated = True
            unrelated_rows.append(f"{path.as_posix()}::file-without-changed-row")
            current = _current_bytes(repo_root, path)
            previous = _git_bytes(repo_root, base_ref, path)
            unrelated_bytes += max(len(current or b""), len(previous or b""))
        if path_has_related:
            related_paths.append(path.as_posix())
        if path_has_unrelated:
            unrelated_paths.append(path.as_posix())

    relation_state = (
        "matched"
        if related_paths and unrelated_bytes <= MAX_UNRELATED_GENERATED_BYTES
        else "unmatched"
    )
    return {
        "state": relation_state,
        "changed_source_paths_digest": sha256_bytes(
            canonical_json_bytes(source_paths)
        ),
        "related_generated_paths_digest": sha256_bytes(
            canonical_json_bytes(sorted(related_paths))
        ),
        "unrelated_generated_paths_digest": sha256_bytes(
            canonical_json_bytes(sorted(unrelated_paths))
        ),
        "related_generated_rows_digest": sha256_bytes(
            canonical_json_bytes(sorted(related_rows))
        ),
        "unrelated_generated_rows_digest": sha256_bytes(
            canonical_json_bytes(sorted(unrelated_rows))
        ),
        "related_generated_files": len(related_paths),
        "unrelated_generated_files": len(unrelated_paths),
        "related_generated_rows": len(related_rows),
        "unrelated_generated_rows": len(unrelated_rows),
        "unrelated_generated_bytes": unrelated_bytes,
    }


def _budget_identity(manifest: Mapping[str, Any]) -> dict[str, Any]:
    identity = manifest.get("family_identity")
    if not isinstance(identity, Mapping):
        raise PortableFamilyError("portable budget family identity is missing")
    digest = identity.get("content_digest")
    source_snapshot = identity.get("source_snapshot")
    distribution_digest = identity.get("distribution_digest")
    if not isinstance(digest, str) or not digest:
        raise PortableFamilyError("portable budget family digest is missing")
    if not isinstance(source_snapshot, str) or not source_snapshot:
        raise PortableFamilyError("portable budget source snapshot is missing")
    if distribution_digest is not None and not isinstance(distribution_digest, str):
        raise PortableFamilyError("portable budget distribution digest is malformed")
    return {
        "family_digest": digest,
        "source_snapshot": source_snapshot,
        "distribution_digest": distribution_digest,
    }


def _base_identity(
    base_ref: str,
    base_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    identity = (
        _budget_identity(base_manifest)
        if base_manifest is not None
        and isinstance(base_manifest.get("family_identity"), Mapping)
        else {
            "family_digest": None,
            "source_snapshot": None,
            "distribution_digest": None,
        }
    )
    return {"ref": base_ref, **identity}


def _budget_base_supported(base_manifest: Mapping[str, Any] | None) -> bool:
    return bool(
        base_manifest is not None
        and base_manifest.get("schema_version")
        in {SCHEMA_VERSION, TIERED_DISTRIBUTION_SCHEMA_VERSION}
        and isinstance(base_manifest.get("family_identity"), Mapping)
    )


def _git_json(
    repo_root: Path,
    ref: str,
    path: Path,
) -> dict[str, Any] | None:
    content = _git_bytes(repo_root, ref, path)
    if content is None:
        return None
    try:
        payload = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PortableFamilyError(
            f"{ref} JSON control surface is invalid: {path.as_posix()}"
        ) from exc
    if not isinstance(payload, dict):
        raise PortableFamilyError(
            f"{ref} JSON control surface must be an object: {path.as_posix()}"
        )
    return payload


def _legacy_v3_projection_placement(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Name the real placement represented by a portable v3 predecessor."""
    partitioning = manifest.get("partitioning")
    if not isinstance(partitioning, Mapping):
        raise PortableFamilyError(
            "legacy v3 predecessor has no exact partitioning placement"
        )
    legacy_hot_profile = {
        "schema_version": SCHEMA_VERSION,
        "placement": "git-hot-portable-shards",
        "record_kinds": list(COMPATIBILITY_ORDER),
        "surface": MANIFEST_RELATIVE_PATH.as_posix(),
    }
    return {
        "state": "legacy_v3",
        "hot_profile_digest": _digest_value(legacy_hot_profile),
        "partitioning_digest": _digest_value(partitioning),
    }


def derive_transition_predecessor(
    repo_root: Path,
    base_ref: str,
) -> dict[str, Any]:
    """Derive an exact predecessor identity and placement from Git history."""
    resolved_ref = resolve_exact_git_commit(repo_root, base_ref)
    manifest = _git_json(repo_root, resolved_ref, MANIFEST_RELATIVE_PATH)
    if manifest is None:
        raise PortableFamilyError(
            f"transition predecessor is unavailable at {resolved_ref}"
        )
    schema_version = manifest.get("schema_version")
    if schema_version == SCHEMA_VERSION:
        identity = manifest.get("family_identity")
        if not isinstance(identity, Mapping):
            raise PortableFamilyError("transition predecessor v3 identity is malformed")
        digest = identity.get("content_digest")
        source_snapshot = identity.get("source_snapshot")
        if not isinstance(digest, str) or not isinstance(source_snapshot, str):
            raise PortableFamilyError("transition predecessor v3 identity is incomplete")
        return {
            "schema_version": schema_version,
            "ref": resolved_ref,
            "family_digest": digest,
            "source_snapshot": source_snapshot,
            "distribution_digest": None,
            "placement": _legacy_v3_projection_placement(manifest),
        }
    if schema_version != TIERED_DISTRIBUTION_SCHEMA_VERSION:
        raise PortableFamilyError(
            f"unsupported transition predecessor schema: {schema_version}"
        )
    corpus = _git_json(repo_root, resolved_ref, TIERED_CORPUS_MANIFEST_PATH)
    hot_profile = _git_json(repo_root, resolved_ref, TIERED_HOT_PROFILE_PATH)
    distribution_identity = manifest.get("distribution_identity")
    corpus_identity = corpus.get("corpus_identity") if corpus else None
    placement = manifest.get("placement")
    if not isinstance(corpus_identity, Mapping) or not isinstance(
        distribution_identity,
        Mapping,
    ) or not isinstance(placement, Mapping) or not isinstance(hot_profile, Mapping):
        raise PortableFamilyError("transition predecessor tiered identities are incomplete")
    corpus_digest = corpus_identity.get("content_digest")
    source_snapshot = corpus_identity.get("source_snapshot")
    distribution_digest = distribution_identity.get("content_digest")
    placement_state = placement.get("state")
    hot_identity = hot_profile.get("profile_identity")
    partitioning = corpus.get("partitioning")
    if (
        not all(isinstance(value, str) for value in (corpus_digest, source_snapshot, distribution_digest))
        or placement_state not in {"shadow", "externalized"}
        or not isinstance(hot_identity, Mapping)
        or not isinstance(hot_identity.get("content_digest"), str)
        or not isinstance(partitioning, Mapping)
    ):
        raise PortableFamilyError("transition predecessor tiered identities are malformed")
    return {
        "schema_version": schema_version,
        "ref": resolved_ref,
        "family_digest": str(corpus_digest).removeprefix("sha256:"),
        "source_snapshot": source_snapshot,
        "distribution_digest": distribution_digest,
        "placement": {
            "state": placement_state,
            "hot_profile_digest": hot_identity["content_digest"],
            "partitioning_digest": _digest_value(partitioning),
        },
    }


def _digest_value(value: object) -> str | None:
    if value is None:
        return None
    return f"sha256:{sha256_bytes(canonical_json_bytes(value))}"


def _placement_state(payload: Mapping[str, Any] | None) -> str | None:
    placement = payload.get("placement") if isinstance(payload, Mapping) else None
    state = placement.get("state") if isinstance(placement, Mapping) else None
    return state if isinstance(state, str) else None


def _hot_profile_digest(payload: Mapping[str, Any] | None) -> str | None:
    profile = payload.get("hot_profile") if isinstance(payload, Mapping) else None
    digest = profile.get("content_digest") if isinstance(profile, Mapping) else None
    return digest if isinstance(digest, str) else None


def _partitioning_value(
    repo_root: Path,
    base_ref: str,
    payload: Mapping[str, Any] | None,
    *,
    base: bool,
) -> object:
    if isinstance(payload, Mapping):
        partitioning = payload.get("partitioning")
        if partitioning is not None:
            return partitioning
    if not base:
        return None
    corpus = _git_json(
        repo_root,
        base_ref,
        Path("kag/indexes/corpus.manifest.json"),
    )
    return corpus.get("partitioning") if isinstance(corpus, Mapping) else None


def _budget_topology_context(
    repo_root: Path,
    *,
    base_ref: str,
    procedure_base_ref: str,
    manifest: Mapping[str, Any],
    base_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    head_identity = _budget_identity(manifest)
    base_identity = _base_identity(base_ref, base_manifest)
    head_source = head_identity["source_snapshot"]
    base_source = base_identity["source_snapshot"]
    if isinstance(head_source, str) and isinstance(base_source, str):
        source_snapshot_relation = (
            "unchanged" if head_source == base_source else "changed"
        )
    else:
        source_snapshot_relation = "unknown"

    head_partitioning = _partitioning_value(
        repo_root,
        base_ref,
        manifest,
        base=False,
    )
    base_partitioning = _partitioning_value(
        repo_root,
        base_ref,
        base_manifest,
        base=True,
    )
    head_partitioning_digest = _digest_value(head_partitioning)
    base_partitioning_digest = _digest_value(base_partitioning)
    base_hot_profile_digest = _hot_profile_digest(base_manifest)
    head_hot_profile_digest = _hot_profile_digest(manifest)
    transition = "none"
    base_legacy_paths = {
        Path("kag/indexes") / filename
        for filename in LEGACY_INDEX_FILENAMES.values()
        if _git_bytes(
            repo_root.resolve(),
            base_ref,
            Path("kag/indexes") / filename,
        )
        is not None
    }
    complete_legacy_family = base_legacy_paths == {
        Path("kag/indexes") / filename
        for filename in LEGACY_INDEX_FILENAMES.values()
    }
    first_family_migration = (
        base_manifest is None
        and manifest.get("schema_version")
        in {SCHEMA_VERSION, TIERED_DISTRIBUTION_SCHEMA_VERSION}
        and (not base_legacy_paths or complete_legacy_family)
    )
    if first_family_migration:
        transition = "first_family_migration"
    elif (
        _placement_state(manifest) == "externalized"
        and _placement_state(base_manifest) != "externalized"
    ):
        transition = "artifact_delivery_externalization"
    elif (
        head_partitioning_digest is not None
        and base_partitioning_digest is not None
        and head_partitioning_digest != base_partitioning_digest
    ):
        transition = "partitioning_change"
    elif (
        head_hot_profile_digest is not None
        and base_hot_profile_digest is not None
        and head_hot_profile_digest != base_hot_profile_digest
    ):
        transition = "hot_profile_change"

    return {
        "base_schema_version": (
            base_manifest.get("schema_version")
            if isinstance(base_manifest, Mapping)
            else None
        ),
        "head_schema_version": manifest.get("schema_version"),
        "base_placement_state": _placement_state(base_manifest),
        "head_placement_state": _placement_state(manifest),
        "base_hot_profile_digest": base_hot_profile_digest,
        "head_hot_profile_digest": head_hot_profile_digest,
        "base_partitioning_digest": base_partitioning_digest,
        "head_partitioning_digest": head_partitioning_digest,
        "procedure_base_ref": procedure_base_ref,
        "source_snapshot_relation": source_snapshot_relation,
        "transition": transition,
    }


def _record_delta_stats(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "delta_bytes": sum(int(record["delta_bytes"]) for record in records),
        "deleted_files": sum(
            1 for record in records if int(record.get("new_bytes", 0)) == 0
        ),
        "added_or_modified_files": sum(
            1 for record in records if int(record.get("new_bytes", 0)) > 0
        ),
    }


def _procedure_root(repo_root: Path) -> Path:
    del repo_root
    root = Path(__file__).resolve().parents[2]
    if not (root / BUDGET_PROCEDURE_PATHS[0]).is_file():
        raise PortableFamilyError(
            "executing aoa-kag procedure checkout is missing its owner module"
        )
    return root


def _procedure_baseline_ref(owner_root: Path) -> str:
    """Resolve an immutable baseline owned by the executing KAG checkout."""
    for candidate in ("origin/HEAD", "origin/main", "main"):
        try:
            return _resolve_git_ref(owner_root, candidate)
        except subprocess.CalledProcessError:
            continue
    raise PortableFamilyError(
        "executing aoa-kag procedure checkout has no local immutable baseline"
    )


def _procedure_measurement_base_ref(
    repo_root: Path,
    target_base_ref: str,
) -> str:
    owner_root = _procedure_root(repo_root)
    if owner_root == repo_root.resolve():
        return _resolve_git_ref(owner_root, target_base_ref)
    return _procedure_baseline_ref(owner_root)


def _published_budget_schema_path(kind: str) -> Path:
    if kind == "evidence":
        relative = BUDGET_EVIDENCE_SCHEMA_PATH
    elif kind == "receipt":
        relative = BUDGET_RECEIPT_SCHEMA_PATH
    else:  # pragma: no cover - private helper guard
        raise PortableFamilyError(f"unknown published budget schema kind: {kind}")
    return _procedure_root(Path(".")) / relative


def _validate_published_budget_schema(
    kind: str,
    payload: Mapping[str, Any],
) -> None:
    path = _published_budget_schema_path(kind)
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(dict(payload))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PortableFamilyError(
            f"published budget {kind} schema cannot be loaded: {path}"
        ) from exc
    except SchemaError as exc:
        raise PortableFamilyError(
            f"published budget {kind} schema is invalid: {path}"
        ) from exc
    except JsonSchemaValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path)
        suffix = f" at {location}" if location else ""
        raise PortableFamilyError(
            f"budget {kind} does not match its published schema{suffix}: "
            f"{exc.message}"
        ) from exc


def _transition_schema_path(kind: str) -> Path:
    if kind == "producer_migration":
        return _procedure_root(Path(".")) / PRODUCER_MIGRATION_SCHEMA_PATH
    if kind == "projection_transition":
        return _procedure_root(Path(".")) / PROJECTION_TRANSITION_SCHEMA_PATH
    raise TransitionAuthorityError(
        "unsupported",
        f"unknown transition authority kind: {kind}",
    )


def _validate_transition_schema(
    kind: str,
    payload: Mapping[str, Any],
) -> None:
    path = _transition_schema_path(kind)
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(dict(payload))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TransitionAuthorityError(
            "migration_required",
            f"transition {kind} schema is unavailable: {path}",
        ) from exc
    except SchemaError as exc:
        raise TransitionAuthorityError(
            "unknown",
            f"transition {kind} schema is invalid: {path}",
        ) from exc
    except JsonSchemaValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path)
        suffix = f" at {location}" if location else ""
        raise TransitionAuthorityError(
            "unknown",
            f"transition {kind} does not match its published schema{suffix}: "
            f"{exc.message}",
        ) from exc


def _transition_contract_identity(
    owner_root: Path | None = None,
) -> dict[str, Any]:
    """Return the exact non-authorizing code/schema contract identity.

    This identity is intentionally separate from ``BUDGET_PROCEDURE_PATHS``.
    A transition authority can bind this stricter contract without changing
    the ordinary D-0043 producer identity or receipt ABI.
    """
    del owner_root
    root = _procedure_root(Path("."))
    files: list[dict[str, Any]] = []
    for relative in TRANSITION_CONTRACT_PATHS:
        path = root / relative
        if not path.is_file():
            raise TransitionAuthorityError(
                "migration_required",
                f"transition contract surface is missing: {relative}",
            )
        files.append(
            {
                "path": relative.as_posix(),
                "digest": sha256_bytes(path.read_bytes()),
                "bytes": path.stat().st_size,
            }
        )
    return {
        "contract_version": TRANSITION_AUTHORITY_VERSION,
        "owner": "aoa-kag",
        "files": files,
        "digest": f"sha256:{sha256_bytes(canonical_json_bytes(files))}",
    }


def _transition_subject_digest(payload: Mapping[str, Any]) -> str:
    subject = {
        key: copy.deepcopy(value)
        for key, value in payload.items()
        if key != "authority"
    }
    replay = subject.get("replay")
    if isinstance(replay, dict):
        # These two fields are attestations of the external replay snapshot;
        # including either in the subject would make the binding circular.
        replay.pop("subject_digest", None)
        replay.pop("snapshot_digest", None)
    return f"sha256:{sha256_bytes(canonical_json_bytes(subject))}"


def _transition_family_identity(
    payload: Mapping[str, Any],
    *,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {label} family identity is not an object",
        )
    family_digest = payload.get("family_digest")
    source_snapshot = payload.get("source_snapshot")
    distribution_digest = payload.get("distribution_digest")
    if (
        not isinstance(family_digest, str)
        or len(family_digest) != 64
        or any(character not in HEX_DIGITS for character in family_digest)
    ):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {label} family digest is malformed",
        )
    if (
        not isinstance(source_snapshot, str)
        or not source_snapshot.startswith("sha256:")
        or len(source_snapshot.removeprefix("sha256:")) != 64
        or any(
            character not in HEX_DIGITS
            for character in source_snapshot.removeprefix("sha256:")
        )
    ):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {label} source snapshot is malformed",
        )
    if distribution_digest is not None and (
        not isinstance(distribution_digest, str)
        or not distribution_digest.startswith("sha256:")
        or len(distribution_digest.removeprefix("sha256:")) != 64
        or any(
            character not in HEX_DIGITS
            for character in distribution_digest.removeprefix("sha256:")
        )
    ):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {label} distribution digest is malformed",
        )
    ref = payload.get("ref")
    schema_version = payload.get("schema_version")
    if (
        not isinstance(ref, str)
        or not 40 <= len(ref) <= 64
        or any(character not in HEX_DIGITS for character in ref)
        or not isinstance(schema_version, str)
    ):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {label} family reference is malformed",
        )
    return payload


def _transition_validate_decision(
    payload: Mapping[str, Any],
    *,
    owner_root: Path,
    candidate_root: Path | None,
) -> str:
    decision = payload.get("decision")
    if not isinstance(decision, Mapping):
        raise TransitionAuthorityError(
            "unknown",
            "transition decision binding is missing",
        )
    if decision.get("ref") != TRANSITION_DECISION_REF:
        raise TransitionAuthorityError(
            "unsupported",
            "transition decision is not the owner transition decision",
        )
    posture = decision.get("posture")
    if posture != "accepted":
        raise TransitionAuthorityError(
            "migration_required",
            "transition decision is not independently accepted",
        )
    if candidate_root is None:
        raise TransitionAuthorityError(
            "migration_required",
            "independent transition decision root is missing",
        )
    resolved_owner_root = owner_root.resolve()
    resolved_candidate_root = candidate_root.resolve()
    if (
        resolved_owner_root == resolved_candidate_root
        or resolved_owner_root in resolved_candidate_root.parents
        or resolved_candidate_root in resolved_owner_root.parents
    ):
        raise TransitionAuthorityError(
            "migration_required",
            "transition decision source is not detached from the candidate",
        )
    try:
        resolve_exact_git_commit(resolved_owner_root, "HEAD")
    except PortableFamilyError as exc:
        raise TransitionAuthorityError(
            "migration_required",
            "transition decision source has no immutable owner Git root",
        ) from exc
    source_commit = decision.get("source_commit")
    if (
        not isinstance(source_commit, str)
        or len(source_commit) != 40
        or any(character not in HEX_DIGITS for character in source_commit)
    ):
        raise TransitionAuthorityError(
            "migration_required",
            "transition decision has no immutable source commit",
        )
    try:
        resolved_source_commit = resolve_exact_git_commit(
            resolved_owner_root,
            source_commit,
        )
    except PortableFamilyError as exc:
        raise TransitionAuthorityError(
            "migration_required",
            "transition decision source commit is unavailable",
        ) from exc
    if resolved_source_commit != source_commit:
        raise TransitionAuthorityError(
            "unknown",
            "transition decision source commit is not exact",
        )
    relative = Path(TRANSITION_DECISION_REF.removeprefix("aoa-kag:"))
    if relative.is_absolute() or ".." in relative.parts:
        raise TransitionAuthorityError(
            "unsupported",
            "transition decision reference escapes the owner root",
        )
    decision_bytes = _git_bytes(
        resolved_owner_root,
        source_commit,
        relative,
    )
    if decision_bytes is None:
        raise TransitionAuthorityError(
            "migration_required",
            f"accepted transition decision is unavailable: {relative}",
        )
    digest = decision.get("digest")
    if digest != sha256_bytes(decision_bytes):
        raise TransitionAuthorityError(
            "unknown",
            "transition decision digest is stale",
        )
    try:
        posture_lines = [
            line.strip()
            for line in decision_bytes.decode("utf-8").splitlines()
            if line.strip().startswith("- Posture:")
        ]
    except UnicodeDecodeError as exc:
        raise TransitionAuthorityError(
            "unknown",
            "transition decision source is not UTF-8 text",
        ) from exc
    if posture_lines != ["- Posture: accepted"]:
        raise TransitionAuthorityError(
            "migration_required",
            "transition decision source is not accepted",
        )
    return source_commit


def _external_transition_file(
    path: Path | None,
    *,
    label: str,
    candidate_root: Path,
    owner_root: Path,
) -> tuple[Path, bytes]:
    if path is None:
        raise TransitionAuthorityError(
            "migration_required",
            f"trusted {label} is missing",
        )
    resolved = Path(path).resolve()
    if (
        not resolved.is_file()
        or resolved.is_symlink()
        or resolved == candidate_root
        or candidate_root in resolved.parents
        or resolved == owner_root
        or owner_root in resolved.parents
    ):
        raise TransitionAuthorityError(
            "migration_required",
            f"trusted {label} is not an independent regular file",
        )
    try:
        return resolved, resolved.read_bytes()
    except (FileNotFoundError, IsADirectoryError, OSError) as exc:
        raise TransitionAuthorityError(
            "migration_required",
            f"trusted {label} is unavailable: {resolved}",
        ) from exc


def _transition_load_trust_registry(
    owner_root: Path,
    source_commit: str,
) -> dict[str, Any]:
    registry_bytes = _git_bytes(
        owner_root.resolve(),
        source_commit,
        TRANSITION_TRUST_REGISTRY_PATH,
    )
    if registry_bytes is None:
        raise TransitionAuthorityError(
            "migration_required",
            "transition trust registry is unavailable at the immutable decision source",
        )
    schema_path = _procedure_root(Path(".")) / TRANSITION_TRUST_REGISTRY_SCHEMA_PATH
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        registry = json.loads(registry_bytes.decode("utf-8"))
        Draft202012Validator(schema).validate(registry)
    except FileNotFoundError as exc:
        raise TransitionAuthorityError(
            "migration_required",
            "transition trust registry schema is unavailable",
        ) from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransitionAuthorityError(
            "unknown",
            "transition trust registry is not typed JSON",
        ) from exc
    except SchemaError as exc:
        raise TransitionAuthorityError(
            "unknown",
            "transition trust registry schema is invalid",
        ) from exc
    except JsonSchemaValidationError as exc:
        raise TransitionAuthorityError(
            "unknown",
            f"transition trust registry is not schema-valid: {exc.message}",
        ) from exc
    if registry.get("schema_version") != TRANSITION_TRUST_REGISTRY_VERSION:
        raise TransitionAuthorityError(
            "unknown",
            "transition trust registry version is unsupported",
        )
    return dict(registry)


def _transition_validate_trust_root(
    *,
    role: str,
    root_binding: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> tuple[dict[str, Any], bytes]:
    if root_binding.get("role") != role:
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} trust root role is wrong",
        )
    expected_keys = {"role", "ref", "registry_ref", "signer_id", "digest"}
    if set(root_binding) != expected_keys:
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} trust root has unknown or missing fields",
        )
    if root_binding.get("registry_ref") != (
        "aoa-kag:config/transition_authority_trust.json"
    ):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} trust root registry reference is not owner-pinned",
        )
    roots = registry.get(f"{role}_roots")
    if not isinstance(roots, list):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} trust registry section is malformed",
        )
    matches = [
        entry
        for entry in roots
        if isinstance(entry, dict)
        and entry.get("ref") == root_binding.get("ref")
    ]
    if len(matches) != 1:
        raise TransitionAuthorityError(
            "migration_required",
            f"transition {role} trust root is not independently registered",
        )
    entry = matches[0]
    if entry.get("role") != role:
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} trust root registry role is wrong",
        )
    if entry.get("state") != "active":
        raise TransitionAuthorityError(
            "migration_required",
            f"transition {role} trust root is not active",
        )
    if entry.get("owner") == "aoa-kag":
        raise TransitionAuthorityError(
            "migration_required",
            f"transition {role} trust root is not independently owned",
        )
    if (
        root_binding.get("digest")
        != f"sha256:{sha256_bytes(canonical_json_bytes(entry))}"
        or root_binding.get("signer_id") != entry.get("signer_id")
    ):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} trust root binding is stale",
        )
    encoded = entry.get("public_key_base64url")
    try:
        public_key = base64.b64decode(
            str(encoded) + ("=" * (-len(str(encoded)) % 4)),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, binascii.Error) as exc:
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} trust root public key is malformed",
        ) from exc
    if (
        len(public_key) != 32
        or entry.get("signer_id")
        != f"sha256:{hashlib.sha256(public_key).hexdigest()}"
    ):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} trust root public key identity is stale",
        )
    return dict(entry), public_key


def _transition_verify_signature(
    signature: Mapping[str, Any] | None,
    statement: Mapping[str, Any],
    *,
    role: str,
    trust_entry: Mapping[str, Any],
    public_key: bytes,
) -> None:
    if signature is None or set(signature) != {
        "algorithm",
        "signer_id",
        "value",
    }:
        raise TransitionAuthorityError(
            "migration_required",
            f"transition {role} signature is unavailable or untyped",
        )
    if (
        signature.get("algorithm") != TRANSITION_SIGNATURE_ALGORITHM
        or signature.get("signer_id") != trust_entry.get("signer_id")
        or trust_entry.get("algorithm") != TRANSITION_SIGNATURE_ALGORITHM
    ):
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} signature is not issued by its registered root",
        )
    encoded = signature.get("value")
    try:
        signature_bytes = base64.b64decode(
            str(encoded) + ("=" * (-len(str(encoded)) % 4)),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, binascii.Error) as exc:
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} signature is malformed",
        ) from exc
    if len(signature_bytes) != 64:
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} signature has the wrong length",
        )
    public_der = bytes.fromhex("302a300506032b6570032100") + public_key
    with tempfile.TemporaryDirectory(prefix="aoa-kag-transition-verify-") as directory:
        root = Path(directory)
        public_path = root / "public.der"
        statement_path = root / "statement.json"
        signature_path = root / "signature.bin"
        public_path.write_bytes(public_der)
        statement_path.write_bytes(canonical_json_bytes(statement))
        signature_path.write_bytes(signature_bytes)
        result = subprocess.run(
            (
                "openssl",
                "pkeyutl",
                "-verify",
                "-pubin",
                "-inkey",
                str(public_path),
                "-keyform",
                "DER",
                "-rawin",
                "-in",
                str(statement_path),
                "-sigfile",
                str(signature_path),
            ),
            check=False,
            capture_output=True,
        )
    if result.returncode != 0:
        raise TransitionAuthorityError(
            "unknown",
            f"transition {role} signature verification failed",
        )


def _validate_transition_replay_snapshot(
    payload: Mapping[str, Any],
    *,
    kind: str,
    replay_state: Mapping[str, Any] | None,
    replay_state_path: Path | None,
    owner_root: Path | None,
    candidate_root: Path | None,
) -> None:
    if replay_state is None or replay_state_path is None:
        raise TransitionAuthorityError(
            "migration_required",
            "immutable external transition replay ledger snapshot is missing",
        )
    effective_owner_root = (
        owner_root.resolve()
        if owner_root is not None
        else _procedure_root(Path("."))
    )
    effective_candidate_root = (
        candidate_root.resolve()
        if candidate_root is not None
        else _procedure_root(Path("."))
    )
    source_commit = _transition_validate_decision(
        payload,
        owner_root=effective_owner_root,
        candidate_root=candidate_root,
    )
    registry = _transition_load_trust_registry(
        effective_owner_root,
        source_commit,
    )
    snapshot_path, snapshot_bytes = _external_transition_file(
        replay_state_path,
        label="transition replay snapshot",
        candidate_root=effective_candidate_root,
        owner_root=effective_owner_root,
    )
    if snapshot_bytes != canonical_json_bytes(dict(replay_state)):
        raise TransitionAuthorityError(
            "unknown",
            f"transition replay snapshot bytes are not canonical: {snapshot_path}",
        )
    schema_path = _procedure_root(Path(".")) / Path(
        "schemas/repo-local-kag-transition-replay-snapshot.schema.json"
    )
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(dict(replay_state))
    except (FileNotFoundError, IsADirectoryError, OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TransitionAuthorityError(
            "migration_required",
            "transition replay snapshot schema is unavailable",
        ) from exc
    except SchemaError as exc:
        raise TransitionAuthorityError(
            "unknown",
            "transition replay snapshot schema is invalid",
        ) from exc
    except JsonSchemaValidationError as exc:
        raise TransitionAuthorityError(
            "unknown",
            f"transition replay snapshot is not schema-valid: {exc.message}",
        ) from exc
    if replay_state.get("schema_version") != TRANSITION_REPLAY_SNAPSHOT_VERSION:
        raise TransitionAuthorityError(
            "unknown",
            "transition replay snapshot version is unsupported",
        )

    replay = payload.get("replay")
    if not isinstance(replay, Mapping):
        raise TransitionAuthorityError("unknown", "transition replay is missing")
    consumption = replay.get("consumption")
    if not isinstance(consumption, Mapping) or consumption.get("state") != "unconsumed":
        raise TransitionAuthorityError(
            "unknown",
            "transition replay state is already consumed or malformed",
        )
    subject_digest = _transition_subject_digest(payload)
    if (
        replay.get("subject_digest") != subject_digest
        or replay_state.get("subject_digest") != subject_digest
        or replay_state.get("owner") != "aoa-kag"
        or replay_state.get("transition_kind") != kind
        or replay_state.get("state") != "current"
        or replay_state.get("ledger_ref") != replay.get("ledger_ref")
        or replay_state.get("ledger_digest") != replay.get("ledger_digest")
        or replay_state.get("snapshot_digest") != replay.get("snapshot_digest")
        or replay_state.get("source_ref") != replay.get("source_ref")
    ):
        raise TransitionAuthorityError(
            "unknown",
            "transition replay snapshot is stale or bound to another subject",
        )
    trust_binding = replay_state.get("trust_root")
    if not isinstance(trust_binding, Mapping):
        raise TransitionAuthorityError(
            "migration_required",
            "transition replay snapshot trust root is missing",
        )
    trust_entry, public_key = _transition_validate_trust_root(
        role="replay",
        root_binding=trust_binding,
        registry=registry,
    )
    snapshot = copy.deepcopy(dict(replay_state))
    snapshot["snapshot_digest"] = f"sha256:{ZERO_DIGEST}"
    signature = snapshot.pop("signature", None)
    expected_snapshot_digest = f"sha256:{sha256_bytes(canonical_json_bytes(snapshot))}"
    if replay_state.get("snapshot_digest") != expected_snapshot_digest:
        raise TransitionAuthorityError(
            "unknown",
            "transition replay snapshot content digest does not match",
        )
    _transition_verify_signature(
        signature,
        {
            key: copy.deepcopy(value)
            for key, value in replay_state.items()
            if key != "signature"
        },
        role="replay snapshot",
        trust_entry=trust_entry,
        public_key=public_key,
    )
    used_nonces = replay_state.get("used_nonces")
    nonce = replay.get("nonce")
    sequence = replay.get("sequence")
    if (
        not isinstance(used_nonces, list)
        or len(used_nonces) != len(set(used_nonces))
        or not isinstance(nonce, str)
        or type(sequence) is not int
        or type(replay_state.get("last_sequence")) is not int
        or replay_state.get("last_sequence", -1) < 0
    ):
        raise TransitionAuthorityError(
            "unknown",
            "transition replay nonce or sequence is malformed",
        )
    if nonce in used_nonces or sequence <= replay_state["last_sequence"]:
        raise TransitionAuthorityError(
            "unknown",
            "transition nonce or sequence was already consumed",
        )


def _transition_validate_authority(
    payload: Mapping[str, Any],
    *,
    kind: str,
    owner_root: Path | None,
    candidate_root: Path | None,
    detached_authority_path: Path | None,
    acceptance_record: Mapping[str, Any] | None,
    acceptance_record_path: Path | None,
) -> None:
    effective_owner_root = (
        owner_root.resolve()
        if owner_root is not None
        else _procedure_root(Path("."))
    )
    effective_candidate_root = (
        candidate_root.resolve() if candidate_root is not None else effective_owner_root
    )
    authority = payload.get("authority")
    if not isinstance(authority, Mapping):
        raise TransitionAuthorityError("unknown", "transition issuer authority is missing")
    contract = _transition_contract_identity(effective_owner_root)
    if authority.get("contract_version") != TRANSITION_AUTHORITY_VERSION:
        raise TransitionAuthorityError(
            "unsupported",
            "transition authority contract version is unsupported",
        )
    if authority.get("contract_digest") != contract["digest"]:
        raise TransitionAuthorityError(
            "unknown",
            "transition authority contract identity is stale",
        )
    source_commit = _transition_validate_decision(
        payload,
        owner_root=effective_owner_root,
        candidate_root=candidate_root,
    )
    registry = _transition_load_trust_registry(
        effective_owner_root,
        source_commit,
    )

    issuer = authority.get("issuer")
    acceptance = authority.get("acceptance")
    if not isinstance(issuer, Mapping) or not isinstance(acceptance, Mapping):
        raise TransitionAuthorityError(
            "unknown",
            "transition issuer or acceptance binding is missing",
        )
    if acceptance.get("state") != "independently_accepted":
        raise TransitionAuthorityError("migration_required", "transition acceptance is pending")
    issuer_root = issuer.get("trust_root")
    acceptor_root = acceptance.get("trust_root")
    if not isinstance(issuer_root, Mapping) or not isinstance(acceptor_root, Mapping):
        raise TransitionAuthorityError(
            "migration_required",
            "independent issuer and acceptor trust roots are missing",
        )
    if (
        issuer_root.get("ref") == acceptor_root.get("ref")
        or issuer_root.get("signer_id") == acceptor_root.get("signer_id")
    ):
        raise TransitionAuthorityError(
            "unknown",
            "issuer and acceptor trust roots must be independently distinct",
        )
    issuer_entry, issuer_public_key = _transition_validate_trust_root(
        role="issuer",
        root_binding=issuer_root,
        registry=registry,
    )
    acceptor_entry, acceptor_public_key = _transition_validate_trust_root(
        role="acceptor",
        root_binding=acceptor_root,
        registry=registry,
    )
    if issuer_entry.get("owner") == acceptor_entry.get("owner"):
        raise TransitionAuthorityError(
            "unknown",
            "issuer and acceptor trust roots must have separate owners",
        )
    detached_path, artifact_bytes = _external_transition_file(
        detached_authority_path,
        label="detached transition authority artifact",
        candidate_root=effective_candidate_root,
        owner_root=effective_owner_root,
    )
    artifact_digest = f"sha256:{sha256_bytes(artifact_bytes)}"
    if issuer.get("artifact_digest") != artifact_digest:
        raise TransitionAuthorityError(
            "unknown",
            "detached transition authority artifact digest does not match",
        )
    acceptance_path, acceptance_bytes = _external_transition_file(
        acceptance_record_path,
        label="independent transition acceptance record",
        candidate_root=effective_candidate_root,
        owner_root=effective_owner_root,
    )
    if acceptance_record is None:
        raise TransitionAuthorityError(
            "migration_required",
            "independent transition acceptance record is missing",
        )
    try:
        acceptance_payload = json.loads(acceptance_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransitionAuthorityError(
            "unknown",
            "independent transition acceptance record is not typed JSON",
        ) from exc
    if (
        not isinstance(acceptance_payload, dict)
        or acceptance_payload != dict(acceptance_record)
        or acceptance_bytes != canonical_json_bytes(acceptance_payload)
    ):
        raise TransitionAuthorityError(
            "unknown",
            "independent transition acceptance record bytes are not canonical or do not match its input",
        )
    acceptance_digest = f"sha256:{sha256_bytes(acceptance_bytes)}"
    if acceptance.get("digest") != acceptance_digest:
        raise TransitionAuthorityError(
            "unknown",
            "independent transition acceptance digest does not match its bytes",
        )
    subject_digest = _transition_subject_digest(payload)
    try:
        detached_record = json.loads(artifact_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransitionAuthorityError(
            "unknown",
            "detached transition authority artifact is not typed JSON",
        ) from exc
    if (
        not isinstance(detached_record, dict)
        or artifact_bytes != canonical_json_bytes(detached_record)
    ):
        raise TransitionAuthorityError(
            "unknown",
            "detached transition authority artifact is not canonical",
        )
    detached_signature = detached_record.pop("signature", None)
    expected_detached_record = {
        "schema_version": TRANSITION_AUTHORITY_ARTIFACT_VERSION,
        "owner": "aoa-kag",
        "transition_kind": kind,
        "subject_digest": subject_digest,
        "issuer_root_ref": issuer_root.get("ref"),
        "issuer_ref": issuer.get("ref"),
        "acceptance_ref": acceptance.get("ref"),
        "acceptance_digest": acceptance_digest,
        "state": "independently_accepted",
    }
    if detached_record != expected_detached_record:
        raise TransitionAuthorityError(
            "unknown",
            "detached transition authority is not bound to this transition",
        )
    _transition_verify_signature(
        detached_signature,
        detached_record,
        role="issuer authority",
        trust_entry=issuer_entry,
        public_key=issuer_public_key,
    )
    acceptance_signature = acceptance_payload.pop("signature", None)
    expected_acceptance = {
        "schema_version": TRANSITION_ACCEPTANCE_RECORD_VERSION,
        "owner": "aoa-kag",
        "transition_kind": kind,
        "subject_digest": subject_digest,
        "acceptance_ref": acceptance.get("ref"),
        "acceptor_root_ref": acceptor_root.get("ref"),
        "state": "independently_accepted",
    }
    if acceptance_payload != expected_acceptance:
        raise TransitionAuthorityError(
            "unknown",
            "independent transition acceptance does not match",
        )
    _transition_verify_signature(
        acceptance_signature,
        acceptance_payload,
        role="acceptance",
        trust_entry=acceptor_entry,
        public_key=acceptor_public_key,
    )


def _validate_transition_binding(
    payload: Mapping[str, Any],
    *,
    kind: str,
    predecessor: Mapping[str, Any],
    target: Mapping[str, Any],
    owner_root: Path | None,
    candidate_root: Path | None,
    detached_authority_path: Path | None,
    acceptance_record: Mapping[str, Any] | None,
    acceptance_record_path: Path | None,
    replay_state: Mapping[str, Any] | None,
    replay_state_path: Path | None,
) -> None:
    owner = payload.get("owner")
    if isinstance(owner, Mapping) and owner.get("name") != "aoa-kag":
        raise TransitionAuthorityError(
            "unsupported",
            "transition owner identity is not aoa-kag",
        )
    _validate_transition_schema(kind, payload)
    if payload.get("owner") != {
        "name": "aoa-kag",
        "namespace": "aoa:aoa-kag",
        "owner_type": "organ",
        "root": ".",
    }:
        raise TransitionAuthorityError(
            "unsupported",
            "transition owner identity is not aoa-kag",
        )
    if payload.get("predecessor") != dict(predecessor):
        raise TransitionAuthorityError(
            "unknown",
            "transition predecessor is not the immutable base family",
        )
    if payload.get("target") != dict(target):
        raise TransitionAuthorityError(
            "unknown",
            "transition target identity is stale or wrong",
        )
    predecessor_family = _transition_family_identity(
        payload["predecessor"],
        label="predecessor",
    )
    target_payload = payload["target"]
    target_family = _transition_family_identity(
        target_payload["family"],
        label="target",
    )
    if target_family.get("schema_version") != TIERED_DISTRIBUTION_SCHEMA_VERSION:
        raise TransitionAuthorityError(
            "unsupported",
            "transition target is not the v4 distribution family",
        )
    if target_family.get("distribution_digest") is None:
        raise TransitionAuthorityError(
            "unknown",
            "transition target is missing its distribution identity",
        )
    if (
        predecessor_family.get("schema_version") == SCHEMA_VERSION
        and predecessor_family.get("distribution_digest") is not None
    ):
        raise TransitionAuthorityError(
            "unknown",
            "legacy v3 predecessor carries an invalid distribution identity",
        )
    if target_family.get("family_digest") == predecessor_family.get(
        "family_digest"
    ):
        raise TransitionAuthorityError(
            "unknown",
            "transition target does not differ from its predecessor",
        )
    producer_identity = target_payload.get("producer_identity")
    if not isinstance(producer_identity, Mapping) or _valid_procedure_identity(
        producer_identity
    ) is None:
        raise TransitionAuthorityError(
            "unknown",
            "transition target producer identity is not authenticated",
        )
    if kind == "producer_migration" and predecessor_family.get(
        "schema_version"
    ) != SCHEMA_VERSION:
        raise TransitionAuthorityError(
            "unsupported",
            "producer migration predecessor is not the legacy v3 family",
        )
    _validate_transition_replay_snapshot(
        payload,
        kind=kind,
        replay_state=replay_state,
        replay_state_path=replay_state_path,
        owner_root=owner_root,
        candidate_root=candidate_root,
    )
    _transition_validate_authority(
        payload,
        kind=kind,
        owner_root=owner_root,
        candidate_root=candidate_root,
        detached_authority_path=detached_authority_path,
        acceptance_record=acceptance_record,
        acceptance_record_path=acceptance_record_path,
    )


def validate_detached_producer_migration(
    migration: Mapping[str, Any],
    *,
    predecessor: Mapping[str, Any],
    target: Mapping[str, Any],
    detached_authority_path: Path | None = None,
    acceptance_record: Mapping[str, Any] | None = None,
    acceptance_record_path: Path | None = None,
    replay_state: Mapping[str, Any] | None = None,
    replay_state_path: Path | None = None,
    owner_root: Path | None = None,
    candidate_root: Path | None = None,
) -> None:
    """Admit one detached v3 -> v4 producer-lineage transition.

    The function validates supplied evidence only.  It never issues a
    migration, advances a replay ledger, writes a receipt, or mutates a
    generated family.
    """
    if not isinstance(migration, Mapping):
        raise TransitionAuthorityError(
            "unknown",
            "producer migration must be an object",
        )
    _validate_transition_binding(
        migration,
        kind="producer_migration",
        predecessor=predecessor,
        target=target,
        owner_root=owner_root,
        candidate_root=candidate_root,
        detached_authority_path=detached_authority_path,
        acceptance_record=acceptance_record,
        acceptance_record_path=acceptance_record_path,
        replay_state=replay_state,
        replay_state_path=replay_state_path,
    )


def validate_full_projection_transition(
    transition: Mapping[str, Any],
    *,
    predecessor: Mapping[str, Any],
    target: Mapping[str, Any],
    expected_projection: Mapping[str, Any],
    expected_output: Mapping[str, Any],
    detached_authority_path: Path | None = None,
    acceptance_record: Mapping[str, Any] | None = None,
    acceptance_record_path: Path | None = None,
    replay_state: Mapping[str, Any] | None = None,
    replay_state_path: Path | None = None,
    owner_root: Path | None = None,
    candidate_root: Path | None = None,
) -> None:
    """Admit a complete projection transition as a separate typed lane."""
    if not isinstance(transition, Mapping):
        raise TransitionAuthorityError(
            "unknown",
            "projection transition must be an object",
        )
    _validate_transition_binding(
        transition,
        kind="projection_transition",
        predecessor=predecessor,
        target=target,
        owner_root=owner_root,
        candidate_root=candidate_root,
        detached_authority_path=detached_authority_path,
        acceptance_record=acceptance_record,
        acceptance_record_path=acceptance_record_path,
        replay_state=replay_state,
        replay_state_path=replay_state_path,
    )
    if transition.get("projection") != dict(expected_projection):
        raise TransitionAuthorityError(
            "unknown",
            "complete projection transition has a partition or placement residue",
        )
    if transition.get("output") != dict(expected_output):
        raise TransitionAuthorityError(
            "unknown",
            "complete projection output is incomplete or stale",
        )
    output = transition["output"]
    output_digest = output.get("output_digest")
    candidate_output = copy.deepcopy(dict(output))
    candidate_output["output_digest"] = f"sha256:{ZERO_DIGEST}"
    expected_digest = f"sha256:{sha256_bytes(canonical_json_bytes(candidate_output))}"
    if output_digest != expected_digest:
        raise TransitionAuthorityError(
            "unknown",
            "complete projection output fixed point does not match",
        )
    target_family = target["family"]
    if (
        output.get("state") != "complete"
        or output.get("family_digest") != target_family.get("family_digest")
        or output.get("source_snapshot") != target_family.get("source_snapshot")
        or output.get("placement", {}).get("state")
        != transition.get("projection", {}).get("after", {}).get("state")
    ):
        raise TransitionAuthorityError(
            "unknown",
            "complete projection output is not bound to the target family",
        )


def transition_admission_state(
    kind: str,
    payload: Mapping[str, Any] | None,
    **kwargs: Any,
) -> str:
    """Return a fail-closed transition state without changing owner state."""
    if payload is None:
        return "migration_required"
    try:
        if kind == "producer_migration":
            validate_detached_producer_migration(payload, **kwargs)
        elif kind == "projection_transition":
            validate_full_projection_transition(payload, **kwargs)
        else:
            return "unsupported"
    except TransitionAuthorityError as exc:
        return exc.state
    except PortableFamilyError:
        return "unknown"
    return "supported"


def _budget_procedure_identity(
    repo_root: Path,
    *,
    procedure_base_ref: str | None = None,
) -> dict[str, Any]:
    root = _procedure_root(repo_root)
    resolved_base_ref = (
        _procedure_baseline_ref(root)
        if procedure_base_ref is None
        else _resolve_git_ref(root, procedure_base_ref)
    )
    files: list[dict[str, Any]] = []
    for relative in BUDGET_PROCEDURE_PATHS:
        path = root / relative
        if not path.is_file():
            files.append(
                {"path": relative.as_posix(), "state": "missing"}
            )
            continue
        files.append(
            {
                "path": relative.as_posix(),
                "state": "present",
                "digest": sha256_bytes(path.read_bytes()),
                "bytes": path.stat().st_size,
            }
        )
    return {
        "contract_version": BUDGET_PROCEDURE_VERSION,
        "owner": "aoa-kag",
        "base_ref": resolved_base_ref,
        "files": files,
        "digest": sha256_bytes(canonical_json_bytes(files)),
    }


def _procedure_identity_files(
    identity: Mapping[str, Any],
    *,
    require_sizes: bool,
) -> dict[str, Mapping[str, Any]] | None:
    files = identity.get("files")
    if not isinstance(files, Sequence) or isinstance(
        files,
        (str, bytes, bytearray),
    ):
        return None
    by_path: dict[str, Mapping[str, Any]] = {}
    for entry in files:
        if not isinstance(entry, Mapping):
            return None
        path = entry.get("path")
        state = entry.get("state")
        digest = entry.get("digest")
        size = entry.get("bytes")
        if (
            not isinstance(path, str)
            or not path
            or path in by_path
            or state != "present"
            or not isinstance(digest, str)
            or (
                require_sizes
                and (not isinstance(size, int) or size < 0)
            )
        ):
            return None
        by_path[path] = entry
    expected_paths = {path.as_posix() for path in BUDGET_PROCEDURE_PATHS}
    if set(by_path) != expected_paths:
        return None
    return by_path


def _procedure_identity_change_records(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Compare producer identities carried by two authenticated family heads."""
    previous_files = _procedure_identity_files(previous, require_sizes=True)
    current_files = _procedure_identity_files(current, require_sizes=True)
    if previous_files is None or current_files is None:
        return []
    if (
        previous.get("contract_version") != BUDGET_PROCEDURE_VERSION
        or current.get("contract_version") != BUDGET_PROCEDURE_VERSION
        or previous.get("owner") != "aoa-kag"
        or current.get("owner") != "aoa-kag"
        or previous.get("digest")
        != sha256_bytes(canonical_json_bytes(list(previous.get("files", []))))
        or current.get("digest")
        != sha256_bytes(canonical_json_bytes(list(current.get("files", []))))
    ):
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(previous_files):
        old = previous_files[path]
        new = current_files[path]
        if old.get("digest") == new.get("digest") and old.get("bytes") == new.get(
            "bytes"
        ):
            continue
        old_bytes = int(old["bytes"])
        new_bytes = int(new["bytes"])
        records.append(
            {
                "path": path,
                "old_digest": old["digest"],
                "new_digest": new["digest"],
                "old_bytes": old_bytes,
                "new_bytes": new_bytes,
                "changed_bytes": max(old_bytes, new_bytes),
                "delta_bytes": max(
                    abs(new_bytes - old_bytes),
                    MIN_CAUSAL_DELTA_BYTES,
                ),
            }
        )
    return records


def _valid_procedure_identity(
    identity: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    if (
        identity.get("contract_version") != BUDGET_PROCEDURE_VERSION
        or identity.get("owner") != "aoa-kag"
    ):
        return None
    base_ref = identity.get("base_ref")
    if (
        not isinstance(base_ref, str)
        or not 40 <= len(base_ref) <= 64
        or any(character not in HEX_DIGITS for character in base_ref)
    ):
        return None
    if _procedure_identity_files(identity, require_sizes=True) is None:
        return None
    if identity.get("digest") != sha256_bytes(
        canonical_json_bytes(list(identity.get("files", [])))
    ):
        return None
    return identity


def _authenticated_base_procedure_identity(
    repo_root: Path,
    *,
    base_ref: str,
    base_manifest: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Recover a producer identity only from the base head's paired proof."""
    if not _budget_base_supported(base_manifest):
        return None
    assert base_manifest is not None
    producer_identity = base_manifest.get("producer_identity")
    if isinstance(producer_identity, Mapping):
        valid_producer = _valid_procedure_identity(producer_identity)
        if valid_producer is not None:
            return valid_producer
    receipt_path = receipt_path_for(base_manifest)
    evidence_path = evidence_path_for(base_manifest)
    receipt_bytes = _git_bytes(repo_root, base_ref, receipt_path)
    evidence_bytes = _git_bytes(repo_root, base_ref, evidence_path)
    if receipt_bytes is None or evidence_bytes is None:
        return None
    try:
        receipt = json.loads(receipt_bytes)
        evidence = json.loads(evidence_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(receipt, dict) or not isinstance(evidence, dict):
        return None
    try:
        _validate_published_budget_schema("receipt", receipt)
        _validate_published_budget_schema("evidence", evidence)
    except PortableFamilyError:
        return None
    base_identity = _budget_identity(base_manifest)
    base_repo = base_manifest.get("repo")
    if not isinstance(base_repo, Mapping):
        return None
    if (
        receipt.get("repo") != base_repo.get("name")
        or receipt.get("head_family_digest") != base_identity["family_digest"]
        or receipt.get("head_source_snapshot") != base_identity["source_snapshot"]
        or receipt.get("head_distribution_digest")
        != base_identity["distribution_digest"]
        or receipt.get("semantic_admission") != "supported"
        or receipt.get("semantic_evidence_ref") != evidence_path.as_posix()
        or receipt.get("semantic_evidence_digest")
        != sha256_bytes(render_manifest(evidence))
        or evidence.get("state") != "supported"
        or evidence.get("owner") != base_repo
        or evidence.get("head_identity") != base_identity
    ):
        return None
    procedure = evidence.get("procedure")
    if not isinstance(procedure, Mapping):
        return None
    return _valid_procedure_identity(procedure)


def _review_identity(repo_root: Path, review_ref: str) -> dict[str, str]:
    if not isinstance(review_ref, str) or not review_ref.startswith("aoa-kag:"):
        raise PortableFamilyError(
            "budget semantic evidence review_ref must use the aoa-kag owner ref"
        )
    relative = Path(review_ref.removeprefix("aoa-kag:"))
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.as_posix().startswith("docs/decisions/")
        or _is_semantic_derived_path(relative)
    ):
        raise PortableFamilyError(
            "budget semantic evidence review_ref must name an authored decision"
        )
    owner_root = _procedure_root(repo_root)
    path = owner_root / relative
    if not path.is_file():
        raise PortableFamilyError(
            f"budget semantic evidence review ref is missing: {review_ref}"
        )
    return {
        "ref": review_ref,
        "digest": sha256_bytes(path.read_bytes()),
    }


def _duplicate_materialization(
    records: Sequence[Mapping[str, Any]],
    *,
    changed_paths: set[str] | None = None,
) -> dict[str, Any]:
    by_digest: dict[str, list[str]] = {}
    for record in records:
        digest = record.get("new_digest")
        new_bytes = record.get("new_bytes")
        if not isinstance(digest, str) or not isinstance(new_bytes, int):
            continue
        if new_bytes <= 0:
            continue
        by_digest.setdefault(digest, []).append(str(record["path"]))
    groups = [
        {"digest": digest, "paths": sorted(paths)}
        for digest, paths in sorted(by_digest.items())
        if len(paths) > 1
        and (
            changed_paths is None
            or any(path in changed_paths for path in paths)
        )
    ]
    return {
        "state": "present" if groups else "absent",
        "groups": groups,
    }


def _head_family_records(
    repo_root: Path,
    manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Read the complete materialized head family once for duplicate admission."""
    total_bytes = 0
    records: list[dict[str, Any]] = []
    for path in sorted(expected_portable_paths(manifest)):
        content = _current_bytes(repo_root, path)
        if content is None:
            continue
        total_bytes += len(content)
        if total_bytes > GLOBAL_TRACKED_BYTES_MAX:
            raise PortableFamilyError(
                "portable family duplicate scan exceeds the global bounded read ceiling"
            )
        records.append(
            {
                "path": path.as_posix(),
                "old_digest": None,
                "new_digest": sha256_bytes(content),
                "old_bytes": 0,
                "new_bytes": len(content),
                "changed_bytes": len(content),
                "delta_bytes": len(content),
            }
        )
    return records


def _semantic_admission_state(
    *,
    base_supported: bool,
    cause_class: str,
    source_measurement: Mapping[str, Any],
    duplicate_materialization: Mapping[str, Any],
    causal_measurements: Mapping[str, Any] | None = None,
) -> str:
    if cause_class == "accidental_generated_amplification":
        return "unsupported"
    if duplicate_materialization.get("state") == "present":
        return "unsupported"
    if not base_supported and causal_measurements is None:
        return "migration_required"
    if causal_measurements is None:
        return "unknown"
    source_records = causal_measurements.get("source_records")
    procedure_records = causal_measurements.get("procedure_records")
    topology = causal_measurements.get("topology")
    generated_delta = causal_measurements.get("generated_delta")
    if not isinstance(source_records, Sequence) or isinstance(
        source_records,
        (str, bytes, bytearray),
    ):
        return "unknown"
    if not isinstance(procedure_records, Sequence) or isinstance(
        procedure_records,
        (str, bytes, bytearray),
    ):
        return "unknown"
    if not isinstance(topology, Mapping) or not isinstance(
        generated_delta,
        Mapping,
    ):
        return "unknown"

    source_stats = _record_delta_stats(source_records)
    procedure_stats = _record_delta_stats(procedure_records)
    transition = topology.get("transition")
    if not base_supported and transition != "first_family_migration":
        return "migration_required"
    try:
        source_files = int(source_measurement.get("files", 0))
        generated_bytes = int(generated_delta.get("bytes", -1))
        generated_files = int(generated_delta.get("files", -1))
    except (TypeError, ValueError):
        return "unknown"

    def generated_delta_is_bounded(
        *,
        causal_delta_bytes: int,
        causal_files: int,
    ) -> bool:
        return (
            causal_delta_bytes >= MIN_CAUSAL_DELTA_BYTES
            and causal_files >= 1
            and generated_files
            <= causal_files * MAX_GENERATED_FILES_PER_CAUSAL_FILE
            and generated_bytes
            <= causal_delta_bytes * MAX_GENERATED_BYTES_PER_CAUSAL_BYTE
        )

    source_relation = topology.get("source_snapshot_relation")
    source_dependency = causal_measurements.get("source_dependency")
    if cause_class in SOURCE_CAUSE_CLASSES and (
        not isinstance(source_dependency, Mapping)
        or source_dependency.get("state") != "matched"
    ):
        return "unknown"
    if (
        source_stats["deleted_files"] > 0
        or not generated_delta_is_bounded(
            causal_delta_bytes=source_stats["delta_bytes"],
            causal_files=source_files,
        )
        or procedure_stats["deleted_files"] > 0
        or procedure_stats["added_or_modified_files"] > 0
    ) and cause_class in SOURCE_CAUSE_CLASSES:
        return "unknown"
    if cause_class in SOURCE_CAUSE_CLASSES:
        return (
            "supported"
            if source_relation == "changed"
            else "unknown"
        )

    if cause_class == "schema_builder_migration":
        if not base_supported and transition != "first_family_migration":
            return "migration_required"
        if (
            not base_supported
            and (
                source_records
                or source_stats["deleted_files"] > 0
                or topology.get("source_snapshot_relation") != "unknown"
            )
        ):
            return "unknown"
        if base_supported and (
            source_records
            or topology.get("source_snapshot_relation") != "unchanged"
        ):
            return "unknown"
        if (
            procedure_stats["deleted_files"] > 0
            or not generated_delta_is_bounded(
                causal_delta_bytes=procedure_stats["delta_bytes"],
                causal_files=procedure_stats["added_or_modified_files"],
            )
        ):
            return "unknown"
        return "supported"

    if cause_class == "artifact_delivery_migration":
        source_delta_is_bounded = (
            source_stats["deleted_files"] == 0
            and generated_delta_is_bounded(
                causal_delta_bytes=source_stats["delta_bytes"],
                causal_files=source_files,
            )
        )
        return (
            "supported"
            if (
                transition == "artifact_delivery_externalization"
                and not procedure_records
                and (
                    (not source_records and source_relation == "unchanged")
                    or (
                        bool(source_records)
                        and source_relation == "changed"
                        and source_delta_is_bounded
                    )
                )
            )
            else "unknown"
        )
    if cause_class == "hot_set_pressure":
        return (
            "supported"
            if (
                transition == "hot_profile_change"
                and not source_records
                and not procedure_records
                and source_relation == "unchanged"
            )
            else "unknown"
        )
    if cause_class == "shard_topology_pressure":
        return (
            "supported"
            if (
                transition == "partitioning_change"
                and not source_records
                and not procedure_records
                and source_relation == "unchanged"
            )
            else "unknown"
        )
    return "unknown"


def _cause_witness(
    cause_class: str,
    measurements: Mapping[str, Any],
) -> dict[str, Any]:
    source_measurement = measurements["authored_source_delta"]
    procedure_measurement = measurements["procedure_delta"]
    generated_measurement = measurements["generated_delta"]
    source_stats = _record_delta_stats(measurements["source_records"])
    procedure_stats = _record_delta_stats(measurements["procedure_records"])
    topology = measurements["topology"]
    if cause_class in SOURCE_CAUSE_CLASSES:
        kind = "authored_source_delta"
    elif cause_class == "schema_builder_migration":
        kind = "procedure_delta"
    elif cause_class in TOPOLOGY_CAUSE_CLASSES:
        kind = "distribution_transition"
    else:
        kind = "generated_delta_amplification"
    return {
        "kind": kind,
        "source_paths_digest": source_measurement["paths_digest"],
        "procedure_paths_digest": procedure_measurement["paths_digest"],
        "generated_paths_digest": generated_measurement["paths_digest"],
        "source_delta_bytes": source_stats["delta_bytes"],
        "procedure_delta_bytes": procedure_stats["delta_bytes"],
        "source_deleted_files": source_stats["deleted_files"],
        "source_dependency_state": measurements["source_dependency"]["state"],
        "source_snapshot_relation": topology["source_snapshot_relation"],
        "transition": topology["transition"],
    }


def _budget_measurements(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
    base_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    generated_records = _changed_generated_records(
        repo_root,
        base_ref=base_ref,
        manifest=manifest,
    )
    source_records = _changed_source_records(repo_root, base_ref=base_ref)
    procedure_root = _procedure_root(repo_root)
    procedure_base_ref = _procedure_measurement_base_ref(repo_root, base_ref)
    current_procedure = _budget_procedure_identity(
        repo_root,
        procedure_base_ref=procedure_base_ref,
    )
    if procedure_root == repo_root.resolve():
        procedure_records = _path_change_records(
            procedure_root,
            base_ref=procedure_base_ref,
            paths=BUDGET_PROCEDURE_PATHS,
        )
    else:
        previous_procedure = _authenticated_base_procedure_identity(
            repo_root,
            base_ref=base_ref,
            base_manifest=base_manifest,
        )
        procedure_records = (
            _procedure_identity_change_records(previous_procedure, current_procedure)
            if previous_procedure is not None
            else []
        )
    budgets = manifest["budgets"]
    summary = manifest["summary"]
    head_family_records = _head_family_records(repo_root, manifest)
    changed_generated_paths = {
        str(record["path"])
        for record in generated_records
        if record.get("new_bytes", 0) > 0
    }
    return {
        "generated_delta": _measurement_payload(generated_records),
        "tracked_size": {
            "bytes": summary["tracked_bytes"],
            "limit_bytes": budgets["tracked_bytes_max"],
        },
        "authored_source_delta": _measurement_payload(source_records),
        "duplicate_materialization": _duplicate_materialization(
            head_family_records,
            changed_paths=changed_generated_paths,
        ),
        "procedure_delta": _measurement_payload(procedure_records),
        "source_dependency": _source_dependency_measurement(
            repo_root,
            base_ref=base_ref,
            manifest=manifest,
            source_records=source_records,
            generated_records=generated_records,
        ),
        "topology": _budget_topology_context(
            repo_root,
            base_ref=base_ref,
            procedure_base_ref=procedure_base_ref,
            manifest=manifest,
            base_manifest=base_manifest,
        ),
        "generated_records": generated_records,
        "source_records": source_records,
        "procedure_records": procedure_records,
        "procedure_base_ref": procedure_base_ref,
        "base_supported": _budget_base_supported(base_manifest),
    }


def changed_generated_bytes(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
) -> tuple[int, int, str]:
    root = repo_root.resolve()
    resolved = _resolve_git_ref(root, base_ref)
    records = _changed_generated_records(
        root,
        base_ref=resolved,
        manifest=manifest,
    )
    measurement = _measurement_payload(records)
    return measurement["bytes"], measurement["files"], resolved


def receipt_path_for(manifest: Mapping[str, Any]) -> Path:
    digest = manifest["family_identity"]["content_digest"]
    return (
        BUDGET_RECEIPT_ROOT_RELATIVE_PATH
        / f"{digest}.json"
    )


def evidence_path_for(manifest: Mapping[str, Any]) -> Path:
    digest = manifest["family_identity"]["content_digest"]
    return (
        BUDGET_RECEIPT_ROOT_RELATIVE_PATH
        / f"{digest}.evidence.json"
    )


def build_budget_evidence(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
    reason: str,
    cause_class: str,
    review_ref: str,
) -> tuple[Path, dict[str, Any]]:
    if not isinstance(reason, str) or not reason.strip():
        raise PortableFamilyError("budget semantic evidence reason must not be empty")
    if cause_class not in BUDGET_CAUSE_CLASSES:
        raise PortableFamilyError(
            "budget semantic evidence cause_class is not a supported typed cause"
        )
    root = repo_root.resolve()
    resolved = _resolve_git_ref(root, base_ref)
    base_manifest = _base_manifest(root, resolved)
    _validate_standing_budget(manifest, base_manifest)
    measurements = _budget_measurements(
        root,
        base_ref=resolved,
        manifest=manifest,
        base_manifest=base_manifest,
    )
    state = _semantic_admission_state(
        base_supported=measurements["base_supported"],
        cause_class=cause_class,
        source_measurement=measurements["authored_source_delta"],
        duplicate_materialization=measurements["duplicate_materialization"],
        causal_measurements=measurements,
    )
    head_identity = _budget_identity(manifest)
    source_bytes = int(measurements["authored_source_delta"]["bytes"])
    generated_bytes = int(measurements["generated_delta"]["bytes"])
    evidence = {
        "schema_version": BUDGET_EVIDENCE_SCHEMA_VERSION,
        "state": state,
        "owner": copy.deepcopy(manifest["repo"]),
        "scope": _budget_receipt_scope(
            base_has_v3=measurements["base_supported"],
            generated_delta_exceeded=generated_bytes
            > manifest["budgets"]["changed_generated_bytes_max"],
            tracked_size_exceeded=manifest["summary"]["tracked_bytes"]
            > manifest["budgets"]["tracked_bytes_max"],
        ),
        "base_identity": _base_identity(resolved, base_manifest),
        "head_identity": head_identity,
        "procedure": _budget_procedure_identity(
            root,
            procedure_base_ref=measurements["procedure_base_ref"],
        ),
        "review": _review_identity(root, review_ref),
        "cause": {
            "class": cause_class,
            "reason": reason.strip(),
            "evidence": _cause_witness(cause_class, measurements),
        },
        "measurements": {
            "generated_delta": measurements["generated_delta"],
            "tracked_size": measurements["tracked_size"],
            "authored_source_delta": measurements["authored_source_delta"],
            "procedure_delta": measurements["procedure_delta"],
            "source_dependency": measurements["source_dependency"],
            "topology": measurements["topology"],
            "amplification": {
                "generated_bytes": generated_bytes,
                "authored_source_bytes": source_bytes,
                "ratio_numerator": generated_bytes,
                "ratio_denominator": max(source_bytes, 1),
            },
            "duplicate_materialization": measurements[
                "duplicate_materialization"
            ],
        },
        "fixed_point": {
            "state": "required_external_gate",
            "family_digest": head_identity["family_digest"],
        },
    }
    return evidence_path_for(manifest), evidence


def _validate_budget_semantic_evidence(
    repo_root: Path,
    *,
    manifest: Mapping[str, Any],
    base_ref: str,
    base_manifest: Mapping[str, Any] | None,
    expected_scope: str,
    receipt: Mapping[str, Any],
    evidence: Mapping[str, Any],
    recompute_measurements: bool = True,
) -> None:
    if evidence.get("schema_version") != BUDGET_EVIDENCE_SCHEMA_VERSION:
        raise PortableFamilyError(
            "budget semantic admission is migration_required for legacy evidence"
        )
    _validate_published_budget_schema("evidence", evidence)
    _validate_published_budget_schema("receipt", receipt)
    state = evidence.get("state")
    if state not in BUDGET_SEMANTIC_STATES:
        raise PortableFamilyError("budget semantic evidence state is invalid")
    if state != "supported":
        raise PortableFamilyError(
            f"budget semantic admission state={state}; supported owner evidence is required"
        )
    if evidence.get("owner") != manifest.get("repo"):
        raise PortableFamilyError("budget semantic evidence owner identity mismatches family")
    if evidence.get("scope") != expected_scope:
        raise PortableFamilyError("budget semantic evidence scope mismatches exceedance")
    if recompute_measurements:
        if evidence.get("base_identity") != _base_identity(base_ref, base_manifest):
            raise PortableFamilyError(
                "budget semantic evidence base identity mismatches current base"
            )
    else:
        base_identity = evidence.get("base_identity")
        if not isinstance(base_identity, Mapping) or base_identity.get("ref") != base_ref:
            raise PortableFamilyError(
                "budget semantic evidence base identity is not bound to the receipt"
            )
    head_identity = _budget_identity(manifest)
    if evidence.get("head_identity") != head_identity:
        raise PortableFamilyError("budget semantic evidence head identity mismatches family")
    if evidence.get("fixed_point") != {
        "state": "required_external_gate",
        "family_digest": head_identity["family_digest"],
    }:
        raise PortableFamilyError("budget semantic evidence fixed-point binding mismatches family")
    procedure_base_ref = _procedure_measurement_base_ref(repo_root, base_ref)
    if evidence.get("procedure") != _budget_procedure_identity(
        repo_root,
        procedure_base_ref=procedure_base_ref,
    ):
        raise PortableFamilyError(
            "budget semantic evidence procedure/environment identity is stale"
        )
    review = evidence.get("review")
    if not isinstance(review, Mapping):
        raise PortableFamilyError("budget semantic evidence review binding is missing")
    expected_review = _review_identity(repo_root, str(review.get("ref", "")))
    if dict(review) != expected_review:
        raise PortableFamilyError("budget semantic evidence review binding is stale")
    cause = evidence.get("cause")
    if not isinstance(cause, Mapping) or cause.get("class") not in BUDGET_CAUSE_CLASSES:
        raise PortableFamilyError("budget semantic evidence cause class is invalid")
    if cause.get("reason") != receipt.get("reason"):
        raise PortableFamilyError(
            "budget semantic evidence reason is not bound to the receipt"
        )
    observed = evidence.get("measurements")
    if not isinstance(observed, Mapping):
        raise PortableFamilyError("budget semantic evidence measurements are missing")
    if recompute_measurements:
        measurements = _budget_measurements(
            repo_root,
            base_ref=base_ref,
            manifest=manifest,
            base_manifest=base_manifest,
        )
        expected_measurements = {
            "generated_delta": measurements["generated_delta"],
            "tracked_size": measurements["tracked_size"],
            "authored_source_delta": measurements["authored_source_delta"],
            "procedure_delta": measurements["procedure_delta"],
            "source_dependency": measurements["source_dependency"],
            "topology": measurements["topology"],
            "amplification": {
                "generated_bytes": measurements["generated_delta"]["bytes"],
                "authored_source_bytes": measurements["authored_source_delta"]["bytes"],
                "ratio_numerator": measurements["generated_delta"]["bytes"],
                "ratio_denominator": max(
                    measurements["authored_source_delta"]["bytes"],
                    1,
                ),
            },
            "duplicate_materialization": measurements[
                "duplicate_materialization"
            ],
        }
        if dict(observed) != expected_measurements:
            raise PortableFamilyError(
                "budget semantic evidence measurements do not match current source and family"
            )
        expected_cause_evidence = _cause_witness(
            str(cause["class"]),
            measurements,
        )
        if cause.get("evidence") != expected_cause_evidence:
            raise PortableFamilyError(
                "budget semantic evidence cause witness is stale or incomplete"
            )
        expected_state = _semantic_admission_state(
            base_supported=measurements["base_supported"],
            cause_class=str(cause["class"]),
            source_measurement=measurements["authored_source_delta"],
            duplicate_materialization=measurements["duplicate_materialization"],
            causal_measurements=measurements,
        )
        if expected_state != state:
            raise PortableFamilyError(
                f"budget semantic evidence state={state} does not match measured state={expected_state}"
            )
    else:
        generated = observed.get("generated_delta")
        tracked = observed.get("tracked_size")
        if not isinstance(generated, Mapping) or not isinstance(tracked, Mapping):
            raise PortableFamilyError(
                "shallow checkout evidence measurements are incomplete"
            )
        if (
            generated.get("bytes") != receipt.get("changed_generated_bytes")
            or generated.get("files") != receipt.get("changed_generated_files")
            or tracked.get("bytes") != manifest["summary"]["tracked_bytes"]
            or tracked.get("limit_bytes") != manifest["budgets"]["tracked_bytes_max"]
        ):
            raise PortableFamilyError(
                "shallow checkout evidence measurements do not match current family"
            )
        if str(cause["class"]) in SOURCE_CAUSE_CLASSES:
            source_dependency = observed.get("source_dependency")
            if (
                not isinstance(source_dependency, Mapping)
                or source_dependency.get("state") != "matched"
            ):
                raise PortableFamilyError(
                    "shallow checkout source-caused evidence lacks a matched "
                    "generated dependency witness"
                )
        duplicate = observed.get("duplicate_materialization")
        if not isinstance(duplicate, Mapping) or duplicate.get("state") != "absent":
            raise PortableFamilyError(
                "shallow checkout evidence does not prove duplicate-free admission"
            )
    if receipt.get("semantic_admission") != state:
        raise PortableFamilyError("budget receipt semantic admission state is not supported")


def build_budget_receipt(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
    reason: str,
    semantic_evidence: Mapping[str, Any] | None = None,
    approved_by: str = "repository-owner",
) -> tuple[Path, dict[str, Any]]:
    if not reason.strip():
        raise PortableFamilyError("budget receipt reason must not be empty")
    if semantic_evidence is None:
        raise PortableFamilyError(
            "budget receipt requires typed semantic owner evidence"
        )
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
        base_has_v3=_budget_base_supported(base_manifest),
        generated_delta_exceeded=delta_exceeded,
        tracked_size_exceeded=tracked_exceeded,
    )
    receipt = {
        "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "scope": scope,
        "base_ref": resolved,
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "head_source_snapshot": _budget_identity(manifest)["source_snapshot"],
        "head_distribution_digest": _budget_identity(manifest)[
            "distribution_digest"
        ],
        "changed_generated_bytes": changed_bytes,
        "changed_generated_files": changed_files,
        "default_limit_bytes": DEFAULT_DELTA_BYTES_MAX,
        "allowed_bytes": changed_bytes,
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "allowed_tracked_bytes": summary["tracked_bytes"],
        "reason": reason.strip(),
        "approved_by": approved_by,
        "decision_ref": _budget_decision_ref(manifest),
        "semantic_admission": semantic_evidence.get("state"),
        "semantic_evidence_ref": evidence_path_for(manifest).as_posix(),
        "semantic_evidence_digest": sha256_bytes(
            render_manifest(semantic_evidence)
        ),
    }
    _validate_budget_semantic_evidence(
        repo_root,
        manifest=manifest,
        base_ref=resolved,
        base_manifest=base_manifest,
        expected_scope=scope,
        receipt=receipt,
        evidence=semantic_evidence,
    )
    return receipt_path_for(manifest), receipt


def build_budget_publication(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
    reason: str,
    cause_class: str,
    review_ref: str,
    approved_by: str = "repository-owner",
) -> tuple[Path, dict[str, Any], Path, dict[str, Any]]:
    """Build and semantically validate both members before any pair write."""
    evidence_path, evidence = build_budget_evidence(
        repo_root,
        base_ref=base_ref,
        manifest=manifest,
        reason=reason,
        cause_class=cause_class,
        review_ref=review_ref,
    )
    receipt_path, receipt = build_budget_receipt(
        repo_root,
        base_ref=base_ref,
        manifest=manifest,
        reason=reason,
        semantic_evidence=evidence,
        approved_by=approved_by,
    )
    return evidence_path, evidence, receipt_path, receipt


def _budget_destination(repo_root: Path, path: Path) -> Path:
    if path.is_absolute() or ".." in path.parts:
        raise BudgetPairPublicationError(
            f"budget pair path must be repo-relative: {path}"
        )
    return repo_root.resolve() / path


def _stage_budget_bytes(destination: Path, content: bytes) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        mode = (
            stat.S_IMODE(destination.stat().st_mode)
            if destination.is_file()
            else 0o644
        )
        os.chmod(temporary, mode)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _replace_budget_pair_member(source: Path, destination: Path) -> None:
    os.replace(source, destination)


def _restore_budget_pair_member(
    destination: Path,
    previous: Path | None,
) -> None:
    if previous is None:
        destination.unlink(missing_ok=True)
    else:
        _replace_budget_pair_member(previous, destination)


def publish_budget_pair(
    repo_root: Path,
    *,
    evidence_path: Path,
    evidence: Mapping[str, Any],
    receipt_path: Path,
    receipt: Mapping[str, Any],
) -> None:
    """Publish a validated pair with rollback around the two-file boundary.

    Each member is staged and replaced atomically.  If either replacement (or
    an in-process interruption) fails, the exact previous member bytes and
    presence are restored.  POSIX still cannot make two independent renames
    crash-atomic; a process death between the replacements remains an
    explicit bounded window rather than an implicit success claim.
    """
    evidence_content = render_manifest(evidence)
    receipt_content = render_manifest(receipt)
    if evidence_path == receipt_path:
        raise BudgetPairPublicationError(
            "budget pair evidence and receipt paths must be distinct"
        )
    if receipt.get("semantic_evidence_ref") != evidence_path.as_posix():
        raise BudgetPairPublicationError(
            "budget pair receipt does not reference the staged evidence path"
        )
    if receipt.get("semantic_evidence_digest") != sha256_bytes(evidence_content):
        raise BudgetPairPublicationError(
            "budget pair receipt digest does not match staged evidence"
        )
    if receipt.get("semantic_admission") != evidence.get("state"):
        raise BudgetPairPublicationError(
            "budget pair semantic admission does not match evidence state"
        )

    root = repo_root.resolve()
    evidence_destination = _budget_destination(root, evidence_path)
    receipt_destination = _budget_destination(root, receipt_path)
    if evidence_destination.parent != receipt_destination.parent:
        raise BudgetPairPublicationError(
            "budget pair members must share one publication directory"
        )
    destinations = (
        (evidence_destination, evidence_content),
        (receipt_destination, receipt_content),
    )
    staged_new: dict[Path, Path] = {}
    staged_previous: dict[Path, Path | None] = {}
    cleanup_staged = True
    try:
        for destination, content in destinations:
            staged_new[destination] = _stage_budget_bytes(destination, content)
        for destination, _ in destinations:
            if destination.exists() and not destination.is_file():
                raise BudgetPairPublicationError(
                    f"budget pair destination is not a regular file: {destination}"
                )
            staged_previous[destination] = (
                _stage_budget_bytes(destination, destination.read_bytes())
                if destination.is_file()
                else None
            )
        try:
            for destination, _ in destinations:
                _replace_budget_pair_member(staged_new[destination], destination)
        except BaseException as exc:
            try:
                for destination, _ in reversed(destinations):
                    _restore_budget_pair_member(
                        destination,
                        staged_previous[destination],
                    )
            except BaseException as rollback_exc:
                cleanup_staged = False
                raise BudgetPairPublicationError(
                    "budget pair publication failed and rollback failed; "
                    "accepted pair recovery artifacts were retained"
                ) from rollback_exc
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise BudgetPairPublicationError(
                "budget pair publication failed; accepted pair was restored"
            ) from exc
    finally:
        if cleanup_staged:
            for temporary in (*staged_new.values(), *staged_previous.values()):
                if temporary is not None:
                    temporary.unlink(missing_ok=True)


def _write_budget_file_atomically(
    repo_root: Path,
    path: Path,
    content: bytes,
) -> None:
    destination = _budget_destination(repo_root, path)
    temporary: Path | None = None
    try:
        temporary = _stage_budget_bytes(destination, content)
        _replace_budget_pair_member(temporary, destination)
    except (OSError, BudgetPairPublicationError) as exc:
        raise BudgetPairPublicationError(
            f"budget file publication failed for {path}"
        ) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_budget_evidence(
    repo_root: Path,
    path: Path,
    evidence: Mapping[str, Any],
) -> None:
    _write_budget_file_atomically(repo_root, path, render_manifest(evidence))


def write_budget_receipt(
    repo_root: Path,
    path: Path,
    receipt: Mapping[str, Any],
) -> None:
    _write_budget_file_atomically(repo_root, path, render_manifest(receipt))


def _validate_budget_receipt_without_history(
    repo_root: Path,
    manifest: Mapping[str, Any],
    *,
    base_ref: str,
    require_tracked: bool = False,
) -> tuple[int, int, bool]:
    """Validate a receipt when its immutable base object is outside a shallow clone.

    A receipt/evidence packet cannot replace the missing causal base.  The
    structural current-head checks remain useful for an under-budget family,
    but any exceedance fails closed until immutable history is available.
    """
    try:
        path = repo_root.resolve() / receipt_path_for(manifest)
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict):
            raise PortableFamilyError("budget receipt must be an object")
        if receipt.get("schema_version") == LEGACY_BUDGET_RECEIPT_SCHEMA_VERSION:
            raise PortableFamilyError(
                "budget receipt semantic admission is migration_required; legacy v1 "
                "receipt is structural-only"
            )
        _validate_published_budget_schema("receipt", receipt)
        if receipt.get("base_ref") != base_ref:
            raise PortableFamilyError(
                "shallow checkout receipt base_ref does not match the requested ref"
            )
        budgets = manifest["budgets"]
        summary = manifest["summary"]
        expected = {
            "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
            "repo": manifest["repo"]["name"],
            "head_family_digest": manifest["family_identity"]["content_digest"],
            "head_source_snapshot": _budget_identity(manifest)["source_snapshot"],
            "head_distribution_digest": _budget_identity(manifest)[
                "distribution_digest"
            ],
            "default_limit_bytes": DEFAULT_DELTA_BYTES_MAX,
            "tracked_bytes": summary["tracked_bytes"],
            "tracked_bytes_max": budgets["tracked_bytes_max"],
            "decision_ref": _budget_decision_ref(manifest),
        }
        for field, value in expected.items():
            if receipt.get(field) != value:
                raise PortableFamilyError(
                    f"shallow checkout receipt field {field} does not match family"
                )
        changed_bytes = receipt.get("changed_generated_bytes")
        changed_files = receipt.get("changed_generated_files")
        if not isinstance(changed_bytes, int) or not isinstance(changed_files, int):
            raise PortableFamilyError(
                "shallow checkout receipt generated-delta measurement is missing"
            )
        delta_exceeded = changed_bytes > budgets["changed_generated_bytes_max"]
        tracked_exceeded = summary["tracked_bytes"] > budgets["tracked_bytes_max"]
        if require_tracked and not tracked_exceeded:
            raise PortableFamilyError(
                "shallow checkout tracked-size receipt is not required by the current family"
            )
        if not delta_exceeded and not tracked_exceeded:
            return changed_bytes, changed_files, False
        raise PortableFamilyError(
            "shallow checkout semantic admission requires immutable base history; "
            "receipt/evidence cannot replace a causal base or an independently "
            "authenticated full-history verdict"
        )
    except BudgetReceiptValidationError:
        raise
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise BudgetReceiptValidationError(
            "shallow checkout cannot validate a missing or malformed receipt"
        ) from exc
    except PortableFamilyError as exc:
        raise BudgetReceiptValidationError(str(exc)) from exc


def validate_changed_generated_budget(
    repo_root: Path,
    *,
    base_ref: str,
    manifest: Mapping[str, Any],
) -> tuple[int, int, bool]:
    try:
        changed_bytes, changed_files, resolved = changed_generated_bytes(
            repo_root,
            base_ref=base_ref,
            manifest=manifest,
        )
    except subprocess.CalledProcessError:
        return _validate_budget_receipt_without_history(
            repo_root,
            manifest,
            base_ref=base_ref,
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
        raise BudgetReceiptValidationError(
            "portable family budget is exceeded and no matching receipt exists: "
            f"changed={changed_bytes}/{limit}, "
            f"tracked={summary['tracked_bytes']}/"
            f"{budgets['tracked_bytes_max']}"
        ) from exc
    if not isinstance(receipt, dict):
        raise BudgetReceiptValidationError("budget receipt must be an object")
    if receipt.get("schema_version") == LEGACY_BUDGET_RECEIPT_SCHEMA_VERSION:
        raise BudgetReceiptValidationError(
            "budget receipt semantic admission is migration_required; legacy v1 "
            "receipt is structural-only"
        )
    try:
        _validate_published_budget_schema("receipt", receipt)
    except PortableFamilyError as exc:
        raise BudgetReceiptValidationError(str(exc)) from exc
    expected_scope = _budget_receipt_scope(
        base_has_v3=_budget_base_supported(base_manifest),
        generated_delta_exceeded=delta_exceeded,
        tracked_size_exceeded=tracked_exceeded,
    )
    expected = {
        "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "base_ref": resolved,
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "head_source_snapshot": _budget_identity(manifest)["source_snapshot"],
        "head_distribution_digest": _budget_identity(manifest)[
            "distribution_digest"
        ],
        "changed_generated_bytes": changed_bytes,
        "changed_generated_files": changed_files,
        "default_limit_bytes": DEFAULT_DELTA_BYTES_MAX,
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "decision_ref": _budget_decision_ref(manifest),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise BudgetReceiptValidationError(
                f"budget receipt field {field} does not match current delta"
            )
    if receipt.get("scope") != expected_scope:
        raise BudgetReceiptValidationError(
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
        raise BudgetReceiptValidationError("budget receipt approval is incomplete")
    evidence_ref = receipt.get("semantic_evidence_ref")
    evidence_path = evidence_path_for(manifest)
    if evidence_ref != evidence_path.as_posix():
        raise BudgetReceiptValidationError(
            "budget receipt semantic evidence ref does not match current family"
        )
    evidence_digest = receipt.get("semantic_evidence_digest")
    if not isinstance(evidence_digest, str):
        raise BudgetReceiptValidationError("budget receipt semantic evidence digest is missing")
    evidence_file = repo_root.resolve() / evidence_path
    try:
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise BudgetReceiptValidationError(
            "budget receipt semantic admission is migration_required; typed evidence is missing"
        ) from exc
    if not isinstance(evidence, dict) or sha256_bytes(
        render_manifest(evidence)
    ) != evidence_digest:
        raise BudgetReceiptValidationError("budget semantic evidence digest does not match receipt")
    if evidence.get("schema_version") != BUDGET_EVIDENCE_SCHEMA_VERSION:
        raise BudgetReceiptValidationError(
            "budget semantic admission is migration_required for legacy evidence"
        )
    try:
        _validate_published_budget_schema("evidence", evidence)
    except PortableFamilyError as exc:
        raise BudgetReceiptValidationError(str(exc)) from exc
    try:
        _validate_budget_semantic_evidence(
            repo_root,
            manifest=manifest,
            base_ref=resolved,
            base_manifest=base_manifest,
            expected_scope=expected_scope,
            receipt=receipt,
            evidence=evidence,
        )
    except BudgetReceiptValidationError:
        raise
    except PortableFamilyError as exc:
        raise BudgetReceiptValidationError(str(exc)) from exc
    return changed_bytes, changed_files, True


def _validate_tracked_size_receipt(
    repo_root: Path,
    manifest: Mapping[str, Any],
) -> None:
    try:
        _validate_tracked_size_receipt_with_history(repo_root, manifest)
    except subprocess.CalledProcessError:
        try:
            fallback_receipt = json.loads(
                (
                    repo_root.resolve() / receipt_path_for(manifest)
                ).read_text(encoding="utf-8")
            )
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise BudgetReceiptValidationError(
                "shallow checkout cannot validate a missing or malformed receipt"
            ) from exc
        _validate_budget_receipt_without_history(
            repo_root,
            manifest,
            base_ref=str(fallback_receipt.get("base_ref", "")),
            require_tracked=True,
        )
    except BudgetReceiptValidationError:
        raise
    except PortableFamilyError as exc:
        raise BudgetReceiptValidationError(str(exc)) from exc


def _validate_tracked_size_receipt_with_history(
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
    if not isinstance(receipt, dict):
        raise PortableFamilyError("tracked-size receipt must be an object")
    if receipt.get("schema_version") == LEGACY_BUDGET_RECEIPT_SCHEMA_VERSION:
        raise PortableFamilyError(
            "portable tracked byte budget is migration_required; legacy v1 receipt "
            "is structural-only"
        )
    _validate_published_budget_schema("receipt", receipt)
    summary = manifest["summary"]
    budgets = manifest["budgets"]
    expected = {
        "schema_version": BUDGET_RECEIPT_SCHEMA_VERSION,
        "repo": manifest["repo"]["name"],
        "head_family_digest": manifest["family_identity"]["content_digest"],
        "head_source_snapshot": _budget_identity(manifest)["source_snapshot"],
        "head_distribution_digest": _budget_identity(manifest)[
            "distribution_digest"
        ],
        "tracked_bytes": summary["tracked_bytes"],
        "tracked_bytes_max": budgets["tracked_bytes_max"],
        "decision_ref": _budget_decision_ref(manifest),
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
    base_ref = receipt.get("base_ref")
    if not isinstance(base_ref, str) or not base_ref:
        raise PortableFamilyError(
            "tracked-size receipt semantic admission is missing base identity"
        )
    resolved = _resolve_git_ref(repo_root, base_ref)
    if resolved != base_ref:
        raise PortableFamilyError(
            "tracked-size receipt base_ref must be the resolved full Git ref"
        )
    base_manifest = _base_manifest(repo_root, resolved)
    changed_bytes, changed_files, _ = changed_generated_bytes(
        repo_root,
        base_ref=resolved,
        manifest=manifest,
    )
    expected_scope = _budget_receipt_scope(
        base_has_v3=_budget_base_supported(base_manifest),
        generated_delta_exceeded=changed_bytes
        > budgets.get("changed_generated_bytes_max", DEFAULT_DELTA_BYTES_MAX),
        tracked_size_exceeded=True,
    )
    if receipt.get("scope") != expected_scope:
        raise PortableFamilyError(
            "tracked-size receipt scope does not match current generated delta"
        )
    evidence_path = evidence_path_for(manifest)
    if receipt.get("semantic_evidence_ref") != evidence_path.as_posix():
        raise PortableFamilyError(
            "tracked-size receipt semantic evidence ref does not match family"
        )
    try:
        evidence = json.loads(
            (repo_root.resolve() / evidence_path).read_text(encoding="utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise PortableFamilyError(
            "portable tracked byte budget is migration_required; typed evidence is missing"
        ) from exc
    if not isinstance(evidence, dict) or sha256_bytes(
        render_manifest(evidence)
    ) != receipt.get("semantic_evidence_digest"):
        raise PortableFamilyError("tracked-size semantic evidence digest does not match")
    if evidence.get("schema_version") != BUDGET_EVIDENCE_SCHEMA_VERSION:
        raise PortableFamilyError(
            "budget semantic admission is migration_required for legacy evidence"
        )
    _validate_published_budget_schema("evidence", evidence)
    _validate_budget_semantic_evidence(
        repo_root,
        manifest=manifest,
        base_ref=resolved,
        base_manifest=base_manifest,
        expected_scope=expected_scope,
        receipt=receipt,
        evidence=evidence,
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
