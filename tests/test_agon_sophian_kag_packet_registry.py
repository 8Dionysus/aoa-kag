from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATED = ROOT / 'generated/agon_sophian_kag_packet_registry.min.json'
SCRIPT = ROOT / 'scripts/build_agon_sophian_kag_packet_registry.py'
VALIDATOR = ROOT / 'scripts/validate_agon_sophian_kag_packet_registry.py'
EXPECTED_COUNT = 7
ITEM_KEY = 'sophian_kag_packet_candidates'


class AgonSophianKagPacketRegistryTestCase(unittest.TestCase):
    def test_generated_registry_shape(self) -> None:
        reg = json.loads(GENERATED.read_text(encoding='utf-8'))
        self.assertEqual(reg['wave'], 'XVIII')
        self.assertEqual(reg['count'], EXPECTED_COUNT)
        self.assertEqual(len(reg[ITEM_KEY]), EXPECTED_COUNT)
        self.assertTrue(all(item.get('live_protocol') is False for item in reg[ITEM_KEY]))
        self.assertTrue(all(item.get('review_status') == 'candidate_only' for item in reg[ITEM_KEY]))

    def test_builder_check_and_validator(self) -> None:
        builder = subprocess.run([sys.executable, str(SCRIPT), '--check'], cwd=str(ROOT), text=True, capture_output=True)
        self.assertEqual(builder.returncode, 0, builder.stderr)
        validator = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(ROOT), text=True, capture_output=True)
        self.assertEqual(validator.returncode, 0, validator.stderr)


if __name__ == '__main__':
    unittest.main()
