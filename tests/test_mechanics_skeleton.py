from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate_mechanics_skeleton  # noqa: E402


class MechanicsSkeletonTests(unittest.TestCase):
    def test_repository_mechanics_skeleton_validates(self) -> None:
        self.assertEqual([], validate_mechanics_skeleton.validate(REPO_ROOT))

    def test_forbidden_root_entry_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mechanics = root / "mechanics"
            mechanics.mkdir()
            for filename in validate_mechanics_skeleton.REQUIRED_ROOT_FILES:
                (mechanics / filename).write_text(
                    (REPO_ROOT / "mechanics" / filename).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            (mechanics / "notes").mkdir()

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(any("root entries must match required root files" in issue for issue in issues))
        self.assertIn("mechanics/notes: forbidden root mechanics entry", issues)

    def test_missing_canonical_heading_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mechanics = root / "mechanics"
            mechanics.mkdir()
            for filename in validate_mechanics_skeleton.REQUIRED_ROOT_FILES:
                (mechanics / filename).write_text(
                    (REPO_ROOT / "mechanics" / filename).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            agents_path = mechanics / "AGENTS.md"
            agents_path.write_text("# AGENTS.md\n\n## Role\n", encoding="utf-8")

            issues = validate_mechanics_skeleton.validate(root)

        self.assertIn("mechanics/AGENTS.md: missing heading '## Applies to'", issues)


if __name__ == "__main__":
    unittest.main()
