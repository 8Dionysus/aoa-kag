from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.repo_local.code_scip import normalize_scip_workspace
from scripts.repo_local.code_coordinates import CodeObservationError, SourceText


SYMBOL = "scip-python python example 1 api/Widget#"
EXTERNAL = "scip-python python dependency 2 api/Widget#"
UNRESOLVED = "scip-python python unavailable 3 api/Widget#"
ANALYSIS = {"provider": "scip-python", "version": "fixture-v1",
            "artifact_sha256": "a" * 64, "config_sha256": "b" * 64,
            "environment_sha256": "c" * 64}


def fixture():
    sources = {"api.py": "class Widget: pass\r\n",
               "use.py": "# 🚀\r\nx = Widget()\r\n", "other.py": "other\n"}
    payload = {
        "metadata": {"toolInfo": {"name": "scip-python", "version": "fixture-v1"}},
        "documents": [
            # The reference is deliberately before the other file's definition.
            {"relativePath": "use.py", "language": "python", "positionEncoding": 2,
             "occurrences": [{"range": [1, 4, 10], "symbol": SYMBOL}]},
            {"relativePath": "api.py", "language": "python", "positionEncoding": 2,
             "symbols": [{"symbol": SYMBOL, "displayName": "Widget", "kind": 7}],
             "occurrences": [{"range": [0, 6, 12], "symbol": SYMBOL, "symbolRoles": 1}]},
        ],
    }
    return payload, sources


def build(payload=None, sources=None, **kwargs):
    original, original_sources = fixture()
    return normalize_scip_workspace(
        original if payload is None else payload, repo="example", source_epoch="commit:fixture",
        sources=original_sources if sources is None else sources, analysis=ANALYSIS, **kwargs,
    )


def symbol(workspace, native=SYMBOL, path=None):
    return next(row for row in workspace.to_dict()["symbols"]
                if row["native_symbol"] == native and row["scope_path"] == path)


