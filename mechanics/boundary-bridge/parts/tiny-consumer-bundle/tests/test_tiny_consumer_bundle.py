from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import kag_generation
import validate_kag


class TinyConsumerBundlePartTests(unittest.TestCase):
    def test_builder_matches_part_local_generated_outputs(self) -> None:
        expected = kag_generation.build_tiny_consumer_bundle_payload(
            kag_generation.build_registry_payload()
        )
        full = json.loads(
            kag_generation.TINY_CONSUMER_BUNDLE_OUTPUT_PATH.read_text(encoding="utf-8")
        )
        compact = json.loads(
            kag_generation.TINY_CONSUMER_BUNDLE_MIN_OUTPUT_PATH.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(full, expected)
        self.assertEqual(compact, expected)
        validate_kag.validate_tiny_consumer_bundle_pack(expected)
        validate_kag.validate_tiny_consumer_bundle_example(expected)

    def test_bundle_refs_are_part_local(self) -> None:
        expected_prefix = "mechanics/boundary-bridge/parts/tiny-consumer-bundle/"
        for ref in (
            kag_generation.TINY_CONSUMER_BUNDLE_MANIFEST_REF,
            kag_generation.TINY_CONSUMER_BUNDLE_OUTPUT_REF,
            kag_generation.TINY_CONSUMER_BUNDLE_MIN_OUTPUT_REF,
        ):
            self.assertTrue(ref.startswith(expected_prefix), ref)


if __name__ == "__main__":
    unittest.main()
