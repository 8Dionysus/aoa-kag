# AOA-KAG-D-0041 Preparation Seed And History Boundary

## Index Metadata

- Decision ID: AOA-KAG-D-0041
- Original date: 2026-08-21
- Surface classes: validation workflow, preparation sentinel, provider registry
- KAG surfaces: owner coverage seed, CI evidence DAG, provider pin
- Source lanes: aoa-kag, provider owner repositories
- Guard families: source-owned authority, history boundary, seed reuse, fail-closed proof
- Posture: accepted

## Context

The preparation-only coverage sentinel needs a complete canonical owner seed
when an external owner has repaired its local family but that repair is not yet
available from the owner's public checkout. The historical PR base remains the
correct donor boundary for source-fast and release evidence, but it can carry
an older owner row and therefore fail before the unchanged full proof starts.
Using the candidate itself as the history ref would conflate preparation input
with source lineage and would weaken the meaning of the receipts.

## Decision

Keep `base-ref` as the explicit historical boundary for source-fast, provider
identity, event history, receipts, and the release continuation. Add the
optional `coverage-seed-ref` only to `scripts/ci_preflight_dag.py`; hosted PR
and default executions provide the exact candidate/default-branch head for the
two seed-only sentinels. The existing ancestry and canonical-runtime checks
remain in `prepare_landing.py`, and sentinel receipts identify the seed as
preparation-only. The seed never becomes owner proof, release evidence, or a
landing verdict, and the unchanged full owner proof still reads the pinned
provider checkouts.

Advance the active `aoa-agents` provider pin to its landed main commit
`cc4c2b55af22ada44874b6c8fa6668e7414ab7b6` in both the provider registry and
the source-fast workflow checkout. Keep `aoa-session-memory` on its public
pin until its local repair is admitted by that owner; a local-only family row
may support preparation evidence but cannot be treated as remote admission.

## Options Considered

- Reuse the PR base as both history and seed: rejected because the seed can be
  stale for an independently repaired owner and blocks the preparation retry.
- Replace `base-ref` with the candidate head: rejected because it changes the
  historical proof boundary and receipt semantics.
- Add a separate candidate seed coordinate while preserving base history:
  chosen because it removes only the stale seed dependency and leaves all
  blocking proof and owner admission unchanged.
- Pin the unpushed session-memory repair: rejected because GitHub cannot admit
  a local-only commit and KAG must not mutate that owner's remote.

## Rationale

KAG is a derived substrate and may accelerate bounded preparation, but it does
not own provider meaning or admission. Separating the two coordinates makes
the useful local evidence consumable by the early sentinel without allowing a
local owner repair to masquerade as a public checkout or to bypass the full
owner audit.

## Consequences

- Preparation receipts expose both the historical boundary and the seed
  coordinate, so later readers can distinguish the claims.
- A candidate seed is valid only when it is an ancestor and its canonical
  coverage runtime inputs match the candidate.
- The full release lane remains blocking and can still stop on an unavailable,
  stale, or unadmitted external owner.
- Owner-local repair and remote publication remain the source owner's duties;
  KAG records the residual rather than manufacturing admission.

## Source Surfaces

- `scripts/ci_preflight_dag.py`
- `scripts/prepare_landing.py`
- `.github/workflows/repo-validation.yml`
- `manifests/provider_registry.json`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `aoa-agents` landed main `cc4c2b55af22ada44874b6c8fa6668e7414ab7b6`
- `aoa-session-memory` local-only repair `69f0ec581256`

## Validation

Run the CI preflight unit tests, provider-registry/workflow tests, decision
index and decision-record checks, the unchanged source-fast and owner-family
lanes, and the hosted full release audit. A local-only owner row is reported
as preparation evidence, not as remote admission or release success.
