from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


PART_ROOT = Path(__file__).resolve().parents[1]
STEMS = ("kag_promotion_evidence_bundle", "kag_to_tos_dossier_bridge")
GUARDRAIL_BOOLEAN_FIELDS = {"direct_write"}


def load_contract(stem: str) -> tuple[dict[str, object], dict[str, object]]:
    schema = json.loads((PART_ROOT / "schemas" / f"{stem}_v1.json").read_text(encoding="utf-8"))
    example = json.loads((PART_ROOT / "examples" / f"{stem}.example.json").read_text(encoding="utf-8"))
    return schema, example


def validation_errors(schema: dict[str, object], value: dict[str, object]) -> list[object]:
    return sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))


class PromotionDossierContractTests(unittest.TestCase):
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
            mutated["payload"]["contract_escape"] = "loose-payload"
            self.assert_invalid(schema, mutated, f"{stem} unknown payload field")

    def test_rejects_direct_write_inversion(self) -> None:
        schema, example = load_contract("kag_to_tos_dossier_bridge")
        mutated = copy.deepcopy(example)
        self.assertIsInstance(mutated["payload"], dict)
        mutated["payload"]["direct_write"] = True
        self.assert_invalid(schema, mutated, "kag_to_tos_dossier_bridge direct_write")

    def test_rejects_bad_evidence_arrays(self) -> None:
        for stem in STEMS:
            schema, example = load_contract(stem)
            mutated = copy.deepcopy(example)
            mutated["evidence_refs"] = [12345]
            self.assert_invalid(schema, mutated, f"{stem} non-string evidence ref")


if __name__ == "__main__":
    unittest.main()
