from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[5]
VALIDATOR_PATH = (
    REPO_ROOT
    / "mechanics"
    / "growth-cycle"
    / "parts"
    / "surface-growth-stop-rule"
    / "scripts"
    / "validate_surface_growth_stop_rule.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "surface_growth_stop_rule_validator",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stop_rule = load_validator()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class SurfaceGrowthStopRuleTests(unittest.TestCase):
    def write_valid_surface(self, repo_root: Path) -> None:
        for relative_path in (
            stop_rule.MATURITY_DOC,
            stop_rule.OWNER_WAIT_DOC,
            stop_rule.PROOF_EXPECTATIONS_DOC,
            stop_rule.MATURITY_DECISION,
            stop_rule.MANIFEST,
            stop_rule.GENERATED_MIN,
            stop_rule.EXAMPLE,
        ):
            source = REPO_ROOT / relative_path
            target = repo_root / relative_path
            write_text(target, source.read_text(encoding="utf-8"))

    def test_valid_surface_growth_stop_rule_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            stop_rule.validate_surface_growth_stop_rule(repo_root)

    def test_owner_wait_state_order_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            manifest_path = repo_root / stop_rule.MANIFEST
            manifest = load_json(manifest_path)
            assert isinstance(manifest, dict)
            manifest["owner_wait_states"] = list(reversed(manifest["owner_wait_states"]))
            write_json(manifest_path, manifest)

            with self.assertRaises(stop_rule.SurfaceGrowthStopRuleError) as context:
                stop_rule.validate_surface_growth_stop_rule(repo_root)

        self.assertIn("owner_wait_states", str(context.exception))

    def test_unblocked_generated_growth_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            generated_path = repo_root / stop_rule.GENERATED_MIN
            generated = load_json(generated_path)
            assert isinstance(generated, dict)
            generated["stop_rule"] = copy.deepcopy(generated["stop_rule"])
            generated["stop_rule"]["blocked_surface_ids"] = []
            write_json(generated_path, generated)

            with self.assertRaises(stop_rule.SurfaceGrowthStopRuleError) as context:
                stop_rule.validate_surface_growth_stop_rule(repo_root)

        self.assertIn("stop_rule", str(context.exception))

    def test_bounded_output_contract_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            manifest_path = repo_root / stop_rule.MANIFEST
            manifest = load_json(manifest_path)
            assert isinstance(manifest, dict)
            manifest["bounded_output_contract"] = copy.deepcopy(
                manifest["bounded_output_contract"]
            )
            manifest["bounded_output_contract"]["proof_ownership"] = "allowed"
            write_json(manifest_path, manifest)

            with self.assertRaises(stop_rule.SurfaceGrowthStopRuleError) as context:
                stop_rule.validate_surface_growth_stop_rule(repo_root)

        self.assertIn("bounded_output_contract", str(context.exception))

    def test_example_must_center_blocked_counterpart_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "aoa-kag"
            self.write_valid_surface(repo_root)
            example_path = repo_root / stop_rule.EXAMPLE
            example = load_json(example_path)
            assert isinstance(example, dict)
            example["surfaces"] = copy.deepcopy(example["surfaces"])
            example["surfaces"][0]["surface_id"] = "AOA-K-0001"
            write_json(example_path, example)

            with self.assertRaises(stop_rule.SurfaceGrowthStopRuleError) as context:
                stop_rule.validate_surface_growth_stop_rule(repo_root)

        self.assertIn("AOA-K-0008", str(context.exception))


if __name__ == "__main__":
    unittest.main()
