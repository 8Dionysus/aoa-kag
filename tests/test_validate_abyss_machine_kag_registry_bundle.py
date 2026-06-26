import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_abyss_machine_kag_registry_bundle as validator


class _FakeArtifactBundles:
    def __init__(self, trust_gate_response: dict) -> None:
        self.trust_gate_response = trust_gate_response

    def trust_gate(self, *args, **kwargs) -> dict:
        return self.trust_gate_response


class AbyssMachineKagRegistryBundleValidatorTest(unittest.TestCase):
    def test_manifest_declares_materialized_consumer_trust_gate_path(self) -> None:
        manifest = json.loads(validator.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        commands = "\n".join(manifest["consumer_command"])

        self.assertIn("evidence-promote", commands)
        self.assertIn("materialize-subjects", commands)
        self.assertIn("trust-gate", commands)
        self.assertIn("registry-latest", commands)
        self.assertIn("--consumer-ref aoa-kag:kag-registry", commands)
        self.assertIn("--source-repo aoa-kag", commands)
        self.assertIn("--trust-root-mode host_managed", commands)
        self.assertTrue(manifest["consumer_contract"]["subject_store_required"])
        self.assertEqual(
            manifest["consumer_contract"]["admission_gate"],
            "fail_closed_consumer_admission",
        )

    def test_portable_contract_fallback_when_abyss_machine_is_unavailable(self) -> None:
        with patch.object(
            validator,
            "_import_artifact_bundles",
            side_effect=validator.ArtifactBundlesUnavailable("missing abyss_machine"),
        ):
            payload = validator.validate_bundle(
                validator.DEFAULT_MANIFEST,
                validator.DEFAULT_SUBJECT,
                bundle_dir=None,
                registry_dir=None,
                clean=False,
            )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "portable_contract_only")
        self.assertEqual(payload["external_controls_unavailable"], validator.EXPECTED_REQUIRED_CONTROLS)
        self.assertTrue(payload["subject_inventory"])
        self.assertTrue(payload["adversarial_checks"]["checks"]["private_registry_marker"]["ok"])

    def test_require_abyss_machine_rejects_portable_fallback(self) -> None:
        with patch.object(
            validator,
            "_import_artifact_bundles",
            side_effect=validator.ArtifactBundlesUnavailable("missing abyss_machine"),
        ):
            with self.assertRaises(validator.ArtifactBundlesUnavailable):
                validator.validate_bundle(
                    validator.DEFAULT_MANIFEST,
                    validator.DEFAULT_SUBJECT,
                    bundle_dir=None,
                    registry_dir=None,
                    clean=False,
                    require_abyss_machine=True,
                )

    def test_pre_materialization_gate_accepts_fail_closed_subject_store_denial(self) -> None:
        trust_gate_response = {
            "ok": False,
            "verdict": "deny",
            "blockers": ["required_artifact_subject_store_not_verified"],
            "decision": {
                "model": "fail_closed_consumer_admission",
                "allow": False,
                "blockers": ["required_artifact_subject_store_not_verified"],
            },
            "inspected_claims": {
                "registry_latest": {"selected_record_is_latest": True},
                "controls": {"required_controls_missing": []},
                "source": {"source_repo_matched": True},
                "trust_root": {"trust_root_mode_matched": True},
                "verification": {"ok": True},
                "artifact_subject_store": {"required": True, "ok": False},
            },
        }
        payload = validator._trust_gate_denies_missing_subject_store(
            _FakeArtifactBundles(trust_gate_response),
            Path("registry"),
            {"promoted": {"record": {"subject_digest": "sha256:subject"}}},
        )

        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
