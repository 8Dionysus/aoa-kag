# Guarded Generated-Continuation Prefix Handoff

## Index Metadata

- Decision ID: AOA-KAG-D-0030
- Original date: 2026-08-01
- Surface classes: validation guard, CI performance, command authority, same-run proof handoff
- KAG surfaces: source-fast, generated fixed point, release continuation
- Source lanes: aoa-kag, GitHub landing
- Guard families: exact receipt identity, declared omitted prefix, final local validation, full-release fallback
- Posture: accepted

## Context

AOA-KAG-D-0025 removed the repeated complete source-fast lane from the second
high-impact CI job through an exact same-run receipt. The retained generated
lane nevertheless began with the same `validate_kag --scope local` command
that source-fast had already completed on the exact repository, command
authority, validator inputs, donor pins, owner family, workflow run, and
attempt identified by that receipt.

The generated sequence also ends with a second local validation after two
generation passes and the final coverage, portable-family, and generated
checks. That concluding command is not duplicate proof: it validates the
post-generation fixed point and must remain blocking.

On the accepted D-0029 hosted control run, the leading repeated local command
occupied 21.566 seconds and the required concluding local command occupied
20.866 seconds. Two isolated local measurements of the same leading command
were 15.02 and 15.99 seconds. The complete generated continuation was 517.640
seconds, so the opportunity is bounded to roughly twenty seconds and does not
justify weakening fixed-point or provider coverage.

## Decision

Keep the standalone `generated` and `release` sequences unchanged. They still
run the leading local validator, one OS-wide provider/coverage audit, two
generation passes, all final checks, and the concluding local validator.

For the CI-only `release_continuation`, declare one exact omitted prefix in
`config/validation_lanes.json`: the single leading local-scope KAG validator
command. The lane loader must
reject command authority unless that prefix is byte-for-byte the beginning of
the generated sequence, is present in source-fast, and leaves exactly one
final local validator in the continuation.

The continuation invokes a guarded `ci_gate` mode. That child recomputes and
accepts the same encoded source-fast receipt again before running the derived
generated-continuation sequence. Direct use without an exact receipt, or a
receipt that becomes invalid between the release selector and child process,
fails closed. The outer selector retains its existing behavior: any initially
missing, malformed, stale, tampered, ambiguous, cross-run, cross-attempt,
wrong-job, dirty, pin-mismatched, family-mismatched, or otherwise non-identical
receipt selects the complete `release` lane.

No generated command after the declared prefix is omitted. In particular,
the OS-wide 23-owner provider/coverage proof, both generator passes, final
coverage/index/generated `--check` commands, concluding local validation,
machine-registry bundle validation, and workflow cleanliness check remain
blocking.

## Options Considered

- Keep both local commands in the continuation: simple and safe, but repeats
  an exact same-run proof for every full pull-request and main audit.
- Remove both local commands: rejected because the concluding command proves
  the post-generation fixed point rather than the pre-generation source state.
- Add an unguarded fast CLI flag: rejected because a standalone caller could
  skip proof without receipt admission.
- Let the outer selector alone authorize the omission: rejected because the
  child boundary should fail closed if its environment changes after lane
  selection.
- Declare and guard exactly one derived prefix: selected as the smallest
  proof-preserving continuation.

## Rationale

The receipt already binds the complete source-fast command authority and all
inputs used by its local validator, and the independent full-audit checkout
recomputes that receipt exactly. Reusing this proof inside the same workflow
run removes computation, not validation authority. The manifest-owned prefix,
loader invariants, and second child verification prevent the optimization from
becoming a general skip switch.

Keeping the final local validator and every fixed-point command preserves the
stronger claim made after generated outputs have been reconstructed and
checked. Keeping standalone lanes unchanged preserves local, manual, release,
and invalid-receipt behavior.

## Consequences

- Exact accepted high-impact CI runs avoid one repeated local KAG validation.
- Standalone generated and release callers pay the complete original cost.
- Invalid source-fast handoffs still run the full release path; a late child
  mismatch fails closed rather than silently widening the omission.
- The optimization has no cross-run authority, cache, artifact, registry,
  permission, or owner-truth effect.
- Hosted landing still requires proof that the guarded mode runs the complete
  derived suffix, preserves the final local validator and 23-owner receipt,
  and produces a material non-regressing result.

## Source Surfaces

- `config/validation_lanes.json`
- `scripts/validation_lanes.py`
- `scripts/source_fast_handoff.py`
- `scripts/ci_gate.py`
- `scripts/ci_release_check.py`
- `scripts/release_check.py`
- `docs/decisions/AOA-KAG-D-0025-exact-same-run-source-fast-handoff.md`
- `tests/test_source_fast_handoff.py`
- `tests/test_validation_command_authority.py`

## Validation

Validate exact derived-sequence equality, final-local preservation, guarded
receipt acceptance/rejection, outer full-release fallback, command authority,
workflow topology, decision records and indexes, source-fast, complete
generated fixed point, and standalone release behavior. Hosted proof must show
the exact handoff accepted twice, no leading local invocation before OS-wide,
one concluding local invocation after final checks, complete 23-owner receipt,
zero proof rejects/failures, required summary success, and a non-regressing
wall/CPU/RSS result against the current cold control.
