from __future__ import annotations

import ast
import hashlib
import json
import posixpath
import re
from pathlib import PurePosixPath
from typing import Any, Mapping
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
CAPABILITY_ID_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
# The shared capability-home projector enriches skill and mode nodes with
# owner-layer bindings. These fields are source-linked projection metadata,
# not KAG node semantics; KAG intentionally does not project or trust them as
# replacements for authored family fields.
CAPABILITY_GRAPH_DERIVED_FIELDS_BY_KIND = {
    "skill": frozenset({"owner_contract", "owner_contract_ref", "package"}),
    "mode": frozenset({"mode_contract", "owner_contract_ref"}),
}


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
    source_path: str = "",
    parser: str,
) -> dict[str, Any]:
    key = f"{source_id}:{kind}:{semantic_key}"
    anchor = {
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
    if source_path:
        anchor["source_path"] = source_path
    return anchor


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


def validate_capability_graph_against_sources(
    payload: Mapping[str, Any],
    authored_sources: Mapping[str, bytes],
) -> None:
    """Fail closed unless a derived graph agrees with authored family files."""

    if (
        payload.get("schema_version") != CAPABILITY_GRAPH_SCHEMA_VERSION
        or payload.get("authority") is not False
    ):
        return

    issues: list[str] = []
    source = payload.get("source")
    nodes = payload.get("nodes")
    relations = payload.get("relations")
    if not authored_sources:
        issues.append("authored family source snapshot is missing")
    if not isinstance(source, Mapping):
        issues.append("source must be an object")
    if not isinstance(nodes, list):
        issues.append("nodes must be an array")
    if not isinstance(relations, list):
        issues.append("relations must be an array")
    if issues:
        raise ValueError("capability graph validation failed: " + "; ".join(issues))

    declared_family_files = source.get("family_files")
    declared_by_path: dict[str, str] = {}
    if not isinstance(declared_family_files, list) or not declared_family_files:
        issues.append("source.family_files must be a non-empty array")
    else:
        for index, raw_file in enumerate(declared_family_files):
            if not isinstance(raw_file, Mapping):
                issues.append(f"source.family_files[{index}] must be an object")
                continue
            path = raw_file.get("path")
            digest = raw_file.get("sha256")
            if not isinstance(path, str) or not path:
                issues.append(f"source.family_files[{index}].path is invalid")
                continue
            if path in declared_by_path:
                issues.append(f"source.family_files contains duplicate path {path!r}")
                continue
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                issues.append(f"source.family_files[{index}].sha256 is invalid")
                continue
            declared_by_path[path] = digest

    expected_paths = set(authored_sources)
    if set(declared_by_path) != expected_paths:
        issues.append(
            "source.family_files paths do not match the resolved authored sources: "
            f"declared={sorted(declared_by_path)}, expected={sorted(expected_paths)}"
        )
    for path, content in authored_sources.items():
        actual_digest = hashlib.sha256(content).hexdigest()
        if declared_by_path.get(path) != actual_digest:
            issues.append(
                f"source.family_files digest mismatch for {path}: "
                f"declared={declared_by_path.get(path)!r}, actual={actual_digest!r}"
            )

    try:
        import yaml
    except ModuleNotFoundError as exc:  # pragma: no cover - repository dependency
        raise RuntimeError(
            "PyYAML is required to validate capability graph sources"
        ) from exc

    authored_nodes: dict[str, tuple[str, Mapping[str, Any], str | None]] = {}
    authored_relations: list[tuple[str, Mapping[str, Any]]] = []
    for path, content in authored_sources.items():
        try:
            family = yaml.safe_load(content.decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            issues.append(f"authored family {path} is not valid UTF-8 YAML: {exc}")
            continue
        if not isinstance(family, Mapping):
            issues.append(f"authored family {path} must be an object")
            continue
        family_id = family.get("family_id", family.get("family"))
        family_id_value = family_id if isinstance(family_id, str) else None
        family_nodes = family.get("nodes")
        if not isinstance(family_nodes, list):
            issues.append(f"authored family {path}.nodes must be an array")
        else:
            for index, raw_node in enumerate(family_nodes):
                if not isinstance(raw_node, Mapping):
                    issues.append(f"authored family {path}.nodes[{index}] must be an object")
                    continue
                node_id = raw_node.get("id")
                if not isinstance(node_id, str) or not CAPABILITY_ID_RE.fullmatch(node_id):
                    issues.append(f"authored family {path}.nodes[{index}].id is invalid")
                    continue
                if node_id in authored_nodes:
                    issues.append(
                        f"authored capability node {node_id!r} appears in both "
                        f"{authored_nodes[node_id][0]} and {path}"
                    )
                    continue
                authored_nodes[node_id] = (path, raw_node, family_id_value)
        family_relations = family.get("relations", [])
        if not isinstance(family_relations, list):
            issues.append(f"authored family {path}.relations must be an array")
            continue
        for index, raw_relation in enumerate(family_relations):
            if not isinstance(raw_relation, Mapping):
                issues.append(
                    f"authored family {path}.relations[{index}] must be an object"
                )
                continue
            if not all(
                isinstance(raw_relation.get(key), str) and raw_relation.get(key)
                for key in ("kind", "source", "target")
            ):
                issues.append(
                    f"authored family {path}.relations[{index}] lacks kind/source/target"
                )
                continue
            authored_relations.append((path, raw_relation))

    graph_nodes: dict[str, Mapping[str, Any]] = {}
    for index, raw_node in enumerate(nodes):
        if not isinstance(raw_node, Mapping):
            issues.append(f"graph nodes[{index}] must be an object")
            continue
        node_kind = raw_node.get("kind")
        if not isinstance(node_kind, str) or not node_kind:
            issues.append(f"graph nodes[{index}].kind is required")
        node_id = raw_node.get("id")
        if not isinstance(node_id, str) or not CAPABILITY_ID_RE.fullmatch(node_id):
            issues.append(f"graph nodes[{index}].id is invalid")
            continue
        if node_id in graph_nodes:
            issues.append(f"graph contains duplicate node {node_id!r}")
            continue
        graph_nodes[node_id] = raw_node

    if set(graph_nodes) != set(authored_nodes):
        issues.append(
            "graph node IDs do not match authored family nodes: "
            f"graph_only={sorted(set(graph_nodes) - set(authored_nodes))}, "
            f"authored_only={sorted(set(authored_nodes) - set(graph_nodes))}"
        )

    for node_id, (authored_path, authored_node, family_id) in authored_nodes.items():
        graph_node = graph_nodes.get(node_id)
        if graph_node is None:
            continue
        graph_path = graph_node.get("source_path")
        if graph_path != authored_path:
            issues.append(
                f"graph node {node_id!r} source_path {graph_path!r} does not match "
                f"authored family {authored_path!r}"
            )
        if family_id is not None and graph_node.get("source_family") != family_id:
            issues.append(
                f"graph node {node_id!r} source_family {graph_node.get('source_family')!r} "
                f"does not match authored family_id {family_id!r}"
            )
        authored_keys = set(authored_node)
        graph_keys = set(graph_node)
        derived_keys = CAPABILITY_GRAPH_DERIVED_FIELDS_BY_KIND.get(
            str(graph_node.get("kind")),
            frozenset(),
        )
        extra_keys = sorted(
            graph_keys
            - authored_keys
            - {"source_family", "source_path"}
            - derived_keys
        )
        if extra_keys:
            issues.append(
                f"graph node {node_id!r} contains unauthored fields: {extra_keys}"
            )
        missing_keys = sorted(
            authored_keys - graph_keys - {"source_family", "source_path"}
        )
        if missing_keys:
            issues.append(
                f"graph node {node_id!r} omits authored fields: {missing_keys}"
            )
        for key, value in authored_node.items():
            if key in {"source_family", "source_path"}:
                continue
            if key not in graph_node or graph_node[key] != value:
                issues.append(
                    f"graph node {node_id!r} field {key!r} does not match authored source"
                )

    matched_relations: set[int] = set()
    graph_primary_parent: set[tuple[str, str, str]] = set()
    for index, raw_relation in enumerate(relations):
        if not isinstance(raw_relation, Mapping):
            issues.append(f"graph relations[{index}] must be an object")
            continue
        kind = raw_relation.get("kind")
        source_id = raw_relation.get("source")
        target_id = raw_relation.get("target")
        source_path = raw_relation.get("source_path")
        if not all(
            isinstance(value, str) and value
            for value in (kind, source_id, target_id, source_path)
        ):
            issues.append(
                f"graph relations[{index}] lacks kind/source/target/source_path"
            )
            continue
        if source_id not in authored_nodes or target_id not in authored_nodes:
            issues.append(
                f"graph relation {kind!r} {source_id!r}->{target_id!r} "
                "references an unauthored node"
            )
        if source_path not in expected_paths:
            issues.append(
                f"graph relation {kind!r} {source_id!r}->{target_id!r} "
                f"has an unauthored source_path {source_path!r}"
            )
        duplicate_primary_parent = False
        if kind == "primary-parent":
            relation_key = (source_id, target_id, source_path)
            duplicate_primary_parent = relation_key in graph_primary_parent
            if relation_key in graph_primary_parent:
                issues.append(
                    "graph contains duplicate primary-parent relation "
                    f"{source_id!r}->{target_id!r} ({source_path})"
                )
            graph_primary_parent.add(relation_key)

        graph_keys = set(raw_relation)
        authored_candidates = [
            (relation_index, authored_relation)
            for relation_index, (authored_path, authored_relation) in enumerate(
                authored_relations
            )
            if authored_path == source_path
            and all(
                raw_relation.get(key) == authored_relation.get(key)
                for key in ("kind", "source", "target")
            )
        ]
        matched = False
        for relation_index, authored_relation in authored_candidates:
            if relation_index in matched_relations:
                continue
            expected_relation = dict(authored_relation)
            expected_relation["source_path"] = source_path
            if all(
                raw_relation.get(key) == value
                for key, value in expected_relation.items()
            ) and set(raw_relation) == set(expected_relation):
                matched_relations.add(relation_index)
                matched = True
                break
        if matched:
            continue

        allowed_keys = (
            set(authored_candidates[0][1]) | {"source_path"}
            if authored_candidates
            else {"kind", "source", "target", "source_path"}
        )
        extra_keys = sorted(graph_keys - allowed_keys)
        if extra_keys:
            issues.append(
                "graph relation "
                f"{kind!r} {source_id!r}->{target_id!r} contains "
                f"unauthored fields: {extra_keys}"
            )

        if (
            kind == "primary-parent"
            and source_id in graph_nodes
            and not duplicate_primary_parent
        ):
            if (
                graph_nodes[source_id].get("primary_parent") == target_id
                and graph_nodes[source_id].get("source_path") == source_path
                and graph_keys == {"kind", "source", "target", "source_path"}
            ):
                continue
        issues.append(
            f"graph relation {kind!r} {source_id!r}->{target_id!r} "
            "does not match an authored relation"
        )

    for relation_index, (authored_path, authored_relation) in enumerate(authored_relations):
        if relation_index not in matched_relations:
            issues.append(
                "authored relation is absent from graph: "
                f"{authored_relation.get('kind')!r} "
                f"{authored_relation.get('source')!r}->{authored_relation.get('target')!r} "
                f"({authored_path})"
            )

    for node_id, (authored_path, authored_node, _) in authored_nodes.items():
        parent = authored_node.get("primary_parent")
        if isinstance(parent, str) and (node_id, parent, authored_path) not in graph_primary_parent:
            issues.append(
                f"authored primary_parent for {node_id!r} is absent from graph"
            )

    if all(
        isinstance(authored_node, Mapping) and "primary_parent" in authored_node
        for _, authored_node, _ in authored_nodes.values()
    ):
        expected_roots = sorted(
            node_id
            for node_id, (_, authored_node, _) in authored_nodes.items()
            if authored_node.get("primary_parent") is None
        )
        actual_roots = payload.get("roots")
        actual_roots_sorted = sorted(actual_roots) if isinstance(actual_roots, list) else None
        if actual_roots_sorted != expected_roots:
            issues.append(
                f"graph roots {actual_roots!r} do not match authored roots {expected_roots!r}"
            )

    if issues:
        raise ValueError("capability graph validation failed: " + "; ".join(issues))


def _capability_graph_structure(
    repo: str,
    source_id: str,
    payload: dict[str, Any],
    *,
    authored_sources: Mapping[str, bytes] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if payload.get("schema_version") != CAPABILITY_GRAPH_SCHEMA_VERSION:
        raise ValueError("selected capability graph has an invalid schema_version")
    if payload.get("authority") is not False:
        raise ValueError("selected capability graph must declare authority=false")
    validate_capability_graph_against_sources(payload, authored_sources or {})

    anchors: list[dict[str, Any]] = []
    outbound: list[dict[str, Any]] = []
    nodes = payload.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("capability graph nodes must be an array")
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError(f"capability graph nodes[{index}] must be an object")
        node_id = node.get("id")
        node_kind = node.get("kind")
        if not isinstance(node_id, str) or not CAPABILITY_ID_RE.fullmatch(node_id):
            raise ValueError(f"capability graph nodes[{index}].id is invalid")
        if not isinstance(node_kind, str) or not node_kind:
            raise ValueError(f"capability graph nodes[{index}].kind is required")
        pointer = f"/nodes/{index}"
        source_path = node.get("source_path")
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
                source_path=(source_path if isinstance(source_path, str) else ""),
                parser="aoa-capability-graph",
            )
        )

    relations = payload.get("relations")
    if not isinstance(relations, list):
        raise ValueError("capability graph relations must be an array")
    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            raise ValueError(f"capability graph relations[{index}] must be an object")
        relation_kind = relation.get("kind")
        source = relation.get("source")
        target = relation.get("target")
        if not all(
            isinstance(value, str) and value
            for value in (relation_kind, source, target)
        ):
            raise ValueError(
                f"capability graph relations[{index}] lacks kind/source/target"
            )
        pointer = f"/relations/{index}"
        source_path = relation.get("source_path")
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
            source_path=(source_path if isinstance(source_path, str) else ""),
            parser="aoa-capability-graph",
        )
        anchors.append(relation_anchor)
        reference = {
            "relation_kind": relation_kind,
            "source_anchor_id": relation_anchor["id"],
            "source_context": f"capability:{source}",
            "target_ref": f"capability:{target}",
            "evidence_class": "declared",
        }
        if isinstance(source_path, str) and source_path:
            reference["source_path"] = source_path
        outbound.append(reference)
    return anchors, outbound


def _json_structure(
    repo: str,
    source_id: str,
    text: str,
    *,
    enable_capability_graph: bool,
    capability_graph_sources: Mapping[str, bytes] | None,
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
    if enable_capability_graph:
        capability_anchors, capability_outbound = _capability_graph_structure(
            repo,
            source_id,
            payload,
            authored_sources=capability_graph_sources,
        )
        anchors.extend(capability_anchors)
        return anchors, capability_outbound
    return anchors, []


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
    enable_capability_graph: bool = False,
    capability_graph_sources: Mapping[str, bytes] | None = None,
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
        extracted, references = _json_structure(
            repo,
            source_id,
            text,
            enable_capability_graph=enable_capability_graph,
            capability_graph_sources=capability_graph_sources,
        )
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
