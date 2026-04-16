from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> object:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


class AntifragilityPublicSurfaceTests(unittest.TestCase):
    def test_projection_health_examples_validate(self) -> None:
        surfaces = (
            (
                "schemas/projection_health_receipt_v1.json",
                "examples/projection_health_receipt.example.json",
            ),
            (
                "schemas/regrounding_ticket_v1.json",
                "examples/regrounding_ticket.example.json",
            ),
            (
                "schemas/projection_health_receipt_v1.json",
                "examples/projection_health_receipt.retrieval-outage-honesty.example.json",
            ),
            (
                "schemas/regrounding_ticket_v1.json",
                "examples/regrounding_ticket.retrieval-outage-honesty.example.json",
            ),
        )

        for schema_path, example_path in surfaces:
            with self.subTest(schema=schema_path, example=example_path):
                schema = load_json(schema_path)
                example = load_json(example_path)
                self.assertIsInstance(schema, dict)
                Draft202012Validator.check_schema(schema)
                Draft202012Validator(schema).validate(example)

    def test_projection_health_surfaces_are_discoverable_and_bounded(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        docs_readme = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        regrounding = (REPO_ROOT / "docs" / "KAG_STRESS_REGROUNDING.md").read_text(encoding="utf-8")
        quarantine = (REPO_ROOT / "docs" / "KAG_PROJECTION_QUARANTINE.md").read_text(encoding="utf-8")
        chaos = (REPO_ROOT / "docs" / "KAG_REGROUNDING_CHAOS_WAVE1.md").read_text(encoding="utf-8")

        self.assertIn("docs/KAG_STRESS_REGROUNDING.md", readme)
        self.assertIn("docs/KAG_PROJECTION_QUARANTINE.md", readme)
        self.assertIn("docs/KAG_REGROUNDING_CHAOS_WAVE1.md", readme)
        self.assertIn("KAG_STRESS_REGROUNDING", docs_readme)
        self.assertIn("KAG_PROJECTION_QUARANTINE", docs_readme)
        self.assertIn("KAG_REGROUNDING_CHAOS_WAVE1", docs_readme)

        for token in (
            "do not silently regenerate and republish drifted surfaces as if nothing happened",
            "do not let KAG overrule source-owned truth",
            "It is not a new claim about source meaning.",
        ):
            self.assertIn(token, regrounding)

        for token in (
            "preserve evidence refs",
            "narrow consumer posture",
            "silently disappear without review",
        ):
            self.assertIn(token, quarantine)

        for token in (
            "KAG owns projection-health truth",
            "generated/return_regrounding_pack.min.json",
            "`aoa-playbooks` owns the runtime-chaos lane and re-entry gate",
        ):
            self.assertIn(token, chaos)

    def test_examples_target_existing_local_surfaces(self) -> None:
        for projection_path in (
            "examples/projection_health_receipt.example.json",
            "examples/projection_health_receipt.retrieval-outage-honesty.example.json",
        ):
            projection = load_json(projection_path)
            assert isinstance(projection, dict)
            self.assertTrue((REPO_ROOT / projection["bounded_scope"]["value"]).is_file())
            for relative_path in projection["affected_generated_surfaces"]:
                self.assertTrue((REPO_ROOT / relative_path).is_file())

        for ticket_path in (
            "examples/regrounding_ticket.example.json",
            "examples/regrounding_ticket.retrieval-outage-honesty.example.json",
        ):
            ticket = load_json(ticket_path)
            assert isinstance(ticket, dict)
            self.assertTrue((REPO_ROOT / ticket["projection_ref"]).is_file())
            for relative_path in ticket["expected_outputs"]:
                self.assertTrue((REPO_ROOT / relative_path).is_file())


if __name__ == "__main__":
    unittest.main()
