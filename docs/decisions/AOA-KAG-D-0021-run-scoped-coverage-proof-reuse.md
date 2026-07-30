# Run-Scoped Coverage Proof Reuse

## Index Metadata

- Decision ID: AOA-KAG-D-0021
- Original date: 2026-07-29
- Surface classes: validation guard, release tooling, command authority, ephemeral proof artifact, telemetry receipt
- KAG surfaces: local integrity, OS-wide provider coverage, generated fixed point, validation input identity
- Source lanes: aoa-kag, provider registry
- Guard families: command authority, owner completeness, generated-output parity, fail-closed identity, fail-closed scope selection, tamper rejection
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

After packet reuse was proved, one authority coupling remained:
`validate_kag.py` still combined repository-local schemas, manifests,
provenance, routes, examples, and generated structures with two OS-wide
operations: provider-home family completeness and coverage generation. Every
invocation therefore loaded every owner family even when a lane needed only
local integrity.

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

Expose explicit `local`, `os-wide`, and `full` validator scopes. `local` never
loads every provider family. `os-wide` validates provider-home completeness
and committed coverage against the complete current provider build, reusing
the packet for coverage consumers when a lane run scope is active. `full`
composes both and remains the no-argument compatibility behavior. Source-fast
always selects `local`; generated and compatibility lanes select one blocking
`os-wide` scope before fixed-point generation. Release continues to compose
source-fast and generated, so owner completeness remains pre-merge proof
rather than a scheduled substitute.

## Options Considered

- Keep every full sweep: simplest execution model, but makes landing cost
  proportional to consumer count instead of source change.
- Use a shared mutable or cross-run cache: potentially faster, but introduces a
  trust and invalidation surface that this change cannot prove.
- Skip repeated generated or validator consumers: cheaper, but weakens
  fixed-point and parity evidence.
- Reuse one verified packet inside a bounded run: preserves every consumer and
  owner invariant while removing redundant sibling reads.
- Keep the combined validator after packet reuse: preserves proof strength but
  leaves local and federation-completeness claims operationally inseparable.
- Add explicit scopes while keeping a full compatibility default: makes lane
  intent inspectable without weakening existing callers.

## Rationale

KAG is a derived substrate, so the reusable object must be a fully identified
derivative of owner-controlled inputs, never a replacement for them. Limiting
reuse to one temporary run makes the trust boundary small enough to validate
directly and keeps provider repositories, manifests, schemas, and generated
outputs as the stronger surfaces.

This route also preserves the command authority established by
AOA-KAG-D-0005. Lanes and consumers keep their existing blocking roles; only
the execution of an identical expensive sub-proof is shared.

Local validity and federation completeness are distinct claims. Selecting
them explicitly lets command authority preserve both while preventing a local
validator rerun from silently initiating another owner audit. Placing the
OS-wide scope before fixed-point mutation preserves the previous
fail-before-mutation posture.

## Consequences

- A stable release epoch performs one full owner audit; a real generated input
  transition may perform a second, but repeated consumers do not create more.
- Generated fixed-point, full/incremental parity, compatibility assembly,
  budgets, receipts, and blocking verdicts remain unchanged.
- Provider checkouts must match registry pins before packet reuse is available.
- Local mixed-root runs that cannot prove every identity fail instead of
  silently trusting partial state.
- Local and OS-wide validation are explicit scopes; packet availability never
  permits skipping required local checks.
- `source-fast` alone proves local integrity. The generated/release command
  authority owns the blocking OS-wide audit, and scheduled audits cannot
  replace it for required pre-merge changes.
- The no-argument validator remains full for compatibility.
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
- `scripts/validate_kag.py`
- `scripts/validators/repo_local_kag_index.py`
- `scripts/validators/orchestration/runner.py`
- `scripts/ci_gate.py`
- `scripts/release_check.py`
- `tests/test_validate_kag.py`
- `tests/test_repo_local_kag_index.py`
- `tests/test_validation_command_authority.py`
- `tests/test_validator_module_topology.py`

## Validation

Regenerate and validate decision indexes. Run focused packet lifecycle,
identity, tamper, validator-scope, command-authority, and script-topology
tests; the complete pinned test suite; then one release gate on exact provider
pins. A stable release receipt must show one coverage build, while a proved
identity transition may show a second; the generated coverage payload digest
must match the committed output.
