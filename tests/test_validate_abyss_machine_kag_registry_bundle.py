import unittest
from unittest.mock import patch

from scripts import validate_abyss_machine_kag_registry_bundle as validator


class AbyssMachineKagRegistryBundleValidatorTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
