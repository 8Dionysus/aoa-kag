# AOA-KAG-D-0043 Consolidated V0.5.0 Campaign And Stats Provider Boundary

## Index Metadata

- Decision ID: AOA-KAG-D-0043
- Original date: 2026-08-23
- Surface classes: provider registry, generated readmodel, release contour, historical provenance, decision supersession
- KAG surfaces: exact provider identity, generated provider maps, coverage, canonical changelog, release artifact inputs
- Source lanes: aoa-kag, aoa-stats, 8Dionysus
- Guard families: source-owned authority, provider-before-consumer, immutable release identity, historical provenance, fail-closed artifact admission
- Posture: accepted

## Context

`AOA-KAG-D-0042` preserved the rationale for an earlier campaign in which the
KAG consumer followed `aoa-stats` at `f119805...` and the next KAG release was
described as a successor to `v0.5.1`. The release-cleanup campaign found three
same-day KAG Releases (`v0.5.0`, `v0.5.1`, and `v0.5.2`) and a later provider
execution that landed the exact `aoa-stats` source at
`88ff38b1b38eef939f2c5b4541cbe8363a05fc8d`.

The cleanup must converge the current version-bearing route to one canonical
campaign release, while retaining every superseded body, tag-scoped changelog,
merged PR, commit, contract, validation result, limitation, and non-claim as
historical evidence. The older decision's moving-sibling canary boundary is
still useful, but its provider identity and successor-release wording cannot
remain current.

## Decision

Supersede `AOA-KAG-D-0042` for the current release and consumer-identity route.
The authored provider registry, blocking source-fast checkout, and scheduled
compatibility canary bind `aoa-stats` to the exact landed commit
`88ff38b1b38eef939f2c5b4541cbe8363a05fc8d`. Regenerate the provider map,
coverage, and repository-local owner family from that exact source input.

The canonical campaign release for this repository is exactly `v0.5.0`.
Its changelog and release body are the one consolidated human-facing record;
the same-day superseded release identities are not reissued or treated as
current. Their source bodies, tag changelogs, tags, PRs, commits, and
reconciliation evidence remain preserved in the cleanup ledger and historical
corpus. Cleanup may remove only the explicitly pretruth-enumerated same-day
GitHub Releases and tag refs after landed-main gates, then recreate one
`v0.5.0` on the exact landed main commit.

Retain the non-conflicting canary boundary from D-0042: a canary proves
compatibility against exact `aoa-stats` plus its observed moving sibling set;
it does not prove an immutable release artifact, runtime health, proof,
delivery, closure, or human acceptance. Provider, artifact, source, CI/merge,
runtime, proof, delivery, closure, and acceptance claims remain separate.

## Options Considered

- Keep D-0042 accepted: rejected because its `v0.5.1` and `f119805...`
  references would remain an authoritative current route.
- Rewrite D-0042 in place: rejected because it would erase the rationale and
  evidence of the earlier repair.
- Add a superseding decision and mark D-0042 historical: chosen because it
  preserves the prior boundary while making the current provider and release
  identity unambiguous.
- Keep all same-day release identities: rejected because release cleanup must
  leave exactly one canonical campaign Release without losing material.

## Consequences

- Current KAG generated surfaces and CI inputs identify `aoa-stats@88ff38b...`.
- Current release documentation and release execution bind to one `v0.5.0`
  changelog/body; no other campaign version is created.
- D-0042 remains discoverable as superseded historical rationale, including
  its old `f119805...` and `v0.5.1` evidence.
- The cleanup ledger is the preservation route for material that is removed
  from live same-day Release/tag surfaces; it does not elevate artifact,
  runtime, proof, delivery, closure, or acceptance verdicts.

## Source Surfaces

- `manifests/provider_registry.json`
- `.github/workflows/repo-validation.yml`
- `.github/workflows/compatibility-canary.yml`
- `generated/local_kag_provider_map.min.json`
- `generated/repo_local_kag_coverage.min.json`
- `CHANGELOG.md`
- `docs/decisions/AOA-KAG-D-0042-exact-stats-consumer-pin-and-canary-boundary.md`
- release-cleanup content-conservation ledger and execution report

## Validation

Run decision-record validation and regenerate decision indexes. Run the owner
source-fast, generated, repository-family, release, and full OS-wide provider
lanes separately. Before any live Release/tag cleanup, prove exact landed-main
identity, preservation of all pre-campaign refs, canonical changelog/body
equality, and the absence of all same-day superseded campaign identities.
