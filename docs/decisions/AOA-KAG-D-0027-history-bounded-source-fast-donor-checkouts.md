# History-Bounded Source-Fast Donor Checkouts

## Index Metadata

- Decision ID: AOA-KAG-D-0027
- Original date: 2026-08-01
- Surface classes: GitHub landing, validation guard, dependency checkout, CI performance
- KAG surfaces: local integrity, owner portable family, source-fast handoff
- Source lanes: aoa-kag, provider registry
- Guard families: exact donor pin, working-tree parity, explicit history boundary, full-audit preservation
- Posture: accepted

## Context

The required source-fast job checks out eight exact-pinned donor repositories
before local validation. Their working trees are read by source-fast validators
and bound into the same-run handoff, but their commit ancestry is not queried.
The owner `aoa-kag` checkout is different: its repository event family and
expected history refs require ancestry. The full OS-wide release audit also
retains history-sensitive validation across all provider repositories.

Three hosted owner-local samples took 179-198 seconds, with a median of 188
seconds. Donor checkout steps consumed 45-49 seconds per sample. The cached
local donor histories contained 2,857 commits and about 145 MiB of Git data,
despite source-fast consuming only the eight exact pinned working trees.

## Decision

Use depth-one checkouts for exactly the eight donor repositories in the
`source_fast` job. Keep the owner `aoa-kag` checkout at full history. Keep every
checkout in the full OS-wide release audit at full history, and leave the
compatibility canary unchanged.

The donor refs remain the exact pins owned by
`manifests/provider_registry.json`. Source-fast continues to validate the full
donor working trees, and the same-run handoff continues to bind the observed
HEAD, index tree, dirty state, registry pin, owner-family identity, and explicit
history boundaries. A future source-fast dependency on donor ancestry must
restore full history for that donor or introduce a separately enforced and
proved history contract before landing.

## Options Considered

- Keep full donor history in source-fast: simple, but transfers history that no
  source-fast consumer reads.
- Use depth-one donor checkouts only in source-fast: removes unused transfer
  while preserving exact pinned working trees and every stronger audit.
- Add partial or sparse checkouts: deferred because current validators read
  broad donor working trees and no enforced path manifest proves completeness.
- Reuse persistent checkout caches: rejected for this pressure because cache
  admission and invalidation would widen the trust boundary.
- Shallow the owner or full-audit checkouts: rejected because those lanes retain
  history-sensitive proof.

## Rationale

Checkout history is an input only when a consumer observes ancestry. The eight
source-fast donors are content inputs at exact immutable pins, so depth one is
equivalent for their current consumers. This does not turn a shallow checkout
into proof authority: exact pin parity, clean index and worktree state, local
validation, owner-family validation, and the typed same-run handoff remain
blocking.

Restricting the change to one job keeps the boundary inspectable. Full audit
and compatibility behavior stay unchanged, so uncertainty or future history
use still fails in the stronger lanes instead of silently reducing coverage.

## Consequences

- Owner-local and high-impact source-fast jobs transfer only the pinned donor
  commits rather than all eight histories.
- The owner checkout still supports repository event and ancestry validation.
- The full OS-wide release audit preserves complete provider histories and all
  existing proof obligations.
- Workflow tests pin the eight-to-one shallow/full split and reject shallow
  release-audit checkouts.
- Further sparse checkout, trusted owner fragments, and parallel execution
  remain separate decisions with their own equivalence evidence.

## Source Surfaces

- `.github/workflows/repo-validation.yml`
- `manifests/provider_registry.json`
- `scripts/source_fast_handoff.py`
- `scripts/ci_gate.py`
- `tests/test_repo_validation_workflow.py`
- `docs/decisions/AOA-KAG-D-0025-exact-same-run-source-fast-handoff.md`

## Validation

Regenerate and validate decision indexes. Assert that source-fast contains
exactly eight depth-one donor checkouts and one full-history owner checkout,
while release audit contains no depth-one checkout. Materialize all eight exact
pins as real shallow repositories and run the complete source-fast lane against
them. Then run one hosted high-impact workflow and compare checkout and job wall
time with the accepted three-sample owner-local baseline. Land only if exact
proof remains green and the hosted result shows a meaningful benefit.
