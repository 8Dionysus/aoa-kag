# AOA-KAG-D-0044 Detached Transition Authority

## Index Metadata

- Decision ID: AOA-KAG-D-0044
- Original date: 2026-08-22
- Surface classes: schema contract, owner procedure, transition admission
- KAG surfaces: producer lineage, complete tiered projection, generator validation
- Source lanes: aoa-kag
- Guard families: source-owned authority, exact identity, fail-closed admission
- Posture: proposed

## Context

The v3 to v4 KAG family transition currently carries stable producer content
identity and generated migration provenance, but neither is an independently
issuable transition authority. The ordinary D-0043 causal witness is also not
an exact proof that a mixed whole projection was regenerated completely. A
consumer must therefore remain fail-closed even when the generated family is
internally consistent.

The pressure is generic: a producer-lineage change needs an immutable base and
target binding, while a broad projection change needs an exact complete-output
fixed point. These are related owner transitions, but they are not the same
receipt, evidence packet, consumer admission, or human acceptance claim.

## Decision

Add two separate, owner-native typed transition contracts. The detached
producer-lineage migration binds the immutable predecessor family, target
v4 family, target producer identity, one-time nonce and sequence, replay-ledger
snapshot, detached issuer artifact, and independent acceptance record. The
complete-projection transition binds the same authority boundary plus an exact
before/after placement contract and a complete output identity covering corpus,
distribution, hot profile, locators, pack index, owner release, placement
object sets, and a fixed-point digest.

The generator may validate supplied transition artifacts through an explicit
read-only lane, but it never creates authority, advances replay state, writes a
transition receipt, or turns the proposal into acceptance. The ordinary D-0043
receipt/evidence ABI and its 131072-byte unrelated-generated ceiling remain
unchanged. Current migration provenance remains descriptive derived metadata,
not transition authority.

## Options Considered

- Treat the v4 producer identity or corpus migration field as positive
  bootstrap authority: rejected because content identity has no issuer,
  predecessor, nonce, replay, or independent acceptance binding.
- Extend the ordinary causal budget receipt to cover the mixed projection:
  rejected because a receipt measures a budget event and cannot prove complete
  partition/output coverage without changing its ABI and ownership boundary.
- Partition the projection into causal phases: deferred because the observed
  mixed projection does not provide a demonstrated complete phase partition;
  an incomplete phase claim would remain fail-closed.
- Use detached producer authority plus a separately typed complete projection:
  chosen because each authority claim is exact, independently reviewable, and
  can fail closed without widening budget or consumer contracts.

## Rationale

`aoa-kag` owns the derived family structure and its provenance-aware validator
boundary. A transition validator can recompute exact target and projection
identities from owner-built surfaces, while a detached artifact and independent
acceptance record prevent a candidate from authorizing itself. The replay
snapshot makes reuse visible without mutating the ledger. Separating the
transition lane from ordinary budget admission preserves D-0042/D-0043
semantics and keeps source meaning, receipt measurement, consumer admission,
runtime health, proof, and human acceptance distinct.

## Consequences

- Missing, proposed, stale, copied, candidate-authored, replayed, incomplete,
  or wrong-family transition artifacts resolve to `migration_required`,
  `unknown`, or `unsupported`; none becomes positive admission by shape alone.
- A future independently accepted decision and externally issued authority
  artifact are required before a real v3 to v4 transition can be admitted.
- Existing corpus migration metadata and ordinary budget receipts remain
  useful descriptive/mechanical surfaces but cannot substitute for this lane.
- This decision does not claim publication, consumer admission, runtime health,
  proof, landing, or human acceptance.

## Source Surfaces

- `scripts/repo_local/portable_family.py`
- `scripts/repo_local/tiered_family.py`
- `scripts/generate_repo_local_kag_index.py`
- `schemas/repo-local-kag-producer-migration.schema.json`
- `schemas/repo-local-kag-projection-transition.schema.json`
- `tests/test_repo_local_kag_repository_indexes.py`
- `tests/test_repo_local_kag_tiered_family.py`
- `docs/decisions/AOA-KAG-D-0042-semantic-owner-evidence-for-budget-admission.md`
- `docs/decisions/AOA-KAG-D-0043-causal-budget-witness-and-owner-schema-admission.md`

## Validation

The owner tests cover schema shape, exact predecessor/target binding, wrong
owner and base, replay nonce/sequence reuse, candidate self-issuance, legacy
fallback, incomplete projection, wrong placement, residue, fixed-point drift,
and separation from the ordinary D-0043 receipt ABI. The decision index is
regenerated by its owner builder. The decision remains proposed until an
independent authority holder accepts it.
