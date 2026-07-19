from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from scripts.generate_repo_local_kag_index import (
        build_index,
        build_repository_indexes,
        main as generate_index_main,
    )
except ImportError:  # pragma: no cover - direct script execution
    from generate_repo_local_kag_index import (  # type: ignore
        build_index,
        build_repository_indexes,
        main as generate_index_main,
    )

from .portable_family import (
    MANIFEST_RELATIVE_PATH,
    SCHEMA_VERSION as PORTABLE_V3_SCHEMA_VERSION,
    build_portable_family,
    render_manifest,
)
from .tiered_family import (
    BUNDLE_MANIFEST_PATH,
    CORPUS_MANIFEST_RELATIVE_PATH,
    DISTRIBUTION_SCHEMA_VERSION,
    HOT_PROFILE_RELATIVE_PATH,
    LOCATOR_MANIFEST_RELATIVE_PATH,
    OWNER_RELEASE_ARTIFACT_PATH,
    PACK_INDEX_ARTIFACT_PATH,
    TieredFamilyBuild,
    TieredFamilyError,
    TieredFamilyUnavailable,
    build_distribution_manifest,
    build_locator_manifest,
    build_owner_release,
    build_pack_index,
    build_tiered_family,
    export_portable_bundle,
    import_portable_bundle,
    load_tiered_family,
    load_tiered_manifests,
    validate_owner_release,
    validate_tiered_artifact_release,
    write_tiered_artifact,
    write_tiered_git_surface,
)
from .tiered_governance import (
    build_os_composition_candidate,
    validate_os_composition,
)


ROLLOUT_EVIDENCE_SCHEMA_VERSION = "aoa-kag-tiered-rollout-evidence-v1"
EXPECTED_OWNER_COUNT = 24
CANARY_OWNERS = (
    "aoa-techniques",
    "abyss-machine",
    "aoa-evals",
    "Agents-of-Abyss",
    "abyss-stack",
)
ZERO_DIGEST = "sha256:" + ("0" * 64)


class TieredRolloutError(TieredFamilyError):
    pass


