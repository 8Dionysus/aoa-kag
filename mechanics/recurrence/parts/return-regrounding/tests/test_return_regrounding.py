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
    / "recurrence"
    / "parts"
    / "return-regrounding"
    / "scripts"
    / "validate_return_regrounding.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "return_regrounding_validator",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


regrounding = load_validator()


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class ReturnRegroundingTests(unittest.TestCase):
    def expected_payload(self) -> dict[str, object]:
        return regrounding.validate_kag.build_return_regrounding_pack_payload(
            regrounding.validate_kag.build_registry_payload()
        )

    def patched_generation_read_json(self, overrides: dict[Path, object]):
        original = regrounding.kag_generation.read_json
        normalized = {Path(path).resolve(): copy.deepcopy(payload) for path, payload in overrides.items()}

        def side_effect(path: Path) -> object:
            resolved = Path(path).resolve()
            if resolved in normalized:
                return copy.deepcopy(normalized[resolved])
            return original(path)

        return patch.object(regrounding.kag_generation, "read_json", side_effect=side_effect)

    def test_valid_return_regrounding_boundary_passes(self) -> None:
        regrounding.validate_return_regrounding_boundary()

    def test_pack_rejects_local_kag_stronger_ref(self) -> None:
        expected_payload = self.expected_payload()
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["modes"][2]["stronger_refs"][0] = "mechanics/boundary-bridge/parts/federation-spine/generated/federation_spine.min.json"

        with self.assertRaises(regrounding.validate_kag.ValidationError) as context:
            regrounding.validate_kag.validate_return_regrounding_pack(
                broken_payload,
                expected_payload,
            )

        self.assertIn("stronger_refs", str(context.exception))

    def test_pack_rejects_counterpart_review_as_stronger_ref(self) -> None:
        expected_payload = self.expected_payload()
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["modes"][2]["stronger_refs"][0] = "mechanics/audit/parts/exposure-review/docs/counterpart-federation-exposure-review.md"

        with self.assertRaises(regrounding.validate_kag.ValidationError) as context:
            regrounding.validate_kag.validate_return_regrounding_pack(
                broken_payload,
                expected_payload,
            )

        self.assertIn("counterpart", str(context.exception))

    def test_pack_rejects_wrong_owner_repo_in_handoff_mode(self) -> None:
        expected_payload = self.expected_payload()
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["modes"][3]["stronger_refs"][0] = "aoa-routing/README.md"

        with self.assertRaises(regrounding.validate_kag.ValidationError) as context:
            regrounding.validate_kag.validate_return_regrounding_pack(
                broken_payload,
                expected_payload,
            )

        self.assertIn("stronger_refs", str(context.exception))

    def test_pack_rejects_duplicate_mode(self) -> None:
        expected_payload = self.expected_payload()
        broken_payload = copy.deepcopy(expected_payload)
        broken_payload["modes"][4]["mode_id"] = "handoff_guardrail_reentry"

        with self.assertRaises(regrounding.validate_kag.ValidationError) as context:
            regrounding.validate_kag.validate_return_regrounding_pack(
                broken_payload,
                expected_payload,
            )

        self.assertIn("duplicated", str(context.exception))

    def test_memo_memory_readiness_stays_owner_owned(self) -> None:
        regrounding.validate_return_regrounding_boundary()

    def test_recurrence_projection_example_is_part_local_contract(self) -> None:
        schema = load_json(REPO_ROOT / regrounding.RECURRENCE_KAG_PROJECTION_SCHEMA_PATH)
        assert isinstance(schema, dict)
        example = load_json(REPO_ROOT / regrounding.RECURRENCE_KAG_PROJECTION_EXAMPLE_PATH)
        assert isinstance(example, dict)

        broken_example = copy.deepcopy(example)
        broken_example["schema_version"] = "wrong"

        with patch.object(regrounding, "read_json") as read_json:
            def side_effect(path: Path) -> object:
                if Path(path).resolve() == (
                    REPO_ROOT / regrounding.RECURRENCE_KAG_PROJECTION_SCHEMA_PATH
                ).resolve():
                    return copy.deepcopy(schema)
                if Path(path).resolve() == (
                    REPO_ROOT / regrounding.RECURRENCE_KAG_PROJECTION_EXAMPLE_PATH
                ).resolve():
                    return copy.deepcopy(broken_example)
                return load_json(path)

            read_json.side_effect = side_effect
            with self.assertRaises(regrounding.ReturnRegroundingValidationError) as context:
                regrounding.validate_recurrence_kag_projection_companion()

        self.assertIn("schema violation", str(context.exception))

    def test_builder_rejects_mode_order_drift(self) -> None:
        manifest = load_json(regrounding.kag_generation.RETURN_REGROUNDING_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["mode_bindings"] = list(reversed(broken_manifest["mode_bindings"]))

        with self.patched_generation_read_json(
            {
                regrounding.kag_generation.RETURN_REGROUNDING_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(regrounding.kag_generation.GenerationError) as context:
                regrounding.kag_generation.build_return_regrounding_pack_payload(
                    regrounding.kag_generation.build_registry_payload()
                )

        self.assertIn("stable mode order", str(context.exception))

    def test_builder_rejects_unknown_dependency_ref(self) -> None:
        manifest = load_json(regrounding.kag_generation.RETURN_REGROUNDING_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["mode_bindings"][0]["dependency_refs"] = ["wrong-dependency"]

        with self.patched_generation_read_json(
            {
                regrounding.kag_generation.RETURN_REGROUNDING_MANIFEST_PATH: broken_manifest,
            }
        ):
            with self.assertRaises(regrounding.kag_generation.GenerationError) as context:
                regrounding.kag_generation.build_return_regrounding_pack_payload(
                    regrounding.kag_generation.build_registry_payload()
                )

        self.assertIn("unknown dependency", str(context.exception))


if __name__ == "__main__":
    unittest.main()
