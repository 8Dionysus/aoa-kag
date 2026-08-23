from __future__ import annotations

import copy
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Callable

from jsonschema import Draft202012Validator

from scripts.generate_repo_local_kag_index import (
    build_index,
    build_repository_indexes,
)
from scripts.repo_local.portable_family import (
    BUDGET_PROCEDURE_PATHS,
    BUDGET_RECEIPT_SCHEMA_VERSION,
    TRANSITION_ACCEPTANCE_RECORD_VERSION,
    TRANSITION_AUTHORITY_ARTIFACT_VERSION,
    TRANSITION_AUTHORITY_VERSION,
    MANIFEST_RELATIVE_PATH,
    MAX_UNRELATED_GENERATED_BYTES,
    SEMANTIC_BUDGET_DECISION_REF,
    TRANSITION_CONTRACT_PATHS,
    TRANSITION_TRUST_REGISTRY_PATH,
    TRANSITION_TRUST_REGISTRY_SCHEMA_PATH,
    TRANSITION_REPLAY_SNAPSHOT_VERSION,
    TransitionAuthorityError,
    _transition_contract_identity,
    _transition_subject_digest,
    _transition_validate_trust_root,
    build_portable_family,
    canonical_json_bytes,
    sha256_bytes,
    transition_admission_state,
)
from scripts.repo_local.tiered_family import (
    TieredFamilyError,
    build_tiered_family,
    complete_tiered_projection_expectations,
    tiered_projection_target,
    tiered_transition_target,
)
from tests.test_repo_local_kag_repository_indexes import write_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]


def _build_fixture(root: Path):
    write_fixture(root)
    source = build_index(root)
    family = build_repository_indexes(source, repo_root=root)
    portable_manifest, portable_shards = build_portable_family(source, family)
    return build_tiered_family(portable_manifest, portable_shards), portable_manifest


def _rebuild_fixture(root: Path):
    source = build_index(root)
    family = build_repository_indexes(source, repo_root=root)
    portable_manifest, portable_shards = build_portable_family(source, family)
    return build_tiered_family(portable_manifest, portable_shards)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(
        root,
        "-c",
        "user.name=KAG transition test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        message,
    )
    return _git(root, "rev-parse", "HEAD")


def _git_fixture(root: Path):
    root.mkdir(parents=True)
    build, portable_manifest = _build_fixture(root)
    manifest_path = root / MANIFEST_RELATIVE_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(portable_manifest, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    _git(root, "init", "-q")
    base_ref = _git_commit(root, "legacy v3 fixture")
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8") + "\nTarget source change.\n",
        encoding="utf-8",
    )
    target_build = _rebuild_fixture(root)
    _git_commit(root, "target v4 fixture")
    return target_build, base_ref


def _example(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / "examples" / name).read_text(encoding="utf-8"))


def _ed25519_signer(root: Path, label: str, owner: str, role: str):
    key_path = root / f"{label}.key.pem"
    public_path = root / f"{label}.public.der"
    subprocess.run(
        ("openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key_path)),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        (
            "openssl",
            "pkey",
            "-in",
            str(key_path),
            "-pubout",
            "-outform",
            "DER",
            "-out",
            str(public_path),
        ),
        check=True,
        capture_output=True,
    )
    public_key = public_path.read_bytes()[-32:]
    signer_id = "sha256:" + hashlib.sha256(public_key).hexdigest()
    entry = {
        "role": role,
        "ref": f"aoa-kag://trust-root/{role}/{label}",
        "owner": owner,
        "algorithm": "ed25519",
        "signer_id": signer_id,
        "public_key_base64url": base64.urlsafe_b64encode(public_key)
        .decode("ascii")
        .rstrip("="),
        "state": "active",
    }

    def sign(statement: dict[str, object]) -> dict[str, str]:
        statement_path = root / f"{label}.statement.json"
        signature_path = root / f"{label}.signature.bin"
        statement_path.write_bytes(canonical_json_bytes(statement))
        subprocess.run(
            (
                "openssl",
                "pkeyutl",
                "-sign",
                "-inkey",
                str(key_path),
                "-rawin",
                "-in",
                str(statement_path),
                "-out",
                str(signature_path),
            ),
            check=True,
            capture_output=True,
        )
        return {
            "algorithm": "ed25519",
            "signer_id": signer_id,
            "value": base64.urlsafe_b64encode(signature_path.read_bytes())
            .decode("ascii")
            .rstrip("="),
        }

    return entry, sign


