# Bounded Repository Family Reconstruction

## Index Metadata

- Decision ID: AOA-KAG-D-0034
- Original date: 2026-08-08
- Surface classes: validation guard, repository family, CI performance, evidence DAG
- KAG surfaces: repository index family, portable family, OS-wide release audit, generated fixed point
- Source lanes: aoa-kag, provider repositories
- Guard families: exact output parity, mutable-reference isolation, owner completeness, atomic SCC, explicit rollback
- Posture: accepted

## Context

After checkout, schema, source-snapshot, and same-run coverage improvements, the
remaining release proof was dominated by repeated repository-family
reconstruction rather than source I/O. Three current cold baselines measured a
95.454-second local `release_continuation` median. cProfile attributed 52.206
seconds to compatibility-family reconstruction and 36.982 seconds to
`copy.deepcopy`, including repeated linear lineage-record scans and copies of
already immutable record structure.

The proof graph also contains a real cycle: root coverage describes the root
family, generated root surfaces enter that family, and the portable root family
feeds coverage. Treating those nodes as an ordinary acyclic pipeline would
remove a dependency or weaken final parity. The cycle therefore needs an
explicit SCC boundary while independent proof nodes remain visible in the
outer DAG.

## Decision

Build one first-wins relation-source lookup for each lineage traversal and use
bounded structural copies when constructing repository and portable families.
Copy the top-level record and isolate the mutable `refs` mapping; in portable
reconstruction, also copy only the mutable nested reference structures. Reuse
immutable parent, source, and event values. Every schema check, semantic
validator, owner proof, digest, canonical fan-in, and final verdict continues
to execute.

Model coverage, generated root projections, and the root portable family as
one atomic SCC in the outer evidence DAG. Inside it, preserve ordered staged
Gauss-Seidel regeneration: stage each owner-source output before the next
generator reads the Git index, then run coverage, portable-family, generated
root, parity, and cleanliness checks as blocking confirmation. This decision
does not authorize a pure DAG inside the SCC or parallel owner validation.

## Options Considered

- Keep repeated lineage scans and whole-record deep copies: proof-equivalent,
  and retained as the source rollback, but materially slower.
- Land only the relation-source lookup: promising local result, but one pair
  lost and another control swapped, so the mechanism was not admitted alone.
- Land either shallow-copy change alone: exact-output checks passed, but the
  measured improvements of 8.06 and 13.79 percent were below the standalone
  full-path gate.
- Compose the three independently measured mechanisms and repeat full-path
  admission: selected after three local and three hosted wins.
- Flatten the self-coverage cycle into a pure DAG: rejected because it would
  omit a real dependency or final fixed-point proof.
- Reintroduce generic provider workers or cross-run proof reuse: rejected or
  deferred under the existing hosted regression and `AOA-KAG-D-0029`.

## Rationale

The selected changes remove implementation duplication without reusing a
verdict or changing an authoritative input. First-wins lookup preserves the
existing lineage-order rule. Shallow immutable fields cannot carry mutation
between consumers, while copied reference containers preserve the isolation
previously provided by whole-record deep copies. Focused mutation tests,
twenty-one-owner digest parity, malformed/tamper/mismatch cases, forced-cold,
and forced-Python paths bound that claim.

The combined candidate won all three interleaved local pairs, reducing the
median from 90.752 to 73.040 seconds (19.52 percent). On immutable hosted SHAs
with the same `workflow_dispatch` event it won all three pairs; medians changed
from 140.350 to 111.452 seconds, saving 28.898 seconds or 20.59 percent. All six
receipts retained 21/21 owners, exact pins, 76/76 successful timings, stable
per-head payloads, and zero schema disagreements. Median process peak RSS fell
from 513,292 to 510,036 KiB.

## Consequences

- The complete release proof is faster without removing or advisory-routing a
  proof node.
- Future family fields must be classified as immutable or explicitly copied;
  adding a mutable nested field without extending isolation tests is invalid.
- The SCC remains one atomic outer-DAG node with an ordered internal protocol;
  this decision is not evidence for semantic parallelism inside it.
- No generated projection becomes owner truth, and no cross-run artifact gains
  authority.
- Reverting PR 204 restores the whole-record copy implementation. Three clean
  hosted control runs at `cc74651e` prove that rollback path with all owners and
  validators; it is slower but operationally admitted.
- Reopen scheduling only with a distinct resource-isolation mechanism and
  full-path evidence. Reopen cross-run reuse only after owner-approved artifact
  authority and consumer admission exist.

## Source Surfaces

- `scripts/repo_local/indexes.py`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/repo_local/portable_family.py`
- `docs/validation/CI_EVIDENCE_DAG.md`
- `config/validation_lanes.json`
- `docs/decisions/AOA-KAG-D-0024-immutable-batch-owner-source-scan.md`
- `docs/decisions/AOA-KAG-D-0028-run-scoped-provider-coverage-fusion.md`
- `docs/decisions/AOA-KAG-D-0029-defer-cross-run-owner-proof-fragments.md`

## Validation

Regenerate and check decision indexes and the repo-local KAG family. Run the
normal, forced-cold, and forced-Python test paths; malformed, tamper, mismatch,
missing, and unsupported-input tests; the complete twenty-one-owner release
continuation; and all final SCC fixed-point and generated-cleanliness checks.

Landing requires three comparable local and three exact-head hosted pairs, at
least two wins, and at least 15 percent or 60 seconds full-path median benefit
without a resource regression. Claim landed benefit only after a clean
postmerge `main` run. PR 204 landed as `fa6f71ee`; push run `31250935353`
completed successfully with 21/21 owners in 112.382 seconds, within 0.83
percent of the hosted candidate median.
