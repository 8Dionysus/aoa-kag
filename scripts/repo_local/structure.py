from __future__ import annotations

import ast
import json
import posixpath
import re
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

from .identity import qualified_id


ATX_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
MARKDOWN_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
YAML_KEY = re.compile(
    r"^(?P<key>(?:\"[^\"]+\"|'[^']+'|[^:#][^:]*?))[ \t]*:(?P<value>.*)$"
)
TOML_TABLE = re.compile(r"^[ \t]*\[\[?(?P<name>[^\]]+)\]\]?[ \t]*(?:#.*)?$")
TOML_KEY = re.compile(r"^[ \t]*(?P<key>[A-Za-z0-9_.-]+)[ \t]*=")
CAPABILITY_GRAPH_SCHEMA_VERSION = "aoa-capability-graph-v1"


def _anchor(
    *,
    repo: str,
    source_id: str,
    kind: str,
    semantic_key: str,
    label: str,
    line: int,
    end_line: int | None = None,
    column: int = 1,
    end_column: int | None = None,
    fragment: str = "",
    pointer: str = "",
    symbol_kind: str = "",
    qualified_name: str = "",
    parser: str,
) -> dict[str, Any]:
    key = f"{source_id}:{kind}:{semantic_key}"
    return {
        "id": qualified_id(repo, "anchor", key),
        "anchor_kind": kind,
        "semantic_key": semantic_key,
        "label": label,
        "locator": {
            "start_line": max(line, 1),
            "end_line": max(end_line or line, line, 1),
            "start_column": max(column, 1),
            "end_column": max(end_column or column, column, 1),
            "fragment": fragment,
            "pointer": pointer,
        },
        "symbol_kind": symbol_kind,
        "qualified_name": qualified_name,
        "parser": {"name": parser, "version": "1"},
    }


def _artifact_anchor(repo: str, source_id: str) -> dict[str, Any]:
    return _anchor(
        repo=repo,
        source_id=source_id,
        kind="artifact",
        semantic_key="$artifact",
        label="$artifact",
        line=1,
        parser="aoa-artifact",
    )


def _occurrence_key(base: str, counts: dict[str, int]) -> str:
    occurrence = counts.get(base, 0) + 1
    counts[base] = occurrence
    return base if occurrence == 1 else f"{base}#occurrence-{occurrence}"


def _visible_markdown_lines(text: str) -> list[tuple[int, str]]:
    visible: list[tuple[int, str]] = []
    fenced = False
    fence_marker = ""
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not fenced:
                fenced = True
                fence_marker = marker
            elif marker == fence_marker:
                fenced = False
            continue
        if not fenced:
            visible.append((line_number, line))
    return visible


def markdown_headings(text: str) -> list[dict[str, int | str]]:
    headings: list[dict[str, int | str]] = []
    counts: dict[str, int] = {}
    for line_number, line in _visible_markdown_lines(text):
        match = ATX_HEADING.match(line)
        if not match:
            continue
        title = match.group(2).strip()
        base = re.sub(
            r"-+",
            "-",
            re.sub(r"[^\w\s-]", "", title.lower()).replace(" ", "-"),
        ).strip("-")
        if not base:
            continue
        occurrence = counts.get(base, 0)
        counts[base] = occurrence + 1
        headings.append(
            {
                "level": len(match.group(1)),
                "title": title,
                "fragment": base if occurrence == 0 else f"{base}-{occurrence}",
                "line": line_number,
                "end_column": max(len(line), 1),
            }
        )
    return headings


