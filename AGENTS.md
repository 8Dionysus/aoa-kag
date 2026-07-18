# AGENTS.md

## Applies to

This root card applies to the whole `aoa-kag` repository unless a nearer
nested `AGENTS.md` narrows the lane.

## Role

This card is the agent-facing route law for `aoa-kag`.

It keeps local work inside the provenance-aware derived knowledge substrate
lane, names the nearest owner boundary, and routes stronger claims to the
owning surface.

It does not replace `README.md`, `CHARTER.md`, `DESIGN.md`,
`DESIGN.AGENTS.md`, `docs/KAG_MODEL.md`, `docs/BOUNDARIES.md`,
`docs/SOURCE_POLICY.md`, local `AGENTS.md` cards, manifests, schemas,
builders, validators, tests, or generated-source owners.

## Read before editing

Read this root card first. Then read the nearest nested `AGENTS.md` for every
touched path, followed by the route-mode surface and the nearest source doc,
manifest, schema, builder, validator, test, generated-source owner, decision,
or source-owner surface that owns the local claim.

For changes to KAG system form, source versus derived authority, federation
posture, local `/kag` protocol posture, or root surface roles, also read
`DESIGN.md`.

For changes to `AGENTS.md` card shape, root-to-local precedence, route modes,
validation posture, closeout expectations, Codex Spark lane placement, or
agent-facing guidance shape, also read `DESIGN.AGENTS.md`.

For changes to repeatable KAG operation topology or future mechanic packages,
also read `mechanics/README.md` and `mechanics/AGENTS.md`.

For changes to the `kag/` source-home preflight, repo-local `/kag` protocol
shape, local subtree rollout posture, portable graph/index record classes, or
sibling `/kag` stop-lines, also read `kag/AGENTS.md`, `kag/README.md`,
`kag/source_home.manifest.json`, and `kag/LOCAL_SUBTREE_PROTOCOL.md`.

For changes to the repository-owned callable KAG procedure, its capability
contract, or its OS user exposure, also read `skills/AGENTS.md`,
`skills/README.md`, `skills/port.manifest.json`, and the selected bundle
surface.

For changes to repository authority, owner boundaries, root posture, or claims
about what `aoa-kag` may own, also read `CHARTER.md`,
`docs/BOUNDARIES.md`, and `docs/SOURCE_POLICY.md`.

## Boundaries

Do not use this lane to override authored source meaning in sibling
repositories or Tree of Sophia.

Do not treat generated outputs, compact packs, exported capsules, runtime
receipts, graph-ready wording, retrieval-ready wording, or future local `/kag`
pressure as source truth.

Keep proof doctrine in `aoa-evals`, memory truth in `aoa-memo`, routing in
`aoa-routing`, role meaning in `aoa-agents`, scenario composition in
`aoa-playbooks`, shared portable skill procedures and home-port grammar in
`aoa-skills`, admitted repository-local skill procedures in their owner
repositories, reusable practice in `aoa-techniques`, and authored
knowledge-architecture content in `Tree-of-Sophia`.

## Validation

Use the nearest nested `AGENTS.md` for focused owner checks. Full lane command
sequences live in `config/validation_lanes.json`; do not duplicate them in
route cards.

For the default read-only integrity pass, run:

```bash
python scripts/ci_gate.py --mode source-fast
```

If manifests, packs, or generated KAG surfaces change, regenerate before
rerunning the same pass:

```bash
python scripts/ci_gate.py --mode generated
```

For release-prep parity, also run:

```bash
python scripts/release_check.py
git status -sb
```

Do not claim checks you did not run.

## Closeout

Report changed KAG surfaces, whether semantics or metadata changed, whether
provenance, bridge, handoff, federation, regrounding, or local `/kag` posture
changed, generated refresh result when relevant, checks run, checks skipped,
remaining risk, decision-review result, and the next owner route.

## Purpose

`aoa-kag` is the derived knowledge substrate layer of AoA.
It stores provenance-aware, source-first derived structures and graph-ready or
retrieval-oriented projections that support downstream consumers without
replacing authored meaning in source repositories.

For the full authority boundary, use `CHARTER.md`.

## Owner lane

This repository owns:

- derived substrate structure and KAG-layer metadata;
- provenance-aware lifted surfaces, normalized packs, manifests, schemas,
  examples, and generated outputs;
- source-first graph and retrieval projection posture;
- bridge, consumer, reasoning-handoff, federation, quarantine, and regrounding
  seams when defined here;
