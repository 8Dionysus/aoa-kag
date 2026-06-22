from __future__ import annotations

import sys
import unittest
import json
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

    def test_common_center_packages_are_active_without_titan(self) -> None:
        topology = json.loads((REPO_ROOT / "mechanics" / "topology.json").read_text(encoding="utf-8"))
        active = {package["path"] for package in topology["active_packages"]}

        self.assertEqual(set(validate_mechanics_skeleton.COMMON_CENTER_PACKAGES), active)
        self.assertNotIn("titan", active)
        self.assertEqual([], topology["local_only_mechanics"])
        self.assertIn(
            "local-kag-subtree-protocol",
            {item["id"] for item in topology["local_only_candidate_pressure"]},
        )
        pressure = {
            item["id"]: item
            for item in topology["local_only_candidate_pressure"]
        }["local-kag-subtree-protocol"]
        self.assertEqual("source_home_preflight_active", pressure["status"])
        self.assertEqual("kag/README.md", pressure["home_ref"])

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

    def test_missing_package_readme_heading_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_mechanics_tree(root)
            readme_path = root / "mechanics" / "agon" / "README.md"
            readme_path.write_text("# Agon\n\n## Mechanic card\n", encoding="utf-8")

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(
            any(issue.endswith("mechanics/agon/README.md: missing heading '### Trigger'") for issue in issues)
        )

    def test_root_readme_package_map_must_match_topology(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_mechanics_tree(root)
            readme_path = root / "mechanics" / "README.md"
            readme_path.write_text(
                readme_path.read_text(encoding="utf-8").replace("| `agon` |", "| `ag0n` |"),
                encoding="utf-8",
            )

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(
            any(
                issue.endswith(
                    "mechanics/README.md: common mechanics map must include package row '| `agon` |'"
                )
                for issue in issues
            )
        )

    def test_package_status_must_match_active_parts_topology(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_mechanics_tree(root)
            readme_path = root / "mechanics" / "agon" / "README.md"
            readme_path.write_text(
                readme_path.read_text(encoding="utf-8").replace(
                    "Status: mapped common-center mechanic; active part-local routes exist for\n"
                    "promotion candidates and Sophian threshold packets.",
                    "Status: mapped common-center mechanic; no active part directories yet.",
                ),
                encoding="utf-8",
            )

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(
            any(
                issue.endswith(
                    "mechanics/agon/README.md: Status paragraph must reflect active part routes from topology"
                )
                for issue in issues
            )
        )

    def test_parts_map_must_name_topology_candidate_routes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_mechanics_tree(root)
            parts_path = root / "mechanics" / "agon" / "PARTS.md"
            parts_path.write_text(
                parts_path.read_text(encoding="utf-8").replace("`promotion-candidates`", "`promotion-candidatez`"),
                encoding="utf-8",
            )

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(
            any(
                issue.endswith(
                    "mechanics/agon/PARTS.md: candidate part route 'promotion-candidates' "
                    "from topology must be named"
                )
                for issue in issues
            )
        )

    def test_premature_part_directory_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_mechanics_tree(root)
            (root / "mechanics" / "rpg" / "parts").mkdir()

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(
            any(issue.endswith("mechanics/rpg/parts: part directories are not active yet") for issue in issues)
        )

    def test_unlisted_active_part_directory_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_mechanics_tree(root)
            extra_part = root / "mechanics" / "agon" / "parts" / "unspecified"
            extra_part.mkdir()
            (extra_part / "README.md").write_text("# Unspecified\n", encoding="utf-8")
            (extra_part / "CONTRACT.md").write_text("# Contract\n", encoding="utf-8")
            (extra_part / "VALIDATION.md").write_text("# Validation\n", encoding="utf-8")

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(
            any("mechanics/agon/parts: entries must match active part routes" in issue for issue in issues)
        )

    def test_active_part_requires_contract_surface(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_mechanics_tree(root)
            (root / "mechanics" / "agon" / "parts" / "promotion-candidates" / "CONTRACT.md").unlink()

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(
            any(
                issue.endswith(
                    "mechanics/agon/parts/promotion-candidates/CONTRACT.md: required part file is missing"
                )
                for issue in issues
            )
        )

    def test_active_part_legacy_path_name_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_mechanics_tree(root)
            stale_path = (
                root
                / "mechanics"
                / "agon"
                / "parts"
                / "promotion-candidates"
                / "docs"
                / "promotion-candidate-landing.md"
            )
            stale_path.write_text("# Stale\n", encoding="utf-8")

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(
            any(
                issue.endswith(
                    "mechanics/agon/parts/promotion-candidates/docs/promotion-candidate-landing.md: "
                    "active part path must use functional naming, found legacy token 'landing'"
                )
                for issue in issues
            )
        )

    def test_missing_common_package_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_mechanics_tree(root)
            topology_path = root / "mechanics" / "topology.json"
            topology = json.loads(topology_path.read_text(encoding="utf-8"))
            topology["active_packages"] = [
                package for package in topology["active_packages"] if package["path"] != "rpg"
            ]
            topology_path.write_text(json.dumps(topology, indent=2) + "\n", encoding="utf-8")

            issues = validate_mechanics_skeleton.validate(root)

        self.assertTrue(
            any("active_packages must match common center packages" in issue for issue in issues)
        )


def copy_mechanics_tree(root: Path) -> None:
    source = REPO_ROOT / "mechanics"
    target = root / "mechanics"
    for source_path in source.rglob("*"):
        relative_path = source_path.relative_to(source)
        if "__pycache__" in relative_path.parts or source_path.suffix == ".pyc":
            continue
        target_path = target / relative_path
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
