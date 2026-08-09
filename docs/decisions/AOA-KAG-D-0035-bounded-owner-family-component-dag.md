# Bounded Owner-Family Component DAG

## Index Metadata

- Decision ID: AOA-KAG-D-0035
- Original date: 2026-08-09
- Surface classes: validation guard, repository family, CI performance, evidence DAG
- KAG surfaces: portable family, repo-local validation action, owner landing preparation
- Source lanes: aoa-kag, provider repositories
- Guard families: exact output parity, stable candidate identity, explicit history boundary, bounded scheduling, sequential rollback
- Posture: accepted

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

Three interleaved GitHub-hosted pairs then compared one and two workers at the
exact candidate `cc7bbee9` and base `4915882d`, with identical history, event,
and budget refs. The canonical gate took 13.323/15.609/15.456 seconds with one
worker and 10.535/10.704/8.314 seconds with two. Two workers won 3/3; medians
fell from 15.456 to 10.535 seconds, saving 4.921 seconds or 31.8 percent. All
six unchanged full OS-wide audits and typed summaries passed. The hosted
receipt does not expose runner RSS, so resource admission remains bounded by
the target-host measurements: two workers added about 147 MiB of typical peak
memory over sequential execution, while the rejected three-worker default
added further memory for negligible median benefit. No hosted run showed
resource failure or proof instability.

This satisfies the predeclared hosted benefit and equivalence gates. The
one-worker path remains the immediate rollback, and provider rollout remains a
separate immutable-pin landing obligation rather than evidence retroactively
attributed to this decision.

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
complete release route. Hosted admission used three interleaved exact-head
pairs with `owner_family_workers=1` and `2`: runs `31326322051`/`31326425913`,
`31326517490`/`31326637679`, and `31326733710`/`31326847375`. Require the clean
PR and postmerge workflow, then roll out only the admitted immutable action
SHA.