class CodeWorkspaceTests(unittest.TestCase):
    def test_empty_workspace_accepts_omitted_documents_without_hiding_sources(self):
        sources = {"unindexed.py": "value = 1\n"}
        for payload in ({}, {"documents": []}):
            with self.subTest(payload=payload):
                snapshot = build(payload, sources).to_dict()
                self.assertEqual(snapshot["symbols"], [])
                self.assertEqual(snapshot["occurrences"], [])
                self.assertEqual(snapshot["relations"], [])
                self.assertEqual(snapshot["coverage"], {
                    "scope": "supplied_index_only", "indexed_paths": [],
                    "unindexed_paths": ["unindexed.py"], "native_occurrences": 0,
                    "retained_occurrences": 0, "deduplicated_occurrences": 0,
                    "unresolved_symbols": 0,
                })
        with self.assertRaisesRegex(CodeObservationError, "documents"):
            build({"documents": {}}, sources)

    def test_cross_file_reference_needs_no_enclosing_symbol(self):
        workspace = build()
        row = symbol(workspace)
        self.assertEqual(row["resolution"], "workspace")
        definitions = workspace.query(row["handle"], "definitions")
        references = workspace.query(row["handle"], "references")
        self.assertEqual([hit["path"] for hit in definitions["items"]], ["api.py"])
        self.assertEqual([hit["path"] for hit in references["items"]], ["use.py"])
        self.assertEqual(references["total"], 1)
        self.assertEqual(workspace.to_dict()["relations"], [])  # not a made-up call edge
        hit = references["items"][0]
        self.assertEqual(workspace.read(hit["handle"], source=fixture()[1]["use.py"])["text"], "Widget")

    def test_two_pass_join_does_not_depend_on_document_order(self):
        payload, sources = fixture()
        payload["documents"].reverse()
        row = symbol(build(payload, sources))
        self.assertEqual(row["resolution"], "workspace")
        self.assertEqual((len(row["definitions"]), len(row["references"])), (1, 1))

    def test_native_identity_not_display_name_or_package_name(self):
        payload, sources = fixture()
        payload["externalSymbols"] = [{"symbol": EXTERNAL, "displayName": "Widget"}]
        payload["documents"][0]["occurrences"].extend([
            {"range": [1, 4, 10], "symbol": EXTERNAL},
            {"range": [1, 4, 10], "symbol": UNRESOLVED},
        ])
        workspace = build(payload, sources)
        rows = [symbol(workspace, native) for native in (SYMBOL, EXTERNAL, UNRESOLVED)]
        self.assertEqual(len({row["handle"] for row in rows}), 3)
        self.assertEqual([row["resolution"] for row in rows], ["workspace", "external", "unresolved"])
        self.assertEqual(workspace.to_dict()["coverage"]["unresolved_symbols"], 1)

    def test_local_symbols_are_document_scoped(self):
        payload, sources = fixture()
        for document in payload["documents"]:
            document["symbols"] = []
            document["occurrences"][0]["symbol"] = "local 0"
        workspace = build(payload, sources)
        self.assertNotEqual(symbol(workspace, "local 0", "api.py")["handle"],
                            symbol(workspace, "local 0", "use.py")["handle"])
        self.assertEqual(symbol(workspace, "local 0", "use.py")["resolution"], "unresolved")

    def test_multiple_definitions_remain_explicit(self):
        payload, sources = fixture()
        payload["documents"][0]["occurrences"][0]["symbolRoles"] = 1
        row = symbol(build(payload, sources))
        self.assertEqual(row["resolution"], "multiple_definitions")
        self.assertEqual(len(row["definitions"]), 2)

    def test_metadata_is_not_a_definition(self):
        payload, sources = fixture()
        payload["documents"][1]["occurrences"] = []
        self.assertEqual(symbol(build(payload, sources))["resolution"], "unresolved")

    def test_symbol_relationships_and_highlighting_are_preserved(self):
        payload, sources = fixture()
        payload["documents"][1]["symbols"][0]["relationships"] = [
            {"symbol": EXTERNAL, "isImplementation": True, "isReference": False}]
        payload["documents"][0]["occurrences"].append({"range": [0, 0, 4], "syntaxKind": 1})
        batch = build(payload, sources).to_dict()
        self.assertEqual(batch["relations"][0]["native"]["isImplementation"], True)
        self.assertEqual(sum(row["role"] == "highlight" for row in batch["occurrences"]), 1)
        self.assertIsNone(next(row for row in batch["occurrences"] if row["role"] == "highlight")["symbol_handle"])

    def test_typed_range_has_precedence_and_proto_defaults(self):
        payload, sources = fixture()
        reference = payload["documents"][0]["occurrences"][0]
        reference["range"] = [999, 999, 999]
        reference["singleLineRange"] = {"line": 1, "startCharacter": 4, "endCharacter": 10}
        workspace = build(payload, sources)
        hit = workspace.query(symbol(workspace)["handle"], "references")["items"][0]
        self.assertEqual(workspace.read(hit["handle"], source=sources["use.py"])["text"], "Widget")
        reference["singleLineRange"] = {"endCharacter": 1}
        self.assertEqual(build(payload, sources).to_dict()["coverage"]["retained_occurrences"], 2)

    def test_unspecified_encoding_requires_bound_explicit_fallback(self):
        payload, sources = fixture()
        del payload["documents"][0]["positionEncoding"]
        with self.assertRaisesRegex(CodeObservationError, "encoding"):
            build(payload, sources)
        workspace = build(payload, sources, default_position_encoding="utf-16")
        self.assertEqual(workspace.to_dict()["analysis"]["default_position_encoding"], "utf-16")

    def test_invalid_source_and_native_inputs_fail_closed(self):
        mutations = [
            lambda p: p["documents"][0].update(relativePath="../use.py"),
            lambda p: p["documents"][0].update(relativePath="/use.py"),
            lambda p: p["documents"][0].update(relativePath="use//file.py"),
            lambda p: p["documents"][0].update(relativePath="absent.py"),
            lambda p: p["documents"].append(copy.deepcopy(p["documents"][0])),
            lambda p: p["documents"][0].update(text="different bytes"),
            lambda p: p["documents"][0].update(text=False),
            lambda p: p["documents"][0].update(positionEncoding=999),
            lambda p: p["documents"][0].update(positionEncoding=True),
            lambda p: p["metadata"]["toolInfo"].update(version="other version"),
            lambda p: p["metadata"].update(textDocumentEncoding="UTF16"),
            lambda p: p["metadata"].update(textDocumentEncoding=[]),
            lambda p: p["metadata"].update(textDocumentEncoding=1.0),
            lambda p: p.update(externalSymbols=[{"symbol": "local 0"}]),
            lambda p: p["documents"][0]["occurrences"][0].update(symbolRoles=True),
            lambda p: p["documents"][0]["occurrences"][0].update(symbol=0),
            lambda p: p["documents"][0]["occurrences"][0].update(range=[1, 10, 4]),
            lambda p: p["documents"][0]["occurrences"][0].update(range=[1, 4, 99]),
            lambda p: p["documents"][0]["occurrences"][0].update(range=[0, 3, 4]),  # inside surrogate
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(CodeObservationError):
                payload, sources = fixture()
                mutate(payload)
                build(payload, sources)

    def test_snake_case_proto_json_and_zero_roles(self):
        payload, sources = fixture()
        document = payload["documents"][0]
        document["relative_path"] = document.pop("relativePath")
        document["position_encoding"] = document.pop("positionEncoding")
        document["occurrences"][0]["symbol_roles"] = 0
        self.assertEqual(len(symbol(build(payload, sources))["references"]), 1)
        document["relativePath"] = "other.py"
        with self.assertRaisesRegex(CodeObservationError, "aliases"):
            build(payload, sources)

    def test_exact_source_and_analysis_identity(self):
        before = build()
        _, sources = fixture()
        sources["other.py"] += "# changed resolver context\n"
        after = build(sources=sources)
        self.assertNotEqual(before.snapshot_id, after.snapshot_id)
        self.assertNotEqual(symbol(before)["handle"], symbol(after)["handle"])
        reference = before.query(symbol(before)["handle"], "references")["items"][0]
        with self.assertRaisesRegex(CodeObservationError, "source bytes"):
            before.read(reference["handle"], source="different")
        with self.assertRaisesRegex(CodeObservationError, "snapshot"):
            after.read(reference["handle"])
        payload = before.to_dict()
        payload["symbols"].clear()
        self.assertTrue(before.to_dict()["symbols"])
        self.assertEqual(before.snapshot_id, build().snapshot_id)

    def test_duplicate_aliases_preserve_json_type_distinctions(self):
        mutations = [
            lambda d: d.update(position_encoding=2.0),
            lambda d: d.update(positionEncoding=1, position_encoding=True),
            lambda d: d["occurrences"][0].update(symbolRoles=0, symbol_roles=False),
            lambda d: d["occurrences"][0].update(
                singleLineRange={"line": 1, "startCharacter": 4, "endCharacter": 10},
                single_line_range={"line": 1.0, "startCharacter": 4, "endCharacter": 10}),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index), self.assertRaisesRegex(CodeObservationError, "aliases"):
                payload, sources = fixture()
                mutate(payload["documents"][0])
                build(payload, sources)
        payload, sources = fixture()
        payload["documents"][0]["position_encoding"] = 2
        self.assertEqual(len(symbol(build(payload, sources))["references"]), 1)

    def test_analysis_change_does_not_masquerade_as_source_change(self):
        payload, sources = fixture()
        before = build()
        analysis = {**ANALYSIS, "config_sha256": "d" * 64}
        after = normalize_scip_workspace(payload, repo="example", source_epoch="commit:fixture",
                                         sources=sources, analysis=analysis)
        self.assertEqual(before.to_dict()["source"], after.to_dict()["source"])
        self.assertNotEqual(before.to_dict()["analysis"]["digest"], after.to_dict()["analysis"]["digest"])
        self.assertNotEqual(before.snapshot_id, after.snapshot_id)
        self.assertNotEqual(symbol(before)["handle"], symbol(after)["handle"])

    def test_identical_occurrences_are_deduplicated_with_visible_coverage(self):
        payload, sources = fixture()
        document = payload["documents"][0]
        document["occurrences"].append(copy.deepcopy(document["occurrences"][0]))
        workspace = build(payload, sources)
        coverage = workspace.to_dict()["coverage"]
        self.assertEqual((coverage["native_occurrences"], coverage["retained_occurrences"],
                          coverage["deduplicated_occurrences"]), (3, 2, 1))
        self.assertEqual(coverage["unindexed_paths"], ["other.py"])
        self.assertEqual(len(symbol(workspace)["references"]), 1)

    def test_source_reads_are_bounded_and_return_detached_records(self):
        workspace = build()
        handle = workspace.query(symbol(workspace)["handle"], "references")["items"][0]["handle"]
        result = workspace.read(handle, source=fixture()[1]["use.py"], max_chars=3)
        self.assertEqual((result["text"], result["truncated"]), ("Wid", True))
        result["record"]["range"]["start_byte"] = 999
        self.assertNotEqual(workspace.read(handle)["record"]["range"]["start_byte"], 999)
        for maximum in (False, 0, 4097):
            with self.assertRaises(CodeObservationError):
                workspace.read(handle, max_chars=maximum)
        with self.assertRaises(CodeObservationError):
            workspace.read(symbol(workspace)["handle"], source=fixture()[1]["use.py"])

    def test_bounded_cursor_is_bound_to_snapshot_symbol_kind_and_limit(self):
        payload, sources = fixture()
        sources["use.py"] = "\n".join("Widget" for _ in range(23))
        payload["documents"][0]["occurrences"] = [
            {"range": [line, 0, 6], "symbol": SYMBOL} for line in range(23)]
        workspace = build(payload, sources)
        handle = symbol(workspace)["handle"]
        first = workspace.query(handle, "references")
        second = workspace.query(handle, "references", cursor=first["next_cursor"])
        third = workspace.query(handle, "references", cursor=second["next_cursor"])
        self.assertEqual([len(page["items"]) for page in (first, second, third)], [10, 10, 3])
        self.assertIsNone(third["next_cursor"])
        self.assertNotIn("manifest", first["source"])
        self.assertNotIn("native", first["items"][0])
        self.assertEqual(first["coverage"]["indexed_paths_count"], 2)
        self.assertNotIn("indexed_paths", first["coverage"])
        for kind, limit in (("definitions", 10), ("references", 9)):
            with self.assertRaises(CodeObservationError):
                workspace.query(handle, kind, limit=limit, cursor=first["next_cursor"])
        for limit in (True, 0, 11):
            with self.assertRaises(CodeObservationError):
                workspace.query(handle, "references", limit=limit)
        for cursor in ("bad", "W10=", "a" * 2049):
            with self.assertRaises(CodeObservationError):
                workspace.query(handle, "references", cursor=cursor)

    def test_output_schema_and_no_runtime_or_proof_promotion(self):
        workspace = build()
        schema = json.loads((Path(__file__).resolve().parents[1] /
                             "schemas/code-workspace.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(workspace.to_dict())
        example = json.loads((Path(__file__).resolve().parents[1] /
                              "examples/code_workspace.example.json").read_text())
        Draft202012Validator(schema).validate(example)
        self.assertEqual(example, workspace.to_dict())
        result = workspace.query(symbol(workspace)["handle"], "references")
        self.assertEqual(result["proof"], "not_evaluated")
        self.assertEqual(result["admission"], "not_assessed")
        self.assertEqual(result["publication"], "unreleased")
        self.assertEqual(result["coverage"]["scope"], "supplied_index_only")


class CodeCoordinateTests(unittest.TestCase):
    def test_all_encodings_converge_on_same_exact_unicode_blob(self):
        blob = SourceText('"🚀é" Widget\r\nnext\n')
        ranges = {"utf-8": [0, 9, 15], "utf-16": [0, 6, 12], "utf-32": [0, 5, 11]}
        for encoding, coordinates in ranges.items():
            with self.subTest(encoding=encoding):
                span = blob.span(coordinates, encoding)
                self.assertEqual(blob.raw[span["start_byte"]:span["end_byte"]], b"Widget")
                self.assertEqual(blob.offset(1, 0, encoding), 17)
                self.assertEqual(blob.offset(2, 0, encoding), len(blob.raw))

    def test_boundaries_newlines_empty_and_multiline(self):
        self.assertEqual(SourceText("").span([0, 0, 0], "utf-8")["end_byte"], 0)
        self.assertEqual(SourceText("a\rb\r\nc\n").offset(2, 0, "utf-8"), 5)
        self.assertEqual(SourceText("a\r\nb").span([0, 0, 1, 1], "utf-8")["end_byte"], 4)
        for content, coordinates, encoding in [
            ("🚀", [0, 1, 4], "utf-8"), ("🚀", [0, 1, 2], "utf-16"),
            ("a", [0, 0, True], "utf-8"), ("a", [0, 0, -1], "utf-8"),
            ("a", [1, 0, 0], "utf-8"), ("a", [0, 0], "utf-8"),
        ]:
            with self.subTest(coordinates=coordinates), self.assertRaises(CodeObservationError):
                SourceText(content).span(coordinates, encoding)
        with self.assertRaises(CodeObservationError):
            SourceText(b"\xff")


if __name__ == "__main__":
    unittest.main()