def _signed_projection_fixture(
    base: Path,
    *,
    candidate: Path | None = None,
    build=None,
    predecessor: dict[str, object] | None = None,
    target: dict[str, object] | None = None,
    projection: dict[str, object] | None = None,
    output: dict[str, object] | None = None,
    owner_registry: dict[str, object] | None = None,
):
    candidate = candidate or (base / "candidate")
    owner = base / "owner"
    external = base / "external"
    candidate.mkdir(exist_ok=True)
    owner.mkdir()
    external.mkdir()
    if build is None:
        build, _ = _build_fixture(candidate)
        _git(candidate, "init", "-q")
        _git_commit(candidate, "synthetic candidate source")

    issuer_entry, sign_issuer = _ed25519_signer(
        external,
        "issuer",
        "independent-issuer",
        "issuer",
    )
    acceptor_entry, sign_acceptor = _ed25519_signer(
        external,
        "acceptor",
        "independent-acceptor",
        "acceptor",
    )
    replay_entry, sign_replay = _ed25519_signer(
        external,
        "replay",
        "independent-replay-ledger",
        "replay",
    )
    registry = (
        owner_registry
        if owner_registry is not None
        else {
            "schema_version": "aoa-kag:transition-trust-registry-v1",
            "owner": "aoa-kag",
            "issuer_roots": [issuer_entry],
            "acceptor_roots": [acceptor_entry],
            "replay_roots": [replay_entry],
        }
    )
    (owner / TRANSITION_TRUST_REGISTRY_PATH).parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    (owner / TRANSITION_TRUST_REGISTRY_PATH).write_bytes(
        canonical_json_bytes(registry)
    )
    decision_path = owner / "docs/decisions/AOA-KAG-D-0044-detached-transition-authority.md"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_bytes = b"# Synthetic test decision\n\n- Posture: accepted\n"
    decision_path.write_bytes(decision_bytes)
    _git(owner, "init", "-q")
    source_commit = _git_commit(owner, "synthetic accepted transition source")

    payload = _example("repo_local_kag_projection_transition.example.json")
    if predecessor is not None:
        payload["predecessor"] = copy.deepcopy(predecessor)
    if projection is not None:
        payload["projection"] = copy.deepcopy(projection)
    if output is not None:
        payload["output"] = copy.deepcopy(output)
    payload["decision"]["digest"] = sha256_bytes(decision_bytes)
    payload["decision"]["posture"] = "accepted"
    payload["decision"]["source_commit"] = source_commit
    if target is None:
        payload["target"]["producer_identity"] = copy.deepcopy(
            build.corpus_manifest["producer_identity"]
        )
        payload["target"]["family"].update(
            {
                "ref": "4" * 40,
                "family_digest": "d" * 64,
                "source_snapshot": "sha256:" + "e" * 64,
                "distribution_digest": "sha256:" + "f" * 64,
            }
        )
        payload["output"]["family_digest"] = "d" * 64
        payload["output"]["source_snapshot"] = "sha256:" + "e" * 64
        output_without_digest = copy.deepcopy(payload["output"])
        output_without_digest["output_digest"] = "sha256:" + "0" * 64
        payload["output"]["output_digest"] = "sha256:" + sha256_bytes(
            canonical_json_bytes(output_without_digest)
        )
    else:
        payload["target"] = copy.deepcopy(target)
    contract = _transition_contract_identity()
    payload["authority"]["contract_version"] = TRANSITION_AUTHORITY_VERSION
    payload["authority"]["contract_digest"] = contract["digest"]

    def binding(entry: dict[str, object]) -> dict[str, object]:
        return {
            "role": entry["role"],
            "ref": entry["ref"],
            "registry_ref": "aoa-kag:config/transition_authority_trust.json",
            "signer_id": entry["signer_id"],
            "digest": "sha256:" + sha256_bytes(canonical_json_bytes(entry)),
        }

    issuer_binding = binding(issuer_entry)
    acceptor_binding = binding(acceptor_entry)
    replay_binding = binding(replay_entry)
    payload["authority"]["issuer"]["ref"] = "aoa-kag://issuer/synthetic"
    payload["authority"]["issuer"]["trust_root"] = issuer_binding
    payload["authority"]["acceptance"].update(
        {
            "state": "independently_accepted",
            "ref": "aoa-kag://acceptance/synthetic",
            "trust_root": acceptor_binding,
        }
    )
    payload["replay"].update(
        {
            "source_ref": "aoa-kag://replay/source/synthetic",
            "ledger_ref": "aoa-kag://replay/synthetic-ledger",
            "ledger_digest": "sha256:" + "1" * 64,
            "snapshot_digest": "sha256:" + "0" * 64,
            "subject_digest": "sha256:" + "0" * 64,
        }
    )
    subject_digest = _transition_subject_digest(payload)
    payload["replay"]["subject_digest"] = subject_digest

    acceptance_record = {
        "schema_version": TRANSITION_ACCEPTANCE_RECORD_VERSION,
        "owner": "aoa-kag",
        "transition_kind": "projection_transition",
        "subject_digest": subject_digest,
        "acceptance_ref": payload["authority"]["acceptance"]["ref"],
        "acceptor_root_ref": acceptor_entry["ref"],
        "state": "independently_accepted",
    }
    acceptance_record["signature"] = sign_acceptor(acceptance_record)
    acceptance_path = external / "acceptance.json"
    acceptance_path.write_bytes(canonical_json_bytes(acceptance_record))
    acceptance_digest = "sha256:" + sha256_bytes(acceptance_path.read_bytes())
    payload["authority"]["acceptance"]["digest"] = acceptance_digest

    authority_record = {
        "schema_version": TRANSITION_AUTHORITY_ARTIFACT_VERSION,
        "owner": "aoa-kag",
        "transition_kind": "projection_transition",
        "subject_digest": subject_digest,
        "issuer_root_ref": issuer_entry["ref"],
        "issuer_ref": payload["authority"]["issuer"]["ref"],
        "acceptance_ref": payload["authority"]["acceptance"]["ref"],
        "acceptance_digest": acceptance_digest,
        "state": "independently_accepted",
    }
    authority_record["signature"] = sign_issuer(authority_record)
    authority_path = external / "authority.json"
    authority_path.write_bytes(canonical_json_bytes(authority_record))
    payload["authority"]["issuer"]["artifact_digest"] = (
        "sha256:" + sha256_bytes(authority_path.read_bytes())
    )

    replay_state = {
        "schema_version": TRANSITION_REPLAY_SNAPSHOT_VERSION,
        "owner": "aoa-kag",
        "transition_kind": "projection_transition",
        "subject_digest": subject_digest,
        "snapshot_digest": "sha256:" + "0" * 64,
        "source_ref": payload["replay"]["source_ref"],
        "ledger_ref": payload["replay"]["ledger_ref"],
        "ledger_digest": payload["replay"]["ledger_digest"],
        "state": "current",
        "last_sequence": 0,
        "used_nonces": [],
        "trust_root": replay_binding,
    }
    replay_digest_body = copy.deepcopy(replay_state)
    replay_digest = "sha256:" + sha256_bytes(
        canonical_json_bytes(replay_digest_body)
    )
    replay_state["snapshot_digest"] = replay_digest
    replay_state["signature"] = sign_replay(replay_state)
    replay_path = external / "replay.json"
    replay_path.write_bytes(canonical_json_bytes(replay_state))
    payload["replay"]["snapshot_digest"] = replay_digest
    return (
        payload,
        candidate,
        owner,
        authority_path,
        acceptance_path,
        acceptance_record,
        replay_path,
        replay_state,
    )


