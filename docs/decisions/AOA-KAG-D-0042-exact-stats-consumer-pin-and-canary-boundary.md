# AOA-KAG-D-0042 Exact Stats Consumer Pin And Canary Boundary

## Index Metadata

- Decision ID: AOA-KAG-D-0042
- Original date: 2026-08-23
- Surface classes: provider registry, validation workflow, compatibility canary, release contour
- KAG surfaces: exact provider identity, generated provider maps, consumer validation, release artifact inputs
- Source lanes: aoa-kag, aoa-stats, 8Dionysus
- Guard families: source-owned authority, provider-before-consumer, moving-lane claim boundary, fail-closed artifact admission
- Posture: accepted

## Context

The `aoa-kag` v0.5.1 consumer was validated against the published
`aoa-stats@339ecb2db22ac4552fa88756b650896ebbff5b56` provider. The final
provider-spine repair has now published `aoa-stats` v0.2.2 at
`f119805cda69b3edeb2a4c5e407368d70e68650d`, while the scheduled compatibility
canary still checked out `aoa-stats` by moving default branch. That combination
could produce a green canary for a provider that was not the provider admitted
by the KAG registry or immutable release validation.

## Decision

Bind the authored KAG provider registry, the blocking source-fast checkout, and
the scheduled compatibility canary to the exact published `aoa-stats` commit
`f119805cda69b3edeb2a4c5e407368d70e68650d` (tag `v0.2.2`). Regenerate all KAG
provider and coverage read models from that source input. Keep the other
scheduled sibling checkouts moving because the canary remains useful as a
compatibility probe, but state that boundary in the workflow and validation
authority: the canary is not immutable release proof.

The release gate remains stricter than the canary: its full provider set,
source commit, generated family, artifact record, and release identity must be
exactly bound before publication. Artifact verdicts remain owner-derived
`allow`, `warn`, `deny`, `manual_review_required`, or `unknown`; this decision
does not promote any verdict or imply runtime, proof, delivery, or acceptance.

## Options Considered

- Leave the canary floating: rejected because provider-before-consumer would
  remain unprovable for a scheduled result.
- Pin every canary sibling: rejected because it would turn a compatibility
  probe into a second immutable release lane and widen this bounded repair.
- Pin only `aoa-stats` and document the remaining moving lane: chosen because
  it closes the repaired provider identity while preserving the intended
  compatibility signal and the independent immutable release gate.
- Reuse v0.5.1: rejected because a release-bearing provider contract changed and
  the old tag and GitHub Release must remain immutable.

## Consequences

- The KAG generated provider/readiness surfaces carry the final published stats
  provider identity and must be rebuilt by owner generators.
- A canary result proves compatibility against exact `aoa-stats` plus the
  observed moving sibling set only; it cannot prove a release artifact or
  immutable full-family identity.
- The next KAG release is a successor to v0.5.1. The v0.5.1 tag and GitHub
  Release remain unchanged.

## Source Surfaces

- `manifests/provider_registry.json`
- `.github/workflows/repo-validation.yml`
- `.github/workflows/compatibility-canary.yml`
- `config/validation_lanes.json`
- `docs/validation/COMMAND_AUTHORITY.md`
- `generated/local_kag_provider_map.min.json`
- `generated/repo_local_kag_coverage.min.json`
- `aoa-stats` v0.2.2 at `f119805cda69b3edeb2a4c5e407368d70e68650d`

## Validation

Run the owner source-fast, generated, release, and compatibility-canary lanes
separately. Record source, CI, merge, tag, GitHub Release, artifact admission,
runtime, proof, delivery, closure, and human-acceptance claims separately in
the release execution report.
