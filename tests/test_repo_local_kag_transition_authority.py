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
from scripts.repo_local.portable_family import (
    BUDGET_RECEIPT_SCHEMA_VERSION,
    BUDGET_PROCEDURE_PATHS,
    MAX_UNRELATED_GENERATED_BYTES,
    SEMANTIC_BUDGET_DECISION_REF,
    TRANSITION_CONTRACT_PATHS,
    TransitionAuthorityError,
    _transition_contract_identity,
    _transition_subject_digest,
    build_portable_family,
    sha256_bytes,
    transition_admission_state,
    validate_detached_producer_migration,
    validate_full_projection_transition,
)
from scripts.repo_local.tiered_family import (
    build_tiered_family,
    complete_tiered_projection_expectations,
    tiered_projection_target,
    tiered_transition_target,
    validate_tiered_projection_transition,
    validate_tiered_producer_migration,
)
from tests.test_repo_local_kag_repository_indexes import write_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]
DECISION_REF = (
    "aoa-kag:docs/decisions/"
    "AOA-KAG-D-0044-detached-transition-authority.md"
)


def _build_fixture(root: Path):
    write_fixture(root)
    source = build_index(root)
    family = build_repository_indexes(source, repo_root=root)
    portable_manifest, portable_shards = build_portable_family(source, family)
    return build_tiered_family(portable_manifest, portable_shards), portable_manifest


def _family_ref(manifest: dict[str, object], ref: str) -> dict[str, object]:
    identity = manifest["family_identity"]
    assert isinstance(identity, dict)
    return {
        "schema_version": "aoa-repo-local-kag-family-manifest-v3",
        "ref": ref,
        "family_digest": identity["content_digest"],
        "source_snapshot": identity["source_snapshot"],
        "distribution_digest": None,
    }


