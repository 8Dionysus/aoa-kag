from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[5]
BUILDER = ROOT / 'mechanics/agon/parts/promotion-candidates/scripts/build_promotion_candidate_registry.py'
VALIDATOR = ROOT / 'mechanics/agon/parts/promotion-candidates/scripts/validate_promotion_candidate_registry.py'


class AgonKagPromotionCandidateRegistryTestCase(unittest.TestCase):
    def test_promotion_candidate_registry_shape(self) -> None:
        reg = json.loads((ROOT / 'generated/agon_kag_promotion_candidate_registry.min.json').read_text(encoding='utf-8'))
        self.assertEqual(reg['review_stage'], 'kag_promotion_path')
        self.assertEqual(reg['count'], 9)
        self.assertEqual(len(reg['kag_candidates']), 9)
        for item in reg['kag_candidates']:
            self.assertEqual(item['review_stage'], 'kag_promotion_path')
            self.assertIs(item['live_protocol'], False)
            self.assertIn('no_kag_as_canon', item.get('stop_lines', []))
            self.assertIn('single_event_promotion', item.get('forbidden_effects', []))
            self.assertNotIn(item.get('canonical_status'), ('canon', 'canonical', 'tree_of_sophia_canon'))

    def test_builder_check_and_validator(self) -> None:
        builder = subprocess.run(
            [sys.executable, str(BUILDER), '--check'],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(builder.returncode, 0, builder.stderr)
        validator = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(validator.returncode, 0, validator.stderr)


if __name__ == '__main__':
    unittest.main()
