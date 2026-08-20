# Run-Scoped Provider Coverage Fusion

## Index Metadata

- Decision ID: AOA-KAG-D-0028
- Original date: 2026-08-01
- Surface classes: validation guard, coverage builder, CI performance, run-scoped telemetry
- KAG surfaces: provider-home audit, repo-local coverage, portable family
- Source lanes: aoa-kag, provider registry
- Guard families: exact input identity, complete owner order, portable-family digest, final epoch recheck
- Posture: accepted

## Context

The full OS-wide lane validates every portable provider family and then builds
the canonical coverage row for every provider in the same Python process.
Earlier run-scoped reuse suppressed a duplicate schema and semantic traversal,
but coverage still decoded the same portable shards again. Hosted release
receipts showed provider-home validation and coverage reconstruction as the two
dominant serial phases.

Retaining all decoded families or persisting them across runs would widen the
memory and trust boundaries. Replacing either proof would weaken the lane.
The useful overlap is narrower: immediately after one provider-home validation,
the exact decoded family is still available and the owner has not yet left its
run-scoped audit epoch.

## Decision

Fuse one owner's coverage-row construction into the successful end of that
owner's provider-home validation. Reuse only the just-validated decoded family,
bound to the active run scope, resolved owner root, and exact portable-family
digest. Retain the compact coverage row and timing, then release the decoded
family before the next owner.

Capture the complete provider input identity before the sweep. The coverage
consumer accepts the fused result only when all configured owners appear once,
assembles them in canonical registry order regardless of readiness-validation
order, and observes a complete identity after the sweep that exactly matches
the initial identity. Only then may it schema-check and write the existing
ephemeral coverage packet. Missing, duplicate, unexpected-member,
wrong-root, wrong-digest, cross-run, changed-input, failed provider validation,
or non-canonical assembled output remains a blocking failure and writes no
accepted packet.

## Options Considered

- Keep the separate decode in coverage: strongest simplicity, but repeats
  proven work for every owner in the dominant lane.
- Increase the portable-family LRU to all owners: rejected because it retains
  the largest decoded state and obscures its lifetime.
- Persist decoded families or coverage rows across runs: rejected here because
  provenance, admission, invalidation, and artifact trust are a separate
  decision.
- Fuse one row at a time inside the same run: selected because it preserves
  both proofs and bounds decoded state to the current sequential owner.

## Rationale

The optimization changes execution placement, not proof obligations. The
provider-home validator still performs the complete portable-family validation.
Coverage still reconstructs and compares the repository family, scans one
immutable owner source snapshot, produces the same canonical payload, validates
the schema, and checks the full input epoch again. Passing the exact decoded
objects removes serialization and shard decoding only; it does not convert an
in-process object into owner truth or reusable evidence.

An explicit scope and final identity barrier make the lifetime auditable. The
standalone coverage builder keeps its cold path, so no caller silently acquires
the fusion without the preceding provider-home proof.

## Consequences

- Full OS-wide validation performs one decoded portable-family load per owner
  instead of reloading it in the following coverage phase.
- Peak retained decoded-family state stays bounded to one sequential owner;
  only compact rows and timings span the sweep.
- The existing packet identity, schema, same-run lifetime, hit behavior, and
  later consumers remain unchanged.
- Telemetry distinguishes `provider-home-fused` from `cold` builds and reports
  the number of fused owners without claiming proof or causality.
- Cross-run owner fragments, persistent caches, and parallel owner scans remain
  separate decisions requiring their own trust and resource evidence.

## Source Surfaces

- `scripts/validators/orchestration/runner.py`
- `scripts/validators/local_kag_subtree.py`
- `scripts/validators/repo_local_kag_index.py`
- `scripts/generate_repo_local_kag_coverage.py`
- `scripts/coverage_run.py`
- `manifests/provider_registry.json`
- `tests/test_repo_local_kag_index.py`
- `tests/test_validate_kag.py`

## Validation

Prove exact cold-versus-fused payload parity, canonical owner membership and
order, wrong-root and family-digest rejection, final-identity mutation
rejection, no packet after provider failure, same-run packet hits, standalone
cold behavior, and bounded transient-family release. Run the complete local
test and generated fixed-point surfaces, then compare one hosted high-impact
workflow against a paired current-main run. Land only if all blocking proofs
remain green, wall time improves materially, and peak RSS does not regress.