def _markdown_structure(
    repo: str,
    source_id: str,
    text: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    anchors: list[dict[str, Any]] = []
    outbound: list[dict[str, Any]] = []
    headings_by_line = {int(item["line"]): item for item in markdown_headings(text)}
    current_context = "$artifact"
    for line_number, line in _visible_markdown_lines(text):
        heading = headings_by_line.get(line_number)
        if heading:
            fragment = str(heading["fragment"])
            current_context = f"heading:{fragment}"
            anchors.append(
                _anchor(
                    repo=repo,
                    source_id=source_id,
                    kind="markdown_heading",
                    semantic_key=current_context,
                    label=str(heading["title"]),
                    line=line_number,
                    end_column=int(heading["end_column"]),
                    fragment=fragment,
                    parser="aoa-markdown",
                )
            )
        for occurrence, match in enumerate(MARKDOWN_LINK.finditer(line)):
            label, target = match.group(1).strip(), match.group(2).strip()
            semantic_key = f"link:{line_number}:{match.start() + 1}:{occurrence}:{target}"
            link_anchor = _anchor(
                repo=repo,
                source_id=source_id,
                kind="markdown_link",
                semantic_key=semantic_key,
                label=label or target,
                line=line_number,
                column=match.start() + 1,
                end_column=match.end() + 1,
                parser="aoa-markdown",
            )
            anchors.append(link_anchor)
            outbound.append(
                {
                    "relation_kind": "references",
                    "source_anchor_id": link_anchor["id"],
                    "source_context": current_context,
                    "target_ref": target,
                    "evidence_class": "deterministic",
                }
            )
    return anchors, outbound


class _PythonVisitor(ast.NodeVisitor):
    def __init__(self, repo: str, source_id: str) -> None:
        self.repo = repo
        self.source_id = source_id
        self.scope: list[str] = []
        self.anchors: list[dict[str, Any]] = []
        self.outbound: list[dict[str, Any]] = []
        self.anchor_by_scope: dict[str, str] = {}
        self.symbol_counts: dict[str, int] = {}

    def _symbol(self, node: ast.AST, name: str, symbol_kind: str) -> None:
        qualified_name = ".".join((*self.scope, name))
        semantic_key = _occurrence_key(
            f"python:{symbol_kind}:{qualified_name}",
            self.symbol_counts,
        )
        anchor = _anchor(
            repo=self.repo,
            source_id=self.source_id,
            kind="python_symbol",
            semantic_key=semantic_key,
            label=name,
            line=int(getattr(node, "lineno", 1)),
            end_line=int(getattr(node, "end_lineno", getattr(node, "lineno", 1))),
            column=int(getattr(node, "col_offset", 0)) + 1,
            end_column=int(getattr(node, "end_col_offset", getattr(node, "col_offset", 0))) + 1,
            symbol_kind=symbol_kind,
            qualified_name=qualified_name,
            parser="python-ast",
        )
        self.anchors.append(anchor)
        self.anchor_by_scope[qualified_name] = anchor["id"]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._symbol(node, node.name, "class")
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node, "method" if self.scope else "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node, "method" if self.scope else "function")

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, kind: str) -> None:
        self._symbol(node, node.name, kind)
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_Call(self, node: ast.Call) -> None:
        target = _python_name(node.func)
        if target:
            context = ".".join(self.scope)
            source_anchor_id = self.anchor_by_scope.get(context)
            if source_anchor_id:
                self.outbound.append(
                    {
                        "relation_kind": "calls",
                        "source_anchor_id": source_anchor_id,
                        "source_context": f"python:{context}",
                        "target_ref": f"python:{target}",
                        "evidence_class": "deterministic",
                    }
                )
        self.generic_visit(node)


def _python_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _python_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else ""
    return ""


