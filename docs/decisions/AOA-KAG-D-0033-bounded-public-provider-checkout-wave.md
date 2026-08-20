# Bounded Public Provider Checkout Wave

## Index Metadata

- Decision ID: AOA-KAG-D-0033
- Original date: 2026-08-02
- Surface classes: GitHub landing, validation guard, dependency checkout, CI performance
- KAG surfaces: provider registry, OS-wide release audit, evidence DAG
- Source lanes: aoa-kag, provider registry
- Guard families: exact provider pin, complete history, bounded concurrency, private checkout isolation, fail-closed rollback
- Posture: accepted

## Context

The full OS-wide release job materialized twenty pinned provider repositories
through separate sequential checkout actions before beginning the unchanged
release proof. After repeated validation work was accelerated under
AOA-KAG-D-0032, this serial checkout fan-in became a material part of the
critical path. The pressure was to schedule independent acquisition nodes more
efficiently without reducing provider coverage, history, pin identity, or any
downstream proof.

An all-provider hosted experiment compared sequential full-history checkout,
`blob:limit=1m`, and a bounded three-worker full-history checkout wave. Three
paired attempts on one exact commit measured full-job wall times of 324, 317,
and 280 seconds for the sequential control versus 255, 264, and 264 seconds for
the bounded wave. The bounded wave won all three attempts; medians changed from
317 to 264 seconds, a 53-second or 16.7-percent reduction. Every bounded-wave
attempt retained all providers, exact pins, complete history, generated
cleanliness, and the complete release proof.

The partial-clone candidate reduced Git object storage by about one third but
failed all three complete proofs because repository-local coverage changed at
`coverage_summary.migration_needed`. It is therefore semantic evidence against
that checkout mode, not an optimization to admit.

## Decision

Materialize public full-audit provider checkouts from the canonical provider
registry in a bounded wave of three workers. Each checkout must retain complete
Git history, detach at the exact registry pin, verify the observed HEAD, stay
under repo-local `.deps`, and fail the job on any checkout error. Keep the
private `aoa-session-memory` checkout on its explicit pinned SSH-key action with
credentials cleared, outside the public worker pool.

This is a dependency-acquisition DAG only. The OS-wide release proof remains
the same serial, blocking owner order and keeps every existing validator,
coverage row, generated fixed point, artifact check, and required summary.
`AOA_KAG_CHECKOUT_WORKERS=1` is the operational rollback to sequential
registry-driven acquisition; removing the bounded step and restoring the
explicit actions is the source rollback.

## Options Considered

- Keep twenty sequential checkout actions: equivalent but leaves independent
  network waits on the critical path.
- Use a bounded three-worker full-history public wave and isolate the private
  provider: selected after three hosted wins and full proof equivalence.
- Increase generic validation workers: rejected by prior hosted evidence; two
  validation workers regressed the proof by 44 seconds.
- Use partial or sparse clones: rejected for this lane because the tested
  partial clone changed a blocking owner-family result.
- Parallelize owner validation or SCC stages: not authorized by this decision;
  their typed dependencies and convergence behavior require separate proof.

## Rationale

Public provider downloads are independent prerequisites with identities already
owned by `manifests/provider_registry.json`. Scheduling those independent nodes
concurrently changes waiting topology, not KAG meaning. The worker cap avoids
unbounded hosted contention, while exact post-checkout identity and complete
history keep the downstream proof input equal to the sequential route.

Separating the secret-owned checkout prevents the public helper from inheriting
private credentials or widening their lifetime. Keeping proof execution serial
also prevents checkout evidence from being misread as permission to reorder
history-sensitive or convergence-sensitive validation nodes.

## Consequences

- High-impact PR and post-merge release audits begin the complete proof sooner
  while retaining every configured provider and blocking stage.
- Public checkout coordinates have one manifest-owned source instead of
  duplicated workflow pins; the private provider keeps its explicit action and
  secret boundary.
- Invalid worker counts, checkout failures, shallow histories, or pin mismatch
  fail closed before release validation.
- A registry pin change automatically reaches the public checkout wave and
  remains guarded by registry, workflow, checkout-tool, and provider-family
  tests.
- This decision does not authorize partial clones, persistent caches,
  cross-run proof reuse, unbounded concurrency, or parallel owner validation.

## Source Surfaces

- `manifests/provider_registry.json`
- `scripts/sync_provider_checkouts.py`
- `scripts/validators/provider_registry.py`
- `.github/workflows/repo-validation.yml`
- `tests/test_sync_provider_checkouts.py`
- `tests/test_repo_validation_workflow.py`
- `docs/validation/CI_EVIDENCE_DAG.md`
- `docs/decisions/AOA-KAG-D-0027-history-bounded-source-fast-donor-checkouts.md`
- `docs/decisions/AOA-KAG-D-0032-fail-closed-accelerated-schema-validation.md`

## Validation

Regenerate and validate decision indexes. Run focused checkout, provider
registry, and workflow tests; the complete test suite; source-fast; and the full
release continuation with all exact provider worktrees. Hosted acceptance
requires at least two of three paired wins with median full-job saving of at
least 60 seconds or 15 percent and no proof or checkout-identity mismatch.
After implementation, require three clean PR attempts on one exact head and one
clean post-merge `main` workflow before claiming the landed benefit.
