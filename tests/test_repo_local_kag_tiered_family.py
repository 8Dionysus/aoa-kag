from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from scripts.generate_repo_local_kag_index import (
    build_index,
    build_repository_indexes,
    main as generate_main,
)
from scripts.build_repo_local_kag_release import main as build_release_main
from scripts.query_repo_local_kag import (
    MISSING_OBJECT_PREVIEW_LIMIT,
    build_unavailable_payload,
)
from scripts.repo_local.portable_family import (
    build_portable_family,
    load_portable_family,
    load_portable_family_with_state,
)
from scripts.repo_local.tiered_family import (
    TieredFamilyError,
    TieredFamilyUnavailable,
    build_tiered_family,
    export_portable_bundle,
    extract_pack_object,
    import_portable_bundle,
    load_tiered_family,
    validate_tiered_artifact_release,
    write_tiered_artifact,
    write_tiered_git_surface,
)
from tests.test_repo_local_kag_repository_indexes import write_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_OUTPUTS = {
    "repo-local-kag-corpus-manifest.schema.json": "corpus_manifest",
    "repo-local-kag-hot-profile.schema.json": "hot_profile",
    "kag-artifact-locator.schema.json": "locator_manifest",
    "kag-pack-index.schema.json": "pack_index",
    "repo-local-kag-distribution-manifest.schema.json": "distribution_manifest",
    "kag-owner-family-release.schema.json": "owner_release",
}


def build_fixture_family(root: Path):
    write_fixture(root)
    source = build_index(root)
    family = build_repository_indexes(source, repo_root=root)
    portable_manifest, portable_shards = build_portable_family(source, family)
    return source, family, portable_manifest, portable_shards


