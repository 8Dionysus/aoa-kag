"""Provider-neutral, source-bound workspace observations and bounded reads.

This is a pure in-memory substrate, not a provider executor, trust gate,
published owner family, mutable runtime store, or proof verdict.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from typing import Any, Mapping

from .code_coordinates import CodeObservationError, SourceText, source_path
from .identity import qualified_id


SCHEMA_VERSION = "aoa-kag-code-workspace-v1"


def canonical_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def code_handle(repo: str, kind: str, context: str, *key: object) -> str:
    # Hash before qualified_id's path normalization: native keys are opaque,
    # case-sensitive values, not paths or display names.
    return qualified_id(repo, f"code-{kind}", canonical_digest([repo, context, *key]))


def source_identity(
    repo: str, source_epoch: str, sources: Mapping[str, str | bytes],
) -> tuple[dict[str, Any], dict[str, SourceText]]:
    if not isinstance(repo, str) or not repo.strip():
        raise CodeObservationError("repository identity is required")
    if not isinstance(source_epoch, str) or not source_epoch.strip():
        raise CodeObservationError("source epoch is required")
    if not isinstance(sources, Mapping):
        raise CodeObservationError("sources must map paths to exact blobs")
    blobs = {source_path(path): SourceText(content) for path, content in sources.items()}
    identity = {
        "repo": repo,
        "epoch": source_epoch,
        "manifest": {path: hashlib.sha256(blob.raw).hexdigest()
                     for path, blob in sorted(blobs.items())},
    }
    return {**identity, "digest": canonical_digest(identity)}, blobs


class CodeWorkspace:
    """Own a normalized snapshot; return copies, never mutable internal rows."""

    def __init__(self, payload: Mapping[str, Any]):
        self._payload = copy.deepcopy(dict(payload))
        self._snapshot_id = canonical_digest(self._payload)
        self._symbols = {row["handle"]: row for row in self._payload["symbols"]}
        self._occurrences = {row["handle"]: row for row in self._payload["occurrences"]}
        self._relations = {row["handle"]: row for row in self._payload["relations"]}
        self._records = {**self._symbols, **self._occurrences, **self._relations}

    @property
    def snapshot_id(self) -> str:
        return self._snapshot_id

    def to_dict(self) -> dict[str, Any]:
        return {"snapshot_id": self.snapshot_id, **copy.deepcopy(self._payload)}

    def _qualification(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "source": {key: self._payload["source"][key] for key in ("repo", "epoch", "digest")},
            "analysis": copy.deepcopy(self._payload["analysis"]),
            "coverage": {
                (f"{key}_count" if key.endswith("_paths") else key):
                (len(value) if key.endswith("_paths") else value)
                for key, value in self._payload["coverage"].items()
            },
            "plane": "INDEXED",
            "publication": "unreleased",
            "proof": "not_evaluated",
            "admission": "not_assessed",
            "freshness": "exact_snapshot_only",
        }

    @staticmethod
    def _compact(row: Mapping[str, Any]) -> dict[str, Any]:
        bulky = {"definitions", "references", "metadata", "native"}
        result = copy.deepcopy({key: value for key, value in row.items() if key not in bulky})
        for key in ("definitions", "references", "metadata"):
            if key in row:
                result[f"{key}_count"] = len(row[key])
        if "native" in row:
            result["native_sha256"] = canonical_digest(row["native"])
        return result

    def read(
        self, handle: str, *, source: str | bytes | None = None, max_chars: int = 4096,
    ) -> dict[str, Any]:
        if type(max_chars) is not int or not 1 <= max_chars <= 4096:
            raise CodeObservationError("max_chars must be between 1 and 4096")
        if handle not in self._records:
            raise CodeObservationError("handle does not belong to this snapshot")
        row = self._compact(self._records[handle])
        result = {**self._qualification(), "record": row}
        if source is not None:
            if handle not in self._occurrences:
                raise CodeObservationError("source text reads require an occurrence handle")
            blob = SourceText(source)
            if hashlib.sha256(blob.raw).hexdigest() != row["source_sha256"]:
                raise CodeObservationError("source bytes do not match the snapshot")
            span = row["range"]
            text = blob.raw[span["start_byte"]:span["end_byte"]].decode("utf-8")
            result.update(text=text[:max_chars], truncated=len(text) > max_chars)
        return result

    def query(
        self, symbol_handle: str, kind: str, *, limit: int = 10,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Direct definitions/references only; no inferred calls or hierarchy."""
        if kind not in {"definitions", "references"}:
            raise CodeObservationError("query kind must be definitions or references")
        if type(limit) is not int or not 1 <= limit <= 10:
            raise CodeObservationError("limit must be between 1 and 10")
        if symbol_handle not in self._symbols:
            raise CodeObservationError("symbol handle does not belong to this snapshot")
        binding = [self.snapshot_id, symbol_handle, kind, limit]
        offset = 0
        handles = self._symbols[symbol_handle][kind]
        if cursor is not None:
            try:
                if not isinstance(cursor, str) or len(cursor) > 2048:
                    raise ValueError("invalid cursor size")
                decoded = json.loads(base64.b64decode(cursor, altchars=b"-_", validate=True))
                if not isinstance(decoded, list) or len(decoded) != 5 or decoded[:4] != binding:
                    raise ValueError("cursor binding mismatch")
                offset = decoded[4]
                if type(offset) is not int or not 0 < offset < len(handles) or offset % limit:
                    raise ValueError("cursor offset invalid")
            except (ValueError, TypeError, UnicodeError) as exc:
                raise CodeObservationError("cursor does not match this snapshot/query") from exc
        next_offset = offset + limit
        next_cursor = None
        if next_offset < len(handles):
            next_cursor = base64.urlsafe_b64encode(json.dumps(
                [*binding, next_offset], separators=(",", ":"),
            ).encode()).decode()
        return {
            **self._qualification(), "symbol_handle": symbol_handle, "kind": kind,
            "resolution": self._symbols[symbol_handle]["resolution"],
            "items": [self._compact(self._occurrences[handle])
                      for handle in handles[offset:next_offset]],
            "total": len(handles), "next_cursor": next_cursor,
            "relationship_expansion": "not_applied",
        }
