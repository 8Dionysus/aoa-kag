from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


PART_ROOT = Path(__file__).resolve().parents[1]
STEMS = ("kag_pattern_retirement_decision", "kag_pattern_retirement_downlink")


def load_contract(stem: str) -> tuple[dict[str, object], dict[str, object]]:
    schema = json.loads((PART_ROOT / "schemas" / f"{stem}_v1.json").read_text(encoding="utf-8"))
    example = json.loads((PART_ROOT / "examples" / f"{stem}.example.json").read_text(encoding="utf-8"))
    return schema, example


def validation_errors(schema: dict[str, object], value: dict[str, object]) -> list[object]:
    return sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))


class RetirementContractTests(unittest.TestCase):
    def assert_invalid(self, schema: dict[str, object], value: dict[str, object], label: str) -> None:
        self.assertTrue(validation_errors(schema, value), f"{label} unexpectedly validated")

    def test_examples_match_schemas(self) -> None:
        for stem in STEMS:
            with self.subTest(stem=stem):
                schema, example = load_contract(stem)
                Draft202012Validator.check_schema(schema)
                self.assertFalse(validation_errors(schema, example))

    def test_rejects_unknown_fields(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            mutated = copy.deepcopy(example)
            mutated["contract_escape"] = True
            self.assert_invalid(schema, mutated, f"{stem} unknown top-level field")

            mutated = copy.deepcopy(example)
            self.assertIsInstance(mutated["payload"], dict)
            mutated["payload"]["contract_escape"] = "loose"
            self.assert_invalid(schema, mutated, f"{stem} unknown payload field")

    def test_rejects_bad_evidence_refs(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            mutated = copy.deepcopy(example)
            mutated["evidence_refs"] = [12345]
            self.assert_invalid(schema, mutated, f"{stem} non-string evidence ref")

    def test_retirement_downlink_uses_functional_stage_not_wave(self) -> None:
        schema, example = load_contract("kag_pattern_retirement_downlink")
        payload_props = schema["properties"]["payload"]["properties"]
        payload = example["payload"]
        self.assertNotIn("wave", payload_props)
        self.assertNotIn("wave", payload)
        self.assertEqual("retirement_downlink", payload["retirement_stage"])


if __name__ == "__main__":
    unittest.main()
