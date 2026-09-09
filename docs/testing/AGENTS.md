# AGENTS.md

## Applies to

`docs/testing/`.

## Role

This directory maps test-home topology, test families, focused targets, runner
coverage, and command-authority routes for `aoa-kag`.

## Inputs

- `docs/testing/TEST_TOPOLOGY.md`
- `docs/testing/test_inventory.json`
- `tests/AGENTS.md`
- `scripts/run_tests.py`
- `config/validation_lanes.json`

## Routes

| Surface | Function |
| --- | --- |
| `TEST_TOPOLOGY.md` | human-readable test topology |
| `test_inventory.json` | machine-readable test inventory |
| `scripts/run_tests.py` | unittest discovery authority |
| `config/validation_lanes.json` | lane command authority |

## Validation

The test runner and source-fast lane are selected on demand from root
`VALIDATION.md`; the manifest remains command authority.

## Closeout

Report changed test homes, inventory updates, focused checks, lane checks, and
the next owner route.
