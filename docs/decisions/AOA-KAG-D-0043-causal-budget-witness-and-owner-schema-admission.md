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
but complete-family admission pressure exposed several generic gaps: aggregate
source bytes could stand in for causality, topology transitions had no typed
witness, duplicate materialization could be hidden by an unchanged head
shard, first-family migration was rejected before typed causal evidence was
considered, procedure and review identities could resolve from a target
checkout, published-schema failures were not a typed regeneration signal,
pruning could orphan the evidence paired with the current receipt, and a
source edit could authorize unrelated generated churn. Exact-head review also
exposed that a shallow packet could self-report its causal flags, that a
downstream owner could compare against the current KAG procedure instead of
the procedure that produced its base family, and that sub-1 KiB shards could
escape duplicate admission.

## Decision

Evolve the evidence packet and procedure contract to v2/v3. A supported cause
must carry a digest-bound witness containing the localized source and procedure
delta measurements, generated-path identity, source snapshot relation, and an
exact owner topology transition when the cause is delivery or distribution
pressure. Duplicate admission scans the complete materialized head family but
only rejects groups containing a changed generated path, so pre-existing
unchanged duplicates do not self-authorize or self-invalidate a candidate.
First-family creation uses the explicit `first_family_migration` transition and
admits only a bounded, localized owner procedure witness; absent, partial, or
ambiguous legacy evidence remains migration-required or unknown. Source and
procedure witnesses use conservative localized-delta and generated
amplification bounds; source causes additionally require a bounded generated
dependency scan whose typed source IDs or paths explain the changed family
rows, with only a shard-sized unrelated-byte tolerance. Deletions,
insufficient deltas, unrelated procedure changes, and ambiguous transitions
remain unknown. Partitioning transitions take precedence over hot-profile
churn when both identities move. Exact source-free delivery transitions are
admitted only from the owner-authored topology projection. The executing
`aoa-kag` module checkout owns procedure, review, and published-schema
resolution; a supplied target repository cannot shadow those bindings. The
repo-local action installs its schema dependencies before the drift sentinel
imports the owner procedure. When a base object is unavailable in a shallow
checkout, an over-budget admission fails closed: a current-head
receipt/evidence packet is not a causal witness, and this contract has no
independently authenticated full-history verdict. Downstream procedure deltas
instead compare the executing procedure identity with the prior base head's
digest-bound typed evidence; an absent or legacy prior identity leaves the
cause unknown. The producer identity records immutable file sizes, and
duplicate admission includes every nonempty shard. Current receipt and
evidence files are one lifecycle pair during pruning.

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
  not semantic approval. Its topology witness includes the immutable procedure
  baseline used for the delta.
- Receipt or evidence validation failures carry one exact typed marker so the
  preparation lanes regenerate only a known stale/missing pair; unrelated
  validator failures remain code failures.
- `supported` requires a recomputable witness, exact owner provenance, and
  schema-valid paired artifacts. Insufficient or mixed evidence stays
  `unknown` or `unsupported` according to the existing state contract.
- Shallow over-budget validation is typed
  `budget_receipt_validation_failure` until immutable base history is present;
  it never trusts mutable packet measurements as a substitute for the causal
  base.
- Downstream builder migration can be admitted only when the base family has a
  schema-valid paired receipt/evidence packet with a size-bearing producer
  identity; otherwise a positive procedure delta is unavailable.
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