- framework-neutral local `/kag` source-home and protocol contracts when they
  are explicitly designed in `kag/`.

It does not own:

- authored technique, skill, eval, memo, role, playbook, routing, center,
  runtime, cross-owner statistical grammar or composition, or Tree of Sophia
  meaning;
- framework-specific application code that belongs downstream;
- source-replacing world-model sprawl;
- live graph, vector, embedding, index, runtime, or cache state.

## Start here

For first reading or outside orientation, use this route:

1. `README.md`
2. `CHARTER.md`
3. `DESIGN.md`
4. `kag/README.md`
5. `docs/KAG_MODEL.md`
6. `docs/BOUNDARIES.md`
7. `docs/SOURCE_POLICY.md`
8. `ROADMAP.md`

For agent editing, use this route:

1. this `AGENTS.md`
2. nearest nested `AGENTS.md` for every touched path
3. route-mode surface from the table below
4. nearest local source surface: model doc, manifest, schema, example, config,
   builder, validator, test, generated-source owner, or decision record
5. narrowest relevant validator before broader gates

For preserved pre-refactor root guidance, use `docs/AGENTS_ROOT_REFERENCE.md`
only as historical audit material. If a preserved rule still matters, restate
it at the smallest active owner surface instead of treating the reference as a
competing root card.

## Route modes

| Route mode | Use when | First surface |
| --- | --- | --- |
| `first-reading` | you need the shortest honest repository overview | `README.md` |
| `authority-boundary` | repository authority, owner split, source ownership, or root posture changes | `CHARTER.md` |
| `system-design` | KAG form, source/generated authority, federation posture, local `/kag` source-home or protocol posture, or layer relationships change | `DESIGN.md` |
| `agent-surface-design` | AGENTS shape, local-card placement, route modes, validation posture, or closeout changes | `DESIGN.AGENTS.md` |
| `mechanic-change` | repeatable KAG operation topology, mechanics root contract, or future package posture changes | `mechanics/README.md` |
| `local-kag-source-home` | `kag/` source-home preflight, local `/kag` protocol shape, repo-local subtree contract, sibling rollout stop-line, or portable graph/index record posture changes | `kag/README.md` |
| `owner-skill` | the callable KAG procedure, capability contract, manual use posture, or OS user exposure changes | `skills/AGENTS.md` -> `skills/README.md` -> `skills/port.manifest.json` |
| `local-stats` | a KAG-owned statistical question, measurement contract, or reference packet changes | `stats/AGENTS.md` -> `stats/README.md` -> `stats/port.manifest.json` |
| `model-boundary` | KAG model, ownership, source policy, bridge contract, or non-identity boundary changes | `docs/KAG_MODEL.md` |
| `decision-rationale` | durable route rationale or decision metadata changes | `docs/decisions/README.md` |
| `manifest-change` | source-authored lift controls, donor refs, output refs, or pack activation posture change | `manifests/AGENTS.md` |
| `generated-surface` | generated payloads, compact outputs, or registry read models change | `generated/AGENTS.md` |
| `schema-example` | payload contracts or public-safe examples change | `schemas/AGENTS.md` or `examples/AGENTS.md` |
| `builder-validator` | generators, validators, decision-index helpers, or test guards change | `scripts/AGENTS.md` |
| `agent-companion-lane` | `.agents/` companion lanes, handoff prompts, model support, or Spark fast-loop posture changes | `.agents/AGENTS.md` |
| `proof-pressure` | KAG-local eval intake, cases, fixtures, suites, or reports change | `evals/AGENTS.md` |
| `direction-change` | current direction, stop-rules, owner wait states, or future contour changes | `ROADMAP.md` |

## AGENTS stack law

- Start with this root card, then follow the nearest nested `AGENTS.md` for
  every touched path.
- Root guidance owns repository identity, owner boundaries, route choice, and
  the shortest honest verification path.
- Nested guidance owns local contracts, local risk, exact files, and local
  checks.
- Authored source surfaces own meaning. Generated, exported, compact, derived,
  runtime, and adapter surfaces summarize, transport, or support meaning.
- Self-agency, recurrence, quest, progression, checkpoint, graph, retrieval,
  or growth language must stay bounded, reviewable, evidence-linked, and
  reversible.
- Report what changed, what was verified, what was not verified, and where the
  next agent should resume.

## Memory route

