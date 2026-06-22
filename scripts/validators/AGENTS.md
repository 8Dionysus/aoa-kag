# AGENTS.md

## Applies to

`scripts/validators/`.

## Role

This directory contains the implementation modules for the repo-wide
`scripts/validate_kag.py` entrypoint.

## Function Map

| Surface | Function |
| --- | --- |
| `generation.py` | KAG generation constants and payload builders |
| `expected_contracts.py` | expected paths, allowed values, and payload contract data |
| `common.py` | shared validator errors, file readers, markdown helpers, schema helpers |
| `source_refs.py` | repo-relative and cross-repo source reference resolution |
| `schema_surfaces.py` | JSON schema checks |
| `local_contracts.py` | local route, mechanics skeleton, questbook, antifragility, and ToS tiny-entry checks |
| `manifest_contracts.py` | manifest source-input and output contract checks |
| `projection_parity.py` | generated/read-model parity checks |
| `example_contracts.py` | public example payload checks |
| `sibling_readiness.py` | optional source-owned export readiness checks |
| `orchestrator.py` | validate_kag call order and status output |

## Route

Use `docs/validation/validator_inventory.json` for the machine-readable module
map. Use `config/validation_lanes.json` for lane commands.

## Validation

```bash
python -m unittest tests.test_validator_module_topology tests.test_validate_kag
python scripts/validate_kag.py
```

For lane-visible changes:

```bash
python scripts/ci_gate.py --mode source-fast
```
