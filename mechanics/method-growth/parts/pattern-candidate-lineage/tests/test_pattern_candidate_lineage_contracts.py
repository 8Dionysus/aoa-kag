from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


PART_ROOT = Path(__file__).resolve().parents[1]
STEMS = (
    "kag_pattern_candidate",
    "kag_federation_lineage_link",
    "kag_pattern_node",
)
GUARDRAIL_BOOLEAN_FIELDS = {"derived_only"}


def load_contract(stem: str) -> tuple[dict[str, object], dict[str, object]]:
    schema = json.loads((PART_ROOT / "schemas" / f"{stem}_v1.json").read_text(encoding="utf-8"))
    example = json.loads((PART_ROOT / "examples" / f"{stem}.example.json").read_text(encoding="utf-8"))
    return schema, example


def validation_errors(schema: dict[str, object], value: dict[str, object]) -> list[object]:
    return sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))


def wrong_type_value(value: object) -> object:
    if isinstance(value, bool):
        return "not-a-boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "not-an-integer"
    if isinstance(value, str):
        return 12345
    if isinstance(value, list):
        return {"not": "an array"}
    if isinstance(value, dict):
        return "not-an-object"
    return "not-null"


class PatternCandidateLineageContractTests(unittest.TestCase):
    def assert_invalid(self, schema: dict[str, object], value: dict[str, object], label: str) -> None:
        self.assertTrue(validation_errors(schema, value), f"{label} unexpectedly validated")

    def test_examples_match_schemas(self) -> None:
        for stem in STEMS:
            with self.subTest(stem=stem):
                schema, example = load_contract(stem)
                Draft202012Validator.check_schema(schema)
                self.assertFalse(validation_errors(schema, example))

    def test_rejects_escape_hatches_and_wrong_payload_types(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            with self.subTest(stem=stem, case="unknown-top"):
                mutated = copy.deepcopy(example)
                mutated["contract_escape"] = True
                self.assert_invalid(schema, mutated, f"{stem} unknown top-level field")

            payload = example.get("payload")
            self.assertIsInstance(payload, dict)
            for key, value in payload.items():
                with self.subTest(stem=stem, key=key):
                    mutated = copy.deepcopy(example)
                    self.assertIsInstance(mutated["payload"], dict)
                    mutated["payload"][key] = wrong_type_value(value)
                    self.assert_invalid(schema, mutated, f"{stem} wrong {key} type")

    def test_rejects_guardrail_boolean_inversions(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            payload = example.get("payload")
            self.assertIsInstance(payload, dict)
            for key in GUARDRAIL_BOOLEAN_FIELDS & payload.keys():
                with self.subTest(stem=stem, key=key):
                    mutated = copy.deepcopy(example)
                    self.assertIsInstance(mutated["payload"], dict)
                    mutated["payload"][key] = not payload[key]
                    self.assert_invalid(schema, mutated, f"{stem} inverted {key}")

    def test_rejects_bad_array_items(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            for key, value in example.items():
                if isinstance(value, list):
                    with self.subTest(stem=stem, key=key):
                        mutated = copy.deepcopy(example)
                        mutated[key] = [12345]
                        self.assert_invalid(schema, mutated, f"{stem} non-string {key} item")
            payload = example.get("payload")
            self.assertIsInstance(payload, dict)
            for key, value in payload.items():
                if isinstance(value, list):
                    with self.subTest(stem=stem, key=key):
                        mutated = copy.deepcopy(example)
                        self.assertIsInstance(mutated["payload"], dict)
                        mutated["payload"][key] = [12345]
                        self.assert_invalid(schema, mutated, f"{stem} non-string payload.{key} item")


if __name__ == "__main__":
    unittest.main()