def _python_structure(
    repo: str,
    source_id: str,
    text: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return [], []
    visitor = _PythonVisitor(repo, source_id)
    visitor.visit(tree)
    return visitor.anchors, visitor.outbound


def _json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _capability_graph_structure(
    repo: str,
    source_id: str,
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if (
        payload.get("schema_version") != CAPABILITY_GRAPH_SCHEMA_VERSION
        or payload.get("authority") is not False
    ):
        return [], []

    anchors: list[dict[str, Any]] = []
    outbound: list[dict[str, Any]] = []
    nodes = payload.get("nodes")
    for index, node in enumerate(nodes if isinstance(nodes, list) else []):
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        node_kind = node.get("kind")
        if not isinstance(node_id, str) or not node_id:
            continue
        if not isinstance(node_kind, str) or not node_kind:
            continue
        pointer = f"/nodes/{index}"
        anchors.append(
            _anchor(
                repo=repo,
                source_id=source_id,
                kind="json_pointer",
                semantic_key=f"json:{pointer}",
                label=str(node.get("title") or node_id),
                line=1,
                pointer=pointer,
                symbol_kind=f"capability_graph_node:{node_kind}",
                qualified_name=node_id,
                parser="aoa-capability-graph",
            )
        )

    relations = payload.get("relations")
    for index, relation in enumerate(
        relations if isinstance(relations, list) else []
    ):
        if not isinstance(relation, dict):
            continue
        relation_kind = relation.get("kind")
        source = relation.get("source")
        target = relation.get("target")
        if not all(
            isinstance(value, str) and value
            for value in (relation_kind, source, target)
        ):
            continue
        pointer = f"/relations/{index}"
        relation_anchor = _anchor(
            repo=repo,
            source_id=source_id,
            kind="json_pointer",
            semantic_key=f"json:{pointer}",
            label=f"{relation_kind}: {source} -> {target}",
            line=1,
            pointer=pointer,
            symbol_kind="capability_graph_relation",
            qualified_name=f"{source} -> {target}",
            parser="aoa-capability-graph",
        )
        anchors.append(relation_anchor)
        outbound.append(
            {
                "relation_kind": relation_kind,
                "source_anchor_id": relation_anchor["id"],
                "source_context": f"capability:{source}",
                "target_ref": f"capability:{target}",
                "evidence_class": "declared",
            }
        )
    return anchors, outbound


def _json_structure(
    repo: str,
    source_id: str,
    text: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [], []
    if not isinstance(payload, dict):
        return [], []
    anchors: list[dict[str, Any]] = []
    for key in payload:
        pointer = f"/{_json_pointer_token(str(key))}"
        anchors.append(
            _anchor(
                repo=repo,
                source_id=source_id,
                kind="json_pointer",
                semantic_key=f"json:{pointer}",
                label=str(key),
                line=1,
                pointer=pointer,
                symbol_kind="schema_definition" if key in {"$defs", "definitions"} else "json_key",
                parser="python-json",
            )
        )
    for container_name in ("$defs", "definitions"):
        definitions = payload.get(container_name)
        if not isinstance(definitions, dict):
            continue
        for key in definitions:
            pointer = f"/{_json_pointer_token(container_name)}/{_json_pointer_token(str(key))}"
            anchors.append(
                _anchor(
                    repo=repo,
                    source_id=source_id,
                    kind="json_pointer",
                    semantic_key=f"json:{pointer}",
                    label=str(key),
                    line=1,
                    pointer=pointer,
                    symbol_kind="schema_definition",
                    qualified_name=str(key),
                    parser="python-json",
                )
            )
    capability_anchors, capability_outbound = _capability_graph_structure(
        repo,
        source_id,
        payload,
    )
    anchors.extend(capability_anchors)
    return anchors, capability_outbound


def _yaml_structure(repo: str, source_id: str, text: str) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    containers: dict[int, tuple[str, ...]] = {}
    sequence_counts: dict[tuple[tuple[str, ...], int], int] = {}
    semantic_counts: dict[str, int] = {}
    block_scalar_indent: int | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if block_scalar_indent is not None:
            if not stripped or indent > block_scalar_indent:
                continue
            block_scalar_indent = None
        if not stripped or stripped.startswith("#"):
            continue
        for level in tuple(containers):
            if level >= indent:
                del containers[level]
        parent = containers[max(containers)] if containers else ()
        item_path: tuple[str, ...] | None = None
        value_text = stripped
        if stripped == "-" or stripped.startswith("- "):
            sequence_key = (parent, indent)
            item_index = sequence_counts.get(sequence_key, 0)
            sequence_counts[sequence_key] = item_index + 1
            item_path = (*parent, str(item_index))
            value_text = stripped[1:].lstrip()
            containers[indent] = item_path
            if not value_text:
                continue
        match = YAML_KEY.match(value_text)
        if match:
            key = match.group("key").strip().strip("\"'")
            value = match.group("value").strip()
            path = (*(item_path or parent), key)
            containers[indent] = path if not value else (item_path or parent)
            if re.fullmatch(r"[|>](?:[1-9][+-]?|[+-][1-9]?|[+-])?", value):
                block_scalar_indent = indent
            label = key
        elif item_path is not None:
            path = item_path
            label = value_text
        else:
            continue
        pointer = "/" + "/".join(_json_pointer_token(item) for item in path)
        semantic_key = _occurrence_key(f"yaml:{pointer}", semantic_counts)
        anchors.append(
            _anchor(
                repo=repo,
                source_id=source_id,
                kind="yaml_path",
                semantic_key=semantic_key,
                label=label,
                line=line_number,
                column=indent + 1,
                end_column=max(len(line), 1),
                pointer=pointer,
                parser="aoa-yaml-path",
            )
        )
    return anchors


def _toml_structure(repo: str, source_id: str, text: str) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    table = ""
    semantic_counts: dict[str, int] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        table_match = TOML_TABLE.match(line)
        if table_match:
            table = table_match.group("name").strip()
            key = _occurrence_key(f"table:{table}", semantic_counts)
            anchors.append(
                _anchor(
                    repo=repo,
                    source_id=source_id,
                    kind="toml_key",
                    semantic_key=key,
                    label=table,
                    line=line_number,
                    end_column=max(len(line), 1),
                    pointer=table,
                    parser="aoa-toml-path",
                )
            )
            continue
        key_match = TOML_KEY.match(line)
        if key_match:
            name = key_match.group("key")
            qualified = f"{table}.{name}" if table else name
            semantic_key = _occurrence_key(f"key:{qualified}", semantic_counts)
            anchors.append(
                _anchor(
                    repo=repo,
                    source_id=source_id,
                    kind="toml_key",
                    semantic_key=semantic_key,
                    label=name,
                    line=line_number,
                    end_column=max(len(line), 1),
                    pointer=qualified,
                    parser="aoa-toml-path",
                )
            )
    return anchors


def extract_structure(
    *,
    repo: str,
    source_id: str,
    path: str,
    mime: str,
    content: bytes,
) -> dict[str, list[dict[str, Any]]]:
    anchors = [_artifact_anchor(repo, source_id)]
    outbound: list[dict[str, Any]] = []
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return {"anchor_refs": anchors, "outbound_refs": outbound}

    if mime == "text/markdown" or path.endswith(".md"):
        extracted, references = _markdown_structure(repo, source_id, text)
        anchors.extend(extracted)
        outbound.extend(references)
    elif mime == "text/x-python" or path.endswith(".py"):
        extracted, references = _python_structure(repo, source_id, text)
        anchors.extend(extracted)
        outbound.extend(references)
    elif mime == "application/json" or path.endswith(".json"):
        extracted, references = _json_structure(repo, source_id, text)
        anchors.extend(extracted)
        outbound.extend(references)
    elif mime == "application/yaml" or path.endswith((".yaml", ".yml")):
        anchors.extend(_yaml_structure(repo, source_id, text))
    elif mime == "application/toml" or path.endswith(".toml"):
        anchors.extend(_toml_structure(repo, source_id, text))

    anchors.sort(key=lambda item: (item["locator"]["start_line"], item["anchor_kind"], item["id"]))
    outbound.sort(key=lambda item: (item["source_anchor_id"], item["target_ref"]))
    return {"anchor_refs": anchors, "outbound_refs": outbound}


def resolve_markdown_target(source_path: str, target_ref: str) -> tuple[str, str] | None:
    parsed = urlsplit(target_ref)
    if parsed.scheme or parsed.netloc:
        return None
    target_path = unquote(parsed.path)
    if not target_path:
        target_path = source_path
    elif target_path.startswith("/"):
        target_path = target_path.lstrip("/")
    else:
        target_path = posixpath.normpath(
            posixpath.join(PurePosixPath(source_path).parent.as_posix(), target_path)
        )
    if target_path.startswith("../"):
        return None
    return target_path, unquote(parsed.fragment)
