# Bounded Owner-Family Component DAG

## Index Metadata

- Decision ID: AOA-KAG-D-0035
- Original date: 2026-08-09
- Surface classes: validation guard, repository family, CI performance, evidence DAG
- KAG surfaces: portable family, repo-local validation action, owner landing preparation
- Source lanes: aoa-kag, provider repositories
- Guard families: exact output parity, stable candidate identity, explicit history boundary, bounded scheduling, sequential rollback
- Posture: proposed

## Context

The reusable repo-local KAG action is an AbyssOS-wide provider gate, but it ran
four canonical commands sequentially in every consumer: full parity,
incremental parity, family validation, and compatibility assembly. The earlier
optimization work changed the root `aoa-kag` release topology only and did not
change this shared consumer action, so owner sessions continued paying the
same repeated cost and discovering generated drift only after entering CI.

The ordinary owner-family graph is not the root coverage/generated/family SCC.
Incremental parity can detect drift before downstream work. On a clean
candidate, full parity, family validation, and compatibility assembly are
read-only consumers of the same repository identity and exact history/budget
boundaries.

## Decision

Route every reusable owner-family action through a common fail-fast component
DAG. Run incremental parity first. Only after it passes, schedule full parity,
family validation, and compatibility assembly with a bounded worker pool. All
four commands remain blocking, and the final receipt must prove that HEAD,
index tree, and complete status digest stayed unchanged.

Use two workers by default. Preserve one worker as the exact sequential
rollback and expose three only for explicit comparison. Add an owner-neutral
isolated preparation entrypoint so any provider session can regenerate and
validate its family before push without vendoring KAG implementation code or
changing the caller Git index.

## Options Considered

- Keep the shared action sequential: proof-equivalent rollback, but retains
  repeated critical-path latency and late drift discovery across every owner.
- Start all four commands together: rejected because incremental drift should
  stop unnecessary work and all commands would contend before the cheap
  admission boundary is known.
- Use three workers by default: locally fastest by only 0.281 seconds at the
  median beyond two workers while requiring roughly twelve percent more peak
  memory; retained only as an explicit experiment.
- Reuse one command's verdict as another's proof: rejected; no schema,
  semantic, budget, compatibility, or parity assertion is removed or cached as
  authority.
- Put root `aoa-kag` through the same pure DAG: rejected because its coverage,
  generated projections, and portable family form the atomic SCC described by
  `AOA-KAG-D-0034`.

## Rationale

Three interleaved target-host samples on `Agents-of-Abyss` reduced the median
from 34.795 seconds sequentially to 24.703 seconds with two workers, a 29.0
percent improvement. Three workers reached 24.422 seconds, only 1.1 percent
beyond two, while typical peak memory rose from about 444 to 498 MiB. A second
owner, `Tree-of-Sophia`, improved from 21.185 to 14.547 seconds, or 31.3
percent. Every valid-boundary run executed all four canonical commands and
returned a verified, stable-candidate receipt. An intentionally wrong budget
boundary failed closed at the sentinel rather than being hidden by scheduling.

This is local mechanism and resource evidence. The proposed posture remains
until three exact-head hosted pairs show the same proof identity, at least two
wins, and the existing material-benefit threshold without a resource
regression. The workflow exposes the one-worker control on the same commit so
that admission does not depend on incomparable branches.

## Consequences

- Every provider using the shared action can receive the same bounded DAG by
  updating one immutable action pin after central admission.
- Known family drift fails before full parity, validation, and assembly spend
  more runner time.
- Clean owner-family latency can fall without removing a proof command.
- Local sessions gain a common isolated preparation route; owner budget reasons
  remain explicit human/owner authority.
- The rollout is incomplete until every provider is classified as updated,
  not applicable under its owner contract, or routed through an equivalent
  owned KAG path.
- This decision does not authorize parallel OS-wide semantic provider proof,
  cross-run proof reuse, or a pure DAG inside the root SCC.

## Source Surfaces

- `.github/actions/repo-local-kag-index/action.yml`
- `.github/workflows/repo-validation.yml`
- `scripts/repo_local_kag_gate.py`
- `scripts/prepare_owner_landing.py`
- `scripts/generate_repo_local_kag_index.py`
- `scripts/validate_repo_local_kag_family.py`
- `scripts/assemble_repo_local_kag_family.py`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/validation/CI_EVIDENCE_DAG.md`
- `docs/decisions/AOA-KAG-D-0034-bounded-repository-family-reconstruction.md`

## Validation

Run the focused gate, preparation, command-authority, and topology tests; both
decision validators; root source-fast; isolated real-owner checks; and the
complete release route. Before changing posture to accepted, run three
interleaved exact-head hosted pairs with `owner_family_workers=1` and `2`, retain
all receipts and resource observations, then require a clean PR and postmerge
workflow. Roll out only the admitted immutable action SHA.
