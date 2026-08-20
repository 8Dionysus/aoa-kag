# Tiered KAG Migration

This plan governs the transition of all 24 canonical providers. A unit-test
green reference owner, one canary, or one merged PR is not rollout completion.

## Phase 0: Baseline

Pin all 24 owner source commits and record tracked bytes, shard counts, owner
budgets, generated delta, compatibility digests, CI bytes/time, and current
consumer routes. Explain any drift from the release-pinned 24/24 v3 baseline
before changing storage.

For each initial v4 build, derive `migration.from_family_digest` from the
head-equivalent v3 family using the exact v3 manifest parameters at the pinned
history boundary. After that owner lands v4, treat the migration block as
immutable history. Normal regeneration must source it from the pinned base
commit, while the distribution and owner release bind the digest of the full
corpus manifest document. The migration block remains outside logical corpus
identity.

## Phase 1: Shadow Publication 24/24

For every owner:

1. build the v4 corpus and distribution manifests;
2. publish the complete family to the artifact plane while retaining cold Git
   copies;
3. verify corpus parity and byte-exact object/pack roundtrip;
4. admit owner, source ref, signature, schema/ABI, access, and revocation state;
5. prove object reuse, mirror independence, offline export/import, dual-reader
   parity, exact v2 assembly, outage honesty, corruption rejection, rollback,
   and public-safety boundaries.

Externalization is forbidden until every shadow obligation is evidenced.
The executable proof owner is
`scripts/run_repo_local_kag_rollout.py --phase shadow`; its packet is governed
by `schemas/kag-tiered-rollout-evidence.schema.json` and remains outside the
source repositories.

## Phase 2: Five-Owner Canary

Externalize in this order:

1. `aoa-techniques`;
2. `abyss-machine`;
3. `aoa-evals`;
4. `Agents-of-Abyss`;
5. `abyss-stack`.

For each canary, pin before/after corpus and distribution digests, activate the
dual reader, remove only cold current-tree copies, rebuild the hot baseline,
and test local query, incremental federation, runtime materialization, five
MCP operations, offline bundle, outage, last-good rollback, Git reduction, CI
scan reduction, and hydration cost. Git history remains intact.

A canary review must accept the topology before the remaining owners move.
The source mutation owner is
`scripts/prepare_repo_local_kag_externalization.py --canary-only`; it accepts
only the exact ordered five-owner set and stops before commit-bound signing.

## Phase 3: Rollout 24/24

Move the remaining owners in bounded batches. Each migration produces a signed
owner-family release, explicit hot profile, artifact trust result, owner change
receipt, before/after metrics, offline proof, and rollback coordinate. Update
the OS composition incrementally from verified owner releases rather than
rescanning unchanged source trees.
Preparation uses the same isolated-worktree command without `--canary-only`;
publication and aggregate proof use
`scripts/run_repo_local_kag_rollout.py --phase rollout`.

## Phase 4: Landing And Live Verification

All related PRs must pass their selected lanes and merge into canonical
branches. Synchronize clean canonical checkouts with `origin/main`, run the
post-merge 24-owner audit from pinned snapshots, reconstruct all seven v2
views, verify aggregate Git-hot bytes at or below 234,881,024, and exercise
live runtime materialization plus `discover`, `search`, `read`, `traverse`, and
`explain` with freshness, provenance, degradation, and owner-return evidence.

## Stop Lines

- Do not raise the 320 MiB aggregate ceiling.
- Do not rewrite Git history.
- Do not replace Git monoliths with one artifact monolith.
- Do not couple corpus identity to URL, mirror, pack layout, or cache path.
- Do not use runtime popularity for committed hot selection.
- Do not externalize cold shards before shadow and canary proof.
- Do not publish private/session/runtime material.
- Do not hide partial, stale, unavailable, revoked, or denied states.
- Do not call canary, green CI, or a merged reference-owner PR the 24-owner
  rollout.

## Completion Evidence

The final OS report maps every Definition-of-Done requirement to a current
manifest, signature/admission receipt, CI run, merged commit, offline/runtime
scenario, metric, or live MCP result. Missing or indirect evidence is an open
blocking obligation, not an inferred success.
