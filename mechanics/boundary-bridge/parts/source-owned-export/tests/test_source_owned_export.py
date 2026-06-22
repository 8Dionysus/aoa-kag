from __future__ import annotations

import copy
from contextlib import ExitStack, contextmanager
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[5]
VALIDATOR_PATH = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "source-owned-export"
    / "scripts"
    / "validate_source_owned_export.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "source_owned_export_validator",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


source_export = load_validator()


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class SourceOwnedExportTests(unittest.TestCase):
    @contextmanager
    def patched_read_json(self, target_modules, overrides: dict[Path, object]):
        if not isinstance(target_modules, tuple):
            target_modules = (target_modules,)
        normalized = {Path(path).resolve(): copy.deepcopy(payload) for path, payload in overrides.items()}

        def side_effect_for(original):
            def side_effect(path: Path) -> object:
                resolved = Path(path).resolve()
                if resolved in normalized:
                    return copy.deepcopy(normalized[resolved])
                return original(path)

            return side_effect

        with ExitStack() as stack:
            for module in target_modules:
                stack.enter_context(
                    patch.object(
                        module,
                        "read_json",
                        side_effect=side_effect_for(module.read_json),
                    )
                )
            yield

    def memo_kag_export_payload(self) -> dict[str, object]:
        return {
            "owner_repo": "aoa-memo",
            "kind": "bridge",
            "object_id": source_export.validate_kag.EXPECTED_MEMO_KAG_EXPORT_ENTRY_SURFACE["match_value"],
            "primary_question": "How should aoa-memo publish a bridge-bearing memory object for KAG use without turning memo into graph truth?",
            "summary_50": "Source-owned tiny export for a provenance-visible memo bridge.",
            "summary_200": "Source-owned tiny export capsule for the current reviewed memo bridge candidate so aoa-kag can consume one explicit bridge-bearing memory object by source-owned entry surface rather than by inferred graph meaning.",
            "source_inputs": copy.deepcopy(source_export.validate_kag.EXPECTED_MEMO_KAG_EXPORT_SOURCE_INPUTS),
            "entry_surface": copy.deepcopy(source_export.validate_kag.EXPECTED_MEMO_KAG_EXPORT_ENTRY_SURFACE),
            "section_handles": copy.deepcopy(source_export.validate_kag.EXPECTED_MEMO_KAG_EXPORT_SECTION_HANDLES),
            "direct_relations": copy.deepcopy(source_export.validate_kag.EXPECTED_MEMO_KAG_EXPORT_DIRECT_RELATIONS),
            "provenance_note": "Guide to source, not source replacement, built from the memo-owned bridge object plus explicit Tree-of-Sophia support refs.",
            "non_identity_boundary": "Source-owned memo export for KAG readiness; derived consumers must not treat this bridge capsule as normalized graph truth, routing authority, or replacement for Tree-of-Sophia-authored meaning.",
        }

    def test_valid_source_owned_export_boundary_passes(self) -> None:
        source_export.validate_source_owned_export_boundary()

    def test_memo_donor_must_keep_owner_primary_input(self) -> None:
        broken_payload = self.memo_kag_export_payload()
        broken_payload["source_inputs"] = [
            {
                "repo": "aoa-memo",
                "source_class": "memo_object",
                "role": "supporting",
            },
            {
                "repo": "Tree-of-Sophia",
                "source_class": "tos_text",
                "role": "primary",
            },
        ]

        with self.patched_read_json(
            source_export.manifest_contracts,
            {
                source_export.validate_kag.AOA_MEMO_ROOT
                / source_export.validate_kag.EXPECTED_MEMO_KAG_EXPORT_PATH: broken_payload,
            }
        ):
            with self.assertRaises(source_export.SourceOwnedExportValidationError) as context:
                source_export.validate_source_owned_export_boundary()

        self.assertIn(".repo must equal 'aoa-memo'", str(context.exception))

    def test_memo_donor_must_remain_registry_only(self) -> None:
        manifest = load_json(source_export.validate_kag.FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        manifest = copy.deepcopy(manifest)
        memo_export = next(
            export
            for export in manifest["exports"]
            if export["owner_repo"] == "aoa-memo"
        )
        memo_export["activation"]["spine_visible"] = True

        with self.patched_read_json(
            source_export.manifest_contracts,
            {
                source_export.validate_kag.FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH: manifest,
            }
        ):
            with self.assertRaises(source_export.SourceOwnedExportValidationError) as context:
                source_export.validate_source_owned_export_boundary()

        self.assertIn("spine_visible", str(context.exception))

    def test_federation_export_registry_rejects_non_kag_view_routing_binding(self) -> None:
        manifest = load_json(source_export.validate_kag.FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH)
        assert isinstance(manifest, dict)
        manifest = copy.deepcopy(manifest)
        manifest["exports"][0]["routing_binding"]["kind"] = "other_view"

        with self.patched_read_json(
            source_export.manifest_contracts,
            {
                source_export.validate_kag.FEDERATION_EXPORT_REGISTRY_MANIFEST_PATH: manifest,
            }
        ):
            with self.assertRaises(source_export.validate_kag.ValidationError) as context:
                dependencies = source_export.manifest_contracts.validate_source_owned_export_dependency_manifest(
                    source_export.registry_manifest_surfaces()
                )
                source_export.manifest_contracts.validate_federation_export_registry_manifest(
                    dependencies
                )

        self.assertIn("routing_binding.kind", str(context.exception))

    def test_memo_boundary_doc_must_keep_read_only_consumer_stop_line(self) -> None:
        original = source_export.sibling_readiness.read_text

        def read_text(path: Path) -> str:
            if Path(path).resolve() == source_export.validate_kag.SOURCE_OWNED_EXPORT_DEPENDENCIES_DOC_PATH.resolve():
                return "Reviewed memo donor consumer boundary\n"
            return original(path)

        with patch.object(source_export.sibling_readiness, "read_text", side_effect=read_text):
            with self.assertRaises(source_export.SourceOwnedExportValidationError) as context:
                source_export.validate_source_owned_export_boundary()

        self.assertIn("read-only memory consumer", str(context.exception))

    def write_memo_export_fixture(
        self,
        memo_root: Path,
        payload: dict[str, object],
    ) -> None:
        export_path = memo_root / source_export.validate_kag.EXPECTED_MEMO_KAG_EXPORT_PATH
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_optional_memo_export_readiness_allows_missing_root(self) -> None:
        missing_root = REPO_ROOT / ".tmp" / "missing-aoa-memo-export"

        with patch.object(source_export.sibling_readiness, "AOA_MEMO_ROOT", missing_root), patch.object(
            source_export.source_refs,
            "AOA_MEMO_ROOT",
            missing_root,
        ):
            source_export.sibling_readiness.validate_optional_memo_source_owned_export_readiness()

    def test_optional_memo_export_readiness_rejects_wrong_entry_surface(self) -> None:
        payload = self.memo_kag_export_payload()
        payload["entry_surface"]["path"] = "generated/memory_object_sections.full.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            memo_root = Path(tmpdir)
            self.write_memo_export_fixture(memo_root, payload)

            with patch.object(source_export.sibling_readiness, "AOA_MEMO_ROOT", memo_root), patch.object(
                source_export.source_refs,
                "AOA_MEMO_ROOT",
                memo_root,
            ):
                with self.assertRaises(source_export.validate_kag.ValidationError) as context:
                    source_export.sibling_readiness.validate_optional_memo_source_owned_export_readiness()

        self.assertIn("entry_surface", str(context.exception))

    def test_optional_memo_export_readiness_rejects_missing_tos_supporting_input(self) -> None:
        payload = self.memo_kag_export_payload()
        payload["source_inputs"] = [payload["source_inputs"][0]]

        with tempfile.TemporaryDirectory() as tmpdir:
            memo_root = Path(tmpdir)
            self.write_memo_export_fixture(memo_root, payload)

            with patch.object(source_export.sibling_readiness, "AOA_MEMO_ROOT", memo_root), patch.object(
                source_export.source_refs,
                "AOA_MEMO_ROOT",
                memo_root,
            ):
                with self.assertRaises(source_export.validate_kag.ValidationError) as context:
                    source_export.sibling_readiness.validate_optional_memo_source_owned_export_readiness()

        self.assertIn("source_inputs", str(context.exception))

    def test_optional_memo_export_readiness_rejects_missing_direct_relation_target(self) -> None:
        payload = self.memo_kag_export_payload()

        with tempfile.TemporaryDirectory() as tmpdir:
            memo_root = Path(tmpdir)
            self.write_memo_export_fixture(memo_root, payload)
            generated = memo_root / "generated" / "memory-objects"
            generated.mkdir(parents=True)
            (generated / "memory_object_capsules.json").write_text(
                json.dumps({"capsules": []}, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch.object(source_export.sibling_readiness, "AOA_MEMO_ROOT", memo_root), patch.object(
                source_export.source_refs,
                "AOA_MEMO_ROOT",
                memo_root,
            ):
                with self.assertRaises(source_export.validate_kag.ValidationError) as context:
                    source_export.sibling_readiness.validate_optional_memo_source_owned_export_readiness()

        self.assertIn("direct_relations[0]", str(context.exception))

    def test_optional_memo_export_readiness_rejects_missing_provenance_thread_relation(self) -> None:
        payload = self.memo_kag_export_payload()
        payload["direct_relations"] = [
            relation
            for relation in payload["direct_relations"]
            if relation["relation_type"] != "provenance_thread"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            memo_root = Path(tmpdir)
            self.write_memo_export_fixture(memo_root, payload)
            generated = memo_root / "generated" / "memory-objects"
            generated.mkdir(parents=True)
            (generated / "memory_object_capsules.json").write_text(
                json.dumps({"memory_objects": []}, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch.object(source_export.sibling_readiness, "AOA_MEMO_ROOT", memo_root), patch.object(
                source_export.source_refs,
                "AOA_MEMO_ROOT",
                memo_root,
            ):
                with self.assertRaises(source_export.validate_kag.ValidationError) as context:
                    source_export.sibling_readiness.validate_optional_memo_source_owned_export_readiness()

        self.assertIn("direct_relations", str(context.exception))

    def test_memo_source_owned_export_consumer_boundary_rejects_graph_truth_takeover(self) -> None:
        original_read_text = source_export.sibling_readiness.read_text

        def fake_read_text(path: Path) -> str:
            text = original_read_text(path)
            if Path(path) == source_export.validate_kag.SOURCE_OWNED_EXPORT_DEPENDENCIES_DOC_PATH:
                return text.replace(
                    "must not treat the donor as normalized",
                    "may treat the donor as normalized",
                    1,
                )
            return text

        with patch.object(source_export.sibling_readiness, "read_text", side_effect=fake_read_text):
            with self.assertRaises(source_export.validate_kag.ValidationError) as context:
                source_export.sibling_readiness.validate_memo_source_owned_export_consumer_boundary_doc()

        self.assertIn("must not treat the donor", str(context.exception))


if __name__ == "__main__":
    unittest.main()