def _signed_cli_fixture(base: Path):
    candidate = base / "candidate"
    target_build, base_ref = _git_fixture(candidate)
    target_build = _rebuild_fixture(candidate)
    from scripts.repo_local.portable_family import derive_transition_predecessor

    predecessor = derive_transition_predecessor(candidate, base_ref)
    target = tiered_projection_target(target_build, repo_root=candidate)
    projection, output = complete_tiered_projection_expectations(
        target_build,
        predecessor_placement=predecessor["placement"],
    )
    signed = _signed_projection_fixture(
        base,
        candidate=candidate,
        build=target_build,
        predecessor=predecessor,
        target=target,
        projection=projection,
        output=output,
    )
    transition_path = base / "external" / "transition.json"
    transition_path.write_bytes(canonical_json_bytes(signed[0]))
    direct_candidate = base / "direct" / "candidate"
    direct_candidate.parent.mkdir()
    subprocess.run(
        ("git", "clone", "--local", str(candidate), str(direct_candidate)),
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "payload": signed[0],
        "build": target_build,
        "predecessor": predecessor,
        "candidate": candidate,
        "direct_candidate": direct_candidate,
        "owner": signed[2],
        "external": base / "external",
        "authority": signed[3],
        "acceptance": signed[4],
        "replay": signed[6],
        "transition": transition_path,
        "base_ref": base_ref,
    }


