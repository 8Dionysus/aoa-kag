from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[5]
VALIDATOR_PATH = (
    REPO_ROOT
    / "mechanics"
    / "checkpoint"
    / "parts"
    / "reasoning-handoff"
    / "scripts"
    / "validate_reasoning_handoff.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "reasoning_handoff_validator",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


handoff = load_validator()


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class ReasoningHandoffTests(unittest.TestCase):
    def patched_generation_read_json(self, overrides: dict[Path, object]):
        original = handoff.kag_generation.read_json
        normalized = {Path(path).resolve(): copy.deepcopy(payload) for path, payload in overrides.items()}

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized:
                return copy.deepcopy(normalized[resolved])
            return original(path)

        return patch.object(handoff.kag_generation, "read_json", side_effect=side_effect)

    def patched_validation_read_json(self, overrides: dict[Path, object]):
        original = handoff.validate_kag.read_json
        normalized = {Path(path).resolve(): copy.deepcopy(payload) for path, payload in overrides.items()}

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized:
                return copy.deepcopy(normalized[resolved])
            return original(path)

        return patch.object(handoff.validate_kag, "read_json", side_effect=side_effect)

    def test_valid_reasoning_handoff_boundary_passes(self) -> None:
        handoff.validate_reasoning_handoff_boundary()

    def test_example_must_keep_counterpart_contract_refs(self) -> None:
        example_payload = load_json(handoff.validate_kag.REASONING_HANDOFF_EXAMPLE_PATH)
        assert isinstance(example_payload, dict)
        broken_payload = copy.deepcopy(example_payload)
        broken_payload["derived_surface_refs"] = [
            ref
            for ref in broken_payload["derived_surface_refs"]
            if ref != "mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md"
        ]

        with self.patched_validation_read_json(
            {
                handoff.validate_kag.REASONING_HANDOFF_EXAMPLE_PATH: broken_payload,
            }
        ):
            with self.assertRaises(handoff.ReasoningHandoffValidationError) as context:
                handoff.validate_reasoning_handoff_boundary()

        self.assertIn("derived_surface_refs", str(context.exception))

    def test_example_allows_missing_external_dependency_roots(self) -> None:
        missing_tos_root = REPO_ROOT / ".tmp" / "missing-Tree-of-Sophia"
        missing_memo_root = REPO_ROOT / ".tmp" / "missing-aoa-memo"

        with (
            patch.object(handoff.validate_kag, "TREE_OF_SOPHIA_ROOT", missing_tos_root),
            patch.object(handoff.validate_kag, "AOA_MEMO_ROOT", missing_memo_root),
        ):
            handoff.validate_kag.validate_reasoning_handoff_example()

    def test_builder_requires_current_kag_guardrail_refs(self) -> None:
        manifest = load_json(handoff.kag_generation.REASONING_HANDOFF_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["source_inputs"] = [
            source_input
            for source_input in broken_manifest["source_inputs"]
            if source_input["name"] != "counterpart_federation_exposure_review_doc"
        ]

        with self.patched_generation_read_json(
            {
                handoff.kag_generation.REASONING_HANDOFF_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(handoff.kag_generation.GenerationError) as context:
                handoff.kag_generation.build_reasoning_handoff_pack_payload()

        self.assertIn("KAG guardrail refs", str(context.exception))


if __name__ == "__main__":
    unittest.main()
