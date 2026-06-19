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
| `source-fast` | blocking growth gate | route cards, mechanics skeleton, decision records, semantic AGENTS docs, unit tests, committed KAG validation | generated-output mutation, release stabilization, runtime graph/vector/index state |
| `generated` | blocking projection gate | generated KAG output rebuild parity and drift snapshot for `generated/` | source repository authored meaning, live runtime state |
| `release` | blocking release gate | release-prep execution through source-fast and generated lanes | ordinary docs status, compatibility-canary scheduling |
| `compatibility-canary` | blocking scheduled/manual canary | floating sibling checkout compatibility and generated-output drift check | release artifact identity |
| `advisory` | non-blocking boundary inventory | future mechanics part-local, graph/RAG/runtime, and source-authority stop-lines | hard runtime policy, eval verdicts, memory truth |

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

The current mechanics lane has only a root skeleton. No
`mechanics/<package>/parts/<part>/` script or test lane exists yet.

When a future KAG mechanic package is created, package-local builders,
validators, and tests should live beside the part that owns the payload and be
covered by a dedicated lane added to `config/validation_lanes.json`.

## Inventory

The broader script-surface map lives in `SCRIPT_TOPOLOGY.md` and
`script_inventory.json`. That inventory covers every active file under
`*/scripts/*`, including `scripts/AGENTS.md`. It is descriptive coverage, not
command authority.
