from __future__ import annotations

import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from scripts.build_repo_local_kag_federation import (
    load_owner_bundle_with_delivery,
    parse_owner_artifact_roots,
)
from scripts.generate_repo_local_kag_index import (
    build_index,
    build_repository_indexes,
)
from scripts.repo_local.kag_impact import (
    classify_impact,
    immutable_owner_cache_key,
)
from scripts.repo_local.portable_family import build_portable_family
from scripts.repo_local.tiered_family import (
    CORPUS_MANIFEST_RELATIVE_PATH,
    DEFAULT_PACK_BYTES_MAX,
    OWNER_RELEASE_ARTIFACT_PATH,
    PACK_INDEX_ARTIFACT_PATH,
    TieredFamilyBuild,
    TieredFamilyError,
    TieredFamilyUnavailable,
    _identity_digest,
    build_tiered_family,
    copy_bundle_to_empty_destination,
    export_portable_bundle,
    extract_pack_object,
    import_portable_bundle,
    load_tiered_family,
    load_tiered_rows,
    owner_release_digest,
    prepare_owner_release_lifecycle,
    validate_distribution_manifest,
    validate_pack_index,
    validate_tiered_artifact_release,
    write_tiered_artifact,
    write_tiered_git_surface,
)
from scripts.validators import repo_local_kag_index as repo_local_kag_validator
from tests.test_repo_local_kag_repository_indexes import write_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PAYLOADS = {
    "repo-local-kag-corpus-manifest.schema.json": "corpus_manifest",
    "repo-local-kag-distribution-manifest.schema.json": (
        "distribution_manifest"
    ),
    "repo-local-kag-hot-profile.schema.json": "hot_profile",
    "kag-artifact-locator.schema.json": "locator_manifest",
    "kag-pack-index.schema.json": "pack_index",
    "kag-owner-family-release.schema.json": "owner_release",
}


def build_fixture_family(
    root: Path,
    *,
    shadow_mode: bool = True,
    max_pack_bytes: int = DEFAULT_PACK_BYTES_MAX,
    mirrors: list[dict[str, object]] | None = None,
) -> tuple[
    dict[str, object],
    dict[str, dict[str, object]],
    TieredFamilyBuild,
]:
    source = build_index(root)
    family = build_repository_indexes(source, repo_root=root)
    portable, shards = build_portable_family(source, family)
    tiered = build_tiered_family(
        portable,
        shards,
        shadow_mode=shadow_mode,
        max_pack_bytes=max_pack_bytes,
        mirrors=mirrors,
    )
    return source, family, tiered


