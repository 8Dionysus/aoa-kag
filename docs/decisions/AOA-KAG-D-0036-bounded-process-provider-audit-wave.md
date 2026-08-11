# Bounded Process Provider Audit Wave

## Index Metadata

- Decision ID: AOA-KAG-D-0036
- Original date: 2026-08-10
- Surface classes: validation guard, CI performance, process scheduling, evidence DAG
- KAG surfaces: provider-home audit, repo-local coverage, OS-wide release audit, landing preparation
- Source lanes: aoa-kag, provider repositories
- Guard families: exact input epoch, complete owner order, bounded process workers, canonical fan-in, final epoch recheck, sequential rollback
- Posture: accepted

## Context

The complete OS-wide route still spent most of its wall time validating all
provider homes in serial. `AOA-KAG-D-0028` fused one owner's coverage-row build
into its just-validated portable family, but deliberately kept one decoded
owner alive at a time. `AOA-KAG-D-0033` also retained serial semantic proof
because an earlier whole-sweep two-worker experiment improved locally by only
7.86 percent and regressed hosted wall from 938.768 to 990.153 seconds.

That negative result remained evidence against the old scheduler, not against
every owner DAG. Since then, schema evaluation, family reconstruction, and
same-run fusion changed the cost contour. A distinct candidate isolated each
complete owner validation and its fused coverage-row build in one child
process, retained only compact rows in the parent, and performed canonical
fan-in plus the existing final input-epoch barrier after every child returned.

On the full local generated lane at one exact 21-owner epoch, one, two, and
three workers completed in 290.486, 151.282, and 97.712 seconds. All variants
produced the same payload, one build, three packet hits, and zero reject or
failure. An external sampler measured about 0.50 GiB for serial and 1.22 GiB
for three workers; the receipt's per-process RSS maximum is not an aggregate
pool-footprint measurement.

Three interleaved exact-head hosted pairs then ran at `3f8bf2b5`. Serial runs
`31447089078`, `31448072689`, and `31448434708` recorded release-lane walls of
129.754/122.842/116.760 seconds, OS-wide validator walls of
95.655/89.302/83.858 seconds, and full release jobs of 193/192/186 seconds.
Three-worker runs `31447497722`, `31447794988`, and `31448779280` recorded
72.854/76.358/60.060 seconds, 43.920/43.858/35.035 seconds, and 141/138/126
seconds respectively. The process candidate won 3/3. Medians fell from
122.842 to 72.854 seconds for the release lane, 89.302 to 43.858 seconds for
the OS-wide validator, and 192 to 138 seconds for the full release job: a
54-second or 28.1-percent practical CI reduction.

All six hosted runs used the same normalized input identity, exact provider
pins, 21/21 owners, and payload
`sha256:c38bdf0eb13fa1b507228c8c0bec2c0134f08c6d7790f585de31adb951feb16c`.
Every run built one coverage packet, reused it three times, and reported zero
packet reject, build failure, or family-validation miss. Run-scoped identity
digests remained distinct by design and were not treated as cross-run proof.

## Decision

Run the complete provider-home validation plus fused coverage-row construction
as a bounded process wave of three workers on hosts that support `fork`. Make
three the ordinary local and GitHub release-audit default. Keep one as the
exact serial rollback and two as an explicit lower-footprint setting. When no
worker value is configured and `fork` is unavailable, select the serial route;
an explicitly requested unsupported process route still fails closed.

Each child must receive one canonical owner, its resolved root, and the active
OS root; execute the unchanged complete provider-home validator; construct the
coverage row only from that validated portable bundle; and return typed
timings plus exact owner, root, and family identity. The parent must reject an
incomplete, malformed, failed, reordered, wrong-owner, wrong-root, or
wrong-family result, re-emit evidence in registry order, assemble the existing
canonical payload, and retain the final complete input-epoch recheck.

