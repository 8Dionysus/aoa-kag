# Validator Topology

Validators in `aoa-kag` are boundary organs for a provenance-aware derived KAG
substrate. They protect source-owned references, manifests, schemas, examples,
generated/read-model parity, decision records, route cards, and the mechanics
skeleton.

They should not become a historical pile where every future graph, RAG,
runtime, or mechanic concern lands in one broad script without owner routing.

## Lanes

| Lane | Posture | Owns | Does not own |
|---|---|---|---|
| `source-fast` | blocking growth gate | route cards, `kag/` source-home preflight, mechanics skeleton, active mechanics part tests, decision records, semantic AGENTS docs, unit tests, committed KAG validation | generated-output mutation, release stabilization, runtime graph/vector/index state |
| `generated` | blocking projection gate | generated KAG output rebuild parity and drift snapshot for `generated/` | source repository authored meaning, live runtime state |
| `release` | blocking release gate | release-prep execution through source-fast, generated, and OS Abyss artifact bundle lanes | ordinary docs status, compatibility-canary scheduling |
| `compatibility-canary` | blocking scheduled/manual canary | floating sibling checkout compatibility and generated-output drift check | release artifact identity |
| `advisory` | non-blocking boundary inventory | future graph/RAG/runtime and source-authority stop-lines | hard runtime policy, eval verdicts, memory truth |

## Current Validator Shape

`scripts/validate_kag.py` is currently a transitional monolith. It validates
KAG schemas, examples, manifests, source-owned export readiness, generated
payload parity, route docs, and bridge/federation contracts.

For this preflight it remains in place. The point of this change is to create
the command/script/test authority floor needed before a later validator-owner
module split.

Future validator splits should keep compatibility entrypoints stable while
moving implementation ownership into narrower owner modules. Generated/read
model checks should remain projection parity checks. They may rebuild expected
payloads from manifests and source-owned exports, but they must not define
source repository meaning, Tree of Sophia canon, proof verdicts, memory truth,
or runtime graph state.

## Source/Projection Boundary

Authored source repositories, Tree of Sophia, manifests, schemas, examples, and
KAG model docs own meaning.

Generated KAG outputs and compact packs are projections. Generated validators
check rebuild parity and bounded contract shape. They do not define what the
source repository means.

## Mechanics Boundary

The current mechanics lane has common-center package route homes, active Agon
part-local scripts/tests for promotion candidates and Sophian threshold
packets, active Antifragility recovery contract tests, active Audit proof-ref
and exposure-review tests, active Boundary-bridge source-owned export,
retrieval-axis, cross-source projection, and federation-spine tests, active
Checkpoint reasoning-handoff validator/tests, active Distillation technique
lift, ToS chunk-map, and ToS route-lift tests, active Experience contract
packet tests, active Method-growth contract packet tests, active Questbook
quest-store validator/tests, active Recurrence return-regrounding
validator/tests, and active Release-support release-lane tests.
`scripts/run_tests.py` covers those focused tests through the source-fast lane.

`scripts/validate_kag.py` still remains the repo-wide compatibility and
generated/read-model entrypoint, but focused mechanics ownership now routes
through part validators or part tests where a part owns the operation contract:
`mechanics/boundary-bridge/parts/source-owned-export/scripts/validate_source_owned_export.py`,
`mechanics/checkpoint/parts/reasoning-handoff/scripts/validate_reasoning_handoff.py`,
`mechanics/growth-cycle/parts/surface-growth-stop-rule/scripts/validate_surface_growth_stop_rule.py`,
`mechanics/questbook/parts/quest-store/scripts/validate_quest_store.py`, and
`mechanics/recurrence/parts/return-regrounding/scripts/validate_return_regrounding.py`.

When a future KAG mechanic part is created, package-local builders,
validators, and tests should live beside the part that owns the payload and be
covered by `scripts/run_tests.py` or a dedicated lane only when the part needs
execution semantics beyond unittest discovery.

## Local KAG Protocol Boundary

The `kag/` lane is a source-home preflight, not a generated payload home and not
a runtime graph store. Its current protection comes from nested AGENTS
validation and root tests that verify the source-home manifest, reserved future
surfaces, and no-premature-directory stop-line.

Future schema, example, builder, validator, or generated projection surfaces
for repo-local KAG organs should use their normal owner homes first. Add a
dedicated `kag/` validator only when portable record contracts become active.

## Inventory

The broader script-surface map lives in `SCRIPT_TOPOLOGY.md` and
`script_inventory.json`. That inventory covers every active file under
`*/scripts/*`, including `scripts/AGENTS.md`. It is descriptive coverage, not
command authority.
