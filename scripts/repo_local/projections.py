from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from .federation import RepoKagFederation
from .identity import qualified_id


ZERO_DIGEST = "0" * 64
PROJECTION_LANES = ("exact", "lexical", "vector", "hybrid", "graph")
SEMANTIC_ANCHOR_KINDS = {
    "json_pointer",
    "markdown_heading",
    "python_symbol",
    "toml_key",
    "yaml_path",
}
POINT_NAMESPACE = uuid.UUID("c5f54f63-3aef-50be-bbf7-39e62ad94c6d")


class EmbeddingPort(Protocol):
    profile_id: str
    dimensions: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_digest(payload: dict[str, Any], identity_key: str) -> str:
    material = copy.deepcopy(payload)
    material[identity_key]["content_digest"] = ZERO_DIGEST
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(encoded)


def _verified_source_bytes(repo_root: Path, record: dict[str, Any]) -> bytes:
    identity = record["identity"]
    rel_path = str(identity["path"])
    content: bytes | None = None
    blob_id = str(identity.get("git_blob_id") or "")
    if blob_id:
        try:
            content = subprocess.run(
                ("git", "cat-file", "blob", blob_id),
                cwd=repo_root,
                check=True,
                capture_output=True,
            ).stdout
        except (FileNotFoundError, subprocess.CalledProcessError):
            content = None
    if content is None:
        try:
            content = subprocess.run(
                ("git", "show", f":{rel_path}"),
                cwd=repo_root,
                check=True,
                capture_output=True,
            ).stdout
        except (FileNotFoundError, subprocess.CalledProcessError):
            path = repo_root / rel_path
            content = (
                path.readlink().as_posix().encode("utf-8")
                if path.is_symlink()
                else path.read_bytes()
            )
    expected = str(identity["content_hash"])
    observed = _sha256(content)
    if observed != expected:
        raise ValueError(
            f"source digest drift for {rel_path}: expected {expected}, observed {observed}"
        )
    return content


def _json_pointer_value(text: str, pointer: str) -> Any:
    value: Any = json.loads(text)
    if not pointer:
        return value
    for raw_token in pointer.removeprefix("/").split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(token)]
        elif isinstance(value, dict):
            value = value[token]
        else:
            raise KeyError(pointer)
    return value


def _line_segment(lines: list[str], start_line: int, end_line: int) -> str:
    if not lines:
        return ""
    start = max(min(start_line, len(lines)), 1)
    end = max(min(end_line, len(lines)), start)
    return "".join(lines[start - 1 : end])