class RepoLocalKagTieredFamilyTests(unittest.TestCase):
    def test_contract_outputs_validate_against_public_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _, _, manifest, shards = build_fixture_family(root)
            build = build_tiered_family(manifest, shards)

        self.assertEqual(
            "kag_owner_family_release",
            build.owner_release["release_identity"]["artifact_class"],
        )
        self.assertEqual(
            "aoa-kag-owner-family-release-v1",
            build.owner_release["release_identity"]["abi_epoch"],
        )
        for schema_name, field in SCHEMA_OUTPUTS.items():
            schema = json.loads(
                (REPO_ROOT / "schemas" / schema_name).read_text(encoding="utf-8")
            )
            Draft202012Validator(schema).validate(getattr(build, field))

    def test_unavailable_query_result_is_schema_checked_and_bounded(self) -> None:
        missing = tuple(f"sha256:{index:064x}" for index in range(41))
        payload = build_unavailable_payload(
            repo_name="demo",
            state="artifact_required",
            missing_objects=missing,
            corpus_digest=f"sha256:{'a' * 64}",
            distribution_digest=f"sha256:{'b' * 64}",
            next_action="import a verified offline bundle",
        )
        schema = json.loads(
            (
                REPO_ROOT
                / "schemas"
                / "repo-local-kag-query-unavailable.schema.json"
            ).read_text(encoding="utf-8")
        )

        Draft202012Validator(schema).validate(payload)
        self.assertEqual(41, payload["missing_object_count"])
        self.assertEqual(
            MISSING_OBJECT_PREVIEW_LIMIT,
            len(payload["missing_objects"]),
        )
        self.assertTrue(payload["missing_objects_truncated"])

    def test_corpus_identity_is_independent_of_location_pack_and_placement(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _, _, manifest, shards = build_fixture_family(root)
            first = build_tiered_family(
                manifest,
                shards,
                max_pack_bytes=8 * 1024,
                shadow_mode=True,
                mirrors=[
                    {
                        "locator_id": "mirror-a",
                        "transport": "cas",
                        "priority": 10,
                        "object_key_template": "objects/sha256/{prefix}/{digest}",
                        "pack_key_template": "packs/sha256/{prefix}/{digest}.pack",
                        "trust_domain": "public-kag",
                        "mutable_location": True,
                    }
                ],
            )
            second = build_tiered_family(
                manifest,
                shards,
                max_pack_bytes=32 * 1024,
                shadow_mode=False,
                mirrors=[
                    {
                        "locator_id": "mirror-b",
                        "transport": "https",
                        "priority": 20,
                        "object_key_template": "objects/sha256/{prefix}/{digest}",
                        "pack_key_template": "packs/sha256/{prefix}/{digest}.pack",
                        "trust_domain": "public-kag",
                        "mutable_location": True,
                    }
                ],
            )

        self.assertEqual(
            first.corpus_manifest["corpus_identity"]["content_digest"],
            second.corpus_manifest["corpus_identity"]["content_digest"],
        )
        self.assertNotEqual(
            first.pack_index["pack_index_identity"]["content_digest"],
            second.pack_index["pack_index_identity"]["content_digest"],
        )
        self.assertNotEqual(
            first.distribution_manifest["distribution_identity"]["content_digest"],
            second.distribution_manifest["distribution_identity"]["content_digest"],
        )

    def test_record_change_changes_corpus_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _, _, first_manifest, first_shards = build_fixture_family(root)
            first = build_tiered_family(first_manifest, first_shards)
            (root / "README.md").write_text("# Demo\n\nChanged.\n", encoding="utf-8")
            second_source = build_index(root)
            second_family = build_repository_indexes(second_source, repo_root=root)
            second_manifest, second_shards = build_portable_family(
                second_source,
                second_family,
                previous_manifest=first_manifest,
            )
            second = build_tiered_family(second_manifest, second_shards)

        self.assertNotEqual(
            first.corpus_manifest["corpus_identity"]["content_digest"],
            second.corpus_manifest["corpus_identity"]["content_digest"],
        )

    def test_externalized_family_round_trips_v2_through_dual_reader(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as artifact_tmp:
            root = Path(repo_tmp)
            artifact_root = Path(artifact_tmp)
            source, family, manifest, shards = build_fixture_family(root)
            build = build_tiered_family(manifest, shards, shadow_mode=False)
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact_root, build)

            rebuilt_source, rebuilt_family, loaded_manifest = load_portable_family(
                root,
                artifact_root=artifact_root,
                allow_shadow_git=False,
            )
            _, _, _, state = load_tiered_family(
                root,
                artifact_root=artifact_root,
                allow_shadow_git=False,
            )

        self.assertEqual(source, rebuilt_source)
        self.assertEqual(family, rebuilt_family)
        self.assertEqual(
            "aoa-repo-local-kag-distribution-manifest-v1",
            loaded_manifest["schema_version"],
        )
        self.assertEqual("complete", state["state"])

    def test_state_bearing_dual_reader_reports_cas_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as artifact_tmp:
            root = Path(repo_tmp)
            artifact_root = Path(artifact_tmp)
            source, family, manifest, shards = build_fixture_family(root)
            build = build_tiered_family(manifest, shards, shadow_mode=False)
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact_root, build)

            rebuilt_source, rebuilt_family, loaded, state = (
                load_portable_family_with_state(
                    root,
                    artifact_root=artifact_root,
                    allow_shadow_git=False,
                )
            )

        self.assertEqual(source, rebuilt_source)
        self.assertEqual(family, rebuilt_family)
        self.assertEqual(
            "aoa-repo-local-kag-distribution-manifest-v1",
            loaded["schema_version"],
        )
        self.assertTrue(state["complete"])
        self.assertGreater(state["routes"]["local_cas"], 0)
        self.assertEqual(0, state["routes"]["shadow_git"])

    def test_externalized_family_never_claims_missing_cold_objects_complete(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            root = Path(repo_tmp)
            _, _, manifest, shards = build_fixture_family(root)
            build = build_tiered_family(manifest, shards, shadow_mode=False)
            write_tiered_git_surface(root, build, externalize=True)

            with self.assertRaises(TieredFamilyUnavailable) as raised:
                load_tiered_family(root, allow_shadow_git=False)

        self.assertEqual("artifact_required", raised.exception.state)
        self.assertTrue(raised.exception.missing)

    def test_corrupt_cas_object_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as artifact_tmp:
            root = Path(repo_tmp)
            artifact_root = Path(artifact_tmp)
            _, _, manifest, shards = build_fixture_family(root)
            build = build_tiered_family(manifest, shards, shadow_mode=False)
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact_root, build)
            cold = next(
                item
                for item in build.owner_release["objects"]
                if item["placement"] == "artifact_cold"
            )
            (artifact_root / cold["object_key"]).write_bytes(b"corrupt\n")

            with self.assertRaisesRegex(TieredFamilyError, "digest"):
                load_tiered_family(
                    root,
                    artifact_root=artifact_root,
                    allow_shadow_git=False,
                )

    def test_release_validation_checks_every_declared_cas_object(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as artifact_tmp:
            root = Path(repo_tmp)
            artifact_root = Path(artifact_tmp)
            _, _, manifest, shards = build_fixture_family(root)
            build = build_tiered_family(manifest, shards)
            write_tiered_git_surface(root, build, externalize=False)
            write_tiered_artifact(artifact_root, build)
            hot = next(
                item
                for item in build.owner_release["objects"]
                if item["placement"] == "git_hot"
            )
            (artifact_root / hot["object_key"]).write_bytes(b"corrupt\n")

            with self.assertRaisesRegex(TieredFamilyError, "digest"):
                validate_tiered_artifact_release(root, artifact_root)

    def test_pack_ranges_extract_byte_exact_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _, _, manifest, shards = build_fixture_family(root)
            build = build_tiered_family(manifest, shards, max_pack_bytes=8 * 1024)

        for entry in build.pack_index["entries"]:
            content = extract_pack_object(
                build.pack_bytes[entry["pack_digest"]],
                entry,
            )
            self.assertEqual(build.object_bytes[entry["object_digest"]], content)

    def test_offline_bundle_import_serves_full_family_without_shadow_git(self) -> None:
        with (
            tempfile.TemporaryDirectory() as repo_tmp,
            tempfile.TemporaryDirectory() as artifact_tmp,
            tempfile.TemporaryDirectory() as export_tmp,
            tempfile.TemporaryDirectory() as import_tmp,
        ):
            root = Path(repo_tmp)
            artifact_root = Path(artifact_tmp)
            bundle_root = Path(export_tmp) / "owner-family"
            imported_root = Path(import_tmp)
            source, family, manifest, shards = build_fixture_family(root)
            build = build_tiered_family(manifest, shards, shadow_mode=False)
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact_root, build)
            bundle = export_portable_bundle(root, artifact_root, bundle_root)
            receipt = import_portable_bundle(bundle_root, imported_root)
            rebuilt_source, rebuilt_family, _, state = load_tiered_family(
                root,
                artifact_root=imported_root,
                allow_shadow_git=False,
            )

        self.assertFalse(bundle["network_required"])
        self.assertGreater(receipt["objects_added"], 0)
        self.assertEqual(source, rebuilt_source)
        self.assertEqual(family, rebuilt_family)
        self.assertEqual("complete", state["state"])

    def test_git_hot_profile_is_source_only_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _, _, manifest, shards = build_fixture_family(root)
            build = build_tiered_family(manifest, shards)

        selection = build.hot_profile["selection"]
        summary = build.distribution_manifest["summary"]
        budgets = build.distribution_manifest["budgets"]
        self.assertEqual(["source", "source_chunk"], selection["include_record_kinds"])
        self.assertEqual("forbidden", selection["runtime_frequency_inputs"])
        self.assertLess(summary["git_hot_bytes"], summary["corpus_total_bytes"])
        self.assertLessEqual(summary["git_hot_bytes"], budgets["owner_hard_bytes_max"])
        self.assertFalse(budgets["aggregate_ceiling_receiptable_by_owner"])

    def test_tiered_generator_write_check_and_release_validation(self) -> None:
        with (
            tempfile.TemporaryDirectory() as repo_tmp,
            tempfile.TemporaryDirectory() as artifact_tmp,
            tempfile.TemporaryDirectory() as check_artifact_tmp,
        ):
            root = Path(repo_tmp)
            artifact_root = Path(artifact_tmp)
            check_artifact_root = Path(check_artifact_tmp)
            write_fixture(root)
            write_result = generate_main(
                [
                    "--repo-root",
                    str(root),
                    "--tiered-family",
                    "--artifact-root",
                    str(artifact_root),
                ]
            )
            check_result = generate_main(
                [
                    "--repo-root",
                    str(root),
                    "--tiered-family",
                    "--artifact-root",
                    str(artifact_root),
                    "--check",
                ]
            )
            receipt = validate_tiered_artifact_release(root, artifact_root)
            materialized_check_result = generate_main(
                [
                    "--repo-root",
                    str(root),
                    "--tiered-family",
                    "--artifact-root",
                    str(check_artifact_root),
                    "--check",
                    "--materialize-artifact-on-check",
                ]
            )
            materialized_receipt = validate_tiered_artifact_release(
                root,
                check_artifact_root,
            )

        self.assertEqual(0, write_result)
        self.assertEqual(0, check_result)
        self.assertEqual(0, materialized_check_result)
        self.assertEqual("complete", receipt["state"])
        self.assertEqual("complete", materialized_receipt["state"])
        self.assertEqual("unsigned-candidate", receipt["signature_state"])

    def test_generated_lane_release_builder_uses_bounded_transient_artifact_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            transient_parent = base / "transient"
            root.mkdir()
            transient_parent.mkdir()
            write_fixture(root)
            with patch.dict(
                "os.environ",
                {"AOA_KAG_VALIDATION_ARTIFACT_PARENT": str(transient_parent)},
                clear=False,
            ):
                write_result = build_release_main(
                    ["--repo-root", str(root)]
                )
                check_result = build_release_main(
                    ["--repo-root", str(root), "--check"]
                )
                incremental_check_result = build_release_main(
                    [
                        "--repo-root",
                        str(root),
                        "--check",
                        "--incremental",
                    ]
                )

            remaining = list(transient_parent.iterdir())

        self.assertEqual(0, write_result)
        self.assertEqual(0, check_result)
        self.assertEqual(0, incremental_check_result)
        self.assertEqual([], remaining)

    def test_release_builder_routes_first_parent_on_default_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact_root = base / "artifact"
            root.mkdir()
            artifact_root.mkdir()
            subprocess.run(("git", "init", "-q", "-b", "main"), cwd=root, check=True)
            subprocess.run(("git", "config", "user.name", "KAG Test"), cwd=root, check=True)
            subprocess.run(
                ("git", "config", "user.email", "kag@example.test"),
                cwd=root,
                check=True,
            )
            (root / "surface.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(("git", "add", "surface.txt"), cwd=root, check=True)
            subprocess.run(("git", "commit", "-qm", "base"), cwd=root, check=True)
            base_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            (root / "surface.txt").write_text("head\n", encoding="utf-8")
            subprocess.run(("git", "commit", "-am", "head", "-q"), cwd=root, check=True)
            head_sha = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(
                ("git", "update-ref", "refs/remotes/origin/main", head_sha),
                cwd=root,
                check=True,
            )
            subprocess.run(
                (
                    "git",
                    "symbolic-ref",
                    "refs/remotes/origin/HEAD",
                    "refs/remotes/origin/main",
                ),
                cwd=root,
                check=True,
            )

            routed: list[str] = []

            def capture(argv: list[str]) -> int:
                routed.extend(argv)
                return 0

            with patch.dict(
                "os.environ",
                {
                    "AOA_REPO_LOCAL_KAG_HISTORY_REPO": "",
                    "AOA_REPO_LOCAL_KAG_HISTORY_REF": "",
                    "AOA_REPO_LOCAL_KAG_EVENT_HISTORY_REF": "",
                },
                clear=False,
            ), patch(
                "scripts.build_repo_local_kag_release.generate_main",
                side_effect=capture,
            ):
                result = build_release_main(
                    [
                        "--repo-root",
                        str(root),
                        "--artifact-root",
                        str(artifact_root),
                        "--check",
                    ]
                )

        self.assertEqual(0, result)
        self.assertEqual(base_sha, routed[routed.index("--history-ref") + 1])
        self.assertEqual(
            base_sha,
            routed[routed.index("--event-history-ref") + 1],
        )
        self.assertNotIn(head_sha, routed)

    def test_generated_lane_release_builder_preserves_externalized_placement(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact_root = base / "artifact"
            transient_parent = base / "transient"
            root.mkdir()
            transient_parent.mkdir()
            write_fixture(root)
            initial_result = build_release_main(
                [
                    "--repo-root",
                    str(root),
                    "--artifact-root",
                    str(artifact_root),
                    "--externalize-cold",
                ]
            )
            with patch.dict(
                "os.environ",
                {"AOA_KAG_VALIDATION_ARTIFACT_PARENT": str(transient_parent)},
                clear=False,
            ):
                lane_result = build_release_main(
                    ["--repo-root", str(root)]
                )
            manifest = json.loads(
                (
                    root
                    / "kag"
                    / "indexes"
                    / "index_family.manifest.json"
                ).read_text(encoding="utf-8")
            )
            remaining = list(transient_parent.iterdir())

        self.assertEqual(0, initial_result)
        self.assertEqual(0, lane_result)
        self.assertEqual("externalized", manifest["placement"]["state"])
        self.assertEqual([], remaining)

    def test_release_builder_preserves_externalized_placement_by_default(
        self,
    ) -> None:
        with (
            tempfile.TemporaryDirectory() as repo_tmp,
            tempfile.TemporaryDirectory() as artifact_tmp,
        ):
            root = Path(repo_tmp)
            artifact_root = Path(artifact_tmp)
            _, _, manifest, shards = build_fixture_family(root)
            externalized = build_tiered_family(
                manifest,
                shards,
                shadow_mode=False,
            )
            write_tiered_git_surface(root, externalized, externalize=True)
            write_tiered_artifact(artifact_root, externalized)
            cold_paths = [
                root
                / "kag"
                / "indexes"
                / "shards"
                / str(item["kind"])
                / f"{item['range']}.jsonl"
                for item in externalized.owner_release["objects"]
                if item["placement"] == "artifact_cold"
            ]
            self.assertTrue(cold_paths)
            self.assertTrue(all(not path.exists() for path in cold_paths))

            preserved = build_release_main(
                [
                    "--repo-root",
                    str(root),
                    "--artifact-root",
                    str(artifact_root),
                ]
            )
            preserved_manifest = json.loads(
                (
                    root / "kag/indexes/index_family.manifest.json"
                ).read_text(encoding="utf-8")
            )

            self.assertEqual(0, preserved)
            self.assertEqual(
                "externalized",
                preserved_manifest["placement"]["state"],
            )
            self.assertTrue(all(not path.exists() for path in cold_paths))

            restored = build_release_main(
                [
                    "--repo-root",
                    str(root),
                    "--artifact-root",
                    str(artifact_root),
                    "--retain-cold-in-git",
                ]
            )
            restored_manifest = json.loads(
                (
                    root / "kag/indexes/index_family.manifest.json"
                ).read_text(encoding="utf-8")
            )

            self.assertEqual(0, restored)
            self.assertEqual("shadow", restored_manifest["placement"]["state"])
            self.assertTrue(all(path.exists() for path in cold_paths))


if __name__ == "__main__":
    unittest.main()