class RepoLocalKagTransitionAuthorityTests(unittest.TestCase):
    def test_schema_examples_trust_registry_and_ordinary_budget_contract_are_separate(
        self,
    ) -> None:
        pairs = (
            (
                "repo-local-kag-producer-migration.schema.json",
                "repo_local_kag_producer_migration.example.json",
            ),
            (
                "repo-local-kag-projection-transition.schema.json",
                "repo_local_kag_projection_transition.example.json",
            ),
        )
        for schema_name, example_name in pairs:
            schema = json.loads((REPO_ROOT / "schemas" / schema_name).read_text())
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(_example(example_name))

        for schema_name in (
            "repo-local-kag-transition-replay-snapshot.schema.json",
            "repo-local-kag-transition-trust.schema.json",
        ):
            schema = json.loads((REPO_ROOT / "schemas" / schema_name).read_text())
            Draft202012Validator.check_schema(schema)
        trust_schema = json.loads(
            (REPO_ROOT / TRANSITION_TRUST_REGISTRY_SCHEMA_PATH).read_text()
        )
        trust_registry = json.loads(
            (REPO_ROOT / TRANSITION_TRUST_REGISTRY_PATH).read_text()
        )
        Draft202012Validator(trust_schema).validate(trust_registry)

        self.assertEqual(131072, MAX_UNRELATED_GENERATED_BYTES)
        self.assertEqual(
            "aoa-repo-local-kag-budget-receipt-v2",
            BUDGET_RECEIPT_SCHEMA_VERSION,
        )
        self.assertEqual(
            "aoa-kag:docs/decisions/AOA-KAG-D-0042-semantic-owner-evidence-for-budget-admission.md",
            SEMANTIC_BUDGET_DECISION_REF,
        )
        self.assertNotIn(
            Path("schemas/repo-local-kag-projection-transition.schema.json"),
            BUDGET_PROCEDURE_PATHS,
        )
        self.assertIn(
            Path("schemas/repo-local-kag-transition-replay-snapshot.schema.json"),
            TRANSITION_CONTRACT_PATHS,
        )
        self.assertIn(
            Path("config/transition_authority_trust.json"),
            TRANSITION_CONTRACT_PATHS,
        )

    def test_transition_target_is_exact_clean_head_not_a_hex_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            build, base_ref = _git_fixture(root)
            head = _git(root, "rev-parse", "HEAD")
            target = tiered_transition_target(build, repo_root=root)
            self.assertEqual(head, target["family"]["ref"])
            with self.assertRaises(TieredFamilyError):
                tiered_transition_target(
                    build,
                    target_ref=base_ref,
                    repo_root=root,
                )
            (root / "uncommitted.txt").write_text("dirty", encoding="utf-8")
            with self.assertRaises(TieredFamilyError):
                tiered_projection_target(build, repo_root=root)

    def test_predecessor_derivation_and_projection_before_are_non_null_and_exact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            build, base_ref = _git_fixture(root)
            from scripts.repo_local.portable_family import derive_transition_predecessor

            predecessor = derive_transition_predecessor(root, base_ref)
            placement = predecessor["placement"]
            self.assertEqual("legacy_v3", placement["state"])
            self.assertIsInstance(placement["hot_profile_digest"], str)
            self.assertIsInstance(placement["partitioning_digest"], str)

            with self.assertRaises(TieredFamilyError):
                complete_tiered_projection_expectations(build)
            projection, output = complete_tiered_projection_expectations(
                build,
                predecessor_placement=placement,
            )
            self.assertEqual(placement, projection["before"])
            self.assertNotIn(None, projection["before"].values())
            self.assertEqual("complete", output["state"])

            invalid_values = (
                {
                    "state": "legacy_v3",
                    "hot_profile_digest": None,
                    "partitioning_digest": "sha256:" + "a" * 64,
                },
                {
                    "state": "unknown",
                    "hot_profile_digest": "sha256:" + "a" * 64,
                    "partitioning_digest": "sha256:" + "b" * 64,
                },
            )
            for invalid in invalid_values:
                with self.subTest(invalid=invalid), self.assertRaises(TieredFamilyError):
                    complete_tiered_projection_expectations(
                        build,
                        predecessor_placement=invalid,
                    )

    def test_proposed_decision_and_untrusted_material_never_become_supported(self) -> None:
        payload = _example("repo_local_kag_projection_transition.example.json")
        kwargs = {
            "predecessor": payload["predecessor"],
            "target": payload["target"],
            "expected_projection": payload["projection"],
            "expected_output": payload["output"],
            "owner_root": REPO_ROOT,
            "candidate_root": REPO_ROOT,
        }
        self.assertNotEqual(
            "supported",
            transition_admission_state("projection_transition", payload, **kwargs),
        )

        self_issued = copy.deepcopy(payload)
        self_issued["decision"]["posture"] = "accepted"
        self_issued["decision"]["source_commit"] = "0" * 40
        self.assertNotEqual(
            "supported",
            transition_admission_state(
                "projection_transition",
                self_issued,
                **kwargs,
            ),
        )

        copied_authority = copy.deepcopy(payload)
        copied_authority["authority"]["issuer"]["trust_root"]["ref"] = (
            "aoa-kag://trust-root/issuer/copied"
        )
        copied_authority["authority"]["acceptance"]["digest"] = "sha256:" + "f" * 64
        self.assertNotEqual(
            "supported",
            transition_admission_state(
                "projection_transition",
                copied_authority,
                **kwargs,
            ),
        )

    def test_synthetic_independent_signatures_bind_authority_acceptance_and_replay(self) -> None:
        from scripts.repo_local.portable_family import validate_full_projection_transition

        with tempfile.TemporaryDirectory() as tmpdir:
            (
                payload,
                candidate,
                owner,
                authority_path,
                acceptance_path,
                acceptance_record,
                replay_path,
                replay_state,
            ) = _signed_projection_fixture(Path(tmpdir))
            validate_full_projection_transition(
                payload,
                predecessor=payload["predecessor"],
                target=payload["target"],
                expected_projection=payload["projection"],
                expected_output=payload["output"],
                detached_authority_path=authority_path,
                acceptance_record=acceptance_record,
                acceptance_record_path=acceptance_path,
                replay_state=replay_state,
                replay_state_path=replay_path,
                owner_root=owner,
                candidate_root=candidate,
            )

            hardlink_root = Path(tmpdir) / "hardlink-aliases"
            hardlink_root.mkdir()
            authority_alias = hardlink_root / "authority.json"
            acceptance_alias = hardlink_root / "acceptance.json"
            replay_alias = hardlink_root / "replay.json"
            authority_alias.hardlink_to(authority_path)
            acceptance_alias.hardlink_to(acceptance_path)
            replay_alias.hardlink_to(replay_path)
            validate_full_projection_transition(
                payload,
                predecessor=payload["predecessor"],
                target=payload["target"],
                expected_projection=payload["projection"],
                expected_output=payload["output"],
                detached_authority_path=authority_alias,
                acceptance_record=acceptance_record,
                acceptance_record_path=acceptance_alias,
                replay_state=replay_state,
                replay_state_path=replay_alias,
                owner_root=owner,
                candidate_root=candidate,
            )

            copied = candidate / "copied-authority.json"
            copied.write_bytes(authority_path.read_bytes())
            with self.assertRaises(TransitionAuthorityError) as raised:
                validate_full_projection_transition(
                    payload,
                    predecessor=payload["predecessor"],
                    target=payload["target"],
                    expected_projection=payload["projection"],
                    expected_output=payload["output"],
                    detached_authority_path=copied,
                    acceptance_record=acceptance_record,
                    acceptance_record_path=acceptance_path,
                    replay_state=replay_state,
                    replay_state_path=replay_path,
                    owner_root=owner,
                    candidate_root=candidate,
                )
            self.assertEqual("migration_required", raised.exception.state)

            tampered_acceptance = copy.deepcopy(payload)
            tampered_acceptance["authority"]["acceptance"]["digest"] = (
                "sha256:" + "f" * 64
            )
            with self.assertRaises(TransitionAuthorityError):
                validate_full_projection_transition(
                    tampered_acceptance,
                    predecessor=tampered_acceptance["predecessor"],
                    target=tampered_acceptance["target"],
                    expected_projection=tampered_acceptance["projection"],
                    expected_output=tampered_acceptance["output"],
                    detached_authority_path=authority_path,
                    acceptance_record=acceptance_record,
                    acceptance_record_path=acceptance_path,
                    replay_state=replay_state,
                    replay_state_path=replay_path,
                    owner_root=owner,
                    candidate_root=candidate,
                )

            tampered_replay = copy.deepcopy(replay_state)
            tampered_replay["last_sequence"] = 1
            with self.assertRaises(TransitionAuthorityError):
                validate_full_projection_transition(
                    payload,
                    predecessor=payload["predecessor"],
                    target=payload["target"],
                    expected_projection=payload["projection"],
                    expected_output=payload["output"],
                    detached_authority_path=authority_path,
                    acceptance_record=acceptance_record,
                    acceptance_record_path=acceptance_path,
                    replay_state=tampered_replay,
                    replay_state_path=replay_path,
                    owner_root=owner,
                    candidate_root=candidate,
                )

    def test_current_empty_registry_cannot_authorize_current_source(self) -> None:
        from scripts.repo_local.portable_family import validate_full_projection_transition

        empty_registry = {
            "schema_version": "aoa-kag:transition-trust-registry-v1",
            "owner": "aoa-kag",
            "issuer_roots": [],
            "acceptor_roots": [],
            "replay_roots": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            (
                payload,
                candidate,
                owner,
                authority_path,
                acceptance_path,
                acceptance_record,
                replay_path,
                replay_state,
            ) = _signed_projection_fixture(
                Path(tmpdir),
                owner_registry=empty_registry,
            )
            with self.assertRaises(TransitionAuthorityError) as raised:
                validate_full_projection_transition(
                    payload,
                    predecessor=payload["predecessor"],
                    target=payload["target"],
                    expected_projection=payload["projection"],
                    expected_output=payload["output"],
                    detached_authority_path=authority_path,
                    acceptance_record=acceptance_record,
                    acceptance_record_path=acceptance_path,
                    replay_state=replay_state,
                    replay_state_path=replay_path,
                    owner_root=owner,
                    candidate_root=candidate,
                )
            self.assertEqual("migration_required", raised.exception.state)

    def test_signed_builder_validator_module_and_direct_cli_parity(self) -> None:
        from scripts.repo_local.portable_family import validate_full_projection_transition
        from scripts.repo_local.tiered_family import validate_tiered_projection_transition

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = _signed_cli_fixture(Path(tmpdir))
            payload = fixture["payload"]
            schema = json.loads(
                (REPO_ROOT / "schemas/repo-local-kag-projection-transition.schema.json").read_text()
            )
            Draft202012Validator(schema).validate(payload)
            self.assertEqual(
                _git(fixture["candidate"], "rev-parse", "HEAD"),
                payload["target"]["family"]["ref"],
            )
            self.assertEqual(
                fixture["payload"]["target"]["family"]["placement"],
                payload["projection"]["after"],
            )
            validate_full_projection_transition(
                payload,
                predecessor=payload["predecessor"],
                target=payload["target"],
                expected_projection=payload["projection"],
                expected_output=payload["output"],
                detached_authority_path=fixture["authority"],
                acceptance_record=json.loads(fixture["acceptance"].read_text()),
                acceptance_record_path=fixture["acceptance"],
                replay_state=json.loads(fixture["replay"].read_text()),
                replay_state_path=fixture["replay"],
                owner_root=fixture["owner"],
                candidate_root=fixture["candidate"],
            )
            validate_tiered_projection_transition(
                payload,
                predecessor=fixture["predecessor"],
                build=fixture["build"],
                repo_root=fixture["candidate"],
                base_ref=fixture["base_ref"],
                predecessor_placement=fixture["predecessor"]["placement"],
                detached_authority_path=fixture["authority"],
                acceptance_record=json.loads(fixture["acceptance"].read_text()),
                acceptance_record_path=fixture["acceptance"],
                replay_state=json.loads(fixture["replay"].read_text()),
                replay_state_path=fixture["replay"],
                owner_root=fixture["owner"],
                candidate_root=fixture["candidate"],
            )
            with self.assertRaises(TieredFamilyError):
                validate_tiered_projection_transition(
                    payload,
                    predecessor=fixture["predecessor"],
                    build=fixture["build"],
                    repo_root=fixture["candidate"],
                    base_ref=fixture["base_ref"],
                    predecessor_placement=fixture["predecessor"]["placement"],
                    detached_authority_path=fixture["authority"],
                    acceptance_record=json.loads(fixture["acceptance"].read_text()),
                    acceptance_record_path=fixture["acceptance"],
                    replay_state=json.loads(fixture["replay"].read_text()),
                    replay_state_path=fixture["replay"],
                    owner_root=fixture["owner"],
                    candidate_root=fixture["direct_candidate"],
                )
            wrong_placement = copy.deepcopy(payload)
            wrong_placement["target"]["family"]["placement"]["state"] = "legacy_v3"
            with self.assertRaises(TransitionAuthorityError):
                validate_tiered_projection_transition(
                    wrong_placement,
                    predecessor=fixture["predecessor"],
                    build=fixture["build"],
                    repo_root=fixture["candidate"],
                    base_ref=fixture["base_ref"],
                    predecessor_placement=fixture["predecessor"]["placement"],
                    detached_authority_path=fixture["authority"],
                    acceptance_record=json.loads(fixture["acceptance"].read_text()),
                    acceptance_record_path=fixture["acceptance"],
                    replay_state=json.loads(fixture["replay"].read_text()),
                    replay_state_path=fixture["replay"],
                    owner_root=fixture["owner"],
                    candidate_root=fixture["candidate"],
                )

            def run_cli(
                candidate: Path,
                artifact_root: Path,
                *,
                module: bool,
                owner_root: Path | None = None,
                history_ref: str | None = None,
                authority_path: Path | None = None,
                acceptance_path: Path | None = None,
                replay_path: Path | None = None,
            ) -> subprocess.CompletedProcess[str]:
                command = [sys.executable]
                if module:
                    command.extend(["-m", "scripts.generate_repo_local_kag_index"])
                else:
                    command.append("scripts/generate_repo_local_kag_index.py")
                command.extend(
                    [
                        "--repo-root",
                        str(candidate),
                        "--candidate-root",
                        str(candidate),
                        "--owner-root",
                        str(owner_root or fixture["owner"]),
                        "--tiered-family",
                        "--artifact-root",
                        str(artifact_root),
                        "--history-ref",
                        history_ref or fixture["base_ref"],
                        "--event-history-ref",
                        fixture["base_ref"],
                        "--transition-kind",
                        "projection_transition",
                        "--transition-evidence",
                        str(fixture["transition"]),
                        "--transition-authority-artifact",
                        str(authority_path or fixture["authority"]),
                        "--transition-acceptance-record",
                        str(acceptance_path or fixture["acceptance"]),
                        "--transition-replay-state",
                        str(replay_path or fixture["replay"]),
                    ]
                )
                return subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )

            module_result = run_cli(
                fixture["candidate"],
                Path(tmpdir) / "module-artifacts",
                module=True,
            )
            self.assertEqual(
                0,
                module_result.returncode,
                module_result.stdout + module_result.stderr,
            )
            self.assertIn(
                "transition authority admitted kind=projection_transition",
                module_result.stdout,
            )

            direct_result = run_cli(
                fixture["direct_candidate"],
                Path(tmpdir) / "direct-artifacts",
                module=False,
            )
            self.assertEqual(
                0,
                direct_result.returncode,
                direct_result.stdout + direct_result.stderr,
            )
            self.assertIn(
                "transition authority admitted kind=projection_transition",
                direct_result.stdout,
            )

            equal_root = run_cli(
                fixture["direct_candidate"],
                Path(tmpdir) / "equal-root-artifacts",
                module=True,
                owner_root=fixture["direct_candidate"],
            )
            self.assertNotEqual(0, equal_root.returncode)
            self.assertIn("detached", equal_root.stderr)

            def fresh_candidate(label: str) -> Path:
                path = Path(tmpdir) / label / "candidate"
                path.parent.mkdir()
                subprocess.run(
                    ("git", "clone", "--local", str(fixture["candidate"]), str(path)),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return path

            def fresh_owner(label: str) -> Path:
                path = Path(tmpdir) / label / "owner"
                path.parent.mkdir()
                subprocess.run(
                    ("git", "clone", "--local", str(fixture["owner"]), str(path)),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return path

            def assert_owner_variant_rejected(
                label: str,
                owner_root: Path,
                expected_message: str = "current clean owner",
            ) -> None:
                for module in (True, False):
                    with self.subTest(owner_variant=label, module=module):
                        result = run_cli(
                            fresh_candidate(f"{label}-{'module' if module else 'direct'}"),
                            Path(tmpdir) / f"{label}-{'module' if module else 'direct'}-artifacts",
                            module=module,
                            owner_root=owner_root,
                        )
                        self.assertNotEqual(
                            0,
                            result.returncode,
                            result.stdout + result.stderr,
                        )
                        self.assertIn(expected_message, result.stderr)

            owner_head_drift = fresh_owner("owner-head-drift")
            (owner_head_drift / "owner-change.txt").write_text(
                "new current owner state\n",
                encoding="utf-8",
            )
            _git_commit(owner_head_drift, "owner HEAD drift")
            assert_owner_variant_rejected("owner-head-drift", owner_head_drift)

            proposed_owner = fresh_owner("owner-current-proposed")
            proposed_decision = proposed_owner / "docs/decisions/AOA-KAG-D-0044-detached-transition-authority.md"
            proposed_decision.write_text(
                proposed_decision.read_text(encoding="utf-8").replace(
                    "- Posture: accepted", "- Posture: proposed"
                ),
                encoding="utf-8",
            )
            _git_commit(proposed_owner, "current proposed transition decision")
            assert_owner_variant_rejected("owner-current-proposed", proposed_owner)

            superseded_owner = fresh_owner("owner-current-superseded")
            superseded_decision = superseded_owner / "docs/decisions/AOA-KAG-D-0044-detached-transition-authority.md"
            superseded_decision.write_text(
                superseded_decision.read_text(encoding="utf-8").replace(
                    "- Posture: accepted", "- Posture: superseded"
                ),
                encoding="utf-8",
            )
            _git_commit(superseded_owner, "current superseded transition decision")
            assert_owner_variant_rejected("owner-current-superseded", superseded_owner)

            empty_registry_owner = fresh_owner("owner-current-empty-registry")
            (empty_registry_owner / TRANSITION_TRUST_REGISTRY_PATH).write_bytes(
                canonical_json_bytes(
                    {
                        "schema_version": "aoa-kag:transition-trust-registry-v1",
                        "owner": "aoa-kag",
                        "issuer_roots": [],
                        "acceptor_roots": [],
                        "replay_roots": [],
                    }
                )
            )
            _git_commit(empty_registry_owner, "current empty transition registry")
            assert_owner_variant_rejected(
                "owner-current-empty-registry",
                empty_registry_owner,
            )

            dirty_owner = fresh_owner("owner-dirty")
            (dirty_owner / "uncommitted-owner-state.txt").write_text(
                "dirty\n",
                encoding="utf-8",
            )
            assert_owner_variant_rejected(
                "owner-dirty",
                dirty_owner,
                expected_message="clean current owner",
            )

            symlink_root = Path(tmpdir) / "symlink-inputs"
            symlink_root.mkdir()
            symlink_inputs = {
                "authority": symlink_root / "authority.json",
                "acceptance": symlink_root / "acceptance.json",
                "replay": symlink_root / "replay.json",
            }
            for field, symlink_path in symlink_inputs.items():
                symlink_path.symlink_to(fixture[field])
                for module in (True, False):
                    with self.subTest(symlink_input=field, module=module):
                        candidate = fresh_candidate(
                            f"symlink-{field}-{'module' if module else 'direct'}"
                        )
                        result = run_cli(
                            candidate,
                            Path(tmpdir)
                            / f"symlink-{field}-{'module' if module else 'direct'}-artifacts",
                            module=module,
                            authority_path=(
                                symlink_path if field == "authority" else None
                            ),
                            acceptance_path=(
                                symlink_path if field == "acceptance" else None
                            ),
                            replay_path=(
                                symlink_path if field == "replay" else None
                            ),
                        )
                        self.assertNotEqual(
                            0,
                            result.returncode,
                            result.stdout + result.stderr,
                        )
                        self.assertIn("supplied path is a symlink", result.stderr)

            wrong_owner = Path(tmpdir) / "wrong-owner"
            wrong_owner.mkdir()
            (wrong_owner / "README.md").write_text("wrong owner\n", encoding="utf-8")
            _git(wrong_owner, "init", "-q")
            _git_commit(wrong_owner, "wrong owner source")
            wrong_owner_result = run_cli(
                fresh_candidate("wrong-owner-candidate"),
                Path(tmpdir) / "wrong-owner-artifacts",
                module=False,
                owner_root=wrong_owner,
            )
            self.assertNotEqual(0, wrong_owner_result.returncode)
            self.assertIn("transition decision", wrong_owner_result.stderr)

            wrong_base_result = run_cli(
                fresh_candidate("wrong-base-candidate"),
                Path(tmpdir) / "wrong-base-artifacts",
                module=True,
                history_ref=_git(fixture["candidate"], "rev-parse", "HEAD"),
            )
            self.assertNotEqual(0, wrong_base_result.returncode)
            self.assertIn("predecessor", wrong_base_result.stderr)

            missing_placement = copy.deepcopy(payload)
            del missing_placement["target"]["family"]["placement"]
            self.assertTrue(
                list(Draft202012Validator(schema).iter_errors(missing_placement))
            )

    def test_callable_transition_validators_reject_nested_missing_and_non_git_roots(
        self,
    ) -> None:
        from scripts.repo_local.portable_family import (
            validate_detached_producer_migration,
            validate_full_projection_transition,
        )
        from scripts.repo_local.tiered_family import (
            validate_tiered_producer_migration,
            validate_tiered_projection_transition,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = _signed_cli_fixture(Path(tmpdir))
            payload = fixture["payload"]
            producer = _example("repo_local_kag_producer_migration.example.json")

            def validate_low_level(
                validator: object,
                owner_root: Path | None,
                candidate_root: Path | None,
            ) -> None:
                if validator is validate_full_projection_transition:
                    validator(
                        payload,
                        predecessor=payload["predecessor"],
                        target=payload["target"],
                        expected_projection=payload["projection"],
                        expected_output=payload["output"],
                        detached_authority_path=fixture["authority"],
                        acceptance_record=json.loads(
                            fixture["acceptance"].read_text()
                        ),
                        acceptance_record_path=fixture["acceptance"],
                        replay_state=json.loads(fixture["replay"].read_text()),
                        replay_state_path=fixture["replay"],
                        owner_root=owner_root,
                        candidate_root=candidate_root,
                    )
                else:
                    validator(
                        producer,
                        predecessor={},
                        target={},
                        owner_root=owner_root,
                        candidate_root=candidate_root,
                    )

            root_cases = (
                ("nested owner", fixture["owner"] / "docs", fixture["candidate"]),
                (
                    "nested candidate",
                    fixture["owner"],
                    fixture["candidate"] / "kag",
                ),
                ("missing owner", None, fixture["candidate"]),
                ("missing candidate", fixture["owner"], None),
            )
            for validator in (
                validate_full_projection_transition,
                validate_detached_producer_migration,
            ):
                for label, owner_root, candidate_root in root_cases:
                    with self.subTest(
                        low_level_validator=validator.__name__,
                        low_level_root=label,
                    ):
                        with self.assertRaises(TransitionAuthorityError) as raised:
                            validate_low_level(
                                validator,
                                owner_root,
                                candidate_root,
                            )
                        self.assertEqual(
                            "migration_required",
                            raised.exception.state,
                        )

            non_git = Path(tmpdir) / "non-git-owner"
            non_git.mkdir()
            with self.assertRaises(TransitionAuthorityError) as raised:
                validate_low_level(
                    validate_full_projection_transition,
                    non_git,
                    fixture["candidate"],
                )
            self.assertEqual("migration_required", raised.exception.state)

            non_git_candidate = Path(tmpdir) / "non-git-candidate"
            non_git_candidate.mkdir()
            with self.assertRaises(TransitionAuthorityError) as raised:
                validate_low_level(
                    validate_full_projection_transition,
                    fixture["owner"],
                    non_git_candidate,
                )
            self.assertEqual("migration_required", raised.exception.state)

            def validate_tiered(
                validator: Callable[..., None],
                transition: dict[str, object],
                owner_root: Path | None,
                candidate_root: Path | None,
            ) -> None:
                if validator is validate_tiered_projection_transition:
                    validator(
                        transition,
                        predecessor=fixture["predecessor"],
                        build=fixture["build"],
                        repo_root=fixture["candidate"],
                        base_ref=fixture["base_ref"],
                        predecessor_placement=fixture["predecessor"]["placement"],
                        owner_root=owner_root,
                        candidate_root=candidate_root,
                    )
                else:
                    validator(
                        transition,
                        predecessor=fixture["predecessor"],
                        build=fixture["build"],
                        repo_root=fixture["candidate"],
                        base_ref=fixture["base_ref"],
                        owner_root=owner_root,
                        candidate_root=candidate_root,
                    )

            tiered_cases = (
                ("nested owner", fixture["owner"] / "docs", fixture["candidate"]),
                (
                    "nested candidate",
                    fixture["owner"],
                    fixture["candidate"] / "kag",
                ),
                ("missing owner", None, fixture["candidate"]),
                ("missing candidate", fixture["owner"], None),
            )
            for validator, transition in (
                (validate_tiered_projection_transition, payload),
                (validate_tiered_producer_migration, producer),
            ):
                for label, owner_root, candidate_root in tiered_cases:
                    with self.subTest(
                        tiered_validator=validator.__name__,
                        tiered_root=label,
                    ):
                        with self.assertRaises(TieredFamilyError):
                            validate_tiered(
                                validator,
                                transition,
                                owner_root,
                                candidate_root,
                            )

    def test_transition_schema_rejects_unhashed_replay_and_consumed_variants(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "schemas/repo-local-kag-projection-transition.schema.json").read_text()
        )
        payload = _example("repo_local_kag_projection_transition.example.json")
        tampered = copy.deepcopy(payload)
        tampered["replay"]["snapshot_bytes"] = "tampered-not-covered-by-digest"
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(tampered)))

        consumed = copy.deepcopy(payload)
        consumed["replay"]["consumption"] = {
            "state": "consumed",
            "record_ref": "aoa-kag://replay/consumption/1",
            "record_digest": "sha256:" + "a" * 64,
        }
        self.assertEqual(
            "migration_required",
            transition_admission_state(
                "projection_transition",
                consumed,
                predecessor=consumed["predecessor"],
                target=consumed["target"],
                expected_projection=consumed["projection"],
                expected_output=consumed["output"],
                owner_root=REPO_ROOT,
                candidate_root=REPO_ROOT,
            ),
        )

    def test_self_declared_roots_are_not_trusted_by_separate_paths(self) -> None:
        binding = {
            "role": "issuer",
            "ref": "aoa-kag://trust-root/issuer/self",
            "registry_ref": "aoa-kag:config/transition_authority_trust.json",
            "signer_id": "sha256:" + "a" * 64,
            "digest": "sha256:" + "b" * 64,
        }
        registry = {
            "schema_version": "aoa-kag:transition-trust-registry-v1",
            "owner": "aoa-kag",
            "issuer_roots": [
                {
                    "role": "issuer",
                    "ref": binding["ref"],
                    "owner": "aoa-kag",
                    "algorithm": "ed25519",
                    "signer_id": binding["signer_id"],
                    "public_key_base64url": "A" * 43,
                    "state": "active",
                }
            ],
            "acceptor_roots": [],
            "replay_roots": [],
        }
        with self.assertRaises(TransitionAuthorityError) as raised:
            _transition_validate_trust_root(
                role="issuer",
                root_binding=binding,
                registry=registry,
            )
        self.assertEqual("migration_required", raised.exception.state)

    def test_wrong_base_predecessor_is_not_normalized_by_low_level_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            build, base_ref = _git_fixture(root)
            from scripts.repo_local.portable_family import (
                derive_transition_predecessor,
                validate_detached_producer_migration,
            )

            predecessor = derive_transition_predecessor(root, base_ref)
            wrong_predecessor = copy.deepcopy(predecessor)
            wrong_predecessor["ref"] = "f" * 40
            self.assertNotEqual(predecessor, wrong_predecessor)
            with self.assertRaises(TransitionAuthorityError):
                validate_detached_producer_migration(
                    _example("repo_local_kag_producer_migration.example.json"),
                    predecessor=wrong_predecessor,
                    target={},
                    owner_root=root,
                    candidate_root=root,
                )

    def test_budget_receipt_is_not_transition_authority(self) -> None:
        self.assertEqual(
            "unsupported",
            transition_admission_state("unknown_transition", {}),
        )
        from scripts.repo_local.portable_family import validate_full_projection_transition

        with self.assertRaises(TransitionAuthorityError):
            validate_full_projection_transition(
                {"schema_version": BUDGET_RECEIPT_SCHEMA_VERSION},
                predecessor={},
                target={},
                expected_projection={},
                expected_output={},
            )


if __name__ == "__main__":
    unittest.main()
