from __future__ import annotations

import json
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = Path(__file__).resolve().parents[1]
PROJECTION_HEALTH_SCHEMA = (
    REPO_ROOT
    / "mechanics"
    / "antifragility"
    / "parts"
    / "projection-health"
    / "schemas"
    / "projection_health_receipt_v1.json"
)


class ProjectionQuarantineContractTests(unittest.TestCase):
    def test_quarantine_doc_is_bounded(self) -> None:
        doc = (PART_ROOT / "docs" / "projection-quarantine.md").read_text(encoding="utf-8")
        for token in (
            "preserve evidence refs",
            "narrow consumer posture",
            "silently disappear without review",
        ):
            self.assertIn(token, doc)

    def test_projection_health_schema_can_represent_quarantine(self) -> None:
        schema = json.loads(PROJECTION_HEALTH_SCHEMA.read_text(encoding="utf-8"))
        health_enum = schema["properties"]["health_state"]["enum"]
        posture_enum = schema["properties"]["consumer_posture"]["enum"]
        self.assertIn("quarantined", health_enum)
        self.assertIn("source_first", posture_enum)
        self.assertIn("do_not_expand", posture_enum)


if __name__ == "__main__":
    unittest.main()
