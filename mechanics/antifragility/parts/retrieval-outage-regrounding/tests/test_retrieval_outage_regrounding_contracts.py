from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class RetrievalOutageRegroundingContractTests(unittest.TestCase):
    def test_regrounding_ticket_examples_validate(self) -> None:
        schema_path = PART_ROOT / "schemas" / "regrounding_ticket_v1.json"
        schema = load_json(schema_path)
        self.assertIsInstance(schema, dict)
        Draft202012Validator.check_schema(schema)

        for example_path in sorted((PART_ROOT / "examples").glob("regrounding_ticket*.example.json")):
            with self.subTest(example=example_path.name):
                example = load_json(example_path)
                Draft202012Validator(schema).validate(example)

    def test_retrieval_outage_doc_keeps_owner_split(self) -> None:
        doc = (PART_ROOT / "docs" / "retrieval-outage-regrounding.md").read_text(encoding="utf-8")
        for token in (
            "KAG owns projection-health truth",
            "mechanics/recurrence/parts/return-regrounding/generated/return_regrounding_pack.min.json",
            "`aoa-playbooks` owns the runtime-chaos lane and re-entry gate",
        ):
            self.assertIn(token, doc)

    def test_regrounding_tickets_target_existing_local_surfaces(self) -> None:
        for ticket_path in sorted((PART_ROOT / "examples").glob("regrounding_ticket*.example.json")):
            ticket = load_json(ticket_path)
            assert isinstance(ticket, dict)
            self.assertTrue((REPO_ROOT / ticket["projection_ref"]).is_file())
            for relative_path in ticket["expected_outputs"]:
                self.assertTrue((REPO_ROOT / relative_path).is_file())


if __name__ == "__main__":
    unittest.main()
