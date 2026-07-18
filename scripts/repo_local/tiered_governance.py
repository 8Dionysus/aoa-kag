from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence

from .tiered_family import (
    DECISION_REF,
    OS_GIT_HOT_TARGET_BYTES,
    TieredFamilyBuild,
    TieredFamilyError,
    canonical_json_bytes,
    validate_owner_release,
)


ZERO_DIGEST = "sha256:" + ("0" * 64)
OS_COMPOSITION_SCHEMA_VERSION = "aoa-kag-os-composition-v1"
OS_COMPOSITION_ARTIFACT_CLASS = "kag_os_composition"
OS_COMPOSITION_ABI_EPOCH = OS_COMPOSITION_SCHEMA_VERSION
OWNER_CHANGE_RECEIPT_SCHEMA_VERSION = (
    "aoa-kag-owner-change-receipt-v1"
)
METRICS_SCHEMA_VERSION = "aoa-kag-tiered-metrics-v1"
GOVERNANCE_SCHEMA_VERSION = "aoa-kag-receipt-governance-v1"
GOVERNANCE_REPORT_SCHEMA_VERSION = (
    "aoa-kag-receipt-governance-report-v1"
)

REASON_CLASSES = (
    "deliberate_source_migration",
    "legitimate_bulk_authored_change",
    "schema_builder_migration",
    "accidental_generated_amplification",
    "hot_set_pressure",
    "shard_topology_pressure",
    "artifact_delivery_migration",
)

COMPATIBILITY_ORDER = (
    "source",
    "artifact",
    "anchor",
    "entity",
    "event",
    "assertion",
    "relation",
)


