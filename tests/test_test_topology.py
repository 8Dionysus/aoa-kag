from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUPPORT_DIR = REPO_ROOT / "tests" / "support"
if str(SUPPORT_DIR) not in sys.path:
    sys.path.insert(0, str(SUPPORT_DIR))

import topology_inventory


REQUIRED_NORMALIZED_FIELDS = {
    "path",
    "home",
    "home_scope",
    "family",
    "protects",
    "owner_surface",
    "coverage_authority",
    "lane",
    "mode",
    "runtime_cost",
    "focused_target",
    "failure_route",
}
HOME_SCOPES = {"root", "mechanics-part"}
LANES = {"root-tests", "mechanics-part-tests"}
MODES = {"blocking"}
RUNTIME_COSTS = {"fast", "medium", "slow"}


class TestTopologyAuthorityTests(unittest.TestCase):
    def test_topology_doc_names_test_home_boundaries(self) -> None:
        text = topology_inventory.TEST_TOPOLOGY_PATH.read_text(encoding="utf-8")
        for required in (
            "root",
            "family -> protects -> owner surface -> home scope -> coverage authority",
            "Test files are not command authority.",
            "`config/validation_lanes.json`",
            "`scripts/run_tests.py` owns unittest discovery",
        ):
            self.assertIn(required, text)

    def test_inventory_covers_every_source_test_file(self) -> None:
        entries = topology_inventory.normalized_inventory_entries()
        inventory_paths = [entry["path"] for entry in entries]

        self.assertEqual(len(inventory_paths), len(set(inventory_paths)))
        self.assertEqual(topology_inventory.discovered_test_files(), set(inventory_paths))

        for entry in entries:
            with self.subTest(path=entry["path"]):
                self.assertTrue(REQUIRED_NORMALIZED_FIELDS.issubset(entry))
                self.assertTrue((REPO_ROOT / entry["path"]).is_file())
                self.assertTrue((REPO_ROOT / entry["owner_surface"]).exists())
                self.assertIn(entry["home_scope"], HOME_SCOPES)
                self.assertIn(entry["lane"], LANES)
                self.assertIn(entry["mode"], MODES)
                self.assertIn(entry["runtime_cost"], RUNTIME_COSTS)
                self.assertFalse(topology_inventory.looks_like_command(entry["focused_target"]))
                self.assertFalse(topology_inventory.looks_like_command(entry["coverage_authority"]))
                self.assertNotIn("command", entry)

    def test_test_discovery_ignores_dependency_checkouts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            local_test = repo_root / "tests" / "test_local.py"
            dependency_test = (
                repo_root / ".deps" / "aoa-memo" / "tests" / "test_external.py"
            )
            local_test.parent.mkdir(parents=True)
            dependency_test.parent.mkdir(parents=True)
            local_test.write_text("", encoding="utf-8")
            dependency_test.write_text("", encoding="utf-8")

            self.assertEqual(
                {"tests/test_local.py"},
                topology_inventory.discovered_test_files(repo_root),
            )

    def test_inventory_home_scopes_match_filesystem_topology(self) -> None:
        for entry in topology_inventory.normalized_inventory_entries():
            expected_scope, expected_home = topology_inventory.classify_test_home(entry["path"])
            with self.subTest(path=entry["path"]):
                self.assertEqual(expected_scope, entry["home_scope"])
                self.assertEqual(expected_home, entry["home"])
                self.assertTrue(entry["path"].startswith(f"{entry['home']}/"))

    def test_run_tests_covers_blocking_homes(self) -> None:
        entries = topology_inventory.normalized_inventory_entries()
        expected_homes = {
            entry["home"]
            for entry in entries
            if entry["home_scope"] in {"root", "mechanics-part"}
        }

        self.assertTrue(expected_homes)
        self.assertTrue(expected_homes <= topology_inventory.run_tests_homes())

    def test_release_lane_covers_all_inventory_test_files(self) -> None:
        inventory_paths = {
            entry["path"] for entry in topology_inventory.normalized_inventory_entries()
        }
        self.assertTrue(inventory_paths <= topology_inventory.release_lane_test_coverage())

    def test_test_topology_does_not_duplicate_release_command_authority(self) -> None:
        inventory = topology_inventory.load_inventory()
        inventory_text = json.dumps(inventory, sort_keys=True)
        topology_text = topology_inventory.TEST_TOPOLOGY_PATH.read_text(encoding="utf-8")

        self.assertEqual("config/validation_lanes.json", inventory["command_authority"])
        self.assertEqual("scripts/run_tests.py", inventory["runner_authority"])
        self.assertNotIn("command_sequence", inventory_text)
        self.assertNotIn("python ", inventory_text)
        self.assertNotIn("python ", topology_text)


if __name__ == "__main__":
    unittest.main()
