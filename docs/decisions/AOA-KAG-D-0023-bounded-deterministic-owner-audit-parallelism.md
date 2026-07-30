# Bounded Deterministic Owner-Audit Parallelism

## Index Metadata

- Decision ID: AOA-KAG-D-0023
- Original date: 2026-07-29
- Surface classes: validation execution, OS-wide provider audit, command authority, run receipt
- KAG surfaces: provider coverage, portable family, generated fixed point
- Source lanes: aoa-kag, provider registry
- Guard families: deterministic parity, owner completeness, fail closed, bounded resources
- Posture: accepted

## Context

AOA-KAG-D-0021 made one complete owner audit reusable inside a validation run,
and AOA-KAG-D-0022 stopped requiring that audit for explicitly safe
owner-local pull requests. High-impact changes still need the complete
23-owner proof.

On the stabilized input preceding this decision, the owner build consumed
440,121 ms of a 909,715 ms release lane. The owners are independent inputs to
one aggregate coverage payload, but the builder scanned them serially. The
remaining cost therefore scaled with the sum of owner scan times even after
duplicate builds had been removed.

## Decision

The OS-wide coverage builder may execute independent owner audits through a
bounded thread pool. `config/validation_lanes.json` owns the execution policy:
two owner workers by default, a hard maximum of four, the
`AOA_KAG_COVERAGE_WORKERS` comparison override, and provider-registry output
ordering.

Concurrency changes scheduling only. Each worker receives one configured
owner root and produces the same owner row as the sequential path. The
aggregate always assembles rows and receipts in provider-registry order,
regardless of completion order. Every scheduled owner returns a typed
`completed` or `failed` execution receipt. Any failure rejects the aggregate
and no coverage packet is written.

The run-scoped input identity, immutable-input recheck, packet integrity,
coverage schema, provider completeness, generated fixed point, portable-family
validation, and budget checks remain unchanged. Setting the override to `1`
selects the sequential comparator on the same code and inputs; values outside
the configured bound fail before packet reuse or owner execution.

## Options Considered

- Keep all owner scans sequential: preserves behavior but leaves the largest
  remaining measured build cost untouched.
- Use one process per owner: isolates failures, but duplicates the large parsed
  Python and family state and raises host memory pressure.
- Default immediately to four workers: offers a lower ideal schedule, but
  increases filesystem, subprocess, and memory contention before measured
  host evidence exists.
- Use a bounded two-worker thread pool with a four-worker ceiling and a
  sequential comparison switch: overlaps independent I/O-heavy owner audits
  while keeping resource growth and rollback explicit.

## Rationale

The useful parallel boundary is the owner row, not validators or proof
families inside an owner. It is already defined by the provider registry and
does not change source authority, payload meaning, or proof composition.
Threads share the loaded schemas and builder state instead of multiplying
them across processes.

Deterministic registry-order assembly makes completion timing irrelevant to
the committed payload. Per-owner execution receipts expose failures and actual
work without promoting timing data to KAG truth. The worker bound stays in
command authority so CI, local validation, and controlled A/B runs share one
reviewable policy.

## Consequences

- A full audit can overlap two independent owner scans by default while still
  proving every configured owner.
- The committed coverage payload must be byte-identical between worker counts
  on the same immutable input epoch.
- Receipt duration fields remain operational evidence and may vary; owner
  membership, order, status, and payload identity may not.
- A worker exception fails the complete build after all scheduled owner
  receipts are collected; a partial payload is never admitted or cached.
- The maximum of four is a safety ceiling, not evidence that four workers are
  beneficial. Changing the default or ceiling requires new host and
  equivalence evidence.
- This decision does not introduce cross-run caching, weaken full-audit impact
  rules, or permit a skipped owner.

## Source Surfaces

- `config/validation_lanes.json`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `docs/validation/VALIDATOR_TOPOLOGY.md`
- `scripts/coverage_run.py`
- `scripts/generate_repo_local_kag_coverage.py`
- `scripts/validation_lanes.py`
- `tests/test_repo_local_kag_index.py`
- `tests/test_validation_command_authority.py`

## Validation

Regenerate and validate decision indexes. Exercise configuration bounds,
forced out-of-order completion, sequential versus parallel byte parity,
registry-order output and receipts, and aggregate failure with one broken
owner. Run source-fast, owner-family full/incremental parity, and a full pinned
provider release proof.

For operational admission, compare at least three sequential and three
two-worker full release runs on the same commit, provider pins, history
boundary, and generated fixed point. Require identical pass/fail verdicts,
coverage payload digests, owner counts, family identities, compatibility
assembly, and budget receipts before treating timing improvement as valid.