For KAG-layer recall, continuity, compaction recovery, comparison with past
work, or preserved lessons, start with `aoa-memo` and the workspace memory map.
Session grounding routes through `.aoa`; local candidate writing routes through
this repository's `memo/` port when that port exists; durable reviewed memory
lands through `aoa-memo`.

## Decision review

After structural, ownership, route-law, validator-authority, public-contract,
source-ref, generated-pack, maturity, quarantine, federation, bridge, handoff,
or regrounding changes, check whether future agents need a decision record to
understand why the path was chosen. Use `docs/decisions/AGENTS.md`,
`docs/decisions/README.md`, and `docs/decisions/TEMPLATE.md`.

If no record is needed, say so in closeout.

Decision records explain rationale. They do not replace active KAG source docs,
manifests, generated outputs, schemas, builders, validators, tests, or
sibling-owner truth.

## GitHub landing workflow

Root `AGENTS.md` owns the repository-wide branch, PR, CI, and merge route.
`.github/AGENTS.md` owns the GitHub-native files that support it.

When the user asks to commit, push, and merge in this repository, use this
route:

1. Start from a branch based on the current `origin/main`. If the worktree is
   already dirty, inventory it first and carry forward only the intended diff.
2. Commit the intended change with a message that names the changed surface.
3. Push the branch and open a pull request that states changed surfaces,
   validation run, skipped checks, and remaining risk.
4. Wait for GitHub `Repo Validation` and any required GitHub checks. If a check
   fails, fix the branch and wait for the new result.
5. Merge through GitHub after green validation. Use squash unless repository
   settings report a different required method; report the method that landed.
6. Return to `main`, fast-forward from `origin/main`, and confirm the worktree
   is clean before closeout.

If GitHub status or merge permissions cannot be observed, stop the landing
route and report the exact blocker instead of guessing.

## Post-change route review

Before closeout, check whether the change actually affects these surfaces.
Update only the ones that moved; otherwise say no update was needed.

- `DESIGN.md` when KAG system form, repository shape, source/generated
  authority, federation posture, local `/kag` protocol posture, or layer
  relationships changed.
- `DESIGN.AGENTS.md` when agent-facing form, card shape, route modes,
  validation posture, closeout expectations, generated companions, local card
  placement, or Spark fast-loop posture changed.
- `CHARTER.md`, `docs/BOUNDARIES.md`, or `docs/SOURCE_POLICY.md` when
  repository authority, owner boundaries, or source-first policy changed.
- `README.md` or `docs/README.md` when first-reading or docs-map routes
  changed.
- `mechanics/README.md`, `mechanics/AGENTS.md`, or `mechanics/topology.json`
  when repeatable KAG operation topology or mechanics package posture changed.
- `kag/README.md`, `kag/AGENTS.md`, `kag/source_home.manifest.json`, or
  `kag/LOCAL_SUBTREE_PROTOCOL.md` when `kag/` source-home posture, local `/kag`
  protocol posture, portable record classes, runtime-state exclusion, or
  sibling rollout stop-lines changed.
- `stats/` when the KAG-owned statistical question, evidence route,
  measurement contract, or exported reference packet changes.
- `ROADMAP.md` when current direction, stop-rules, owner wait states, or future
  contour changed.
- `docs/decisions/` when future agents need rationale for a route, owner split,
  workflow, validator, generated-pack, source-ref, federation, bridge, handoff,
  quarantine, or regrounding choice.
- generated surfaces, manifests, schemas, builders, validators, and tests when
  a source-backed machine capsule changed.
- neighboring owner repositories when the change routes or constrains their
  truth.

## Route away when

- canonical authored meaning must change in the source repository;
- the task is routing, memory, proof, role, playbook, skill, technique, stats,
  runtime, or Tree of Sophia doctrine;
- graph-ready or retrieval-ready wording starts to replace provenance or source
  authority;
- sibling `/kag` rollout pressure appears before protocol schema, examples, and
  validation exist.

## Report

Name the KAG surface family changed, whether semantics or metadata changed,
whether source refs, provenance, generated outputs, bridge posture, handoff
posture, federation posture, regrounding posture, proof pressure, or local
`/kag` protocol posture changed, which generated surfaces were refreshed, and
which checks ran.

## Historical reference

`docs/AGENTS_ROOT_REFERENCE.md` preserves the former detailed root guidance for
audit only. Do not use it as current route law. Lift any surviving rule into
this card or the nearest owner surface before relying on it.
