# Validation Command Authority Preflight

## Index Metadata

- Decision ID: AOA-KAG-D-0005
- Original date: 2026-06-19
- Surface classes: validation guard, release/tooling, docs route
- KAG surfaces: validation authority, script topology, test topology, mechanics preflight
- Source lanes: aoa-kag
- Guard families: command authority, generated-output parity, source-owned authority, mechanics stop-line
- Posture: accepted

## Context

`aoa-kag` is preparing for a deeper mechanics refactor. The repository already
has a bounded mechanics skeleton, but its validation plane still stored command
meaning across route cards, workflow YAML, and `scripts/release_check.py`.

That was workable while the repo stayed small, but future KAG mechanics,
graph/RAG pressure, and local `/kag` routes need a clearer floor: a script or
test should be able to name its owner, side effects, validation lane, and
failure route without turning docs into a second command store.

## Decision

Use `config/validation_lanes.json` as the canonical command storage surface for
active validation lanes.

Add `docs/validation/` and `docs/testing/` as the route surfaces for command
authority, script topology, validator posture, and test topology. Keep
`script_inventory.json` and `test_inventory.json` descriptive: they record
owner, lane, side-effect, coverage, and failure-route metadata, but they do not
store executable command sequences.

Keep `scripts/validate_kag.py` as the transitional validator monolith for this
preflight. The validator-owner split is a later change after command/script/test
authority is stable.

## Options Considered

- Keep command sequences in `scripts/release_check.py` and route cards:
  smaller diff, but mechanics work would continue without a durable command
  authority.
- Add docs only: useful for humans, but future script/test movement would not
  be mechanically guarded.
- Add lane authority, inventories, and focused topology tests now: larger than
  docs-only, but creates the minimum stable floor before mechanics refactor.

## Rationale

`aoa-kag` is a derived substrate, not the source authoring layer or runtime
graph store. The validation system should therefore prove local derived
contracts, generated parity, route-card shape, decision records, and mechanics
stop-lines without absorbing sibling-owner authority.

Separating command authority from descriptive inventories keeps the active
execution path inspectable while preserving readable route maps for agents.
This matches the sibling-refactor lesson from `aoa-techniques` without copying
its larger validator-module split into this preflight.

## Consequences

- Future scripts and tests need inventory entries before they are treated as
  active durable surfaces.
- Workflow YAML and route cards should name lane entrypoints instead of
  duplicating full command sequences.
- `release_check.py` remains a stable public entrypoint, but it reads the
  `release` lane instead of owning command meaning.
- Future mechanics packages can add part-local lanes later without first
  untangling root command authority.
- `validate_kag.py` remains a known transitional monolith; this decision does
  not bless further unrelated rule accretion inside it.

## Source Surfaces

- `config/validation_lanes.json`
- `docs/validation/COMMAND_AUTHORITY.md`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `docs/validation/VALIDATOR_TOPOLOGY.md`
- `docs/validation/script_inventory.json`
- `docs/testing/TEST_TOPOLOGY.md`
- `docs/testing/test_inventory.json`
- `scripts/validation_lanes.py`
- `scripts/ci_gate.py`
- `scripts/release_check.py`
- `scripts/run_tests.py`
- `tests/test_validation_command_authority.py`
- `tests/test_script_topology.py`
- `tests/test_test_topology.py`

## Validation

Run:

```bash
python -m unittest tests.test_validation_command_authority tests.test_script_topology tests.test_test_topology
python scripts/ci_gate.py --mode source-fast
python scripts/ci_gate.py --mode generated
python scripts/release_check.py
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
```
