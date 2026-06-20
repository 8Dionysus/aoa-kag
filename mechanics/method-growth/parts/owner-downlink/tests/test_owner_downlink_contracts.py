from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


PART_ROOT = Path(__file__).resolve().parents[1]
STEMS = (
    "kag_adoption_boundary",
    "kag_pattern_adoption_dossier",
    "kag_pattern_downlink",
    "kag_to_owner_signal",
)
GUARDRAIL_BOOLEAN_FIELDS = {
    "requires_owner_consent",
    "rollback_required",
    "kag_may_propose",
    "kag_may_force_uptake",
}


def load_contract(stem: str) -> tuple[dict[str, object], dict[str, object]]:
    schema = json.loads((PART_ROOT / "schemas" / f"{stem}_v1.json").read_text(encoding="utf-8"))
    example = json.loads((PART_ROOT / "examples" / f"{stem}.example.json").read_text(encoding="utf-8"))
    return schema, example


def validation_errors(schema: dict[str, object], value: dict[str, object]) -> list[object]:
    return sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))


class OwnerDownlinkContractTests(unittest.TestCase):
    def assert_invalid(self, schema: dict[str, object], value: dict[str, object], label: str) -> None:
        self.assertTrue(validation_errors(schema, value), f"{label} unexpectedly validated")

    def test_examples_match_schemas(self) -> None:
        for stem in STEMS:
            with self.subTest(stem=stem):
                schema, example = load_contract(stem)
                Draft202012Validator.check_schema(schema)
                self.assertFalse(validation_errors(schema, example))

    def test_uses_functional_adoption_stage_not_wave(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            payload_props = schema["properties"]["payload"]["properties"]
            payload = example["payload"]
            self.assertNotIn("wave", payload_props)
            self.assertNotIn("wave", payload)
            self.assertEqual("downstream_adoption", payload["adoption_stage"])

    def test_rejects_guardrail_boolean_inversions(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            payload = example.get("payload")
            self.assertIsInstance(payload, dict)
            for key in GUARDRAIL_BOOLEAN_FIELDS:
                with self.subTest(stem=stem, key=key):
                    mutated = copy.deepcopy(example)
                    self.assertIsInstance(mutated["payload"], dict)
                    mutated["payload"][key] = not payload[key]
                    self.assert_invalid(schema, mutated, f"{stem} inverted {key}")

    def test_rejects_invalid_retention_cycles(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            mutated = copy.deepcopy(example)
            self.assertIsInstance(mutated["payload"], dict)
            mutated["payload"]["retention_cycles"] = 0
            self.assert_invalid(schema, mutated, f"{stem} zero retention_cycles")

    def test_rejects_unknown_payload_fields(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            mutated = copy.deepcopy(example)
            self.assertIsInstance(mutated["payload"], dict)
            mutated["payload"]["contract_escape"] = "loose"
            self.assert_invalid(schema, mutated, f"{stem} unknown payload field")


if __name__ == "__main__":
    unittest.main()
