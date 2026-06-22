# Validator Owner Modules

## Index Metadata

- Decision ID: AOA-KAG-D-0009
- Original date: 2026-06-21
- Surface classes: validation guard, release/tooling, script topology, test topology, docs/decisions
- KAG surfaces: validate_kag entrypoint, validator modules, validator inventory, generated parity, source/projection boundary
- Source lanes: aoa-kag, aoa-techniques
- Guard families: validator modules, command authority, generated-output parity, source-owned authority, inventory sync
- Posture: accepted

## Context

`aoa-kag` validates source refs, manifests, schemas, examples, generated
read-models, decision records, route cards, and mechanics surfaces. Those
checks need clear module homes so each validator surface has one readable
function.

## Decision

`scripts/validate_kag.py` is the repo-wide entrypoint.

Implementation lives in `scripts/validators/`:

| Module | Function |
| --- | --- |
| `generation.py` | KAG generation constants and payload builders |
| `expected_contracts.py` | expected paths, allowed values, and payload contract data |
| `common.py` | shared validator errors, file readers, markdown helpers, schema helpers |
| `source_refs.py` | source reference resolution |
| `schema_surfaces.py` | JSON schema checks |
| `local_contracts.py` | local route and mechanics-adjacent checks |
| `manifest_contracts.py` | manifest source-input and output contract checks |
| `projection_parity.py` | generated/read-model parity checks |
| `example_contracts.py` | public example payload checks |
| `sibling_readiness.py` | optional source-owned export readiness checks |
| `orchestrator.py` | call order and status output |

`docs/validation/validator_inventory.json` stores the machine-readable module
map. `config/validation_lanes.json` stores lane commands.

## Consequences

- Validator ownership is visible from the directory tree and inventory.
- Generation imports, expected data, and shared helpers have separate homes.
- Tests patch the module that reads the surface they override.
- Generated parity checks have a dedicated module.
- Part-local mechanic validators stay in their part directories.
- Further splitting should follow a real function boundary.

## Source Surfaces

- `docs/validation/VALIDATOR_TOPOLOGY.md`
- `docs/validation/validator_inventory.json`
- `docs/validation/script_inventory.json`
- `docs/testing/test_inventory.json`
- `config/validation_lanes.json`
- `scripts/validate_kag.py`
- `scripts/validators/`
- `tests/test_validator_module_topology.py`

## Validation

```bash
python -m unittest tests.test_validator_module_topology
python scripts/validate_kag.py
python scripts/ci_gate.py --mode source-fast
python scripts/release_check.py
python scripts/generate_decision_indexes.py --check
python scripts/validate_decision_records.py
```
