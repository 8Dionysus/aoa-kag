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
    pinned_provider_entries,
    provider_checkout_envs,
    provider_ci_envs,
    provider_dependency_pins,
    provider_entries,
    provider_root_from_entry,
    provider_repo_order,
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
        self.assertNotIn("aoa-kag", provider_ci_envs())
        self.assertIn("aoa-session-memory", provider_dependency_pins())

    def test_provider_checkout_envs_follow_registry_checkout_paths(self) -> None:
        entries = provider_entries()
        checkout_envs = provider_checkout_envs()

        expected_env_names = {
            entry["env"]
            for entry in entries
            if entry.get("checkout_mode") == "pinned"
            and entry.get("env")
            and entry.get("checkout_path")
        }
        self.assertEqual(expected_env_names, set(checkout_envs))
        for entry in entries:
            if entry.get("checkout_mode") != "pinned":
                continue
            env_name = entry.get("env")
            checkout_path = entry.get("checkout_path")
            if not env_name or not checkout_path:
                continue
            with self.subTest(repo=entry["repo"]):
                self.assertEqual((REPO_ROOT / checkout_path).resolve(), checkout_envs[env_name])
        self.assertEqual(
            (REPO_ROOT / ".deps" / "aoa-session-memory").resolve(),
            checkout_envs["AOA_SESSION_MEMORY_ROOT"],
        )

    def test_pinned_provider_entries_match_dependency_pins(self) -> None:
        self.assertEqual(
            provider_dependency_pins(),
            {
                entry["repo"]: entry["pinned_ref"]
                for entry in pinned_provider_entries()
            },
        )

    def test_private_provider_checkout_auth_is_explicit(self) -> None:
        session_memory = next(
            entry for entry in provider_entries() if entry["repo"] == "aoa-session-memory"
        )
        self.assertEqual(
            "AOA_SESSION_MEMORY_DEPLOY_KEY",
            session_memory["checkout_ssh_key_secret"],
        )

    def test_runtime_source_repositories_are_pinned_providers(self) -> None:
        entries = {entry["repo"]: entry for entry in provider_entries()}

        expected = {
            "abyss-stack": ("ABYSS_STACK_ROOT", ".deps/abyss-stack"),
            "abyss-machine": ("ABYSS_MACHINE_REPO_ROOT", ".deps/abyss-machine"),
        }
        for repo, (env_name, checkout_path) in expected.items():
            with self.subTest(repo=repo):
                entry = entries[repo]
                self.assertEqual("runtime_source", entry["owner_type"])
                self.assertEqual("runtime_source", entry["root_kind"])
                self.assertEqual("pinned", entry["checkout_mode"])
                self.assertEqual(env_name, entry["env"])
                self.assertEqual(checkout_path, entry["checkout_path"])
                self.assertRegex(entry["pinned_ref"], r"^[a-f0-9]{40}$")

    def test_runtime_source_roots_resolve_from_home_source_root(self) -> None:
        entry = {
            "repo": "abyss-stack",
            "root_kind": "runtime_source",
            "root": "abyss-stack",
        }

        root = provider_root_from_entry(
            entry,
            os_root=Path("/workspace/os"),
            home_src_root=Path("/workspace/src"),
        )

        self.assertEqual(Path("/workspace/src/abyss-stack"), root)

    def test_provider_registry_contract_validator_passes_current_surfaces(self) -> None:
        validate_provider_registry_contract()

    def test_local_subtree_protocol_lists_every_provider(self) -> None:
        protocol = (REPO_ROOT / "kag" / "LOCAL_SUBTREE_PROTOCOL.md").read_text(
            encoding="utf-8"
        )

        for repo in provider_repo_order():
            with self.subTest(repo=repo):
                self.assertIn(f"| `{repo}` |", protocol)


if __name__ == "__main__":
    unittest.main()
