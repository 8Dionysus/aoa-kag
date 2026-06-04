from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_decision_indexes.py"
SPEC = importlib.util.spec_from_file_location("generate_decision_indexes", SCRIPT_PATH)
decision_indexes = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = decision_indexes
SPEC.loader.exec_module(decision_indexes)


class DecisionIndexesTestCase(unittest.TestCase):
    def test_live_decision_indexes_are_current(self) -> None:
        self.assertEqual([], decision_indexes.validate_decision_indexes(REPO_ROOT))

    def test_by_number_index_exposes_canonical_id_and_path(self) -> None:
        records, issues = decision_indexes.collect_decision_records(REPO_ROOT)

        self.assertEqual([], issues)
        rendered = decision_indexes.render_index_files(records)
        by_number = rendered[decision_indexes.INDEX_DIR / "by-number.md"]

        self.assertIn("| Decision ID | Date | Decision | Path |", by_number)
        self.assertIn("`docs/decisions/AOA-KAG-D-0001-kag-maturity-hardening.md`", by_number)
        self.assertIn("`docs/decisions/AOA-KAG-D-0003-canonical-decision-lane.md`", by_number)

    def test_grouped_indexes_are_lookup_bullets_not_repeated_ledgers(self) -> None:
        records, issues = decision_indexes.collect_decision_records(REPO_ROOT)

        self.assertEqual([], issues)
        rendered = decision_indexes.render_index_files(records)
        by_surface = rendered[decision_indexes.INDEX_DIR / "by-surface.md"]

        self.assertNotIn("| Decision | Date |", by_surface)
        self.assertIn("- [AOA-KAG-D-", by_surface)
        self.assertIn("(`docs/decisions/AOA-KAG-D-", by_surface)

    def test_decision_id_must_match_filename_prefix(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            decision_dir = temp_root / "docs" / "decisions"
            decision_dir.mkdir(parents=True)
            decision = decision_dir / "AOA-KAG-D-0001-example.md"
            decision.write_text(
                "\n".join(
                    [
                        "# Example",
                        "",
                        "## Index Metadata",
                        "",
                        "- Decision ID: AOA-KAG-D-0002",
                        "- Original date: 2026-06-04",
                        "- Surface classes: docs/decisions",
                        "- KAG surfaces: decision lane",
                        "- Source lanes: aoa-kag",
                        "- Guard families: source-owned authority",
                        "- Posture: accepted",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            _, issues = decision_indexes.collect_decision_records(temp_root)

        self.assertTrue(any("Decision ID must match filename prefix" in message for _, message in issues))


if __name__ == "__main__":
    unittest.main()