def _make_authorized_transition(
    root: Path,
    build,
    portable_manifest: dict[str, object],
    *,
    kind: str,
):
    owner_root = root.parent / "authority-owner"
    decision_path = owner_root / "docs" / "decisions" / DECISION_REF.split("/", 2)[-1]
    decision_path.parent.mkdir(parents=True)
    decision_bytes = (
        b"# Detached transition\n\n"
        b"## Index Metadata\n\n"
        b"- Posture: accepted\n"
    )
    decision_path.write_bytes(decision_bytes)

    if kind == "producer_migration":
        target = tiered_transition_target(build, target_ref="b" * 40)
        payload = {
            "schema_version": "aoa-repo-local-kag-producer-migration-v1",
            "kind": "detached_producer_lineage_migration",
            "owner": {
                "name": "aoa-kag",
                "namespace": "aoa:aoa-kag",
                "owner_type": "organ",
                "root": ".",
            },
            "decision": {
                "ref": DECISION_REF,
                "digest": sha256_bytes(decision_bytes),
                "posture": "accepted",
            },
            "predecessor": _family_ref(portable_manifest, "a" * 40),
            "target": target,
            "replay": {
                "nonce": "sha256:" + "c" * 64,
                "sequence": 1,
                "ledger_ref": "aoa-kag://replay/test-ledger",
                "ledger_digest": "sha256:" + "d" * 64,
                "consumption": {"state": "unconsumed"},
            },
            "authority": {
                "contract_version": "aoa-kag:transition-authority-v1",
                "contract_digest": _transition_contract_identity()["digest"],
                "issuer": {
                    "owner": "aoa-kag",
                    "namespace": "aoa:aoa-kag",
                    "ref": "aoa-kag://issuer/test",
                    "artifact_digest": "sha256:" + "0" * 64,
                },
                "acceptance": {
                    "state": "independently_accepted",
                    "ref": "aoa-kag://acceptance/test",
                    "digest": "sha256:" + "e" * 64,
                },
            },
        }
    else:
        target = tiered_projection_target(build, target_ref="b" * 40)
        projection, output = complete_tiered_projection_expectations(build)
        payload = {
            "schema_version": "aoa-repo-local-kag-projection-transition-v1",
            "kind": "complete_projection_transition",
            "owner": {
                "name": "aoa-kag",
                "namespace": "aoa:aoa-kag",
                "owner_type": "organ",
                "root": ".",
            },
            "decision": {
                "ref": DECISION_REF,
                "digest": sha256_bytes(decision_bytes),
                "posture": "accepted",
            },
            "predecessor": _family_ref(portable_manifest, "a" * 40),
            "target": target,
            "projection": projection,
            "output": output,
            "replay": {
                "nonce": "sha256:" + "c" * 64,
                "sequence": 1,
                "ledger_ref": "aoa-kag://replay/test-ledger",
                "ledger_digest": "sha256:" + "d" * 64,
                "consumption": {"state": "unconsumed"},
            },
            "authority": {
                "contract_version": "aoa-kag:transition-authority-v1",
                "contract_digest": _transition_contract_identity()["digest"],
                "issuer": {
                    "owner": "aoa-kag",
                    "namespace": "aoa:aoa-kag",
                    "ref": "aoa-kag://issuer/test",
                    "artifact_digest": "sha256:" + "0" * 64,
                },
                "acceptance": {
                    "state": "independently_accepted",
                    "ref": "aoa-kag://acceptance/test",
                    "digest": "sha256:" + "e" * 64,
                },
            },
        }
    detached_record = {
        "schema_version": "aoa-kag:detached-transition-authority-v1",
        "owner": "aoa-kag",
        "subject_digest": _transition_subject_digest(payload),
        "issuer_ref": "aoa-kag://issuer/test",
        "acceptance_ref": "aoa-kag://acceptance/test",
        "acceptance_digest": "sha256:" + "e" * 64,
        "state": "independently_accepted",
    }
    detached_path = root.parent / "detached-authority.json"
    detached_bytes = json.dumps(
        detached_record,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    detached_path.write_bytes(detached_bytes)
    payload["authority"]["issuer"]["artifact_digest"] = (
        "sha256:" + sha256_bytes(detached_bytes)
    )
    acceptance = {
        "state": "independently_accepted",
        "ref": "aoa-kag://acceptance/test",
        "digest": "sha256:" + "e" * 64,
    }
    replay_state = {
        "ledger_ref": "aoa-kag://replay/test-ledger",
        "ledger_digest": "sha256:" + "d" * 64,
        "last_sequence": 0,
        "used_nonces": [],
    }
    return payload, owner_root, detached_path, acceptance, replay_state


class RepoLocalKagTransitionAuthorityTests(unittest.TestCase):
    def test_schema_examples_and_ordinary_budget_contract_are_separate(self) -> None:
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
            Draft202012Validator(schema).validate(
                json.loads((REPO_ROOT / "examples" / example_name).read_text())
            )
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
            Path("schemas/repo-local-kag-projection-transition.schema.json"),
            TRANSITION_CONTRACT_PATHS,
        )

    def test_detached_producer_migration_is_admitted_only_with_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "candidate"
            root.mkdir()
            build, portable_manifest = _build_fixture(root)
            migration, owner_root, authority_path, acceptance, replay_state = (
                _make_authorized_transition(
                    root,
                    build,
                    portable_manifest,
                    kind="producer_migration",
                )
            )
            validate_tiered_producer_migration(
                migration,
                predecessor=migration["predecessor"],
                build=build,
                target_ref="b" * 40,
                detached_authority_path=authority_path,
                acceptance_record=acceptance,
                replay_state=replay_state,
                owner_root=owner_root,
                candidate_root=root,
            )

    def test_complete_projection_checks_fixed_point_and_full_component_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "candidate"
            root.mkdir()
            build, portable_manifest = _build_fixture(root)
            transition, owner_root, authority_path, acceptance, replay_state = (
                _make_authorized_transition(
                    root,
                    build,
                    portable_manifest,
                    kind="projection_transition",
                )
            )
            validate_tiered_projection_transition(
                transition,
                predecessor=transition["predecessor"],
                build=build,
                target_ref="b" * 40,
                detached_authority_path=authority_path,
                acceptance_record=acceptance,
                replay_state=replay_state,
                owner_root=owner_root,
                candidate_root=root,
            )

            tampered = copy.deepcopy(transition)
            tampered["output"]["placement"]["git_hot_objects"] += 1
            self.assertEqual(
                "unknown",
                transition_admission_state(
                    "projection_transition",
                    tampered,
                    predecessor=transition["predecessor"],
                    target=tiered_projection_target(build, target_ref="b" * 40),
                    expected_projection=transition["projection"],
                    expected_output=transition["output"],
                    detached_authority_path=authority_path,
                    acceptance_record=acceptance,
                    replay_state=replay_state,
                    owner_root=owner_root,
                    candidate_root=root,
                ),
            )
            incomplete = copy.deepcopy(transition)
            incomplete["projection"].pop("after")
            self.assertEqual(
                "unknown",
                transition_admission_state(
                    "projection_transition",
                    incomplete,
                    predecessor=transition["predecessor"],
                    target=tiered_projection_target(build, target_ref="b" * 40),
                    expected_projection=transition["projection"],
                    expected_output=transition["output"],
                    detached_authority_path=authority_path,
                    acceptance_record=acceptance,
                    replay_state=replay_state,
                    owner_root=owner_root,
                    candidate_root=root,
                ),
            )

    def test_adversarial_owner_base_candidate_and_replay_states_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "candidate"
            root.mkdir()
            build, portable_manifest = _build_fixture(root)
            transition, owner_root, authority_path, acceptance, replay_state = (
                _make_authorized_transition(
                    root,
                    build,
                    portable_manifest,
                    kind="projection_transition",
                )
            )
            kwargs = {
                "predecessor": transition["predecessor"],
                "target": tiered_projection_target(build, target_ref="b" * 40),
                "expected_projection": transition["projection"],
                "expected_output": transition["output"],
                "detached_authority_path": authority_path,
                "acceptance_record": acceptance,
                "replay_state": replay_state,
                "owner_root": owner_root,
                "candidate_root": root,
            }
            wrong_owner = copy.deepcopy(transition)
            wrong_owner["owner"]["name"] = "other-owner"
            self.assertEqual(
                "unsupported",
                transition_admission_state(
                    "projection_transition", wrong_owner, **kwargs
                ),
            )
            wrong_base = copy.deepcopy(transition)
            wrong_base["predecessor"]["family_digest"] = "f" * 64
            self.assertEqual(
                "unknown",
                transition_admission_state(
                    "projection_transition", wrong_base, **kwargs
                ),
            )
            candidate_authority = root / "candidate-authority.json"
            candidate_authority.write_bytes(authority_path.read_bytes())
            candidate_self_issued = copy.deepcopy(transition)
            candidate_self_issued["authority"]["issuer"]["artifact_digest"] = (
                "sha256:" + sha256_bytes(candidate_authority.read_bytes())
            )
            self.assertEqual(
                "unsupported",
                transition_admission_state(
                    "projection_transition",
                    candidate_self_issued,
                    **{**kwargs, "detached_authority_path": candidate_authority},
                ),
            )
            replayed = copy.deepcopy(replay_state)
            replayed["last_sequence"] = 1
            self.assertEqual(
                "unknown",
                transition_admission_state(
                    "projection_transition",
                    transition,
                    **{**kwargs, "replay_state": replayed},
                ),
            )
            self.assertEqual(
                "migration_required",
                transition_admission_state(
                    "projection_transition",
                    transition,
                    **{**kwargs, "detached_authority_path": None},
                ),
            )

    def test_unknown_kind_and_receipt_are_not_transition_authority(self) -> None:
        self.assertEqual(
            "unsupported",
            transition_admission_state("unknown_transition", {},),
        )
        with self.assertRaises(TransitionAuthorityError):
            validate_full_projection_transition(
                {"schema_version": BUDGET_RECEIPT_SCHEMA_VERSION},
                predecessor={},
                target={},
                expected_projection={},
                expected_output={},
            )
