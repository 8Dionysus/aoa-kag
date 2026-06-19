# Script Topology

Scripts in `aoa-kag` are command-plane organs for a provenance-aware derived
knowledge substrate. They should name the boundary they protect, the source
truth they read, the projections they may write, and the validation lane that
covers them.

They are not a second command authority. Blocking command sequences live in
`config/validation_lanes.json`. The script inventory is descriptive and
testable: it proves every active script has an owner route, side-effect
boundary, lane posture, and focused test target.

## Inventory

Machine-readable script coverage lives in `script_inventory.json`. It includes
every tracked non-pyc file under `*/scripts/*`, including local `AGENTS.md`
route cards.

Dependency checkouts under `.deps/` are excluded. They are sibling intake
context for CI and compatibility checks, not `aoa-kag` script surfaces.

Each entry records:

- `path`
- `family`
- `organ_lane`
- `owner_surface`
- `source_truth`
- `reads`
- `writes`
- `side_effects`
- `validation_lane`
- `ci_inclusion`
- `test_target`
- `disposition`

`tests/test_script_topology.py` keeps the inventory synchronized with the
filesystem and rejects orphan scripts, missing owner/test targets, hidden lane
commands outside the inventory, and unclear side-effect boundaries.

## Script Families

| Family | Owns | Boundary |
|---|---|---|
| `source_validator` | authored route, AGENTS, decision, mechanics, and source-ref checks | may read source meaning; must not write generated outputs |
| `projection_builder` | generated/read-model writes from source controls | may write tracked projections; must not define source meaning |
| `projection_validator` | generated/read-model parity checks | compares projections; does not own source truth |
| `decision_index_builder` | generated decision lookup indexes | may write decision indexes; decision notes remain source truth |
| `skill_local_contract_tool` | exported skill companion contract helpers | advisory/local-only; not CI hard gates for this repo |
| `lane_executor`, `lane_loader`, `release_entrypoint`, `test_runner` | command execution and release/test orchestration | load command authority from `config/validation_lanes.json` |
| `script_route_card` | local route and stop-line guidance | semantic AGENTS validators cover shape |
| `projection_helper` | shared generation helpers | imported by builders/validators; no direct lane authority |

## Root Scripts

Root `scripts/*.py` own repo-wide builders, validators, lane execution, release
stabilization, and test runners. Root builders may write tracked generated
companions only through generated/read-model lanes. Root validators must keep
source checks separate from generated-output mutation.

`scripts/validate_kag.py` stays a transitional validator monolith for this
preflight. Do not add new unrelated rule families to it while preparing
mechanics; use the topology surfaces here to decide whether a future owner
module split is needed.

## Non-Root Scripts

No non-root mechanic-owned scripts are active yet. Future
`mechanics/<package>/parts/<part>/scripts/` builders and validators should be
inventoried here and covered by a dedicated lane only after a package-local
route exists.

The `.agents/skills/*/scripts` helpers are deterministic contract tools inside
exported skill companion material. They can model dry-run, readiness, and risk
contracts, but they do not become `aoa-kag` runtime policy enforcement and are
not hidden hard gates.

## Promotion Rule

A script may move from advisory/local-only into a blocking lane only when a
current owner surface and decision record prove that `aoa-kag` owns the checked
behavior. Until then, runtime graph/vector/index state, eval verdicts, memory
truth, source-authored meaning, and future local `/kag` protocol execution stay
route-only or sibling-owned.