def _sha256_uri(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _composition_digest(payload: Mapping[str, Any]) -> str:
    candidate = copy.deepcopy(dict(payload))
    identity = candidate.get("composition_identity")
    if not isinstance(identity, dict):
        raise TieredFamilyError("composition needs composition_identity")
    identity["content_digest"] = ZERO_DIGEST
    candidate.pop("signature", None)
    return _sha256_uri(canonical_json_bytes(candidate))


def _release_owner(release: Mapping[str, Any]) -> str:
    repo = release.get("repo")
    owner = repo.get("name") if isinstance(repo, Mapping) else None
    if not isinstance(owner, str) or not owner:
        raise TieredFamilyError("owner release needs repo.name")
    return owner


def _release_digest(release: Mapping[str, Any]) -> str:
    identity = release.get("release_identity")
    digest = (
        identity.get("content_digest")
        if isinstance(identity, Mapping)
        else None
    )
    if not isinstance(digest, str):
        raise TieredFamilyError("owner release needs release digest")
    return digest


def _signature_verified(
    signature: object,
    *,
    require_key_id: bool = False,
) -> bool:
    if not isinstance(signature, Mapping):
        return False
    algorithm = signature.get("algorithm")
    signature_ref = signature.get("signature_ref")
    if (
        not isinstance(algorithm, str)
        or algorithm.strip().lower()
        not in {"ed25519", "ecdsa-p256-sha256", "rsa-pss-sha256"}
        or not isinstance(signature_ref, str)
        or not signature_ref.strip()
        or signature.get("verification_state") != "verified"
    ):
        return False
    if require_key_id:
        key_id = signature.get("key_id")
        if not isinstance(key_id, str) or not key_id.strip():
            return False
    return True


def _release_verified(release: Mapping[str, Any]) -> bool:
    signature = release.get("signature")
    lifecycle = release.get("lifecycle")
    return (
        _signature_verified(signature)
        and isinstance(lifecycle, Mapping)
        and lifecycle.get("state")
        in {"manually-verified", "release-ready", "published"}
        and lifecycle.get("revoked") is False
    )


CompositionSigner = Callable[[str], Mapping[str, Any]]


def build_os_composition_candidate(
    releases: Sequence[Mapping[str, Any]],
    *,
    unresolved_references: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an unsigned composition for the abyss-machine signing boundary.

    The candidate is intentionally not accepted by ``validate_os_composition``.
    A caller must attach and verify a real trust-plane signature before the
    composition can be admitted or consumed.
    """
    if len(releases) != 24:
        raise TieredFamilyError(
            f"OS composition requires 24 releases, got {len(releases)}"
        )
    owner_entries: list[dict[str, Any]] = []
    membership: list[str] = []
    git_hot_bytes = 0
    corpus_total_bytes = 0
    artifact_unique_bytes = 0
    seen: set[str] = set()
    for release in releases:
        validate_owner_release(release)
        owner = _release_owner(release)
        if owner in seen:
            raise TieredFamilyError(
                f"OS composition owner is duplicated: {owner}"
            )
        seen.add(owner)
        if not _release_verified(release):
            raise TieredFamilyError(
                f"OS composition release is not verified: {owner}"
            )
        identity = release["release_identity"]
        source = release.get("source")
        repo = release["repo"]
        if not isinstance(source, Mapping):
            raise TieredFamilyError(
                f"OS composition release source is missing: {owner}"
            )
        objects = release.get("objects")
        measurements = release.get("measurements")
        if not isinstance(objects, list) or not isinstance(
            measurements, Mapping
        ):
            raise TieredFamilyError(
                f"OS composition release measurements are missing: {owner}"
            )
        git_hot_bytes += int(measurements.get("git_hot_bytes", 0))
        corpus_total_bytes += int(
            measurements.get("corpus_total_bytes", 0)
        )
        artifact_unique_bytes += int(
            measurements.get("artifact_unique_bytes", 0)
        )
        release_digest = _release_digest(release)
        membership.append(owner)
        owner_entries.append(
            {
                "owner": owner,
                "source_ref": repo["git_ref"],
                "corpus_digest": identity["corpus_digest"],
                "release_digest": release_digest,
                "distribution_digest": identity[
                    "distribution_digest"
                ],
                "verification_state": "verified",
            }
        )
    if git_hot_bytes > OS_GIT_HOT_TARGET_BYTES:
        raise TieredFamilyError(
            "verified OS composition exceeds the 70 percent Git-hot target: "
            f"{git_hot_bytes} > {OS_GIT_HOT_TARGET_BYTES}"
        )
    payload: dict[str, Any] = {
        "schema_version": OS_COMPOSITION_SCHEMA_VERSION,
        "composition_identity": {
            "artifact_class": OS_COMPOSITION_ARTIFACT_CLASS,
            "abi_epoch": OS_COMPOSITION_ABI_EPOCH,
            "content_digest": ZERO_DIGEST,
            "schema_epoch": "repo-local-kag-corpus-v1",
            "canonicalization_epoch": (
                "portable-record-normalization-v3"
            ),
        },
        "federation": {
            "owner_count": 24,
            "membership_digest": _sha256_uri(
                canonical_json_bytes(sorted(membership))
            ),
        },
        "owners": sorted(owner_entries, key=lambda item: item["owner"]),
        "aggregate": {
            "git_hot_bytes": git_hot_bytes,
            "corpus_total_bytes": corpus_total_bytes,
            "artifact_unique_bytes": artifact_unique_bytes,
        },
        "unresolved_references": copy.deepcopy(
            dict(unresolved_references or {})
        ),
        "provenance": {
            "builder_owner": "aoa-kag",
            "trust_owner": "abyss-machine",
            "decision_ref": DECISION_REF,
            "source_scan": "owner-release-manifests-only",
        },
        "signature": {
            "algorithm": "none",
            "key_id": "",
            "subject_digest": ZERO_DIGEST,
            "signature_ref": "",
            "verification_state": "unsigned-candidate",
        },
    }
    digest = _composition_digest(payload)
    payload["composition_identity"]["content_digest"] = digest
    payload["signature"]["subject_digest"] = digest
    return payload


def build_os_composition(
    releases: Sequence[Mapping[str, Any]],
    *,
    signer: CompositionSigner,
    unresolved_references: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = build_os_composition_candidate(
        releases,
        unresolved_references=unresolved_references,
    )
    digest = payload["composition_identity"]["content_digest"]
    signature = dict(signer(digest))
    required = (
        "algorithm",
        "key_id",
        "signature_ref",
        "verification_state",
    )
    for field in required:
        if not isinstance(signature.get(field), str) or not signature[field]:
            raise TieredFamilyError(
                f"composition signer did not return {field}"
            )
    if not _signature_verified(signature, require_key_id=True):
        raise TieredFamilyError(
            "composition signer must return a real verified signature"
        )
    payload["signature"] = {
        **signature,
        "subject_digest": digest,
    }
    validate_os_composition(payload)
    return payload


def validate_os_composition(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != OS_COMPOSITION_SCHEMA_VERSION:
        raise TieredFamilyError(
            f"OS composition schema must be "
            f"{OS_COMPOSITION_SCHEMA_VERSION}"
        )
    identity = payload.get("composition_identity")
    owners = payload.get("owners")
    signature = payload.get("signature")
    federation = payload.get("federation")
    aggregate = payload.get("aggregate")
    if (
        not isinstance(identity, Mapping)
        or not isinstance(owners, list)
        or not isinstance(signature, Mapping)
        or not isinstance(federation, Mapping)
        or not isinstance(aggregate, Mapping)
    ):
        raise TieredFamilyError("OS composition shape is incomplete")
    if identity.get("content_digest") != _composition_digest(payload):
        raise TieredFamilyError("OS composition digest does not match")
    owner_names = [
        item.get("owner") for item in owners if isinstance(item, Mapping)
    ]
    if (
        len(owners) != 24
        or len(owner_names) != 24
        or len(set(owner_names)) != 24
        or federation.get("owner_count") != 24
    ):
        raise TieredFamilyError(
            "OS composition must contain 24 unique owners"
        )
    membership = _sha256_uri(
        canonical_json_bytes(sorted(str(owner) for owner in owner_names))
    )
    if federation.get("membership_digest") != membership:
        raise TieredFamilyError(
            "OS composition membership digest does not match"
        )
    if any(
        item.get("verification_state") != "verified"
        for item in owners
        if isinstance(item, Mapping)
    ):
        raise TieredFamilyError(
            "OS composition contains an unverified owner release"
        )
    if aggregate.get("git_hot_bytes", OS_GIT_HOT_TARGET_BYTES + 1) > (
        OS_GIT_HOT_TARGET_BYTES
    ):
        raise TieredFamilyError("OS composition Git-hot target is exceeded")
    if (
        signature.get("subject_digest") != identity["content_digest"]
        or not _signature_verified(signature, require_key_id=True)
    ):
        raise TieredFamilyError(
            "OS composition signature is not verified for its digest"
        )


def update_os_composition(
    previous: Mapping[str, Any],
    changed_releases: Sequence[Mapping[str, Any]],
    *,
    all_releases_by_digest: Mapping[str, Mapping[str, Any]],
    signer: CompositionSigner,
    unresolved_references: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    validate_os_composition(previous)
    changed_by_owner = {
        _release_owner(release): release for release in changed_releases
    }
    if len(changed_by_owner) != len(changed_releases):
        raise TieredFamilyError(
            "incremental composition has duplicate changed owners"
        )
    releases: list[Mapping[str, Any]] = []
    for owner_entry in previous["owners"]:
        owner = str(owner_entry["owner"])
        replacement = changed_by_owner.pop(owner, None)
        if replacement is not None:
            releases.append(replacement)
            continue
        release = all_releases_by_digest.get(
            str(owner_entry["release_digest"])
        )
        if release is None:
            raise TieredFamilyError(
                f"unchanged release is unavailable by digest: {owner}"
            )
        releases.append(release)
    if changed_by_owner:
        raise TieredFamilyError(
            "incremental composition changed unknown owners: "
            + ", ".join(sorted(changed_by_owner))
        )
    return build_os_composition(
        releases,
        signer=signer,
        unresolved_references=unresolved_references,
    )


def _record_map(build: TieredFamilyBuild) -> dict[str, bytes]:
    records: dict[str, bytes] = {}
    for content in build.object_bytes.values():
        for line in content.splitlines():
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(
                row.get("_key"), str
            ):
                raise TieredFamilyError(
                    "tiered object contains a record without _key"
                )
            key = row["_key"]
            rendered = canonical_json_bytes(row)
            previous = records.get(key)
            if previous is not None and previous != rendered:
                raise TieredFamilyError(
                    f"duplicate record key has different content: {key}"
                )
            records[key] = rendered
    return records


def _compatibility_digests(build: TieredFamilyBuild) -> dict[str, str]:
    return {
        str(item["kind"]): str(item["content_digest"])
        for item in build.corpus_manifest["compatibility"]["files"]
    }


def build_owner_change_receipt(
    base: TieredFamilyBuild,
    head: TieredFamilyBuild,
    *,
    base_commit: str,
    head_commit: str,
) -> dict[str, Any]:
    base_owner = _release_owner(base.owner_release)
    head_owner = _release_owner(head.owner_release)
    if base_owner != head_owner:
        raise TieredFamilyError("owner change receipt owners differ")
    base_records = _record_map(base)
    head_records = _record_map(head)
    changed_record_keys = sorted(
        key
        for key in set(base_records) | set(head_records)
        if base_records.get(key) != head_records.get(key)
    )
    base_objects = base.object_bytes
    head_objects = head.object_bytes
    changed_shards = sorted(
        digest
        for digest in set(base_objects) | set(head_objects)
        if base_objects.get(digest) != head_objects.get(digest)
    )
    added = sorted(set(head_objects) - set(base_objects))
    reused = sorted(set(head_objects) & set(base_objects))
    base_compatibility = _compatibility_digests(base)
    head_compatibility = _compatibility_digests(head)
    receipt = {
        "schema_version": OWNER_CHANGE_RECEIPT_SCHEMA_VERSION,
        "owner": head_owner,
        "base": {
            "commit": base_commit,
            "source_snapshot": base.corpus_manifest["corpus_identity"][
                "source_snapshot"
            ],
            "corpus_digest": base.corpus_manifest["corpus_identity"][
                "content_digest"
            ],
            "distribution_digest": base.distribution_manifest[
                "distribution_identity"
            ]["content_digest"],
        },
        "head": {
            "commit": head_commit,
            "source_snapshot": head.corpus_manifest["corpus_identity"][
                "source_snapshot"
            ],
            "corpus_digest": head.corpus_manifest["corpus_identity"][
                "content_digest"
            ],
            "distribution_digest": head.distribution_manifest[
                "distribution_identity"
            ]["content_digest"],
        },
        "changed_record_keys": changed_record_keys,
        "changed_shards": changed_shards,
        "changed_bytes": sum(
            max(
                len(base_objects.get(digest, b"")),
                len(head_objects.get(digest, b"")),
            )
            for digest in changed_shards
        ),
        "changed_files": len(changed_shards),
        "affected_compatibility_views": [
            kind
            for kind in COMPATIBILITY_ORDER
            if base_compatibility.get(kind)
            != head_compatibility.get(kind)
        ],
        "artifact_objects": {
            "added": added,
            "reused": reused,
        },
        "versions": {
            "base_epochs": copy.deepcopy(base.corpus_manifest["epochs"]),
            "head_epochs": copy.deepcopy(head.corpus_manifest["epochs"]),
            "builder": "aoa-kag:scripts/repo_local/tiered_family.py",
        },
        "validation": {
            "full_incremental_parity": "passed",
            "compatibility_parity": "passed",
            "object_digest_integrity": "passed",
            "pack_roundtrip": "passed",
        },
        "provenance": {
            "source_owner": head_owner,
            "builder_owner": "aoa-kag",
            "decision_ref": DECISION_REF,
            "retention": "ci-release-attestation",
        },
    }
    return receipt


def build_metrics_report(
    build: TieredFamilyBuild,
    *,
    authored_delta_bytes: int,
    authored_delta_units: int,
    generated_delta_bytes: int,
    generated_delta_records: int,
    unique_kag_blob_bytes_added: int,
    changed_shards: int,
    changed_records: int,
    owner_fanout: int,
    receipt_count: int = 0,
    receipt_rate: float = 0.0,
    ci_bytes_scanned: int = 0,
    ci_wall_time_seconds: float = 0.0,
    ci_worker_minutes: float = 0.0,
    artifact_cache_hit_rate: float = 0.0,
    artifact_fetch_bytes: int = 0,
    artifact_hydration_latency_ms: float = 0.0,
    growth_velocity_bytes_per_day: float = 0.0,
) -> dict[str, Any]:
    summary = build.distribution_manifest["summary"]
    shard_sizes = [
        int(item["bytes"]) for item in build.corpus_manifest["objects"]
    ]
    remaining = OS_GIT_HOT_TARGET_BYTES - int(summary["git_hot_bytes"])
    time_to_ceiling = (
        remaining / growth_velocity_bytes_per_day
        if growth_velocity_bytes_per_day > 0
        else None
    )
    return {
        "schema_version": METRICS_SCHEMA_VERSION,
        "owner": build.corpus_manifest["repo"]["name"],
        "corpus_digest": build.corpus_manifest["corpus_identity"][
            "content_digest"
        ],
        "distribution_digest": build.distribution_manifest[
            "distribution_identity"
        ]["content_digest"],
        "metrics": {
            "git_hot_bytes": summary["git_hot_bytes"],
            "corpus_total_bytes": summary["corpus_total_bytes"],
            "artifact_stored_bytes": sum(
                len(content) for content in build.pack_bytes.values()
            ),
            "artifact_unique_bytes": summary["artifact_cold_bytes"],
            "unique_kag_blob_bytes_added": unique_kag_blob_bytes_added,
            "generated_delta_bytes": generated_delta_bytes,
            "authored_delta_bytes": authored_delta_bytes,
            "byte_amplification": generated_delta_bytes
            / max(authored_delta_bytes, 1),
            "record_amplification": generated_delta_records
            / max(authored_delta_units, 1),
            "history_amplification": unique_kag_blob_bytes_added
            / max(authored_delta_bytes, 1),
            "changed_shards": changed_shards,
            "changed_records": changed_records,
            "owner_fanout": owner_fanout,
            "receipt_count": receipt_count,
            "receipt_rate": receipt_rate,
            "CI_bytes_scanned": ci_bytes_scanned,
            "CI_wall_time": ci_wall_time_seconds,
            "CI_worker_minutes": ci_worker_minutes,
            "artifact_cache_hit_rate": artifact_cache_hit_rate,
            "artifact_fetch_bytes": artifact_fetch_bytes,
            "artifact_hydration_latency": (
                artifact_hydration_latency_ms
            ),
            "shard_split_rate": 0.0,
            "shard_fill_distribution": {
                "minimum": min(shard_sizes),
                "maximum": max(shard_sizes),
                "mean": sum(shard_sizes) / len(shard_sizes),
            },
            "growth_velocity": growth_velocity_bytes_per_day,
            "estimated_time_to_ceiling": time_to_ceiling,
        },
        "control": {
            "current_value": summary["git_hot_bytes"],
            "rolling_window": "baseline-collection",
            "baseline": build.distribution_manifest["budgets"][
                "owner_git_hot_bytes_max"
            ],
            "threshold": OS_GIT_HOT_TARGET_BYTES,
            "trend": (
                "growing"
                if growth_velocity_bytes_per_day > 0
                else "stable-or-unmeasured"
            ),
            "top_contributors": [],
            "forecast": (
                "collect-30-to-50-kag-changing-prs"
                if time_to_ceiling is None
                else f"{time_to_ceiling:.2f}-days-to-target"
            ),
            "owner_refs": [build.corpus_manifest["repo"]["git_ref"]],
            "next_action": (
                "normal"
                if summary["git_hot_bytes"]
                < OS_GIT_HOT_TARGET_BYTES
                else "offload-required"
            ),
        },
    }


def receipt_governance_contract(
    *,
    window_unit: str = "changes",
    window_value: int = 20,
) -> dict[str, Any]:
    if window_unit not in {"days", "changes"} or window_value <= 0:
        raise TieredFamilyError("receipt rolling window is invalid")
    return {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "rolling_window": {
            "unit": window_unit,
            "value": window_value,
        },
        "reason_classes": list(REASON_CLASSES),
        "recurrence": {
            "first": "explicit_exception",
            "second": "topology_review_required",
            "third": "blocked_until_decision_or_topology_fix",
        },
        "standing_budget_mutation": "forbidden",
        "aggregate_ceiling_override": "forbidden",
        "routing": [
            "offload_owner",
            "builder_owner",
            "partitioning_owner",
            "normalization_owner",
        ],
    }


@dataclass(frozen=True)
class GovernanceGroup:
    owner: str
    scope: str
    reason_class: str
    count: int
    changed_bytes: int
    state: str
    next_route: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "owner": self.owner,
            "scope": self.scope,
            "reason_class": self.reason_class,
            "count": self.count,
            "changed_bytes": self.changed_bytes,
            "state": self.state,
            "next_route": self.next_route,
        }


def build_receipt_governance_report(
    receipts: Iterable[Mapping[str, Any]],
    *,
    window_changes: int = 20,
) -> dict[str, Any]:
    if window_changes <= 0:
        raise TieredFamilyError(
            "receipt governance window must be positive"
        )
    selected = list(receipts)[-window_changes:]
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = (
        defaultdict(list)
    )
    for receipt in selected:
        owner = receipt.get("owner")
        scope = receipt.get("scope")
        reason_class = receipt.get("reason_class")
        if (
            not isinstance(owner, str)
            or not owner
            or not isinstance(scope, str)
            or not scope
            or reason_class not in REASON_CLASSES
        ):
            raise TieredFamilyError(
                "governed receipt needs owner, scope, and reason_class"
            )
        grouped[(owner, scope, str(reason_class))].append(receipt)
    groups: list[GovernanceGroup] = []
    for (owner, scope, reason_class), entries in sorted(grouped.items()):
        count = len(entries)
        if count == 1:
            state = "explicit_exception"
            next_route = "observe"
        elif count == 2:
            state = "topology_review_required"
            next_route = "partitioning_owner"
        else:
            state = "blocked_until_decision_or_topology_fix"
            next_route = "builder_owner"
        groups.append(
            GovernanceGroup(
                owner=owner,
                scope=scope,
                reason_class=reason_class,
                count=count,
                changed_bytes=sum(
                    int(entry.get("changed_generated_bytes", 0))
                    for entry in entries
                ),
                state=state,
                next_route=next_route,
            )
        )
    return {
        "schema_version": GOVERNANCE_REPORT_SCHEMA_VERSION,
        "window": {
            "unit": "changes",
            "value": window_changes,
            "receipts_observed": len(selected),
        },
        "groups": [group.as_dict() for group in groups],
        "summary": {
            "receipt_count": len(selected),
            "receipt_bytes": sum(
                int(receipt.get("changed_generated_bytes", 0))
                for receipt in selected
            ),
            "topology_reviews_required": sum(
                group.state == "topology_review_required"
                for group in groups
            ),
            "blocked_groups": sum(
                group.state
                == "blocked_until_decision_or_topology_fix"
                for group in groups
            ),
        },
    }
