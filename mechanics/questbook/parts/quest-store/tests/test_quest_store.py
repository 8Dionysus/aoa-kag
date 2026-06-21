from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[5]
VALIDATOR_PATH = (
    REPO_ROOT
    / "mechanics"
    / "questbook"
    / "parts"
    / "quest-store"
    / "scripts"
    / "validate_quest_store.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("quest_store_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


quest_store = load_validator()


def quest_path(repo_root: Path, quest_id: str) -> Path:
    matches = sorted((repo_root / "quests").rglob(f"{quest_id}.yaml"))
    if not matches:
        raise AssertionError(f"missing test quest path for {quest_id}")
    if len(matches) != 1:
        raise AssertionError(f"ambiguous test quest path for {quest_id}: {matches}")
    return matches[0]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class QuestStoreValidationTests(unittest.TestCase):
    def write_valid_surface(self, repo_root: Path) -> None:
        write_text(
            repo_root / "QUESTBOOK.md",
            (REPO_ROOT / "QUESTBOOK.md").read_text(encoding="utf-8"),
        )
        write_text(
            repo_root / quest_store.QUESTBOOK_INTEGRATION_PATH,
            (REPO_ROOT / quest_store.QUESTBOOK_INTEGRATION_PATH).read_text(encoding="utf-8"),
        )
        write_text(
            repo_root / quest_store.QUEST_SCHEMA_PATH,
            (REPO_ROOT / quest_store.QUEST_SCHEMA_PATH).read_text(encoding="utf-8"),
        )
        write_text(
            repo_root / quest_store.QUEST_DISPATCH_SCHEMA_PATH,
            (REPO_ROOT / quest_store.QUEST_DISPATCH_SCHEMA_PATH).read_text(encoding="utf-8"),
        )
        for source_path in sorted((REPO_ROOT / "quests").rglob("AOA-KAG-Q-*.yaml")):
            relative = source_path.relative_to(REPO_ROOT)
            write_text(
                repo_root / relative,
                source_path.read_text(encoding="utf-8"),
            )
        write_text(
            repo_root / quest_store.QUEST_CATALOG_EXAMPLE_PATH,
            (REPO_ROOT / quest_store.QUEST_CATALOG_EXAMPLE_PATH).read_text(encoding="utf-8"),
        )
        write_text(
            repo_root / quest_store.QUEST_DISPATCH_EXAMPLE_PATH,
            (REPO_ROOT / quest_store.QUEST_DISPATCH_EXAMPLE_PATH).read_text(encoding="utf-8"),
        )

    def test_valid_questbook_surface_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            quest_store.validate_questbook_surface(repo_root)

    def test_missing_quest_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            quest_path(repo_root, "AOA-KAG-Q-0003").unlink()

            with self.assertRaises(quest_store.QuestStoreValidationError) as context:
                quest_store.validate_questbook_surface(repo_root)

        self.assertIn("quest_catalog.min.example.json", str(context.exception))

    def test_wrong_repo_value_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            target = quest_path(repo_root, "AOA-KAG-Q-0002")
            write_text(
                target,
                target.read_text(encoding="utf-8").replace("repo: aoa-kag", "repo: aoa-evals"),
            )

            with self.assertRaises(quest_store.QuestStoreValidationError) as context:
                quest_store.validate_questbook_surface(repo_root)

        self.assertIn("repo must equal 'aoa-kag'", str(context.exception))

    def test_missing_required_quest_schema_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            target = quest_path(repo_root, "AOA-KAG-Q-0002")
            write_text(
                target,
                target.read_text(encoding="utf-8").replace(
                    "anchor_ref:\n"
                    "  artifact: source-owned-export-dependencies\n"
                    "  ref: mechanics/boundary-bridge/parts/source-owned-export/docs/source-owned-export-dependencies.md\n"
                    "  note: exports stay derived and source-owned\n",
                    "",
                ),
            )

            with self.assertRaises(quest_store.QuestStoreValidationError) as context:
                quest_store.validate_questbook_surface(repo_root)

        self.assertIn("anchor_ref", str(context.exception))

    def test_source_boundary_phrase_missing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            write_text(
                repo_root / quest_store.QUESTBOOK_INTEGRATION_PATH,
                (repo_root / quest_store.QUESTBOOK_INTEGRATION_PATH)
                .read_text(encoding="utf-8")
                .replace("source repos remain the owners of meaning", "source repos stay nearby"),
            )

            with self.assertRaises(quest_store.QuestStoreValidationError) as context:
                quest_store.validate_questbook_surface(repo_root)

        self.assertIn("source repos remain the owners of meaning", str(context.exception))

    def test_dispatch_example_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            write_text(
                repo_root / quest_store.QUEST_DISPATCH_EXAMPLE_PATH,
                (repo_root / quest_store.QUEST_DISPATCH_EXAMPLE_PATH)
                .read_text(encoding="utf-8")
                .replace(
                    '"source_path": "quests/kag/captured/AOA-KAG-Q-0004.yaml"',
                    '"source_path": "quests/kag/captured/AOA-KAG-Q-9999.yaml"',
                ),
            )

            with self.assertRaises(quest_store.QuestStoreValidationError) as context:
                quest_store.validate_questbook_surface(repo_root)

        self.assertIn("AOA-KAG-Q-0004", str(context.exception))


if __name__ == "__main__":
    unittest.main()
