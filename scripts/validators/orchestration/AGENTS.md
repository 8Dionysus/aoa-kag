# AGENTS.md

## Applies to

`scripts/validators/orchestration/`.

## Role

This package contains the repo-wide `validate_kag` orchestration phases. The
public import facade is `scripts/validators/orchestrator.py`.

## Function Map

| Surface | Function |
| --- | --- |
| `runner.py` | scoped `local`, `os-wide`, and full-compatible `main()` validation flow |
| `static_surfaces.py` | local, schema, route, repo-local family, and stress surface checks |
| `manifests.py` | registry context and manifest contract checks |
| `expected_payloads.py` | expected generated payload construction |
| `generated_text.py` | generated text parity checks |
| `generated_structures.py` | generated structure checks |
| `examples.py` | public example checks |
| `status.py` | success status output |

The OS-wide provider-home and coverage contracts are selected explicitly by
`runner.py`; neither may be added back to `static_surfaces.py` or another
local phase.

## Route

Use `docs/validation/validator_inventory.json` for the machine-readable module
map. Use `docs/validation/VALIDATOR_TOPOLOGY.md` for the human topology map.

## Validation

```bash
python -m unittest tests.test_validator_module_topology tests.test_validate_kag
python scripts/validate_kag.py
```
