from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class ProjectionHealthContractTests(unittest.TestCase):
    def test_projection_health_examples_validate(self) -> None:
        schema_path = PART_ROOT / "schemas" / "projection_health_receipt_v1.json"
        schema = load_json(schema_path)
        self.assertIsInstance(schema, dict)
        Draft202012Validator.check_schema(schema)

        for example_path in sorted((PART_ROOT / "examples").glob("projection_health_receipt*.example.json")):
            with self.subTest(example=example_path.name):
                example = load_json(example_path)
                Draft202012Validator(schema).validate(example)

    def test_projection_health_doc_keeps_source_first_boundary(self) -> None:
        doc = (PART_ROOT / "docs" / "stress-regrounding.md").read_text(encoding="utf-8")
        for token in (
            "do not silently regenerate and republish drifted surfaces as if nothing happened",
            "do not let KAG overrule source-owned truth",
            "It is not a new claim about source meaning.",
        ):
            self.assertIn(token, doc)

    def test_projection_health_examples_target_existing_local_surfaces(self) -> None:
        for example_path in sorted((PART_ROOT / "examples").glob("projection_health_receipt*.example.json")):
            projection = load_json(example_path)
            assert isinstance(projection, dict)
            self.assertTrue((REPO_ROOT / projection["bounded_scope"]["value"]).is_file())
            for relative_path in projection["affected_generated_surfaces"]:
                self.assertTrue((REPO_ROOT / relative_path).is_file())


if __name__ == "__main__":
    unittest.main()
