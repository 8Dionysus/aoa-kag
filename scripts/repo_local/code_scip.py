"""Normalize one complete, caller-captured SCIP workspace in two passes.

Protocol: https://github.com/scip-code/scip/blob/db62094c7f9d464d0a6d9fd7815fcf3c9214b4c2/scip.proto
Provider execution, source capture, admission and proof have stronger owners.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .code_coordinates import CodeObservationError, nonnegative_int, source_path
from .code_observations import (
    SCHEMA_VERSION, CodeWorkspace, canonical_digest, code_handle, source_identity,
)


ADAPTER_VERSION = "scip-workspace-v1"
POSITION_ENCODINGS = {
    1: "utf-8", 2: "utf-16", 3: "utf-32",
    "UTF8CodeUnitOffsetFromLineStart": "utf-8",
    "UTF16CodeUnitOffsetFromLineStart": "utf-16",
    "UTF32CodeUnitOffsetFromLineStart": "utf-32",
}


def _field(value: Mapping[str, Any], camel: str, snake: str, default: Any = None) -> Any:
    if camel in value and snake in value and value[camel] != value[snake]:
        raise CodeObservationError(f"conflicting SCIP field aliases: {camel}")
    return value.get(camel, value.get(snake, default))


def _objects(value: object, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise CodeObservationError(f"{label} must be an array of objects")
    return value


def _range(row: Mapping[str, Any]) -> list[int]:
    single = _field(row, "singleLineRange", "single_line_range")
    multi = _field(row, "multiLineRange", "multi_line_range")
    if single is not None and multi is not None:
        raise CodeObservationError("SCIP range oneof has both alternatives")
    if single is not None:
        if not isinstance(single, Mapping):
            raise CodeObservationError("single-line range must be an object")
        return [single.get("line", 0),
                _field(single, "startCharacter", "start_character", 0),
                _field(single, "endCharacter", "end_character", 0)]
    if multi is not None:
        if not isinstance(multi, Mapping):
            raise CodeObservationError("multi-line range must be an object")
        return [_field(multi, "startLine", "start_line", 0),
                _field(multi, "startCharacter", "start_character", 0),
                _field(multi, "endLine", "end_line", 0),
                _field(multi, "endCharacter", "end_character", 0)]
    return row.get("range")


def normalize_scip_workspace(
    payload: Mapping[str, Any], *, repo: str, source_epoch: str,
    sources: Mapping[str, str | bytes], analysis: Mapping[str, Any],
    default_position_encoding: str | None = None,
) -> CodeWorkspace:
    """Bind native SCIP occurrences to exact source bytes, without executing it.

    ``analysis`` binds the captured indexer's name/version, executable artifact,
    configuration and dependency environment digests. These are evidence, not
    an admission claim. An explicit ABI fallback is mandatory for old indexers
    which omit Document.position_encoding; language is never a fallback.
    """
    if not isinstance(payload, Mapping) or not isinstance(analysis, Mapping):
        raise CodeObservationError("SCIP payload and analysis must be objects")
    required = {"provider", "version", "artifact_sha256", "config_sha256", "environment_sha256"}
    if set(analysis) != required:
        raise CodeObservationError("analysis must bind exact provider, artifact, config and environment")
    for key in ("provider", "version"):
        if not isinstance(analysis[key], str) or not analysis[key].strip():
            raise CodeObservationError(f"analysis {key} is required")
    for key in required - {"provider", "version"}:
        value = analysis[key]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise CodeObservationError(f"analysis {key} must be a SHA-256 digest")
    if default_position_encoding not in {None, "utf-8", "utf-16", "utf-32"}:
        raise CodeObservationError("invalid explicit default position encoding")
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, Mapping):
        raise CodeObservationError("SCIP metadata must be an object")
    tool = _field(metadata, "toolInfo", "tool_info", {})
    if not isinstance(tool, Mapping):
        raise CodeObservationError("SCIP tool info must be an object")
    for native, bound in (("name", "provider"), ("version", "version")):
        if tool.get(native) and tool[native] != analysis[bound]:
            raise CodeObservationError("SCIP tool identity does not match analysis")
    text_encoding = _field(metadata, "textDocumentEncoding", "text_document_encoding", 0)
    if type(text_encoding) not in {int, str} or text_encoding not in {0, 1, "UnspecifiedTextEncoding", "UTF8"}:
        raise CodeObservationError("this adapter requires UTF-8 source files")
    source, blobs = source_identity(repo, source_epoch, sources)
    analysis_identity = {**analysis, "adapter": ADAPTER_VERSION,
                         "default_position_encoding": default_position_encoding}
    analysis_identity["digest"] = canonical_digest(analysis_identity)
    input_digest = canonical_digest(payload)
    context = canonical_digest([source["digest"], analysis_identity["digest"], input_digest])
    documents = _objects(payload.get("documents"), "documents")
    symbols: dict[tuple[str | None, str], dict[str, Any]] = {}
    occurrences: dict[str, dict[str, Any]] = {}
    relations: dict[str, dict[str, Any]] = {}
    indexed_paths: set[str] = set()
    native_count = 0

    def symbol_row(native: object, path: str | None) -> dict[str, Any]:
        if not isinstance(native, str) or not native.strip():
            raise CodeObservationError("SCIP symbol must be a nonempty native key")
        local_path = path if native.startswith("local ") else None
        if native.startswith("local ") and path is None:
            raise CodeObservationError("local symbol cannot escape document scope")
        key = (local_path, native)
        if key not in symbols:
            symbols[key] = {
                "handle": code_handle(repo, "symbol", context, *key),
                "native_symbol": native, "scope_path": local_path,
                "metadata": [], "definitions": [], "references": [],
                "resolution": "unresolved", "external": False,
            }
        return symbols[key]

    def symbol_info(info: Mapping[str, Any], path: str | None) -> None:
        row = symbol_row(info.get("symbol"), path)
        row["external"] |= path is None
        hint = {"path": path, "native": copy.deepcopy(dict(info))}
        if hint not in row["metadata"]:
            row["metadata"].append(hint)
        for relation in _objects(info.get("relationships", []), "relationships"):
            target = symbol_row(relation.get("symbol"), path)
            native = copy.deepcopy(dict(relation))
            handle = code_handle(repo, "relation", context, row["handle"], target["handle"], native)
            relations[handle] = {"handle": handle, "source": row["handle"],
                                 "target": target["handle"], "native": native}

    for info in _objects(_field(payload, "externalSymbols", "external_symbols", []), "external symbols"):
        symbol_info(info, None)
    # Pass one: collect every document's symbol information and occurrence.
    # No requirement for a made-up enclosingSymbol on a reference occurrence.
    for document in documents:
        path = source_path(_field(document, "relativePath", "relative_path"))
        if not isinstance(document.get("language", ""), str):
            raise CodeObservationError("document language must be a string")
        if path in indexed_paths:
            raise CodeObservationError("duplicate SCIP document path")
        indexed_paths.add(path)
        if path not in blobs:
            raise CodeObservationError(f"missing source blob for {path}")
        blob = blobs[path]
        if not isinstance(document.get("text", ""), str):
            raise CodeObservationError("embedded SCIP text must be a string")
        if document.get("text") and document["text"] != blob.text:
            raise CodeObservationError("embedded SCIP text does not match source blob")
        native_encoding = _field(document, "positionEncoding", "position_encoding", 0)
        if type(native_encoding) not in {int, str}:
            raise CodeObservationError("invalid position encoding")
        if native_encoding in {0, "UnspecifiedPositionEncoding"}:
            encoding = default_position_encoding
        else:
            encoding = POSITION_ENCODINGS.get(native_encoding)
        if encoding is None:
            raise CodeObservationError("SCIP position encoding is unspecified or unsupported")
        for info in _objects(document.get("symbols", []), "symbols"):
            symbol_info(info, path)
        for native in _objects(document.get("occurrences", []), "occurrences"):
            native_count += 1
            span = blob.span(_range(native), encoding)
            roles = nonnegative_int(_field(native, "symbolRoles", "symbol_roles", 0), "symbol roles")
            if "symbol" in native and not isinstance(native["symbol"], str):
                raise CodeObservationError("occurrence symbol must be a string")
            symbol = symbol_row(native["symbol"], path) if native.get("symbol") else None
            handle = code_handle(repo, "occurrence", context, path, dict(native))
            occurrences[handle] = {
                "handle": handle, "path": path, "source_sha256": source["manifest"][path],
                "language": document.get("language", ""), "range": span,
                "symbol_handle": symbol["handle"] if symbol else None,
                "role": "highlight" if symbol is None else ("definition" if roles & 1 else "reference"),
                "native": copy.deepcopy(dict(native)),
            }
    # Pass two: join occurrences against the whole workspace, never display names.
    by_handle = {row["handle"]: row for row in symbols.values()}
    ordered_occurrences = sorted(occurrences.values(), key=lambda row: (
        row["path"], row["range"]["start_byte"], row["range"]["end_byte"], row["handle"],
    ))
    for occurrence in ordered_occurrences:
        if occurrence["symbol_handle"] is not None:
            row = by_handle[occurrence["symbol_handle"]]
            row["definitions" if occurrence["role"] == "definition" else "references"].append(occurrence["handle"])
    for row in symbols.values():
        row["metadata"].sort(key=canonical_digest)
        row["resolution"] = ("multiple_definitions" if len(row["definitions"]) > 1 else
                             "workspace" if row["definitions"] else
                             "external" if row["external"] else "unresolved")
    return CodeWorkspace({
        "schema_version": SCHEMA_VERSION, "source": source, "analysis": analysis_identity,
        "provenance": {"format": "SCIP", "input_sha256": input_digest,
                       "metadata": copy.deepcopy(dict(metadata))},
        "coverage": {"scope": "supplied_index_only", "indexed_paths": sorted(indexed_paths),
                     "unindexed_paths": sorted(set(blobs) - indexed_paths),
                     "native_occurrences": native_count, "retained_occurrences": len(occurrences),
                     "deduplicated_occurrences": native_count - len(occurrences),
                     "unresolved_symbols": sum(row["resolution"] == "unresolved" for row in symbols.values())},
        "symbols": sorted(symbols.values(), key=lambda row: row["handle"]),
        "occurrences": ordered_occurrences,
        "relations": sorted(relations.values(), key=lambda row: row["handle"]),
    })
