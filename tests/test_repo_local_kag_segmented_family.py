from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.generate_repo_local_kag_index import (
    build_index,
    build_repository_indexes,
)
from scripts.repo_local.segmented_family import (
    REQUEST_BYTES_MAX,
    SegmentedFamilyError,
    build_segmented_family,
    check_segmented_output,
    load_segmented_family,
    read_segment,
    validate_segmented_manifest,
    write_segmented_output,
)
from tests.test_repo_local_kag_repository_indexes import write_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]


class RepoLocalKagSegmentedFamilyTests(unittest.TestCase):
    def _build(self):
        root = Path(tempfile.mkdtemp())
        write_fixture(root)
        source = build_index(root)
        family = build_repository_indexes(source, repo_root=root)
        return root, source, family, build_segmented_family(source, family)

    def test_manifest_schema_and_bounded_round_trip(self) -> None:
        root, source, family, build = self._build()
        schema = json.loads(
            (REPO_ROOT / "schemas/repo-local-kag-segmented-family.schema.json")
            .read_text(encoding="utf-8")
        )
        Draft202012Validator(schema).validate(build.manifest)
        validate_segmented_manifest(build.manifest)
        write_segmented_output(root, build)
        self.assertTrue(check_segmented_output(root, build))
        loaded_source, loaded_family, loaded_manifest = load_segmented_family(
            root,
            max_materialized_bytes=64 * 1024 * 1024,
        )
        self.assertEqual(source["index_identity"], loaded_source["index_identity"])
        self.assertEqual(
            {kind: len(payload["entries"]) for kind, payload in family.items()},
            {kind: len(payload["entries"]) for kind, payload in loaded_family.items()},
        )
        self.assertEqual(
            build.manifest["family_identity"],
            loaded_manifest["family_identity"],
        )

    def test_request_cap_cannot_bypass_manifest_authority(self) -> None:
        root, _, _, build = self._build()
        write_segmented_output(root, build)
        descriptor = build.manifest["segments"][0]
        for cap in (0, -1, True, REQUEST_BYTES_MAX + 1):
            with self.subTest(cap=cap), self.assertRaises(SegmentedFamilyError):
                read_segment(root, build.manifest, descriptor, request_bytes_max=cap)

    def test_tampering_digest_and_manifest_fails_closed(self) -> None:
        root, _, _, build = self._build()
        write_segmented_output(root, build)
        descriptor = build.manifest["segments"][0]
        path = root / descriptor["path"]
        path.write_bytes(path.read_bytes() + b"tamper\n")
        with self.assertRaisesRegex(SegmentedFamilyError, "(digest|byte count)"):
            read_segment(root, build.manifest, descriptor)
        edited = copy.deepcopy(build.manifest)
        edited["budgets"]["request_bytes_max"] = 0
        with self.assertRaises(SegmentedFamilyError):
            validate_segmented_manifest(edited)

    def test_default_complete_assembly_is_bounded(self) -> None:
        root, _, _, build = self._build()
        write_segmented_output(root, build)
        with self.assertRaisesRegex(SegmentedFamilyError, "materialisation budget"):
            load_segmented_family(root, max_materialized_bytes=0)
        with self.assertRaisesRegex(SegmentedFamilyError, "materialisation budget"):
            load_segmented_family(
                root,
                max_materialized_bytes=build.manifest["summary"]["logical_bytes"] - 1,
            )


if __name__ == "__main__":
    unittest.main()
