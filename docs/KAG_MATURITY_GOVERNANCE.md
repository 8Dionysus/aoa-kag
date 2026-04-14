# KAG Maturity Governance

This note defines when `aoa-kag` is mature enough to pause net-new expansion
and wait for neighboring owner repositories to grow.

The target is not "more graph."
The target is a stable, source-first derived substrate that can hold its shape
without quietly absorbing routing, proof, memory, role, or scenario ownership.

## Core rule

`aoa-kag` is mature enough to pause further widening only when it can:

- ingest source-owned exports through reviewable manifests
- publish bounded derived surfaces with visible provenance
- narrow consumer posture honestly when drift appears
- reground callers back to stronger owner surfaces
- refuse new surface growth unless a bounded need is explicit

## Maturity checkpoints

Treat these as the required checkpoints for a pause-worthy KAG layer.

### 1. Manifest-driven donor governance

Source-owned donor onboarding should live in manifest-backed control surfaces.

At minimum, each donor must declare:

- what export is source-owned
- whether it is only registry-visible, spine-visible, or routing-visible
- what owner boundary still blocks wider activation
- what proof or owner evidence would be needed to widen later

### 2. Surface stability tiers

Every active or consumer-facing KAG surface should have one explicit stability
tier:

- `planned_contract_only`
  - the contract may be documented and example-backed
  - no live generated payload is implied
- `experimental_derived`
  - the surface is generated and validator-backed
  - consumer use stays narrow and review-aware
- `consumer_stable`
  - the surface is generated, validator-backed, bounded by proof expectations,
    and safe for declared downstream consumers

No surface should silently drift between tiers through usage folklore alone.

### 3. Honest recovery posture

Every live derived family should have:

- a bounded output contract
- a source-first re-entry path
- a quarantine path when consumer meaning becomes unsafe
- a regrounding path back to stronger owner refs

If one of those is missing, the surface is not ready to anchor more growth.

### 4. Explicit wait-state boundaries

`aoa-kag` should name what it is waiting on from neighboring repositories
instead of solving their unfinished work internally.

That includes:

- memory readiness and retention pressure in `aoa-memo`
- proof and verdict meaning in `aoa-evals`
- scenario choreography in `aoa-playbooks`
- runtime and role posture in `aoa-agents`
- source-authored expansion in `Tree-of-Sophia`

### 5. Proof expectations without proof capture

`aoa-kag` must not own proof, but it should name what bounded claim a surface
expects a proof layer to check later.

Each live surface should carry:

- the bounded claim it is trying to support
- the current eval anchor refs when they exist
- the missing proof lane when no suitable eval exists yet

### 6. Stop-rule for new `AOA-K-*`

Net-new `AOA-K-*` surfaces should be rare and gated.

A new surface should land only when all of the following are true:

- an existing family cannot carry the need honestly
- the owner-side input is explicit enough to derive from
- the downstream consumer is genuinely blocked or a new honesty gap exists
- proof expectations are named
- re-entry and quarantine posture are declared up front

If those conditions are not met, extend an existing family, improve a guardrail,
or wait for the owner repo to grow.

## Pause threshold

Treat `aoa-kag` as mature enough to pause further widening when:

1. donor onboarding is manifest-driven rather than code-hardcoded
2. every live surface has an explicit stability tier
3. every live surface has re-entry and quarantine posture
4. every neighboring owner layer has an explicit wait-state note
5. every live surface has a proof expectation or a named proof gap
6. the stop-rule governs new `AOA-K-*` landings

At that point, the honest move is usually:

- maintain integrity
- improve existing validators and proofs
- wait for stronger owner-side exports or contracts

## Non-goals

This governance note does not:

- turn `aoa-kag` into a release judge for the whole federation
- authorize KAG-owned verdict language
- authorize KAG-owned routing policy
- authorize KAG-owned memory truth
- authorize KAG-owned canon growth

It exists to keep the derived layer strong enough to stop.
