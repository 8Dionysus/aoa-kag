# Exact Same-Run Source-Fast Handoff

## Index Metadata

- Decision ID: AOA-KAG-D-0025
- Original date: 2026-08-01
- Surface classes: validation guard, GitHub landing, command authority, ephemeral proof artifact, CI performance
- KAG surfaces: local integrity, owner portable family, OS-wide provider coverage, generated fixed point
- Source lanes: aoa-kag, provider registry
- Guard families: exact input identity, donor pin parity, owner-family parity, same-run binding, fail-closed fallback
- Posture: accepted

## Context

The required `Source Fast and Owner Family` job completes repository tests,
local validators, and full/incremental owner-family parity before the
conditional full audit starts. The full audit then entered the standalone
release sequence and repeated source-fast on a second runner before beginning
the still-required OS-wide provider audit, generated fixed point, and artifact
bundle validation.

Removing source-fast from release authority would weaken standalone releases.
Trusting only a successful upstream job result would leave the second job
without an exact binding to repository bytes, command authority, donor pins,
owner-family identity, or workflow attempt. A persistent or cross-run cache
would create a broader invalidation and trust boundary than this pressure
requires.

The source job also carried three stale local checkout refs even though the
full audit and provider registry used newer exact pins. A trusted handoff
cannot admit that split baseline.

## Decision

Keep `scripts/release_check.py` and the `release` command sequence complete for
every standalone caller. Add a separate CI-only `release_continuation` command
sequence that contains the generated lane and machine-registry bundle proof,
omitting only the already completed source-fast command.

The source job may issue one `aoa_kag_source_fast_handoff_v1` receipt after
both the owner-family action and source-fast lane succeed. The receipt binds
the exact repository commit, Git index tree and index-entry digest, command
authority and source-fast sequence digests, validator and builder composite
input digests, every source-fast donor name and exact observed registry pin,
owner-family and source-index identities, explicit history boundaries, the
verified results, and GitHub repository, run, attempt, workflow ref, SHA, and
producer job identity.

The full audit recomputes the complete receipt on its independent checkout.
Only byte-for-byte equality after strict field and receipt-digest validation
admits `release_continuation`. A missing, malformed, stale, tampered,
ambiguous, cross-run, cross-attempt, wrong-job, dirty-checkout, pin-mismatched,
or otherwise non-identical receipt falls back to the original full `release`
sequence. Receipt acceptance never omits the generated lane, OS-wide provider
and coverage proof, generated fixed point, machine-registry bundle proof, or
generated-output cleanliness check.

Align the eight source-fast donor checkouts with the exact pins already owned
by `manifests/provider_registry.json`. Pass owner-family history boundaries
explicitly from the event identity instead of relying on ambient default-branch
resolution.

## Options Considered

- Repeat source-fast in both jobs: strongest simple route, but pays twice for
  identical local proof on every high-impact workflow.
- Remove source-fast from release authority: saves time but weakens standalone
  and fallback release validation.
- Trust the upstream job conclusion alone: cheap, but does not identify the
  validated code, commands, donors, family, or workflow attempt.
- Upload a reusable or cross-run cache: could avoid more work, but introduces
  persistence, invalidation, and artifact-admission pressure not justified by
  this bounded duplicate.
- Transfer and fully recompute a same-run typed receipt, with full fallback:
  removes only the proved duplicate while preserving every stronger audit.

## Rationale

This route treats the handoff as proof continuity, not proof reduction. The
receipt has no authority outside one exact workflow run and cannot make a
different tree, command sequence, donor set, family, run, or attempt valid.
The independent recomputation keeps the consumer from trusting opaque job
state, while the fallback preserves the previous release behavior whenever
identity cannot be proved.

Keeping the continuation sequence in command authority avoids duplicating its
meaning in workflow YAML. Keeping the standalone release sequence unchanged
preserves existing local, manual, and external callers. Exact observed donor
HEADs close the pre-existing gap between source-job checkout text and provider
registry authority.

## Consequences

- High-impact CI runs no longer repeat source-fast after the first job has
  produced an exact accepted receipt.
- Standalone `scripts/release_check.py`, invalid-receipt CI, and any caller
  without the same-run receipt still execute the complete original release
  sequence.
- The full audit still materializes and validates every pinned provider, runs
  the generated lane and fixed point, validates the artifact bundle, and
  checks committed generated output cleanliness.
- Handoff changes classify themselves as full-audit changes and require hosted
  proof before landing.
- The receipt is ephemeral execution evidence, not owner truth, a reusable
  cache, a scheduled substitute, or authorization for future proof fragments.
- Further checkout compression, trusted owner fragments, or parallelism remain
  separate decisions requiring their own equivalence and hosted evidence.

## Source Surfaces

- `config/validation_lanes.json`
- `manifests/provider_registry.json`
- `.github/workflows/repo-validation.yml`
- `.github/actions/repo-local-kag-index/action.yml`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `scripts/source_fast_handoff.py`
- `scripts/ci_release_check.py`
- `scripts/validation_lanes.py`
- `scripts/release_check.py`
- `mechanics/release-support/parts/release-lane/CONTRACT.md`
- `tests/test_source_fast_handoff.py`
- `tests/test_repo_validation_workflow.py`
- `tests/test_validation_command_authority.py`

## Validation

Regenerate and validate decision indexes. Run strict receipt shape, digest,
identity mismatch, donor-pin, dirty-checkout, same-run acceptance, and fallback
tests; command-authority, workflow, provider-registry, script-topology, and
test-topology tests; the complete source-fast lane; then one hosted high-impact
workflow. The hosted run must report receipt acceptance, omit only the second
source-fast execution, preserve the required summary and exact proof payloads,
and improve full-audit wall time against the accepted baseline. Also exercise
one invalid receipt and confirm that it executes the complete release sequence.
