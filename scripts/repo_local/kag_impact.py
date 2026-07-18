from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


IMPACT_CLASSES = (
    "owner-local-authored-change",
    "owner-manifest-distribution-only-change",
    "cross-owner-relation-change",
    "federation-registry-change",
    "family-schema-change",
    "canonicalization-builder-change",
    "shard-partition-policy-change",
    "mcp-canonical-loader-change",
    "artifact-trust-policy-change",
    "owner-membership-change",
)

FULL_FANOUT_CLASSES = {
    "family-schema-change": "family schema changed",
    "canonicalization-builder-change": (
        "shared canonicalization or builder changed"
    ),
    "shard-partition-policy-change": "shard partition policy changed",
    "mcp-canonical-loader-change": "MCP canonical loader changed",
    "artifact-trust-policy-change": "artifact trust or access policy changed",
    "owner-membership-change": "canonical owner membership changed",
}

CLASS_PRIORITY = {
    name: position for position, name in enumerate(reversed(IMPACT_CLASSES))
}

ALL_COMPATIBILITY_VIEWS = (
    "source",
    "artifact",
    "anchor",
    "entity",
    "event",
    "assertion",
    "relation",
)


@dataclass(frozen=True)
class ImpactClassification:
    impact_class: str
    impact_classes: tuple[str, ...]
    affected_owners: tuple[str, ...]
    affected_logical_views: tuple[str, ...]
    required_validation_lane: str
    full_fanout_reason: str
    changed_paths: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "aoa-kag-impact-classification-v1",
            "impact_class": self.impact_class,
            "impact_classes": list(self.impact_classes),
            "affected_owners": list(self.affected_owners),
            "affected_logical_views": list(
                self.affected_logical_views
            ),
            "required_validation_lane": self.required_validation_lane,
            "full_fanout_reason": self.full_fanout_reason,
            "changed_paths": list(self.changed_paths),
        }


def _normalized_path(value: str | Path) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(
            f"impact path must be repository-relative: {value}"
        )
    return path.as_posix().removeprefix("./")


def _path_classes(path: str) -> set[str]:
    result: set[str] = set()
    if path in {
        "manifests/provider_registry.json",
        "manifests/local_kag_provider_map.json",
    }:
        result.update(
            {
                "federation-registry-change",
                "owner-membership-change",
            }
        )
    elif path.startswith("manifests/") and (
        "provider" in path or "owner" in path
    ):
        result.add("federation-registry-change")

    if path.startswith("schemas/") and (
        "repo-local-kag" in path
        or "kag-owner" in path
        or "kag-os-composition" in path
        or "kag-pack" in path
    ):
        result.add("family-schema-change")

    if path in {
        "scripts/generate_repo_local_kag_index.py",
        "scripts/repo_local/identity.py",
        "scripts/repo_local/indexes.py",
        "scripts/repo_local/portable_family.py",
        "scripts/repo_local/structure.py",
        "scripts/repo_local/tiered_family.py",
    }:
        result.add("canonicalization-builder-change")

    if (
        path.endswith("hot_profile.json")
        or "partition" in path
        or path.endswith("repo-local-kag-hot-profile.schema.json")
    ):
        result.add("shard-partition-policy-change")

    if (
        "aoa-kag-mcp" in path
        or path.endswith("kag-mcp-capabilities.schema.json")
        or path.endswith("kag-mcp-result.schema.json")
    ):
        result.add("mcp-canonical-loader-change")

    if (
        "artifact" in path
        and (
            path.startswith("schemas/")
            or path.startswith("policies/")
            or path.startswith("manifests/")
        )
    ) or path in {
        "scripts/repo_local/tiered_governance.py",
        "scripts/repo_local/tiered_rollout.py",
    } or any(
        token in path
        for token in (
            "trust-root",
            "revocation",
            "retention",
            "public-safety",
            "access-policy",
        )
    ):
        result.add("artifact-trust-policy-change")

    if path.startswith(
        (
            "generated/repo_local_kag_federation",
            "kag/federation/",
            "federation/",
        )
    ):
        result.add("cross-owner-relation-change")

    if path.startswith(
        (
            "kag/indexes/",
            "kag/receipts/",
            "artifacts/kag/",
        )
    ):
        result.add("owner-manifest-distribution-only-change")

    if not result:
        result.add("owner-local-authored-change")
    return result


def _views_for(classes: set[str]) -> tuple[str, ...]:
    if classes & {
        "family-schema-change",
        "canonicalization-builder-change",
        "shard-partition-policy-change",
        "mcp-canonical-loader-change",
        "owner-membership-change",
    }:
        return ALL_COMPATIBILITY_VIEWS
    views: set[str] = {"source"}
    if "cross-owner-relation-change" in classes:
        views.update({"anchor", "entity", "relation"})
    if "federation-registry-change" in classes:
        views.update({"entity", "relation"})
    if "owner-local-authored-change" in classes:
        views.update(ALL_COMPATIBILITY_VIEWS)
    return tuple(
        view for view in ALL_COMPATIBILITY_VIEWS if view in views
    )


def classify_impact(
    changed_paths: Iterable[str | Path],
    *,
    owner: str,
    related_owners: Sequence[str] = (),
) -> ImpactClassification:
    if not owner:
        raise ValueError("impact classifier requires an owner")
    normalized = tuple(
        sorted({_normalized_path(path) for path in changed_paths})
    )
    classes: set[str] = set()
    for path in normalized:
        classes.update(_path_classes(path))
    if not classes:
        classes.add("owner-local-authored-change")
    ordered_classes = tuple(
        sorted(classes, key=lambda item: (-CLASS_PRIORITY[item], item))
    )
    full_reasons = [
        FULL_FANOUT_CLASSES[item]
        for item in ordered_classes
        if item in FULL_FANOUT_CLASSES
    ]
    if full_reasons:
        lane = "full-24-owner-audit"
        reason = "; ".join(full_reasons)
    elif "cross-owner-relation-change" in classes:
        lane = "incremental-federation"
        reason = ""
    elif classes == {"owner-manifest-distribution-only-change"}:
        lane = "owner-distribution-fast"
        reason = ""
    elif "federation-registry-change" in classes:
        lane = "incremental-federation"
        reason = ""
    else:
        lane = "owner-local-fast"
        reason = ""
    owners = tuple(sorted({owner, *related_owners}))
    return ImpactClassification(
        impact_class=ordered_classes[0],
        impact_classes=ordered_classes,
        affected_owners=owners,
        affected_logical_views=_views_for(classes),
        required_validation_lane=lane,
        full_fanout_reason=reason,
        changed_paths=normalized,
    )


def immutable_owner_cache_key(
    *,
    owner: str,
    source_snapshot: str,
    builder_digest: str,
    schema_epoch: str,
    canonicalization_epoch: str,
) -> str:
    payload: Mapping[str, str] = {
        "owner": owner,
        "source_snapshot": source_snapshot,
        "builder_digest": builder_digest,
        "schema_epoch": schema_epoch,
        "canonicalization_epoch": canonicalization_epoch,
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