class RepoLocalKagTieredDistributionTests(unittest.TestCase):
    def test_federation_loader_requires_and_reports_externalized_owner_artifact(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact = base / "artifact"
            root.mkdir()
            write_fixture(root)
            expected_source, expected_family, build = build_fixture_family(
                root,
                shadow_mode=False,
            )
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact, build)

            with self.assertRaises(TieredFamilyUnavailable):
                load_owner_bundle_with_delivery(
                    root,
                    allow_shadow_git=False,
                )
            source, family, delivery = load_owner_bundle_with_delivery(
                root,
                artifact_root=artifact,
                allow_shadow_git=False,
            )

        self.assertEqual(source, expected_source)
        self.assertEqual(family, expected_family)
        self.assertEqual(delivery["delivery_state"], "complete")
        self.assertTrue(delivery["complete"])
        self.assertEqual(
            delivery["corpus_digest"],
            build.corpus_manifest["corpus_identity"]["content_digest"],
        )
        self.assertEqual(
            delivery["distribution_digest"],
            build.distribution_manifest["distribution_identity"][
                "content_digest"
            ],
        )

    def test_owner_artifact_root_parser_is_owner_qualified(self) -> None:
        parsed = parse_owner_artifact_roots(
            ["owner-a=relative/artifact"],
            known_owners={"owner-a", "owner-b"},
        )
        self.assertEqual(
            parsed,
            {"owner-a": Path("relative/artifact").resolve()},
        )
        with self.assertRaisesRegex(SystemExit, "unknown artifact-root owner"):
            parse_owner_artifact_roots(
                ["other=/tmp/artifact"],
                known_owners={"owner-a"},
            )
        with self.assertRaisesRegex(SystemExit, "duplicate artifact root"):
            parse_owner_artifact_roots(
                ["owner-a=/tmp/one", "owner-a=/tmp/two"],
                known_owners={"owner-a"},
            )

    def test_baseline_evidence_is_schema_valid_and_reconciles(self) -> None:
        schema = json.loads(
            (
                REPO_ROOT
                / "schemas"
                / "kag-tiered-baseline-evidence.schema.json"
            ).read_text(encoding="utf-8")
        )
        evidence = json.loads(
            (
                REPO_ROOT
                / "docs"
                / "validation"
                / "kag_tiered_baseline.evidence.json"
            ).read_text(encoding="utf-8")
        )

        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(evidence)
        self.assertEqual(24, len(evidence["owners"]))
        self.assertEqual(
            evidence["observed"]["tracked_bytes"],
            sum(owner["tracked_bytes"] for owner in evidence["owners"]),
        )
        self.assertEqual(
            evidence["observed"]["shards"],
            sum(owner["shards"] for owner in evidence["owners"]),
        )
        self.assertEqual(
            evidence["drift"]["tracked_bytes"],
            evidence["observed"]["tracked_bytes"]
            - evidence["claimed"]["tracked_bytes"],
        )

    def test_contract_payloads_match_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            _, _, build = build_fixture_family(root)

        for schema_name, attribute in SCHEMA_PAYLOADS.items():
            with self.subTest(schema=schema_name):
                schema = json.loads(
                    (REPO_ROOT / "schemas" / schema_name).read_text(
                        encoding="utf-8"
                    )
                )
                Draft202012Validator.check_schema(schema)
                errors = list(
                    Draft202012Validator(schema).iter_errors(
                        getattr(build, attribute)
                    )
                )
                self.assertEqual([], errors)

    def test_corpus_identity_is_independent_of_location_pack_and_shadow_state(
        self,
    ) -> None:
        mirrors = [
            {
                "locator_id": "alternate-cas",
                "transport": "https",
                "priority": 10,
                "object_key_template": (
                    "objects/sha256/{prefix}/{digest}"
                ),
                "pack_key_template": (
                    "packs/sha256/{prefix}/{digest}.pack"
                ),
                "trust_domain": "public-kag",
                "mutable_location": True,
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            _, _, default = build_fixture_family(root)
            _, _, relocated = build_fixture_family(
                root,
                shadow_mode=False,
                max_pack_bytes=8 * 1024,
                mirrors=mirrors,
            )

        self.assertEqual(
            default.corpus_manifest["corpus_identity"]["content_digest"],
            relocated.corpus_manifest["corpus_identity"]["content_digest"],
        )
        self.assertNotEqual(
            default.distribution_manifest["distribution_identity"][
                "content_digest"
            ],
            relocated.distribution_manifest["distribution_identity"][
                "content_digest"
            ],
        )
        self.assertNotEqual(
            default.locator_manifest["locator_identity"]["content_digest"],
            relocated.locator_manifest["locator_identity"]["content_digest"],
        )
        self.assertGreater(
            relocated.pack_index["summary"]["packs"],
            default.pack_index["summary"]["packs"],
        )

    def test_record_content_change_changes_corpus_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            _, _, before = build_fixture_family(root)
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\nTiered corpus change.\n",
                encoding="utf-8",
            )
            _, _, after = build_fixture_family(root)

        self.assertNotEqual(
            before.corpus_manifest["corpus_identity"]["content_digest"],
            after.corpus_manifest["corpus_identity"]["content_digest"],
        )

    def test_pack_ranges_extract_exact_shard_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            _, _, build = build_fixture_family(
                root,
                max_pack_bytes=8 * 1024,
            )

        validate_pack_index(build.pack_index, build.pack_bytes)
        for entry in build.pack_index["entries"]:
            content = extract_pack_object(
                build.pack_bytes[entry["pack_digest"]],
                entry,
            )
            self.assertEqual(
                build.object_bytes[entry["object_digest"]],
                content,
            )

    def test_pack_index_rejects_noncanonical_bundle_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            _, _, build = build_fixture_family(
                root,
                max_pack_bytes=8 * 1024,
            )

        for object_key in ("../outside.pack", "/tmp/outside.pack"):
            with self.subTest(object_key=object_key):
                tampered = copy.deepcopy(build.pack_index)
                tampered["packs"][0]["object_key"] = object_key
                tampered["pack_index_identity"]["content_digest"] = (
                    _identity_digest(tampered, "pack_index_identity")
                )
                with self.assertRaisesRegex(
                    TieredFamilyError,
                    "canonical portable digest path",
                ):
                    validate_pack_index(tampered)

    def test_pack_index_binds_declared_sizes_to_actual_pack_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            _, _, build = build_fixture_family(
                root,
                max_pack_bytes=8 * 1024,
            )

        tampered = copy.deepcopy(build.pack_index)
        tampered["packs"][0]["bytes"] -= 1
        tampered["summary"]["bytes"] -= 1
        tampered["pack_index_identity"]["content_digest"] = (
            _identity_digest(tampered, "pack_index_identity")
        )

        with self.assertRaisesRegex(
            TieredFamilyError,
            "declared byte count does not match content",
        ):
            validate_pack_index(tampered, build.pack_bytes)

    def test_distribution_requires_packs_to_cover_every_cold_object(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            _, _, build = build_fixture_family(
                root,
                max_pack_bytes=8 * 1024,
            )

        tampered_pack = copy.deepcopy(build.pack_index)
        descriptor_by_digest = {
            item["pack_digest"]: item
            for item in tampered_pack["packs"]
        }
        removed = next(
            entry
            for entry in tampered_pack["entries"]
            if descriptor_by_digest[entry["pack_digest"]]["objects"] > 1
        )
        tampered_pack["entries"].remove(removed)
        descriptor_by_digest[removed["pack_digest"]]["objects"] -= 1
        tampered_pack["summary"]["objects"] -= 1
        tampered_pack["pack_index_identity"]["content_digest"] = (
            _identity_digest(tampered_pack, "pack_index_identity")
        )

        tampered_distribution = copy.deepcopy(
            build.distribution_manifest
        )
        tampered_distribution["transport"]["pack_index_digest"] = (
            tampered_pack["pack_index_identity"]["content_digest"]
        )
        tampered_distribution["distribution_identity"]["content_digest"] = (
            _identity_digest(
                tampered_distribution,
                "distribution_identity",
            )
        )

        with self.assertRaisesRegex(
            TieredFamilyError,
            "exactly cover artifact-cold corpus objects",
        ):
            validate_distribution_manifest(
                tampered_distribution,
                corpus_manifest=build.corpus_manifest,
                hot_profile=build.hot_profile,
                locator_manifest=build.locator_manifest,
                pack_index=tampered_pack,
            )

    def test_distribution_validation_recomputes_corpus_measurements(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            _, _, build = build_fixture_family(root)

        for field in (
            "corpus_total_bytes",
            "git_hot_shard_bytes",
            "artifact_cold_bytes",
            "git_hot_objects",
            "artifact_cold_objects",
            "shadow_git_bytes",
            "git_hot_bytes",
        ):
            with self.subTest(field=field):
                tampered = copy.deepcopy(build.distribution_manifest)
                tampered["summary"][field] += 1
                tampered["distribution_identity"]["content_digest"] = (
                    _identity_digest(tampered, "distribution_identity")
                )
                with self.assertRaisesRegex(
                    TieredFamilyError,
                    f"summary {field}",
                ):
                    validate_distribution_manifest(
                        tampered,
                        corpus_manifest=build.corpus_manifest,
                        hot_profile=build.hot_profile,
                        locator_manifest=build.locator_manifest,
                        pack_index=build.pack_index,
                    )

    def test_externalized_family_is_hot_only_without_artifact_and_complete_with_cas(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact = base / "artifact"
            root.mkdir()
            write_fixture(root)
            expected_source, expected_family, build = build_fixture_family(
                root,
                shadow_mode=False,
            )
            write_tiered_git_surface(root, build, externalize=True)

            rows, state = load_tiered_rows(
                root,
                allow_shadow_git=False,
                allow_hot_only=True,
            )
            self.assertTrue(rows)
            self.assertEqual("hot_only", state["state"])
            self.assertFalse(state["complete"])
            with (
                patch.object(
                    repo_local_kag_validator,
                    "REPO_ROOT",
                    root,
                ),
                patch.object(
                    repo_local_kag_validator,
                    "REPO_LOCAL_KAG_FAMILY_MANIFEST_PATH",
                    root / "kag/indexes/index_family.manifest.json",
                ),
                patch.dict(
                    os.environ,
                    {"KAG_ARTIFACT_ROOT": ""},
                    clear=False,
                ),
            ):
                repo_local_kag_validator.validate_repo_local_kag_index_generated_payload()
            with self.assertRaises(TieredFamilyUnavailable) as caught:
                load_tiered_family(
                    root,
                    allow_shadow_git=False,
                )
            self.assertEqual("artifact_required", caught.exception.state)

            write_tiered_artifact(artifact, build)
            source, family, _, complete = load_tiered_family(
                root,
                artifact_root=artifact,
                allow_shadow_git=False,
            )

        self.assertEqual(expected_source, source)
        self.assertEqual(expected_family, family)
        self.assertEqual("complete", complete["state"])
        self.assertTrue(complete["complete"])

    def test_corrupt_cas_object_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact = base / "artifact"
            root.mkdir()
            write_fixture(root)
            _, _, build = build_fixture_family(root, shadow_mode=False)
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact, build)
            cold = next(iter(build.cold_shards.values()))
            digest = next(
                descriptor["content_digest"]
                for descriptor in build.corpus_manifest["objects"]
                if build.object_bytes[descriptor["content_digest"]] == cold
            )
            value = digest.removeprefix("sha256:")
            object_path = (
                artifact / "objects/sha256" / value[:2] / value
            )
            object_path.write_bytes(b"corrupt")

            with self.assertRaisesRegex(
                TieredFamilyError,
                "digest does not match",
            ):
                load_tiered_family(
                    root,
                    artifact_root=artifact,
                    allow_shadow_git=False,
                )

    def test_release_validation_binds_source_snapshot_to_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact = base / "artifact"
            root.mkdir()
            write_fixture(root)
            _, _, build = build_fixture_family(root, shadow_mode=False)
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact, build)
            distribution_digest = build.distribution_manifest[
                "distribution_identity"
            ]["content_digest"].removeprefix("sha256:")
            release_path = (
                artifact
                / "releases"
                / build.distribution_manifest["repo"]["name"]
                / distribution_digest
                / OWNER_RELEASE_ARTIFACT_PATH
            )
            release = json.loads(release_path.read_text(encoding="utf-8"))
            release["source"]["snapshot"] = "sha256:" + ("f" * 64)
            release_digest = owner_release_digest(release)
            release["release_identity"]["content_digest"] = release_digest
            release["signature"]["subject_digest"] = release_digest
            release_path.write_text(
                json.dumps(release, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                TieredFamilyError,
                "source snapshot does not match corpus",
            ):
                validate_tiered_artifact_release(root, artifact)

    def test_release_validation_binds_objects_and_packs_to_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact = base / "artifact"
            root.mkdir()
            write_fixture(root)
            _, _, build = build_fixture_family(root, shadow_mode=False)
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact, build)
            distribution_digest = build.distribution_manifest[
                "distribution_identity"
            ]["content_digest"].removeprefix("sha256:")
            release_path = (
                artifact
                / "releases"
                / build.distribution_manifest["repo"]["name"]
                / distribution_digest
                / OWNER_RELEASE_ARTIFACT_PATH
            )
            original = json.loads(release_path.read_text(encoding="utf-8"))

            for field in ("objects", "packs"):
                with self.subTest(field=field):
                    release = copy.deepcopy(original)
                    release[field] = release[field][1:]
                    release_digest = owner_release_digest(release)
                    release["release_identity"][
                        "content_digest"
                    ] = release_digest
                    release["signature"][
                        "subject_digest"
                    ] = release_digest
                    release_path.write_text(
                        json.dumps(release, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(
                        TieredFamilyError,
                        f"owner release {field} do not match",
                    ):
                        validate_tiered_artifact_release(root, artifact)

    def test_portable_bundle_supports_offline_full_read_and_deduplicated_import(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact = base / "artifact"
            bundle = base / "bundle"
            offline_repo = base / "offline-repo"
            offline_artifact = base / "offline-artifact"
            root.mkdir()
            write_fixture(root)
            expected_source, expected_family, build = build_fixture_family(
                root,
                shadow_mode=False,
            )
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact, build)
            exported = export_portable_bundle(
                root,
                artifact,
                bundle,
                lifecycle_state="release-ready",
                source_ref="a" * 40,
                verification_receipt="owner-validator:demo:kag-release",
            )
            exported_release = json.loads(
                (bundle / OWNER_RELEASE_ARTIFACT_PATH).read_text(
                    encoding="utf-8"
                )
            )

            shutil.copytree(root, offline_repo)
            receipt = import_portable_bundle(bundle, offline_artifact)
            second = import_portable_bundle(bundle, offline_artifact)
            source, family, _, state = load_tiered_family(
                offline_repo,
                artifact_root=offline_artifact,
                allow_shadow_git=False,
            )

        self.assertEqual(
            build.corpus_manifest["corpus_identity"]["content_digest"],
            exported["bundle_identity"]["corpus_digest"],
        )
        self.assertEqual(
            "commit:" + ("a" * 40),
            exported_release["source"]["ref"],
        )
        self.assertEqual(
            exported_release["source"]["ref"],
            exported_release["repo"]["git_ref"],
        )
        self.assertEqual(
            "release-ready",
            exported_release["lifecycle"]["state"],
        )
        self.assertGreater(receipt["objects_added"], 0)
        self.assertEqual(0, second["objects_added"])
        self.assertEqual(len(build.object_bytes), second["objects_reused"])
        self.assertEqual(expected_source, source)
        self.assertEqual(expected_family, family)
        self.assertEqual("complete", state["state"])

    def test_source_bound_release_requires_exact_commit_and_verification_receipt(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(root)
            _, _, build = build_fixture_family(root)

        with self.assertRaisesRegex(TieredFamilyError, "exact commit"):
            prepare_owner_release_lifecycle(
                build.owner_release,
                state="release-ready",
                verification_receipt="owner-validator:demo:kag-release",
            )
        with self.assertRaisesRegex(TieredFamilyError, "verification receipt"):
            prepare_owner_release_lifecycle(
                build.owner_release,
                state="release-ready",
                source_ref="b" * 40,
            )

    def test_portable_bundle_import_rejects_tampered_release_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact = base / "artifact"
            bundle = base / "bundle"
            imported = base / "imported"
            root.mkdir()
            write_fixture(root)
            _, _, build = build_fixture_family(root, shadow_mode=False)
            write_tiered_git_surface(root, build, externalize=True)
            write_tiered_artifact(artifact, build)
            export_portable_bundle(root, artifact, bundle)
            release_path = bundle / OWNER_RELEASE_ARTIFACT_PATH
            release = json.loads(release_path.read_text(encoding="utf-8"))
            release["source"]["ref"] = "commit:" + ("c" * 40)
            release["repo"]["git_ref"] = release["source"]["ref"]
            release_path.write_text(
                json.dumps(release, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                TieredFamilyError,
                "owner release digest does not match",
            ):
                import_portable_bundle(bundle, imported)

    def test_bundle_copy_refuses_nonempty_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            source = base / "source"
            destination = base / "destination"
            source.mkdir()
            destination.mkdir()
            (source / "value").write_text("source", encoding="utf-8")
            (destination / "value").write_text(
                "existing",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                TieredFamilyError,
                "destination must be empty",
            ):
                copy_bundle_to_empty_destination(source, destination)

    def test_impact_classifier_keeps_owner_fast_and_semantic_full_lanes_distinct(
        self,
    ) -> None:
        owner = classify_impact(
            ["docs/guide.md"],
            owner="demo",
        )
        distribution = classify_impact(
            ["kag/indexes/artifact_locators.json"],
            owner="demo",
        )
        central = classify_impact(
            ["scripts/repo_local/tiered_family.py"],
            owner="aoa-kag",
        )
        rollout = classify_impact(
            ["scripts/repo_local/tiered_rollout.py"],
            owner="aoa-kag",
        )
        governance = classify_impact(
            ["scripts/repo_local/tiered_governance.py"],
            owner="aoa-kag",
        )
        federation_builder = classify_impact(
            ["scripts/build_repo_local_kag_federation.py"],
            owner="aoa-kag",
        )
        federation_kernel = classify_impact(
            ["scripts/repo_local/federation.py"],
            owner="aoa-kag",
        )
        rollout_entrypoint = classify_impact(
            ["scripts/run_repo_local_kag_rollout.py"],
            owner="aoa-kag",
        )
        externalization_entrypoint = classify_impact(
            ["scripts/prepare_repo_local_kag_externalization.py"],
            owner="aoa-kag",
        )
        rollout_schema = classify_impact(
            ["schemas/kag-tiered-rollout-evidence.schema.json"],
            owner="aoa-kag",
        )
        governance_schema = classify_impact(
            ["schemas/kag-receipt-governance.schema.json"],
            owner="aoa-kag",
        )
        provider_map_schema = classify_impact(
            ["schemas/local-kag-provider-map.schema.json"],
            owner="aoa-kag",
        )
        generated_readmodels = tuple(
            classify_impact([path], owner="aoa-kag")
            for path in (
                "generated/kag_registry.json",
                "generated/kag_registry.min.json",
                "generated/local_kag_provider_map.json",
                "generated/local_kag_provider_map.min.json",
                "generated/repo_local_kag_coverage.json",
                "generated/repo_local_kag_coverage.min.json",
            )
        )
        readiness = classify_impact(
            ["manifests/local_kag_readiness.json"],
            owner="aoa-kag",
        )

        self.assertEqual("owner-local-fast", owner.required_validation_lane)
        self.assertEqual(
            "owner-distribution-fast",
            distribution.required_validation_lane,
        )
        self.assertEqual(
            "full-24-owner-audit",
            central.required_validation_lane,
        )
        self.assertIn("builder changed", central.full_fanout_reason)
        for classified in (rollout, governance):
            self.assertEqual(
                "full-24-owner-audit",
                classified.required_validation_lane,
            )
            self.assertIn(
                "artifact trust",
                classified.full_fanout_reason,
            )
        for classified in (federation_builder, federation_kernel):
            self.assertEqual(
                "incremental-federation",
                classified.required_validation_lane,
            )
            self.assertIn(
                "cross-owner-relation-change",
                classified.impact_classes,
            )
        for classified in (
            rollout_entrypoint,
            externalization_entrypoint,
            rollout_schema,
            governance_schema,
        ):
            self.assertEqual(
                "full-24-owner-audit",
                classified.required_validation_lane,
            )
            self.assertIn(
                "artifact trust",
                classified.full_fanout_reason,
            )
        self.assertEqual(
            "full-24-owner-audit",
            provider_map_schema.required_validation_lane,
        )
        self.assertIn(
            "family schema changed",
            provider_map_schema.full_fanout_reason,
        )
        for classified in generated_readmodels:
            self.assertEqual(
                "full-24-owner-audit",
                classified.required_validation_lane,
            )
            self.assertIn(
                "owner-membership-change",
                classified.impact_classes,
            )
            self.assertIn(
                "canonical owner membership changed",
                classified.full_fanout_reason,
            )
        self.assertEqual(
            "full-24-owner-audit",
            readiness.required_validation_lane,
        )
        self.assertIn(
            "canonical owner membership changed",
            readiness.full_fanout_reason,
        )
        self.assertEqual(
            immutable_owner_cache_key(
                owner="demo",
                source_snapshot="sha256:" + ("1" * 64),
                builder_digest="sha256:" + ("2" * 64),
                schema_epoch="schema-v1",
                canonicalization_epoch="canonical-v1",
            ),
            immutable_owner_cache_key(
                owner="demo",
                source_snapshot="sha256:" + ("1" * 64),
                builder_digest="sha256:" + ("2" * 64),
                schema_epoch="schema-v1",
                canonicalization_epoch="canonical-v1",
            ),
        )

    def test_artifact_release_contains_required_local_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "repo"
            artifact = base / "artifact"
            root.mkdir()
            write_fixture(root)
            _, _, build = build_fixture_family(root)
            receipt = write_tiered_artifact(artifact, build)
            distribution_digest = build.distribution_manifest[
                "distribution_identity"
            ]["content_digest"].removeprefix("sha256:")
            release_root = (
                artifact
                / "releases"
                / build.distribution_manifest["repo"]["name"]
                / distribution_digest
            )

            self.assertGreater(receipt["objects_added"], 0)
            self.assertTrue(
                (release_root / PACK_INDEX_ARTIFACT_PATH).is_file()
            )
            self.assertTrue(
                (release_root / OWNER_RELEASE_ARTIFACT_PATH).is_file()
            )
            self.assertEqual(
                build.corpus_manifest["corpus_identity"]["content_digest"],
                json.loads(
                    (
                        release_root
                        / CORPUS_MANIFEST_RELATIVE_PATH.name
                    ).read_text(encoding="utf-8")
                )["corpus_identity"]["content_digest"],
            )


if __name__ == "__main__":
    unittest.main()
