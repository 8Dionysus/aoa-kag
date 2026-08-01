from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import issue_kag_mcp_source_identity as source_identity


REVISION = "1" * 40
SOURCE_DIGEST = "2" * 64
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


class KagMcpSourceIdentityTests(unittest.TestCase):
    def issue(self) -> tuple[dict, dict]:
        with (
            patch.object(source_identity, "_require_clean_git"),
            patch.object(source_identity, "_git_revision", return_value=REVISION),
            patch.object(
                source_identity,
                "_canonical_source_index_identity",
                return_value=(SOURCE_DIGEST, "kag/indexes/index_family.manifest.json"),
            ),
        ):
            return source_identity.issue_source_identity(
                clock=lambda: NOW,
                require_clean=True,
            )

    def test_receipt_is_content_addressed_and_schema_valid(self) -> None:
        receipt, overlay = self.issue()
        schema = json.loads(source_identity.SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        ).validate(receipt)
        unsigned = dict(receipt)
        claimed = unsigned.pop("receipt_digest")
        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        self.assertEqual(claimed, "sha256:" + hashlib.sha256(canonical).hexdigest())
        self.assertEqual(receipt["tree_digest"], "sha256:" + SOURCE_DIGEST)
        self.assertFalse(receipt["contains_secrets"])
        self.assertEqual(overlay["subjects"][0]["source"]["revision"], REVISION)
        self.assertEqual(
            overlay["subjects"][0]["source"]["evidence"]["evidence_refs"][0][
                "owner"
            ],
            "aoa-kag",
        )

    def test_outputs_are_private_and_distinct(self) -> None:
        receipt, overlay = self.issue()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "identity"
            receipt_path, overlay_path = source_identity.write_outputs(
                receipt,
                overlay,
                root,
            )

            self.assertNotEqual(receipt_path, overlay_path)
            self.assertEqual(receipt_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(overlay_path.stat().st_mode & 0o777, 0o600)

    def test_dirty_tracked_snapshot_is_rejected(self) -> None:
        with patch.object(
            source_identity,
            "_require_clean_git",
            side_effect=source_identity.KagSourceIdentityError("dirty"),
        ):
            with self.assertRaisesRegex(source_identity.KagSourceIdentityError, "dirty"):
                source_identity.issue_source_identity(clock=lambda: NOW)


if __name__ == "__main__":
    unittest.main()
