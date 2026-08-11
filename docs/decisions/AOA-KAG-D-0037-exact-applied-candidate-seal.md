# Exact Applied Candidate Seal

## Index Metadata

- Decision ID: AOA-KAG-D-0037
- Original date: 2026-08-11
- Surface classes: validation guard, landing preparation, session performance, evidence DAG
- KAG surfaces: generated fixed point, landing preparation receipt, caller candidate
- Source lanes: aoa-kag, provider repositories
- Guard families: exact caller index, content identity, provider identity, mutation invalidation, no cross-run proof reuse
- Posture: accepted

## Context

The root landing preparation already performs the complete owner sweep,
converges the atomic coverage/generated/root-family SCC, enforces the final
digest-bound budget receipt, and runs final parity in an isolated copy of the
caller's candidate. Real repair sessions nevertheless followed every
successful `--apply` with an immediate full `--check` on the same unchanged
candidate.

In the observed long-running landing session, the final apply took 244.9
seconds and the unchanged check took another 199.0 seconds. Earlier unchanged
checks in the same campaign took roughly 190--261 seconds. The second sweep
did not discover a new input epoch; it repeated the same complete owner work to
establish that the patch just returned by the first process had been applied
exactly.

## Decision

After final parity, restore the caller's exact Git index state inside the
already validated isolated worktree and capture the complete final candidate
content identity. Apply only the bounded generated patch to the caller, capture
the caller again, and return success only when the two content identities and
provider identities match and the caller remains stable through closeout.
After the caller stages only the receipt-listed generated paths, a cheap
verification command must confirm that the worktree content and provider
identities remain unchanged and that the staged tree equals the already proved
fixed-point tree. Only that exact index-only transition preserves the seal.

The content identity binds bytes, staged and unstaged candidate diffs, index
bytes and tree, modes, directory topology, hardlinks, extended attributes,
untracked content, and nested-checkout identities. It excludes filesystem
access and modification times because validation reads and patch application
necessarily change them. Full candidate identity, including times, still
guards against mutation before apply and around final caller capture.

## Options Considered

- Keep mandatory apply then check: proof-equivalent, but repeats the complete
  21-owner sweep on an unchanged candidate and retains several minutes of
  avoidable session latency.
- Persist and trust the first owner-proof receipt across processes: rejected;
  `AOA-KAG-D-0029` still prohibits cross-run owner-fragment reuse without an
  admitted artifact class and producer trust route.
- Compare only the generated patch digest: rejected because it would not bind
  the caller index, original source delta, untracked inputs, filesystem
  identity, nested validation checkouts, or provider epoch.
- Compare the complete applied caller with the already proved isolated
  candidate before the first process returns, then verify the exact staged-tree
  transition without rebuilding KAG: selected because it closes both gaps the
  immediate second check was being used to test.

## Rationale

The seal does not cache or import a validation verdict. It is issued inside the
same process that performed the full proof and only after exact equality with
the proved content is established. A later index-only staging transition is
accepted only when its worktree identity remains exact and its tree equals the
proved fixed point; any other candidate, index, or provider mutation
invalidates the seal. Source-fast, full owner proof, release audit, hosted CI, and the
stable landing verdict remain separate blocking authorities.

This changes the retry unit from two full preparations of one immutable
candidate to one full preparation, an exact in-process equality barrier, and a
cheap staged-tree verification.
The expected real-session saving is the complete duration of the immediate
unchanged check, not a reduction in assertions or owners.

## Consequences

- A successful root `--apply` plus exact `--verify-applied-seal` result can
  state that no immediate unchanged full `--check` is required.
- Repair sessions still rerun preparation after every proof-relevant mutation.
- Provider roots, caller content, or unapproved index drift fail closed before
  or after the seal is issued.
- The seal has no cross-run, cross-process, source-fast, release, or landing
  authority.
- Non-root owner preparation remains governed by its own stable-candidate
  receipt until an equivalent owner-local apply seal is separately admitted.

## Source Surfaces

- `scripts/prepare_landing.py`
- `tests/test_prepare_landing.py`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `docs/validation/CI_EVIDENCE_DAG.md`
- `docs/decisions/AOA-KAG-D-0029-defer-cross-run-owner-proof-fragments.md`
- `docs/decisions/AOA-KAG-D-0034-bounded-repository-family-reconstruction.md`
- `docs/decisions/AOA-KAG-D-0036-bounded-process-provider-audit-wave.md`

## Validation

The complete `prepare_landing` test module, command-authority and topology
tests, decision generation and validation, source-fast, one real staged apply,
and the full release route passed. The real 21-owner apply completed in 99.785
seconds, issued an exact verified candidate seal, and did not require the
immediate unchanged check. PR #215 passed source-fast and owner-family proof in
2 minutes 18 seconds, the full OS-wide release audit in 2 minutes 20 seconds,
and the stable landing verdict. Merge commit `2f3651c1` then passed postmerge
source-fast and owner-family proof in 2 minutes 29 seconds, the full OS-wide
release audit in 2 minutes 34 seconds, and the stable landing verdict in run
`31512635998`.