@dataclass(frozen=True)
class OwnerSource:
    owner: str
    root: Path
    artifact_root: Path | None = None


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_uri(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise TieredRolloutError(f"cannot read {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise TieredRolloutError(f"{label} must be a JSON object")
    return payload


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
    )


def exact_git_head(root: Path, *, require_clean: bool = True) -> str:
    resolved = root.resolve()
    try:
        head = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=resolved,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ("git", "status", "--porcelain"),
            cwd=resolved,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise TieredRolloutError(
            f"owner source is not a readable Git checkout: {resolved}"
        ) from exc
    if len(head) not in {40, 64} or any(
        character not in "0123456789abcdef" for character in head
    ):
        raise TieredRolloutError(
            f"owner source does not resolve to an exact commit: {resolved}"
        )
    if require_clean and status:
        raise TieredRolloutError(
            f"owner source must be clean for exact-source publication: "
            f"{resolved}"
        )
    return head


def _release_root(
    artifact_root: Path,
    distribution: Mapping[str, Any],
) -> Path:
    owner = str(distribution.get("repo", {}).get("name") or "")
    digest = str(
        distribution.get("distribution_identity", {}).get(
            "content_digest"
        )
        or ""
    ).removeprefix("sha256:")
    if not owner or len(digest) != 64:
        raise TieredRolloutError(
            "tiered distribution is missing owner or digest"
        )
    return artifact_root.resolve() / "releases" / owner / digest


def _object_path(artifact_root: Path, digest: str) -> Path:
    value = digest.removeprefix("sha256:")
    return artifact_root.resolve() / "objects" / "sha256" / value[:2] / value


def _shard_path(kind: str, hash_range: str) -> Path:
    return Path("kag/indexes/shards") / kind / f"{hash_range}.jsonl"


def _load_v3_build(root: Path, *, shadow_mode: bool) -> TieredFamilyBuild:
    manifest = read_json(
        root / MANIFEST_RELATIVE_PATH,
        "portable v3 family manifest",
    )
    if manifest.get("schema_version") != PORTABLE_V3_SCHEMA_VERSION:
        raise TieredRolloutError(
            f"expected {PORTABLE_V3_SCHEMA_VERSION} input"
        )
    shards: dict[Path, bytes] = {}
    for descriptor in manifest.get("shards", []):
        if not isinstance(descriptor, Mapping) or not isinstance(
            descriptor.get("path"), str
        ):
            raise TieredRolloutError(
                "portable v3 family contains a malformed shard descriptor"
            )
        relative = Path(str(descriptor["path"]))
        try:
            shards[relative] = (root / relative).read_bytes()
        except FileNotFoundError as exc:
            raise TieredRolloutError(
                f"portable v3 shard is missing: {relative}"
            ) from exc
    return build_tiered_family(
        manifest,
        shards,
        shadow_mode=shadow_mode,
    )


def _load_v4_build(
    root: Path,
    artifact_root: Path,
) -> TieredFamilyBuild:
    (
        distribution,
        corpus,
        hot_profile,
        locators,
        pack_index,
    ) = load_tiered_manifests(root, artifact_root=artifact_root)
    if pack_index is None:
        raise TieredRolloutError("tiered owner needs a pack index")
    release_root = _release_root(artifact_root, distribution)
    release = read_json(
        release_root / OWNER_RELEASE_ARTIFACT_PATH,
        "owner family release",
    )
    object_bytes: dict[str, bytes] = {}
    hot_shards: dict[Path, bytes] = {}
    cold_shards: dict[Path, bytes] = {}
    hot_kinds = set(
        hot_profile.get("selection", {}).get(
            "include_record_kinds",
            [],
        )
    )
    for descriptor in corpus.get("objects", []):
        if not isinstance(descriptor, Mapping):
            raise TieredRolloutError(
                "tiered corpus contains a malformed object descriptor"
            )
        digest = str(descriptor.get("content_digest") or "")
        content = _object_path(artifact_root, digest).read_bytes()
        object_bytes[digest] = content
        relative = _shard_path(
            str(descriptor.get("kind") or ""),
            str(descriptor.get("range") or ""),
        )
        target = (
            hot_shards
            if descriptor.get("kind") in hot_kinds
            else cold_shards
        )
        target[relative] = content
    pack_bytes = {
        str(descriptor["pack_digest"]): (
            artifact_root.resolve() / str(descriptor["object_key"])
        ).read_bytes()
        for descriptor in pack_index.get("packs", [])
        if isinstance(descriptor, Mapping)
    }
    return TieredFamilyBuild(
        corpus_manifest=corpus,
        hot_profile=hot_profile,
        locator_manifest=locators,
        pack_index=pack_index,
        distribution_manifest=distribution,
        owner_release=release,
        object_bytes=object_bytes,
        hot_shards=hot_shards,
        cold_shards=cold_shards,
        pack_bytes=pack_bytes,
    )


def load_owner_build(
    source: OwnerSource,
    *,
    shadow_mode: bool,
) -> tuple[str, TieredFamilyBuild]:
    root = source.root.resolve()
    manifest = read_json(
        root / MANIFEST_RELATIVE_PATH,
        "owner family manifest",
    )
    schema = str(manifest.get("schema_version") or "")
    if schema == PORTABLE_V3_SCHEMA_VERSION:
        return schema, _load_v3_build(root, shadow_mode=shadow_mode)
    if schema != DISTRIBUTION_SCHEMA_VERSION:
        raise TieredRolloutError(
            f"{source.owner} has unsupported family schema {schema}"
        )
    if source.artifact_root is None:
        raise TieredRolloutError(
            f"{source.owner} v4 source requires an explicit artifact root"
        )
    build = _load_v4_build(root, source.artifact_root)
    current_shadow = (
        build.distribution_manifest.get("placement", {}).get("state")
        == "shadow"
    )
    if current_shadow == shadow_mode:
        return schema, build
    distribution = build_distribution_manifest(
        build.corpus_manifest,
        build.hot_profile,
        build.locator_manifest,
        build.pack_index,
        shadow_mode=shadow_mode,
    )
    release = build_owner_release(
        build.corpus_manifest,
        distribution,
        build.hot_profile,
        build.locator_manifest,
        build.pack_index,
    )
    return schema, replace(
        build,
        distribution_manifest=distribution,
        owner_release=release,
    )


def verify_location_and_pack_independence(
    build: TieredFamilyBuild,
) -> dict[str, Any]:
    relocated_locators = build_locator_manifest(
        build.corpus_manifest,
        mirrors=[
            {
                "locator_id": "rollout-proof-alternate",
                "transport": "https",
                "priority": 90,
                "object_key_template": (
                    "objects/sha256/{prefix}/{digest}"
                ),
                "pack_key_template": (
                    "packs/sha256/{prefix}/{digest}.pack"
                ),
                "trust_domain": "public-kag",
                "mutable_location": True,
            }
        ],
    )
    relocated_pack_index, _ = build_pack_index(
        build.corpus_manifest,
        build.object_bytes,
        hot_kinds=build.hot_profile["selection"][
            "include_record_kinds"
        ],
        max_pack_bytes=4 * 1024 * 1024,
    )
    relocated_distribution = build_distribution_manifest(
        build.corpus_manifest,
        build.hot_profile,
        relocated_locators,
        relocated_pack_index,
        shadow_mode=(
            build.distribution_manifest["placement"]["state"] == "shadow"
        ),
    )
    original_corpus = build.corpus_manifest["corpus_identity"][
        "content_digest"
    ]
    relocated_corpus = relocated_distribution["distribution_identity"][
        "corpus_digest"
    ]
    if original_corpus != relocated_corpus:
        raise TieredRolloutError(
            "locator or pack relocation changed corpus identity"
        )
    if (
        relocated_distribution["distribution_identity"]["content_digest"]
        == build.distribution_manifest["distribution_identity"][
            "content_digest"
        ]
    ):
        raise TieredRolloutError(
            "locator and pack relocation did not change distribution identity"
        )
    return {
        "corpus_identity_stable": True,
        "distribution_identity_changed": True,
        "alternate_pack_count": relocated_pack_index["summary"]["packs"],
    }


def verify_deterministic_source_rebuild(
    source: OwnerSource,
    build: TieredFamilyBuild,
    *,
    shadow_mode: bool,
    source_commit: str,
) -> dict[str, Any]:
    rebuilt_source = build_index(
        source.root,
        history_ref=source_commit,
    )
    rebuilt_family = build_repository_indexes(
        rebuilt_source,
        repo_root=source.root,
        history_ref=source_commit,
        event_history_ref=source_commit,
    )
    previous_manifest = {
        "partitioning": build.corpus_manifest["partitioning"],
        "budgets": {
            "tracked_bytes_max": build.distribution_manifest["budgets"][
                "owner_hard_bytes_max"
            ]
        },
    }
    portable, shards = build_portable_family(
        rebuilt_source,
        rebuilt_family,
        previous_manifest=previous_manifest,
    )
    rebuilt = build_tiered_family(
        portable,
        shards,
        shadow_mode=shadow_mode,
        migration=build.corpus_manifest["migration"],
    )
    expected = build.corpus_manifest["corpus_identity"]["content_digest"]
    actual = rebuilt.corpus_manifest["corpus_identity"]["content_digest"]
    if actual != expected:
        raise TieredRolloutError(
            f"deterministic source rebuild changed corpus identity for "
            f"{source.owner}: {actual} != {expected}"
        )
    return {
        "source_commit": "commit:" + source_commit,
        "corpus_digest": actual,
        "compatibility_digests": {
            str(item["kind"]): str(item["content_digest"])
            for item in rebuilt.corpus_manifest["compatibility"]["files"]
        },
    }


class MachineTrustAdapter:
    def __init__(
        self,
        machine_root: Path,
        *,
        registry_root: Path,
        subject_store_root: Path,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.machine_root = machine_root.resolve()
        self.registry_root = registry_root.resolve()
        self.subject_store_root = subject_store_root.resolve()
        self.env = dict(os.environ if env is None else env)
        # The provider registry uses ABYSS_MACHINE_REPO_ROOT to select the
        # abyss-machine KAG owner checkout.  Do not leak that provider override
        # into the host trust subprocess: artifact policy and CLI code must
        # resolve from the exact machine trust owner passed to this adapter.
        self.env["ABYSS_MACHINE_REPO_ROOT"] = str(self.machine_root)
        pythonpath = str(self.machine_root / "src")
        existing = self.env.get("PYTHONPATH", "")
        self.env["PYTHONPATH"] = (
            pythonpath if not existing else f"{pythonpath}:{existing}"
        )

    def _run(self, arguments: Sequence[str]) -> dict[str, Any]:
        command = (
            self.env.get("PYTHON", "python"),
            "-m",
            "abyss_machine.cli",
            "artifacts",
            *arguments,
            "--json",
        )
        process = subprocess.run(
            command,
            cwd=self.machine_root,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
        )
        try:
            payload = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            raise TieredRolloutError(
                "abyss-machine returned non-JSON output for "
                + " ".join(arguments[:2])
            ) from exc
        if process.returncode != 0:
            errors = payload.get("errors")
            raise TieredRolloutError(
                "abyss-machine trust command failed: "
                + " ".join(arguments[:2])
                + f"; errors={errors}"
            )
        return payload

    def sign_identity(self, payload_path: Path) -> dict[str, Any]:
        result = self._run(
            (
                "kag-sign-identity",
                str(payload_path.resolve()),
                "--backend",
                "cosign-local-key",
            )
        )
        verification = self._run(
            ("kag-verify-identity", str(payload_path.resolve()))
        )
        if not result.get("ok") or not verification.get("ok"):
            raise TieredRolloutError(
                "KAG identity signature did not verify"
            )
        return verification

    def admit(
        self,
        *,
        artifact_class: str,
        manifest_name: str,
        subject_root: Path,
        bundle_dir: Path,
        owner: str,
        source_ref: str,
        consumer_ref: str,
        evidence_ref: str,
        producer: str,
        lifecycle_state: str,
    ) -> dict[str, Any]:
        manifest = (
            self.machine_root
            / "manifests"
            / "artifact_bundles"
            / manifest_name
        )
        bundle_dir.mkdir(parents=True, exist_ok=True)
        built = self._run(
            (
                "build-sidecars",
                "--manifest",
                str(manifest),
                "--bundle-dir",
                str(bundle_dir.resolve()),
                "--subject-root",
                str(subject_root.resolve()),
                "--owner-repo",
                owner,
                "--source-ref",
                source_ref,
                "--access-policy",
                "public-kag",
            )
        )
        signed = self._run(
            (
                "sign",
                str(bundle_dir.resolve()),
                "--backend",
                "cosign-local-key",
            )
        )
        verified = self._run(
            (
                "verify",
                str(bundle_dir.resolve()),
                "--subject-root",
                str(subject_root.resolve()),
            )
        )
        promoted = self._run(
            (
                "evidence-promote",
                str(bundle_dir.resolve()),
                "--registry-dir",
                str(self.registry_root),
                "--lifecycle-state",
                lifecycle_state,
                "--consumer-ref",
                consumer_ref,
                "--evidence-ref",
                evidence_ref,
                "--source-repo",
                owner,
                "--source-ref",
                source_ref,
                "--subject-root",
                str(subject_root.resolve()),
                "--producer",
                producer,
                "--trust-root-mode",
                "host_managed",
            )
        )
        materialized = self._run(
            (
                "materialize-subjects",
                str(bundle_dir.resolve()),
                "--registry-dir",
                str(self.registry_root),
                "--store-root",
                str(self.subject_store_root),
                "--manifest",
                str(manifest),
                "--subject-root",
                str(subject_root.resolve()),
                "--consumer-intent",
                "agent",
                "--source-repo",
                owner,
                "--source-ref",
                source_ref,
                "--access-policy",
                "public-kag",
                "--trust-root-mode",
                "host_managed",
            )
        )
        gate = self._run(
            (
                "trust-gate",
                "--registry-dir",
                str(self.registry_root),
                "--artifact-class",
                artifact_class,
                "--consumer-intent",
                "agent",
                "--source-repo",
                owner,
                "--source-ref",
                source_ref,
                "--access-policy",
                "public-kag",
                "--trust-root-mode",
                "host_managed",
            )
        )
        if gate.get("verdict") != "allow":
            raise TieredRolloutError(
                f"artifact trust gate denied {artifact_class} for {owner}"
            )
        latest = self._run(
            (
                "registry-latest",
                "--registry-dir",
                str(self.registry_root),
                "--artifact-class",
                artifact_class,
                "--consumer-intent",
                "agent",
                "--source-repo",
                owner,
                "--source-ref",
                source_ref,
                "--access-policy",
                "public-kag",
                "--trust-root-mode",
                "host_managed",
            )
        )
        latest_record = (
            latest.get("record")
            if isinstance(latest.get("record"), Mapping)
            else {}
        )
        return {
            "sidecars_ok": bool(built.get("ok")),
            "outer_signature_ok": bool(signed.get("ok")),
            "bundle_verification_ok": bool(verified.get("ok")),
            "record_id": (
                promoted.get("record_id")
                or latest.get("record_id")
                or latest_record.get("record_id")
            ),
            "materialized_ok": bool(materialized.get("ok")),
            "trust_gate_verdict": gate.get("verdict"),
        }


def _reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _public_control_surface_safe(root: Path) -> bool:
    forbidden = (
        "/home/",
        "/srv/",
        "BEGIN PRIVATE KEY",
        "sk-",
        "session transcript",
    )
    for relative in (
        CORPUS_MANIFEST_RELATIVE_PATH,
        MANIFEST_RELATIVE_PATH,
        HOT_PROFILE_RELATIVE_PATH,
        LOCATOR_MANIFEST_RELATIVE_PATH,
        OWNER_RELEASE_ARTIFACT_PATH,
        BUNDLE_MANIFEST_PATH,
    ):
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden):
            return False
    return True


def prove_owner_release(
    source: OwnerSource,
    *,
    output_root: Path,
    shared_cas: Path,
    shadow_mode: bool,
    lifecycle_state: str,
    trust: MachineTrustAdapter,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_commit = exact_git_head(source.root)
    source_ref = "commit:" + source_commit
    input_schema, build = load_owner_build(
        source,
        shadow_mode=shadow_mode,
    )
    owner = str(build.corpus_manifest["repo"]["name"])
    if owner != source.owner:
        raise TieredRolloutError(
            f"owner coordinate mismatch: {source.owner} != {owner}"
        )
    owner_root = output_root / "owners" / owner
    staged_git = owner_root / "git-surface"
    exported = owner_root / "family-export"
    imported_cas = owner_root / "offline-imported-cas"
    outage_git = owner_root / "outage-git-surface"
    for path in (staged_git, exported, imported_cas, outage_git):
        _reset_directory(path)
    write_tiered_git_surface(
        staged_git,
        build,
        externalize=not shadow_mode,
    )
    first_write = write_tiered_artifact(shared_cas, build)
    second_write = write_tiered_artifact(shared_cas, build)
    if second_write["objects_added"] != 0:
        raise TieredRolloutError(
            f"second artifact publication added objects for {owner}"
        )
    release_validation = validate_tiered_artifact_release(
        staged_git,
        shared_cas,
    )
    verification_ref = (
        f"owner-validator:{owner}:tiered-{lifecycle_state}:"
        + build.corpus_manifest["corpus_identity"]["content_digest"]
    )
    bundle = export_portable_bundle(
        staged_git,
        shared_cas,
        exported,
        lifecycle_state=lifecycle_state,
        source_ref=source_ref,
        verification_receipt=verification_ref,
    )
    inner_verification = trust.sign_identity(
        exported / OWNER_RELEASE_ARTIFACT_PATH
    )
    signed_release = read_json(
        exported / OWNER_RELEASE_ARTIFACT_PATH,
        "signed owner release",
    )
    validate_owner_release(signed_release)
    import_receipt = import_portable_bundle(exported, imported_cas)
    (
        imported_source,
        imported_family,
        _,
        imported_state,
    ) = load_tiered_family(
        staged_git,
        artifact_root=imported_cas,
        allow_shadow_git=False,
    )
    if not imported_state.get("complete"):
        raise TieredRolloutError(
            f"offline import did not produce a complete family for {owner}"
        )
    compatibility = {
        "source": imported_source,
        **imported_family,
    }
    expected_compatibility = {
        str(item["kind"]): str(item["content_digest"])
        for item in build.corpus_manifest["compatibility"]["files"]
    }
    actual_compatibility = {
        kind: str(payload["index_identity"]["content_digest"])
        for kind, payload in compatibility.items()
    }
    if actual_compatibility != expected_compatibility:
        raise TieredRolloutError(
            f"v2 compatibility parity failed for {owner}"
        )
    write_tiered_git_surface(
        outage_git,
        build,
        externalize=True,
    )
    try:
        load_tiered_family(
            outage_git,
            artifact_root=None,
            allow_shadow_git=False,
        )
    except TieredFamilyUnavailable as exc:
        outage_state = exc.state
    else:
        raise TieredRolloutError(
            f"artifact outage was reported complete for {owner}"
        )
    cold_descriptors = [
        item
        for item in build.corpus_manifest["objects"]
        if item["kind"]
        not in build.hot_profile["selection"]["include_record_kinds"]
    ]
    corruption_rejected = True
    if cold_descriptors:
        corrupt_cas = owner_root / "corrupt-cas"
        _reset_directory(corrupt_cas)
        selected = cold_descriptors[0]
        corrupt_path = _object_path(
            corrupt_cas,
            str(selected["content_digest"]),
        )
        corrupt_path.parent.mkdir(parents=True, exist_ok=True)
        corrupt_path.write_bytes(b"corrupt\n")
        try:
            load_tiered_family(
                outage_git,
                artifact_root=corrupt_cas,
                allow_shadow_git=False,
            )
        except TieredFamilyError:
            corruption_rejected = True
        else:
            corruption_rejected = False
    if not corruption_rejected:
        raise TieredRolloutError(
            f"corrupt artifact was accepted for {owner}"
        )
    independence = verify_location_and_pack_independence(build)
    source_rebuild = verify_deterministic_source_rebuild(
        source,
        build,
        shadow_mode=shadow_mode,
        source_commit=source_commit,
    )
    trust_result = trust.admit(
        artifact_class="kag_owner_family_release",
        manifest_name="kag_owner_family_release.bundle.json",
        subject_root=exported,
        bundle_dir=output_root / "trust" / "bundles" / owner,
        owner=owner,
        source_ref=source_ref,
        consumer_ref="abyss-stack:kag-materializer",
        evidence_ref=verification_ref,
        producer=f"{owner}-kag-builder",
        lifecycle_state=lifecycle_state,
    )
    if not _public_control_surface_safe(exported):
        raise TieredRolloutError(
            f"public control-surface scan failed for {owner}"
        )
    release_digest = signed_release["release_identity"]["content_digest"]
    evidence = {
        "owner": owner,
        "source_ref": source_ref,
        "input_schema": input_schema,
        "placement_state": build.distribution_manifest["placement"][
            "state"
        ],
        "corpus_digest": build.corpus_manifest["corpus_identity"][
            "content_digest"
        ],
        "distribution_digest": build.distribution_manifest[
            "distribution_identity"
        ]["content_digest"],
        "release_digest": release_digest,
        "measurements": {
            **build.distribution_manifest["summary"],
            "objects_added": first_write["objects_added"],
            "objects_reused_initially": first_write["objects_reused"],
            "objects_reused_on_repeat": second_write["objects_reused"],
        },
        "checks": {
            "artifact_release": (
                "passed"
                if release_validation["state"] == "complete"
                else "failed"
            ),
            "inner_signature": (
                "passed" if inner_verification.get("ok") else "failed"
            ),
            "object_reuse": "passed",
            "mirror_and_pack_independence": "passed",
            "offline_export_import": "passed",
            "deterministic_source_rebuild": "passed",
            "dual_reader_without_shadow_git": "passed",
            "v2_compatibility": "passed",
            "artifact_outage": outage_state,
            "corruption_rejection": "passed",
            "public_control_surface": "passed",
        },
        "offline_import": import_receipt,
        "location_pack_proof": independence,
        "source_rebuild_proof": source_rebuild,
        "trust": trust_result,
        "bundle_digest": bundle["bundle_identity"]["content_digest"],
    }
    return evidence, signed_release, build.distribution_manifest


def prepare_owner_externalization(
    source: OwnerSource,
    *,
    artifact_root: Path,
) -> dict[str, Any]:
    """Write one isolated owner worktree into the externalized v4 shape.

    This step deliberately stops before release signing: the resulting Git
    surface must first be committed so the owner-family release can bind the
    exact commit that contains it.
    """
    base_commit = exact_git_head(source.root, require_clean=False)
    unstaged = subprocess.run(
        ("git", "diff", "--name-only"),
        cwd=source.root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    untracked = subprocess.run(
        ("git", "ls-files", "--others", "--exclude-standard"),
        cwd=source.root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if unstaged or untracked:
        raise TieredRolloutError(
            f"externalization preparation requires all authored changes "
            f"staged and no untracked files: {source.owner}"
        )
    input_manifest = read_json(
        source.root / MANIFEST_RELATIVE_PATH,
        "pre-externalization owner family manifest",
    )
    input_schema = str(input_manifest.get("schema_version") or "")
    generator_args = [
        "--repo-root",
        str(source.root.resolve()),
        "--tiered-family",
        "--artifact-root",
        str(artifact_root.resolve()),
        "--externalize-cold",
        "--history-ref",
        base_commit,
        "--event-history-ref",
        base_commit,
        "--budget-base-ref",
        base_commit,
        "--write-budget-receipt",
        "--budget-reason",
        (
            "artifact delivery migration: tiered content-addressed "
            "KAG distribution"
        ),
    ]
    if generate_index_main(generator_args) != 0:
        raise TieredRolloutError(
            f"authoritative externalization builder failed for "
            f"{source.owner}"
        )
    _, build = load_owner_build(
        OwnerSource(
            owner=source.owner,
            root=source.root,
            artifact_root=artifact_root,
        ),
        shadow_mode=False,
    )
    owner = str(build.corpus_manifest["repo"]["name"])
    if owner != source.owner:
        raise TieredRolloutError(
            f"owner coordinate mismatch: {source.owner} != {owner}"
        )
    publication = write_tiered_artifact(artifact_root, build)
    status = subprocess.run(
        ("git", "status", "--porcelain"),
        cwd=source.root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    changed_paths = sorted(
        line[3:] for line in status if len(line) >= 4
    )
    if not changed_paths:
        raise TieredRolloutError(
            f"externalization produced no Git changes for {owner}"
        )
    cold_paths = {
        path.as_posix() for path in build.cold_shards
    }
    remaining_cold = [
        path
        for path in cold_paths
        if (source.root / path).is_file()
    ]
    if remaining_cold:
        raise TieredRolloutError(
            f"externalization retained cold Git shards for {owner}"
        )
    corpus_digest = build.corpus_manifest["corpus_identity"][
        "content_digest"
    ]
    budget_receipt = (
        source.root
        / "kag"
        / "receipts"
        / "index_family_budget"
        / f"{corpus_digest.removeprefix('sha256:')}.json"
    )
    return {
        "owner": owner,
        "base_commit": base_commit,
        "input_schema": input_schema,
        "corpus_digest": corpus_digest,
        "distribution_digest": build.distribution_manifest[
            "distribution_identity"
        ]["content_digest"],
        "git_hot_bytes": build.distribution_manifest["summary"][
            "git_hot_bytes"
        ],
        "artifact_cold_bytes": build.distribution_manifest["summary"][
            "artifact_cold_bytes"
        ],
        "changed_paths": changed_paths,
        "artifact_publication": publication,
        "budget_receipt": (
            budget_receipt.relative_to(source.root).as_posix()
            if budget_receipt.is_file()
            else ""
        ),
        "head_commit_state": "pending-owner-commit",
    }


def build_signed_composition(
    releases: Sequence[Mapping[str, Any]],
    *,
    distributions_by_digest: Mapping[str, Mapping[str, Any]],
    output_root: Path,
    aoa_kag_source_ref: str,
    lifecycle_state: str,
    trust: MachineTrustAdapter,
    unresolved_references: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate = build_os_composition_candidate(
        releases,
        distributions_by_digest=distributions_by_digest,
        unresolved_references=unresolved_references,
    )
    export_root = output_root / "composition"
    _reset_directory(export_root)
    payload_path = export_root / "os-kag-composition.json"
    write_json(payload_path, candidate)
    inner_verification = trust.sign_identity(payload_path)
    signed = read_json(payload_path, "signed OS KAG composition")
    validate_os_composition(signed)
    trust_result = trust.admit(
        artifact_class="kag_os_composition",
        manifest_name="kag_os_composition.bundle.json",
        subject_root=export_root,
        bundle_dir=output_root / "trust" / "bundles" / "os-composition",
        owner="aoa-kag",
        source_ref=aoa_kag_source_ref,
        consumer_ref="abyss-stack:kag-federation",
        evidence_ref="owner-validator:aoa-kag:os-composition",
        producer="aoa-kag-federation-builder",
        lifecycle_state=lifecycle_state,
    )
    return signed, {
        "inner_signature": (
            "passed" if inner_verification.get("ok") else "failed"
        ),
        "trust": trust_result,
    }


def source_set_digest(owners: Sequence[Mapping[str, Any]]) -> str:
    coordinates = sorted(
        (
            {
                "owner": str(owner["owner"]),
                "source_ref": str(owner["source_ref"]),
                "corpus_digest": str(owner["corpus_digest"]),
            }
            for owner in owners
        ),
        key=lambda item: item["owner"],
    )
    return sha256_uri(canonical_json_bytes(coordinates))


def build_rollout_evidence(
    *,
    phase: str,
    owners: Sequence[Mapping[str, Any]],
    composition: Mapping[str, Any] | None,
    composition_proof: Mapping[str, Any] | None,
    artifact_unique_bytes: int | None = None,
) -> dict[str, Any]:
    owner_count = len(owners)
    git_hot_bytes = sum(
        int(owner["measurements"]["git_hot_bytes"])
        for owner in owners
    )
    corpus_total_bytes = sum(
        int(owner["measurements"]["corpus_total_bytes"])
        for owner in owners
    )
    artifact_cold_logical_bytes = sum(
        int(owner["measurements"]["artifact_cold_bytes"])
        for owner in owners
    )
    shadow_git_bytes = sum(
        int(owner["measurements"].get("shadow_git_bytes", 0))
        for owner in owners
    )
    selected_artifact_unique_bytes = (
        artifact_cold_logical_bytes
        if artifact_unique_bytes is None
        else artifact_unique_bytes
    )
    blocking: list[str] = []
    if owner_count != EXPECTED_OWNER_COUNT:
        blocking.append(
            f"owner_count:{owner_count}!={EXPECTED_OWNER_COUNT}"
        )
    if composition is None:
        blocking.append("signed_os_composition_missing")
    if git_hot_bytes > 234_881_024:
        blocking.append(
            f"git_hot_target_exceeded:{git_hot_bytes}>234881024"
        )
    return {
        "schema_version": ROLLOUT_EVIDENCE_SCHEMA_VERSION,
        "phase": phase,
        "status": "passed" if not blocking else "blocked",
        "source_set_digest": source_set_digest(owners),
        "owners": sorted(owners, key=lambda owner: str(owner["owner"])),
        "composition": (
            {
                "content_digest": composition[
                    "composition_identity"
                ]["content_digest"],
                "owner_count": composition["federation"]["owner_count"],
                "proof": dict(composition_proof or {}),
            }
            if composition is not None
            else None
        ),
        "aggregate": {
            "owner_count": owner_count,
            "git_hot_bytes": git_hot_bytes,
            "shadow_git_bytes": shadow_git_bytes,
            "current_tree_kag_bytes": git_hot_bytes + shadow_git_bytes,
            "corpus_total_bytes": corpus_total_bytes,
            "artifact_cold_logical_bytes": artifact_cold_logical_bytes,
            "artifact_unique_bytes": selected_artifact_unique_bytes,
            "git_hot_hard_ceiling_bytes": 335_544_320,
            "git_hot_target_bytes": 234_881_024,
        },
        "canaries": list(CANARY_OWNERS),
        "blocking_obligations": blocking,
    }
