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
}

RESERVED_FUTURE_SURFACES = {
    "manifest.json",
    "nodes/",
    "edges/",
    "indexes/",
    "projections/",
    "receipts/",
}

FORBIDDEN_ACTIVE_PAYLOAD_PATHS = {
    "manifest.json",
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
}

EXPECTED_SOURCE_HOME_EVIDENCE = {
    "Tree-of-Sophia",
    "aoa-agents",
    "aoa-playbooks",
    "aoa-routing",
    "aoa-sdk",
    "aoa-skills",
    "aoa-techniques",
    "aoa-memo",
    "aoa-evals",
    "Agents-of-Abyss",
}

def load_manifest() -> dict[str, object]:
    payload = json.loads((KAG_ROOT / "source_home.manifest.json").read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


class KagHomeTests(unittest.TestCase):
    def test_kag_home_root_files_are_exact_and_present(self) -> None:
        root_files = {
            path.name
            for path in KAG_ROOT.iterdir()
            if path.is_file()
        }

        self.assertEqual(EXPECTED_ROOT_FILES, root_files)

        manifest = load_manifest()
        self.assertEqual("aoa_kag_source_home_preflight_v1", manifest["schema_version"])
        self.assertEqual("aoa-kag", manifest["owner_repo"])
        self.assertEqual("kag/", manifest["home"])
        self.assertEqual("preflight", manifest["status"])
        self.assertIn(
            "docs/decisions/AOA-KAG-D-0007-kag-source-home-preflight.md",
            manifest["decision_refs"],
        )

    def test_source_home_manifest_names_only_active_preflight_families(self) -> None:
        manifest = load_manifest()
        branches = manifest["branches"]
        self.assertIsInstance(branches, list)
        self.assertEqual(["preflight_contract"], [branch["id"] for branch in branches])
        self.assertEqual("kag/", branches[0]["path"])
        self.assertEqual(sorted(EXPECTED_ACTIVE_FAMILIES), sorted(branches[0]["families"]))

        families = manifest["families"]
        self.assertIsInstance(families, list)
        self.assertEqual(EXPECTED_ACTIVE_FAMILIES, {family["id"] for family in families})
        for family in families:
            with self.subTest(family=family["id"]):
                self.assertEqual("preflight_contract", family["branch"])
                self.assertIn("owner_surface", family)
                self.assertIn("validators", family)
                for source_file in family["source_files"]:
                    self.assertTrue((REPO_ROOT / source_file).is_file())

    def test_reserved_future_surfaces_are_named_but_not_created(self) -> None:
        manifest = load_manifest()
        surfaces = {
            item["path"]
            for item in manifest["reserved_future_surfaces"]
        }

        self.assertEqual(RESERVED_FUTURE_SURFACES, surfaces)
        for relative_path in FORBIDDEN_ACTIVE_PAYLOAD_PATHS:
            with self.subTest(path=relative_path):
                self.assertFalse((KAG_ROOT / relative_path).exists())

    def test_source_home_evidence_map_names_real_home_pattern_repos(self) -> None:
        readme = (KAG_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("This is about the AoA source-home pattern.", readme)
        for repo in EXPECTED_SOURCE_HOME_EVIDENCE:
            with self.subTest(repo=repo):
                self.assertIn(repo, readme)

    def test_protocol_docs_keep_runtime_and_sibling_rollout_stop_lines(self) -> None:
        readme = (KAG_ROOT / "README.md").read_text(encoding="utf-8")
        protocol = (KAG_ROOT / "LOCAL_SUBTREE_PROTOCOL.md").read_text(encoding="utf-8")
        agents = (KAG_ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("source-home preflight", readme)
        self.assertIn("It is not a payload warehouse.", readme)
        self.assertIn("No sibling `/kag` rollout from this home yet.", readme)
        self.assertIn("Do not create sibling `/kag` directories", protocol)
        self.assertIn("live graph databases", protocol)
        self.assertIn("source_home.manifest.json", agents)
        self.assertIn("Do not create `nodes/`, `edges/`, `indexes/`", agents)
        self.assertIn("## Closeout", agents)


if __name__ == "__main__":
    unittest.main()
