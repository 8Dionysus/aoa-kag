from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"

if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from scripts.provider_registry import (
    provider_ci_envs,
    provider_dependency_pins,
    provider_entries,
    provider_repo_order,
    sealed_provider_repos,
)
from scripts.validators.provider_registry import validate_provider_registry_contract


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class ProviderRegistryTests(unittest.TestCase):
    def test_provider_registry_matches_schema(self) -> None:
        payload = load_json(REPO_ROOT / "manifests" / "provider_registry.json")
        schema = load_json(REPO_ROOT / "schemas" / "provider-registry.schema.json")
        assert isinstance(schema, dict)
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(payload),
            key=lambda error: list(error.path),
        )
        self.assertEqual([], errors)

    def test_provider_registry_is_the_provider_coordinate_source(self) -> None:
        entries = provider_entries()
        repos = provider_repo_order()
        self.assertEqual(len(repos), len(set(repos)))
        self.assertEqual({entry["repo"] for entry in entries}, set(repos))
        self.assertIn("aoa-kag", repos)
        self.assertEqual({"aoa-session-memory"}, sealed_provider_repos())
        self.assertNotIn("aoa-kag", provider_ci_envs())
        self.assertNotIn("aoa-session-memory", provider_dependency_pins())

    def test_provider_registry_contract_validator_passes_current_surfaces(self) -> None:
        validate_provider_registry_contract()


if __name__ == "__main__":
    unittest.main()
