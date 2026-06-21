from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from scripts import release_check, validation_lanes


class ReleaseLaneTests(unittest.TestCase):
    def test_release_lane_delegates_to_manifest_authority(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / "config" / "validation_lanes.json").read_text(encoding="utf-8")
        )
        release_lane = manifest["lanes"]["release"]

        self.assertEqual("release", release_check.RELEASE_LANE_ID)
        self.assertEqual(
            validation_lanes.command_sequence_for_lane("release"),
            release_check.release_lane_commands(),
        )
        self.assertEqual("scripts/release_check.py", release_lane["entrypoint"])

    def test_release_entrypoint_does_not_duplicate_command_sequence(self) -> None:
        release_check_text = (REPO_ROOT / "scripts" / "release_check.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("validation_lanes.command_sequence_for_lane(RELEASE_LANE_ID)", release_check_text)
        self.assertNotIn("COMMANDS =", release_check_text)
        self.assertNotIn('"validate committed KAG surfaces"', release_check_text)
        self.assertNotIn('"generate KAG outputs"', release_check_text)

    def test_source_fast_does_not_call_release_entrypoint(self) -> None:
        source_fast_scripts = {
            part
            for command in validation_lanes.SOURCE_FAST_COMMAND_SEQUENCE
            for part in command
            if part.endswith(".py")
        }

        self.assertNotIn("scripts/release_check.py", source_fast_scripts)
        self.assertNotIn("scripts/ci_gate.py", source_fast_scripts)
        self.assertNotIn("scripts/generate_kag.py", source_fast_scripts)


if __name__ == "__main__":
    unittest.main()
