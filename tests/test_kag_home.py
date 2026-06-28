from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
KAG_ROOT = REPO_ROOT / "kag"

EXPECTED_ROOT_FILES = {
    "AGENTS.md",
    "README.md",
    "LOCAL_SUBTREE_PROTOCOL.md",
    "source_home.manifest.json",
    "manifest.json",
}

EXPECTED_RECORD_DIRS = {
    "nodes",
    "edges",
    "indexes",
    "projections",
    "receipts",
}

EXPECTED_ACTIVE_FAMILIES = {
    "home_route_cards",
    "source_home_manifest",
    "local_subtree_protocol",
    "provider_manifest",
    "node_records",
    "edge_records",
    "index_records",
    "projection_records",
    "receipt_records",
}

EXPECTED_PROVIDER_READY_REPOS = {
    "8Dionysus",
    "ATM10-Agent",
    "Agents-of-Abyss",
    "Dionysus",
    "aoa-kag",
    "aoa-4pda-connector",
    "aoa-agents",
    "aoa-discord-connector",
    "aoa-evals",
    "aoa-memo",
    "aoa-playbooks",
    "aoa-routing",
    "aoa-sdk",
    "aoa-session-memory",
    "aoa-skills",
    "aoa-stats",
    "aoa-stackoverflow-connector",
    "Tree-of-Sophia",
    "aoa-techniques",
    "aoa-xda-connector",
}


def load_json(relative_path: str) -> dict[str, object]:
    payload = json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


class KagHomeTests(unittest.TestCase):
    def test_kag_home_root_files_and_record_dirs_are_present(self) -> None:
        root_files = {
            path.name
            for path in KAG_ROOT.iterdir()
            if path.is_file()
        }
        root_dirs = {
            path.name
            for path in KAG_ROOT.iterdir()
            if path.is_dir()
        }

        self.assertEqual(EXPECTED_ROOT_FILES, root_files)
        self.assertEqual(EXPECTED_RECORD_DIRS, root_dirs)
        for directory in EXPECTED_RECORD_DIRS:
            with self.subTest(directory=directory):
                self.assertTrue(list((KAG_ROOT / directory).glob("*.json")))

    def test_source_home_manifest_names_active_protocol_and_provider_families(self) -> None:
        manifest = load_json("kag/source_home.manifest.json")

        self.assertEqual("aoa_kag_source_home_v2", manifest["schema_version"])
        self.assertEqual("aoa-kag", manifest["owner_repo"])
        self.assertEqual("kag/", manifest["home"])
        self.assertEqual("active_protocol_provider", manifest["status"])
        self.assertEqual(EXPECTED_PROVIDER_READY_REPOS, set(manifest["provider_ready_repos"]))

        branches = manifest["branches"]
        self.assertIsInstance(branches, list)
        self.assertEqual(["protocol", "provider_packet"], [branch["id"] for branch in branches])

        families = manifest["families"]
        self.assertIsInstance(families, list)
        self.assertEqual(EXPECTED_ACTIVE_FAMILIES, {family["id"] for family in families})
        for family in families:
            with self.subTest(family=family["id"]):
                self.assertIn("owner_surface", family)
                self.assertIn("validators", family)
                for source_file in family["source_files"]:
                    self.assertTrue((REPO_ROOT / source_file).is_file())

    def test_provider_manifest_names_all_record_classes_and_consumers(self) -> None:
        manifest = load_json("kag/manifest.json")

        self.assertEqual("aoa-local-kag-manifest-v1", manifest["schema_version"])
        self.assertEqual("aoa-kag", manifest["repo"])
        self.assertEqual("kag/AGENTS.md", manifest["owner_surface"])
        self.assertEqual(
            {"node", "edge", "index", "projection", "receipt"},
            set(manifest["record_classes"]),
        )
        self.assertIn("aoa-kag registry", manifest["consumer_routes"])
        self.assertIn("aoa-kag-mcp resource", manifest["consumer_routes"])

    def test_protocol_and_route_docs_name_current_provider_flow(self) -> None:
        readme = (KAG_ROOT / "README.md").read_text(encoding="utf-8")
        protocol = (KAG_ROOT / "LOCAL_SUBTREE_PROTOCOL.md").read_text(encoding="utf-8")
        agents = (KAG_ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("KAG Source Home", readme)
        self.assertIn("Current Files", readme)
        self.assertIn("Tree-of-Sophia", readme)
        self.assertIn("aoa-techniques", readme)
        self.assertIn("aoa-skills", readme)
        self.assertIn("8Dionysus", readme)
        self.assertIn("ATM10-Agent", readme)
        self.assertIn("Dionysus", readme)
        self.assertIn("aoa-stats", readme)
        self.assertIn("aoa-4pda-connector", readme)
        self.assertIn("aoa-discord-connector", readme)
        self.assertIn("aoa-stackoverflow-connector", readme)
        self.assertIn("aoa-xda-connector", readme)
        self.assertIn("OS Surface Layer", readme)
        self.assertIn("connectors", readme)
        self.assertIn("Required Home", protocol)
        self.assertIn("MCP Access Shape", protocol)
        self.assertIn("runtime_source_repo", protocol)
        self.assertIn("Provider Records", agents)
        self.assertIn("## Closeout", agents)


if __name__ == "__main__":
    unittest.main()
