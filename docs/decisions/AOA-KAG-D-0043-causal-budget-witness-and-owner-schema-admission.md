# AOA-KAG-D-0043 Causal Budget Witness And Owner Schema Admission

## Index Metadata

- Decision ID: AOA-KAG-D-0043
- Original date: 2026-08-22
- Surface classes: schema evolution, generated-delta validator, owner procedure
- KAG surfaces: portable family, budget receipt, semantic admission evidence,
  tiered distribution
- Source lanes: aoa-kag, downstream owner-family consumers
- Guard families: source-owned authority, exact identity, fail-closed admission,
  paired artifact lifecycle
- Posture: accepted

## Context

The D-0042 evidence packet bound a typed cause to a generated-family budget,
but the current-head review exposed six generic admission gaps: aggregate
source bytes could stand in for causality, topology transitions had no typed
witness, procedure and review identities could resolve from a target checkout,
published schemas were not enforced at admission, and pruning could orphan
the evidence paired with the current receipt.

## Decision

Evolve the evidence packet and procedure contract to v2/v3. A supported cause
must carry a digest-bound witness containing the localized source and procedure
delta measurements, generated-path identity, source snapshot relation, and an
exact owner topology transition when the cause is delivery or distribution
pressure. Source and procedure witnesses use conservative localized-delta and
generated amplification bounds; deletions, insufficient deltas, unrelated
procedure changes, and ambiguous transitions remain `unknown`. Exact
source-free delivery transitions are admitted only from the owner-authored
topology projection. The executing `aoa-kag` module checkout owns procedure,
review, and published-schema resolution; a supplied target repository cannot
shadow those bindings. Current receipt and evidence files are one lifecycle
pair during pruning.

Older evidence remains `migration_required` before v2 schema validation. The
receipt remains a separate digest-bound measurement envelope and both receipt
and evidence must validate against the published owner schemas with closed
additional properties.

## Options Considered

- Keep aggregate byte and file totals as the cause proof: rejected because a
  tiny edit, deletion, or builder amplification can self-authorize a large
  generated delta.
- Accept cause labels or repository/path allowlists as semantic proof:
  rejected because names and arbitrary path selection do not prove a causal
  transition.
- Reject all topology-only growth: rejected because exact owner-authored
  delivery and distribution transitions are legitimate bounded causes.
- Version the packet while silently rejecting old fields: rejected because
  compatibility must preserve an explicit `migration_required` state.

## Consequences

- New evidence is v2 and the owner procedure identity is v3; old evidence is
  not semantic approval.
- `supported` requires a recomputable witness, exact owner provenance, and
  schema-valid paired artifacts. Insufficient or mixed evidence stays
  `unknown` or `unsupported` according to the existing state contract.
- This repair changes only the aoa-kag owner procedure, schemas, projections,
  lifecycle helper, tests, examples, and decision indexes. It does not admit
  downstream consumers, runtime health, publication, proof, human acceptance,
  or the wider validation Goal.

## Source Surfaces

- `scripts/repo_local/portable_family.py`
- `scripts/repo_local/tiered_family.py`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/prepare_landing.py`
- `schemas/repo-local-kag-budget-evidence.schema.json`
- `examples/repo_local_kag_budget_evidence.example.json`
- `tests/test_repo_local_kag_repository_indexes.py`
- `tests/test_repo_local_kag_tiered_rollout.py`
- `tests/test_prepare_landing.py`
- `docs/decisions/AOA-KAG-D-0043-causal-budget-witness-and-owner-schema-admission.md`

## Validation

The focused owner tests cover localized source/procedure evidence, generated
amplification, source-free artifact delivery, legacy migration, published
schema rejection, executing-checkout provenance, and paired receipt pruning.
Run the repository source-fast, generated fixed-point, decision-record, and
owner-family checks before landing. Downstream canaries remain read-only.
