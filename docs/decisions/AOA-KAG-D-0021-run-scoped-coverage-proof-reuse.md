# Run-Scoped Coverage Proof Reuse

## Index Metadata

- Decision ID: AOA-KAG-D-0021
- Original date: 2026-07-29
- Surface classes: validation guard, release tooling, ephemeral proof artifact, telemetry receipt
- KAG surfaces: OS-wide provider coverage, generated parity, validation input identity
- Source lanes: aoa-kag, provider registry
- Guard families: command authority, owner completeness, generated-output parity, fail-closed identity, tamper rejection
- Posture: accepted

## Context

The release lane audited the same 23 provider families repeatedly across
`validate_kag.py`, coverage generation/check commands, generated parity, and a
possible stabilization pass. The repeated consumers ran in separate processes,
so each one reread and revalidated every sibling repository even when the
provider commits and all relevant KAG inputs were unchanged.

The two-pass generated fixed point and the full OS-wide owner audit remain
blocking proof. Removing either would make the gate cheaper by weakening it.
The avoidable cost is repeated execution of an already completed owner audit
inside one immutable validation epoch.

## Decision

The first OS-wide coverage consumer in a validation run may create one
temporary, run-scoped coverage packet outside the repository. Later consumers
may reuse the payload only after verifying its versioned shape, full input
identity, content digest, owner membership and order, owner count, canonical
display roots, and coverage schema.

The identity binds the KAG commit and dirty worktree state, exact pinned
provider commits, provider order, portable family and event identities,
generator and validator code, schemas, and validation configuration. A
provable identity change starts a new epoch and rebuilds safely; an unprovable
identity, stale pin, missing owner or manifest, malformed packet, digest
mismatch, or symlink substitution fails closed. The packet is deleted with the
run and is not a shared or cross-run cache.

Emit one machine-readable run receipt containing build and hit/miss counts,
compact input and payload identities, owner timings, coverage wall time, and
lane wall time. Telemetry describes execution; it does not become an owner
truth or proof verdict by itself.

## Options Considered

- Keep every full sweep: simplest execution model, but makes landing cost
  proportional to consumer count instead of source change.
- Use a shared mutable or cross-run cache: potentially faster, but introduces a
  trust and invalidation surface that this change cannot prove.
- Skip repeated generated or validator consumers: cheaper, but weakens
  fixed-point and parity evidence.
- Reuse one verified packet inside a bounded run: preserves every consumer and
  owner invariant while removing redundant sibling reads.

## Rationale

KAG is a derived substrate, so the reusable object must be a fully identified
derivative of owner-controlled inputs, never a replacement for them. Limiting
reuse to one temporary run makes the trust boundary small enough to validate
directly and keeps provider repositories, manifests, schemas, and generated
outputs as the stronger surfaces.

This route also preserves the command authority established by
AOA-KAG-D-0005. Lanes and consumers keep their existing blocking roles; only
the execution of an identical expensive sub-proof is shared.

## Consequences

- A stable release epoch performs one full owner audit; a real generated input
  transition may perform a second, but repeated consumers do not create more.
- Generated fixed-point, full/incremental parity, compatibility assembly,
  budgets, receipts, and blocking verdicts remain unchanged.
- Provider checkouts must match registry pins before packet reuse is available.
- Local mixed-root runs that cannot prove every identity fail instead of
  silently trusting partial state.
- A future local/OS-wide validator split may consume this packet contract, but
  must not turn packet availability into permission to skip required local
  checks.
- Cross-run caching and parallel owner execution remain separate decisions with
  separate equivalence evidence.

## Source Surfaces

- `DESIGN.md`
- `docs/KAG_MODEL.md`
- `docs/BOUNDARIES.md`
- `docs/SOURCE_POLICY.md`
- `config/validation_lanes.json`
- `manifests/provider_registry.json`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `scripts/coverage_run.py`
- `scripts/generate_repo_local_kag_coverage.py`
- `scripts/ci_gate.py`
- `scripts/release_check.py`
- `tests/test_repo_local_kag_index.py`
- `tests/test_validation_command_authority.py`

## Validation

Regenerate and validate decision indexes. Run focused packet lifecycle,
identity, tamper, command-authority, and script-topology tests; the complete
pinned test suite; then one release gate on exact provider pins. The release
receipt must show no more than two coverage builds and the generated coverage
payload digest must match the committed output.