def _semantic_segment(
    text: str,
    lines: list[str],
    anchor: dict[str, Any],
    source_anchors: Sequence[dict[str, Any]],
) -> tuple[str, int, int]:
    locator = anchor["locator"]
    start_line = int(locator["start_line"])
    end_line = int(locator["end_line"])
    anchor_kind = str(anchor["anchor_kind"])
    if anchor_kind == "markdown_heading":
        following = [
            int(item["locator"]["start_line"])
            for item in source_anchors
            if item["anchor_kind"] == "markdown_heading"
            and int(item["locator"]["start_line"]) > start_line
        ]
        end_line = min(following) - 1 if following else len(lines)
    elif anchor_kind in {"yaml_path", "toml_key"}:
        start_column = int(locator["start_column"])
        following = [
            int(item["locator"]["start_line"])
            for item in source_anchors
            if item["anchor_kind"] == anchor_kind
            and int(item["locator"]["start_line"]) > start_line
            and int(item["locator"]["start_column"]) <= start_column
        ]
        end_line = min(following) - 1 if following else len(lines)
    if anchor_kind == "json_pointer":
        pointer = str(locator.get("pointer") or "")
        try:
            value = _json_pointer_value(text, pointer)
            rendered = json.dumps(
                {str(anchor["label"]): value},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            return rendered + "\n", start_line, end_line
        except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
    return _line_segment(lines, start_line, end_line), start_line, end_line


def _chunk_text(
    text: str,
    *,
    base_start_line: int,
    max_chunk_chars: int,
    overlap: int,
) -> list[tuple[str, int, int]]:
    if max_chunk_chars < 256:
        raise ValueError("max_chunk_chars must be at least 256")
    if overlap < 0 or overlap >= max_chunk_chars:
        raise ValueError("overlap must be non-negative and smaller than max_chunk_chars")
    chunks: list[tuple[str, int, int]] = []
    cursor = 0
    text_length = len(text)
    while cursor < text_length:
        limit = min(cursor + max_chunk_chars, text_length)
        end = limit
        if limit < text_length:
            floor = cursor + max_chunk_chars // 2
            newline = text.rfind("\n", floor, limit)
            whitespace = text.rfind(" ", floor, limit)
            boundary = max(newline, whitespace)
            if boundary > cursor:
                end = boundary + 1
        raw = text[cursor:end]
        if raw.strip():
            start_line = base_start_line + text.count("\n", 0, cursor)
            end_line = base_start_line + text.count("\n", 0, max(end - 1, cursor))
            chunks.append((raw.strip(), start_line, max(end_line, start_line)))
        if end >= text_length:
            break
        cursor = max(end - overlap, cursor + 1)
    return chunks


def _merged_intervals(intervals: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[list[int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1] + 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def _uncovered_intervals(
    line_count: int,
    covered: Sequence[tuple[int, int]],
) -> list[tuple[int, int]]:
    if line_count <= 0:
        return []
    gaps: list[tuple[int, int]] = []
    cursor = 1
    for start, end in _merged_intervals(covered):
        if cursor < start:
            gaps.append((cursor, start - 1))
        cursor = max(cursor, end + 1)
    if cursor <= line_count:
        gaps.append((cursor, line_count))
    return gaps


def _profile(
    family: Mapping[str, dict[str, Any]],
    node_class: str,
    profile_kind: str,
    profile_ref: str,
) -> dict[str, Any]:
    profile = copy.deepcopy(family[node_class]["profiles"][profile_kind][profile_ref])
    profile["ref"] = profile_ref
    if profile_kind == "provenance":
        extractor_ref = str(profile["extractor_ref"])
        profile["extractor"] = copy.deepcopy(
            family[node_class]["profiles"]["extractors"][extractor_ref]
        )
    return profile


def _retrieval_document(
    *,
    source_index: dict[str, Any],
    family: Mapping[str, dict[str, Any]],
    record: dict[str, Any],
    node: dict[str, Any],
    node_class: str,
    kind: str,
    label: str,
    anchor_ids: Sequence[str],
    locator: dict[str, Any],
    chunk_index: int,
    text: str,
) -> dict[str, Any]:
    repo = str(source_index["repo"]["name"])
    identity = record["identity"]
    source_id = str(identity["id"])
    node_id = str(node["id"])
    text_digest = _sha256(text.encode("utf-8"))
    document_id = qualified_id(
        repo,
        "retrieval-document",
        f"{node_id}:{chunk_index}",
    )
    version_id = qualified_id(
        repo,
        "retrieval-document-version",
        f"{document_id}:{text_digest}",
    )
    provenance_ref = str(node["provenance_ref"])
    temporal_ref = str(node["temporal_ref"])
    trust_ref = str(node["trust_ref"])
    return {
        "id": document_id,
        "version_id": version_id,
        "repo": repo,
        "namespace": str(source_index["repo"]["namespace"]),
        "node_id": node_id,
        "node_class": node_class,
        "kind": kind,
        "label": label,
        "path": str(identity["path"]),
        "locator": copy.deepcopy(locator),
        "chunk_index": chunk_index,
        "text": text,
        "text_digest": text_digest,
        "source_record_ids": [source_id],
        "source_version_ids": [str(identity["version_id"])],
        "anchor_ids": sorted(set(str(item) for item in anchor_ids)),
        "document_role": str(record["document_role"]),
        "surface_state": str(record["surface_state"]),
        "abi": copy.deepcopy(record["abi"]),
        "signs": copy.deepcopy(record["signs"]),
        "provenance": copy.deepcopy(record["provenance"]),
        "freshness": copy.deepcopy(record["freshness"]),
        "access": copy.deepcopy(record["access"]),
        "owner_return_route": copy.deepcopy(record["owner_return_route"]),
        "provenance_ref": provenance_ref,
        "temporal_ref": temporal_ref,
        "trust_ref": trust_ref,
        "profiles": {
            "provenance": _profile(
                family, node_class, "provenance", provenance_ref
            ),
            "temporal": _profile(family, node_class, "temporal", temporal_ref),
            "trust": _profile(family, node_class, "trust", trust_ref),
        },
    }


def build_repo_retrieval_documents(
    repo_root: Path,
    source_index: dict[str, Any],
    family: Mapping[str, dict[str, Any]],
    *,
    max_chunk_chars: int = 1800,
    overlap: int = 180,
) -> list[dict[str, Any]]:
    repo_root = repo_root.resolve()
    anchors_by_source: dict[str, list[dict[str, Any]]] = {}
    for anchor in family["anchor"]["entries"]:
        anchors_by_source.setdefault(str(anchor["source_record_id"]), []).append(anchor)
    artifacts = {
        str(entry["id"]): entry
        for entry in family["artifact"]["entries"]
    }
    documents: list[dict[str, Any]] = []
    for record in source_index["records"]:
        identity = record["identity"]
        source_id = str(identity["id"])
        artifact = artifacts[source_id]
        content = _verified_source_bytes(repo_root, record)
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            continue
        lines = text.splitlines(keepends=True)
        source_anchors = sorted(
            anchors_by_source.get(source_id, []),
            key=lambda item: (
                int(item["locator"]["start_line"]),
                str(item["anchor_kind"]),
                str(item["id"]),
            ),
        )
        semantic_anchors = [
            anchor
            for anchor in source_anchors
            if str(anchor["anchor_kind"]) in SEMANTIC_ANCHOR_KINDS
        ]
        covered: list[tuple[int, int]] = []
        for anchor in semantic_anchors:
            segment, start_line, end_line = _semantic_segment(
                text,
                lines,
                anchor,
                source_anchors,
            )
            if str(anchor["anchor_kind"]) != "json_pointer":
                covered.append((start_line, end_line))
            for chunk_index, (chunk, chunk_start, chunk_end) in enumerate(
                _chunk_text(
                    segment,
                    base_start_line=start_line,
                    max_chunk_chars=max_chunk_chars,
                    overlap=overlap,
                )
            ):
                locator = copy.deepcopy(anchor["locator"])
                locator["start_line"] = chunk_start
                locator["end_line"] = chunk_end
                documents.append(
                    _retrieval_document(
                        source_index=source_index,
                        family=family,
                        record=record,
                        node=anchor,
                        node_class="anchor",
                        kind=str(anchor["anchor_kind"]),
                        label=str(anchor["label"]),
                        anchor_ids=[str(anchor["id"])],
                        locator=locator,
                        chunk_index=chunk_index,
                        text=chunk,
                    )
                )
        artifact_anchor_id = str(artifact["anchor_id"])
        artifact_anchor = next(
            anchor for anchor in source_anchors if str(anchor["id"]) == artifact_anchor_id
        )
        if semantic_anchors and str(identity["mime"]) == "application/json":
            gaps: list[tuple[int, int]] = []
        else:
            gaps = _uncovered_intervals(len(lines), covered)
        artifact_chunk_index = 0
        for gap_start, gap_end in gaps:
            segment = _line_segment(lines, gap_start, gap_end)
            for chunk, chunk_start, chunk_end in _chunk_text(
                segment,
                base_start_line=gap_start,
                max_chunk_chars=max_chunk_chars,
                overlap=overlap,
            ):
                locator = copy.deepcopy(artifact_anchor["locator"])
                locator["start_line"] = chunk_start
                locator["end_line"] = chunk_end
                documents.append(
                    _retrieval_document(
                        source_index=source_index,
                        family=family,
                        record=record,
                        node=artifact,
                        node_class="artifact",
                        kind=str(artifact["artifact_kind"]),
                        label=str(artifact["path"]),
                        anchor_ids=[artifact_anchor_id],
                        locator=locator,
                        chunk_index=artifact_chunk_index,
                        text=chunk,
                    )
                )
                artifact_chunk_index += 1
    documents.sort(
        key=lambda item: (
            item["repo"],
            item["path"],
            item["node_class"],
            item["node_id"],
            item["chunk_index"],
        )
    )
    ids = [str(document["id"]) for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("retrieval document id collision")
    return documents


def _embedding_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "id",
        "model",
        "revision",
        "dimensions",
        "distance",
        "normalization",
        "provider_contract",
    }
    missing = sorted(required - set(profile))
    if missing:
        raise ValueError(f"embedding profile missing fields: {', '.join(missing)}")
    normalized = {key: copy.deepcopy(profile[key]) for key in sorted(required)}
    if not isinstance(normalized["dimensions"], int) or normalized["dimensions"] <= 0:
        raise ValueError("embedding profile dimensions must be a positive integer")
    if normalized["distance"] not in {"cosine", "dot", "euclid", "manhattan"}:
        raise ValueError("unsupported embedding distance")
    if normalized["normalization"] not in {"none", "l2"}:
        raise ValueError("unsupported embedding normalization")
    for key in required - {"dimensions"}:
        if not isinstance(normalized[key], str) or not normalized[key]:
            raise ValueError(f"embedding profile {key} must be a non-empty string")
    return normalized


def build_federated_retrieval_plan(
    owner_roots: Mapping[str, Path],
    bundles: Mapping[str, tuple[dict[str, Any], dict[str, dict[str, Any]]]],
    *,
    embedding_profile: Mapping[str, Any],
    max_chunk_chars: int = 1800,
    overlap: int = 180,
) -> dict[str, Any]:
    if set(owner_roots) != set(bundles):
        raise ValueError("owner roots and bundle owners must match")
    federation = RepoKagFederation(bundles).projection()
    documents: list[dict[str, Any]] = []
    canonical_inputs: list[dict[str, Any]] = []
    for owner in sorted(bundles):
        source, family = bundles[owner]
        documents.extend(
            build_repo_retrieval_documents(
                Path(owner_roots[owner]),
                source,
                family,
                max_chunk_chars=max_chunk_chars,
                overlap=overlap,
            )
        )
        canonical_inputs.append(
            {
                "repo": copy.deepcopy(source["repo"]),
                "source_index_digest": str(source["index_identity"]["content_digest"]),
                "family_digests": {
                    kind: str(payload["index_identity"]["content_digest"])
                    for kind, payload in sorted(family.items())
                },
            }
        )
    documents.sort(key=lambda item: (item["repo"], item["path"], item["id"]))
    node_class_counts = Counter(str(item["node_class"]) for item in documents)
    access_counts = Counter(str(item["access"]["scope"]) for item in documents)
    payload: dict[str, Any] = {
        "schema_version": "aoa-repo-local-kag-retrieval-plan-v1",
        "projection_identity": {
            "local_id": "projection:os-abyss:repo-self-retrieval",
            "content_digest": ZERO_DIGEST,
        },
        "canonical_inputs": canonical_inputs,
        "federation": federation,
        "projection_lanes": list(PROJECTION_LANES),
        "retrieval_profile": {
            "chunking": "semantic-anchor-with-source-gaps-v1",
            "max_chunk_chars": max_chunk_chars,
            "overlap_chars": overlap,
            "source_verification": "sha256-content-digest",
        },
        "embedding_profile": _embedding_profile(embedding_profile),
        "summary": {
            "owner_count": len(canonical_inputs),
            "document_count": len(documents),
            "text_bytes": sum(len(item["text"].encode("utf-8")) for item in documents),
            "node_class_counts": dict(sorted(node_class_counts.items())),
            "access_scope_counts": dict(sorted(access_counts.items())),
        },
        "documents": documents,
    }
    payload["projection_identity"]["content_digest"] = _canonical_digest(
        payload, "projection_identity"
    )
    return payload


def _normalized_vector(vector: Sequence[float], normalization: str) -> list[float]:
    values = [float(item) for item in vector]
    if any(not math.isfinite(item) for item in values):
        raise ValueError("embedding vectors must contain finite numbers")
    if normalization == "l2":
        norm = math.sqrt(sum(item * item for item in values))
        if norm == 0:
            raise ValueError("l2 embedding vector must be non-zero")
        values = [item / norm for item in values]
    return values


def materialize_vector_points(
    plan: Mapping[str, Any],
    embedding_port: EmbeddingPort,
    *,
    batch_size: int = 64,
) -> list[dict[str, Any]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    profile = plan["embedding_profile"]
    if embedding_port.profile_id != profile["id"]:
        raise ValueError("embedding port profile does not match retrieval plan")
    dimensions = int(profile["dimensions"])
    if embedding_port.dimensions != dimensions:
        raise ValueError("embedding port dimensions do not match retrieval plan")
    documents = list(plan["documents"])
    points: list[dict[str, Any]] = []
    for offset in range(0, len(documents), batch_size):
        batch = documents[offset : offset + batch_size]
        vectors = embedding_port.embed([str(item["text"]) for item in batch])
        if len(vectors) != len(batch):
            raise ValueError("embedding port returned a different batch size")
        for document, raw_vector in zip(batch, vectors, strict=True):
            if len(raw_vector) != dimensions:
                raise ValueError("embedding vector dimension mismatch")
            vector = _normalized_vector(raw_vector, str(profile["normalization"]))
            point_id = str(
                uuid.uuid5(
                    POINT_NAMESPACE,
                    f"{document['version_id']}:{profile['id']}",
                )
            )
            points.append(
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "embedding_profile_id": str(profile["id"]),
                        "document_id": str(document["id"]),
                        "document_version_id": str(document["version_id"]),
                        "repo": str(document["repo"]),
                        "namespace": str(document["namespace"]),
                        "node_id": str(document["node_id"]),
                        "node_class": str(document["node_class"]),
                        "kind": str(document["kind"]),
                        "label": str(document["label"]),
                        "path": str(document["path"]),
                        "locator": copy.deepcopy(document["locator"]),
                        "text": str(document["text"]),
                        "text_digest": str(document["text_digest"]),
                        "source_record_ids": copy.deepcopy(document["source_record_ids"]),
                        "source_version_ids": copy.deepcopy(document["source_version_ids"]),
                        "anchor_ids": copy.deepcopy(document["anchor_ids"]),
                        "access": copy.deepcopy(document["access"]),
                        "abi": copy.deepcopy(document["abi"]),
                        "signs": copy.deepcopy(document["signs"]),
                        "provenance_ref": str(document["provenance_ref"]),
                        "temporal_ref": str(document["temporal_ref"]),
                        "trust_ref": str(document["trust_ref"]),
                        "freshness": copy.deepcopy(document["freshness"]),
                    },
                }
            )
    return points