This is an independent-owner DAG outside the root fixed-point SCC. It does not
authorize a pure DAG inside the coverage/generated/root-family cycle, omit a
validator, reuse a verdict across runs, or turn generated evidence into owner
truth.

## Options Considered

- Keep one serial owner at a time: proof-equivalent and retained as the exact
  rollback, but leaves about fifty median seconds on the hosted critical path.
- Restore the earlier generic whole-sweep worker scheduler: rejected by its
  hosted regression; its result is not overwritten by this decision.
- Use two isolated processes: locally reduced the complete lane by 47.9
  percent and remains available for constrained hosts, but three workers were
  materially faster in the full-lane comparison.
- Use three isolated processes with canonical parent fan-in: selected after
  local 1/2/3 comparison and three exact-head hosted wins.
- Persist owner fragments across runs: remains prohibited by
  `AOA-KAG-D-0029` until artifact admission exists.
- Flatten the root SCC into a pure DAG: rejected because it would remove a
  real dependency or the final fixed-point proof owned by `AOA-KAG-D-0034`.

## Rationale

Provider homes are independent read-only consumers of one captured registry
epoch. Process isolation is the material difference from the rejected generic
worker attempt: every child owns its validator state and completes same-run
fusion before returning a compact row, while the parent retains deterministic
ordering and final identity authority. No child result becomes acceptable
until every configured owner has returned and the complete epoch still
matches.

The three-worker route increases simultaneous memory and can consume more CPU
than serial execution, but it shortens billed and human waiting time on the
fixed-size CI runner and on eligible landing hosts. The tradeoff is explicit:
concurrency is capped at three, two and one remain operator-selectable, no
aggregate-memory reduction is claimed, and a non-fork default falls back to
the unchanged serial proof.

## Consequences

- Full OS-wide CI and local landing validation can complete the same blocking
  owner proof materially sooner.
- Every configured provider, schema check, semantic assertion, canonical row,
  packet consumer, generated fixed point, and final cleanliness check remains
  blocking.
- Eligible hosts normally spend roughly 0.7 GiB more sampled peak memory than
  serial in exchange for the measured wall reduction; memory-constrained
  operators may set `AOA_KAG_PROVIDER_AUDIT_WORKERS=2` or `1`.
- `AOA_KAG_PROVIDER_AUDIT_WORKERS=1` is the immediate runtime rollback. Source
  rollback removes the process branch and restores the serial default.
- The earlier negative generic-worker evidence remains valid for that exact
  method. Future scheduling changes still require method-specific full-path
  comparison rather than inference from this acceptance.
- Landed benefit may be claimed only after the final default-setting head and
  the postmerge `main` workflow both complete the full proof.

## Source Surfaces

- `scripts/validators/local_kag_subtree.py`
- `scripts/generate_repo_local_kag_coverage.py`
- `scripts/coverage_run.py`
- `.github/workflows/repo-validation.yml`
- `manifests/provider_registry.json`
- `tests/test_validate_kag.py`
- `tests/test_repo_local_kag_index.py`
- `tests/test_repo_validation_workflow.py`
- `docs/validation/CI_EVIDENCE_DAG.md`
- `docs/decisions/AOA-KAG-D-0028-run-scoped-provider-coverage-fusion.md`
- `docs/decisions/AOA-KAG-D-0029-defer-cross-run-owner-proof-fragments.md`
- `docs/decisions/AOA-KAG-D-0033-bounded-public-provider-checkout-wave.md`
- `docs/decisions/AOA-KAG-D-0034-bounded-repository-family-reconstruction.md`

## Validation

Regenerate and validate decision indexes and the repository-local KAG family.
Run focused process-worker, coverage-fusion, workflow, and decision tests; the
complete test corpus; source-fast; local staged landing preparation; and the
full 21-owner release continuation. Before merge, require one clean hosted
run on the final default-setting head and one explicit serial rollback run.
After merge, require one clean `main` workflow before claiming landed benefit.
