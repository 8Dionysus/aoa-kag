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
| `artifact_bundle_validator` | release artifact bundle sidecars, signatures, and registry rehearsal | may create temporary OS Abyss evidence outside the repo; must not write source or generated truth |
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

Active mechanic-owned scripts may live under
`mechanics/<package>/parts/<part>/scripts/` only after the part is listed in
`mechanics/topology.json` and has `README.md`, `CONTRACT.md`, `VALIDATION.md`,
and focused tests. Agon currently owns part-local promotion-candidate and
Sophian-threshold builders/validators; their generated companions stay in
root `generated/`. Antifragility currently owns part-local projection-health,
projection-quarantine, and retrieval-outage recovery contract packets and
focused tests. Audit currently owns proof expectation and exposure review
part-tests without adding extra script surfaces. Boundary-bridge currently owns
the part-local source-owned export validator, retrieval-axis tests,
cross-source projection tests, and federation-spine tests while source docs,
manifests, generated read models, schemas, and examples remain in their root
homes. Checkpoint currently owns the part-local reasoning-handoff validator and
focused tests while handoff docs, manifests, generated read models, schemas,
and examples remain in their root homes. Distillation currently owns technique
lift, ToS chunk-map, and ToS route-lift part-tests without adding extra script
surfaces. Experience currently owns part-local governance,
release/installation, and office/service schema/example contract packets and
focused tests. Method-growth currently owns part-local schema/example contract
packets and focused tests. Growth-cycle currently owns the part-local
surface-growth stop-rule validator and focused tests while maturity docs,
manifest controls, generated read models, schemas, and examples remain in
their root homes. Questbook currently owns the part-local quest-store validator
and focused tests; lane/state quest records remain in `quests/` while schemas
and examples remain under the quest-store part. Recurrence
currently owns the part-local return-regrounding validator and focused tests
while regrounding docs, manifests, generated read models, schemas, and examples
remain in their root homes. Release-support currently owns release-lane
part-tests without adding extra script surfaces.

Additional part scripts must be inventoried here before entering a blocking
lane.

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
