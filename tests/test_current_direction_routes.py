from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class CurrentDirectionRoutesTestCase(unittest.TestCase):
    def test_root_entrypoints_route_to_roadmap(self) -> None:
        roadmap_path = REPO_ROOT / "ROADMAP.md"
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertTrue(roadmap_path.is_file())
        self.assertIn("ROADMAP.md", readme)
        self.assertIn("ROADMAP.md", agents)

    def test_root_entrypoints_route_to_design_surfaces(self) -> None:
        design_path = REPO_ROOT / "DESIGN.md"
        agent_design_path = REPO_ROOT / "DESIGN.AGENTS.md"
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        design = design_path.read_text(encoding="utf-8")
        agent_design = agent_design_path.read_text(encoding="utf-8")

        self.assertTrue(design_path.is_file())
        self.assertTrue(agent_design_path.is_file())
        self.assertIn("DESIGN.md", agents)
        self.assertIn("DESIGN.AGENTS.md", agents)
        self.assertIn("[DESIGN](DESIGN.md)", readme)
        self.assertIn("DESIGN.AGENTS.md", design)
        self.assertIn("AGENTS.md", agent_design)


if __name__ == "__main__":
    unittest.main()
