# Defer Cross-Run Owner Proof Fragments

## Index Metadata

- Decision ID: AOA-KAG-D-0029
- Original date: 2026-08-01
- Surface classes: validation guard, artifact trust, CI performance, cross-run reuse
- KAG surfaces: provider-home audit, repo-local coverage, owner proof fragments
- Source lanes: aoa-kag, provider registry, abyss-machine artifact policy
- Guard families: trusted producer, exact fragment identity, complete owner order, fail-closed cold fallback
- Posture: accepted

## Context

Run-scoped provider coverage fusion removes the duplicate portable-family load,
but every full OS-wide run still validates all provider homes. A trusted result
from an earlier accepted run could theoretically replace an unchanged owner's
provider-home scan while preserving the final 23-owner composition.

The opportunity is real but uneven. A first-parent study of 106 transitions
from 2026-05-18 through 2026-08-01 classified current coverage runtime inputs,
provider membership and pins, and the always-changing `aoa-kag` owner identity.
Fifty-six transitions changed a global runtime input or membership and could
reuse no fragment. Thirty-eight could reuse all 22 external owners, and twelve
could reuse a partial set. The optimistic fragment-slot hit rate was 43.89%.

On the post-fusion main run, the serial provider-home phase occupied 478.174
seconds; 460.420 seconds belonged to external owners. Applying those measured
owner intervals to the historical invalidation pattern gives an optimistic
mean gross saving of 213.077 seconds per transition and a maximum of 460.420
seconds, but a median of zero. This is feasibility evidence, not hosted warm
proof, and excludes artifact production, retrieval, verification, expiry, and
cold-fallback overhead.

Cross-run reuse is an artifact admission decision, not an extension of the
same-run packet cache. The current `abyss-machine` artifact policy has no class
for an internal, addressable KAG CI proof aggregate. The closest classes are
not equivalent:

- `kag_owner_family_release` is a full content-addressed owner-family release
  and requires ABI, SBOM, SLSA/in-toto, and Sigstore/Cosign controls;
- `kag_os_composition` is a signed composition of already verified owner
  releases, not a bundle of internal provider-home verdicts;
- `host_local_evidence` is private host evidence and is not a portable GitHub
  workflow artifact.

The source-owned trust gate therefore has no admitted registry record for the
candidate and returns `unknown` with `no_registry_record`. GitHub artifact
attestations can bind repository, signer workflow, source ref, source digest,
and subject digest, but that transport and provenance capability does not
define the missing artifact class or authorize the proof substitution.

## Decision

Do not implement or consume cross-run owner proof fragments in `aoa-kag` under
the current trust policy. Keep every main audit cold and keep pull-request full
audits on the complete provider-home path. A cache hit, matching digest,
successful prior workflow, downloadable artifact, or GitHub attestation alone
must not suppress an owner proof.

Reopen implementation only after the `abyss-machine` owner admits an artifact
class and consumer route that explicitly covers an internal KAG CI proof
aggregate, its addressable owner subjects, required provenance controls,
public/private boundary, lifecycle, retention, revocation, and exact gate. The
new route must allow `aoa-kag` to verify one concrete artifact without
promoting generated evidence into owner truth.

If that owner prerequisite lands, the first implementation remains bounded:

- only a successful cold `main` audit may produce the candidate;
- pull requests may consume it, but pull-request workflows may never produce
  trusted fragments and `main` remains independently cold;
- verification binds repository, exact signer workflow, `refs/heads/main`,
  source commit, successful run identity, subject digest, artifact digest,
  artifact schema, builder/runtime epoch, provider membership and order, and
  every owner key field;
- any missing, expired, malformed, tampered, wrong-run, wrong-ref,
  wrong-workflow, wrong-owner, or incompatible fragment is a miss or reject
  and executes the complete cold owner proof;
- the final run still assembles all configured owner rows in canonical order,
  validates schemas and aggregate budgets, checks exact coverage parity,
  performs generated fixed-point, and emits the complete typed receipt;
- hosted admission requires cold, full-hit, partial-hit, changed-owner, global
  invalidation, corrupt-artifact, wrong-provenance, expiry, membership/order,
  and schema/builder-epoch cases, with material warm benefit and no material
  cold regression.

## Options Considered

- Use the ordinary Actions cache: rejected because mutable cache availability
  and a matching key are not provenance or proof.
- Upload one artifact per owner from pull-request runs: rejected because an
  unaccepted producer could mint the evidence it later consumes and because
  private-owner boundaries would be easy to widen accidentally.
- Treat the aggregate as `kag_owner_family_release` or `kag_os_composition`:
  rejected because both classes describe different subjects and lifecycle.
- Define a local `aoa-kag` trust class and proceed with GitHub attestations:
  rejected because artifact-class policy and consumer admission belong to
  `abyss-machine`.
- Preserve the cold path and defer until the owner route exists: selected.

## Rationale

The observed upper bound justifies keeping the idea alive, but not bypassing
the missing authority. Cross-run reuse would replace hundreds of seconds of
blocking source and portable-family validation with an artifact claim. That is
safe only when the claim has an owner-defined class, producer boundary,
retention and revocation posture, and exact consumer gate. A GitHub signature
can authenticate a workflow identity and subject digest; it cannot decide what
the subject proves inside OS Abyss.

Deferral also reflects the measured distribution. More than half of the
sampled transitions invalidate all fragments, so cold overhead and operational
complexity matter as much as the best warm run. The next experiment should
begin after the trust prerequisite, not by spending hosted runs on a candidate
that cannot yet receive an `allow` verdict.

## Consequences

- Current full audits retain their complete proof strength and current
  post-fusion performance.
- No new artifact publication, registry mutation, workflow permission, secret,
  or cross-run cache is introduced.
- The feasibility numbers and stop reason prevent repeated implementation of
  the same unadmitted shortcut.
- `abyss-machine` is the next owner for a possible internal KAG CI proof class;
  `aoa-kag` remains owner of fragment schema, builder semantics, and validators
  after that prerequisite.
- A future positive decision must supersede this record and provide actual
  hosted warm and cold evidence; the optimistic model here is not that proof.

## Source Surfaces

- `docs/decisions/AOA-KAG-D-0028-run-scoped-provider-coverage-fusion.md`
- `scripts/generate_repo_local_kag_coverage.py`
- `scripts/validators/local_kag_subtree.py`
- `scripts/validators/orchestration/runner.py`
- `scripts/coverage_run.py`
- `manifests/provider_registry.json`
- `schemas/repo-local-kag-coverage.schema.json`
- `abyss-machine:manifests/artifact_signature_policy.manifest.json`
- `abyss-machine:skills/os-abyss-artifact-trust-loop/references/contract.yaml`

## Validation

Regenerate and validate decision indexes, regenerate the repository-local KAG
family, prove its full and incremental fixed point, and run source-fast. This
decision changes no validator, workflow, proof payload, or runtime artifact.
