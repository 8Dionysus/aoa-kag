# AGENTS.md

## Applies to

`scripts/validators/expected/`.

## Role

This package contains expected contract data used by validators. The public
import facade is `scripts/validators/expected_contracts.py`.

## Function Map

| Surface | Function |
| --- | --- |
| `core.py` | repo roots, schema/example paths, allowed values, and shared path sets |
| `registry_contracts.py` | registry boundary, counterpart, provenance, and guardrail expectations |
| `governance_contracts.py` | KAG maturity governance expectations |
| `recurrence_contracts.py` | return-regrounding expectations |
| `technique_contracts.py` | technique-lift expectations |
| `tos_contracts.py` | Tree-of-Sophia route, chunk, retrieval, and adjunct expectations |
| `handoff_contracts.py` | reasoning-handoff expectations |
| `federation_contracts.py` | federation spine, export registry, and memo donor expectations |
| `cross_source_contracts.py` | cross-source node projection expectations |
| `consumer_contracts.py` | tiny consumer bundle and counterpart exposure review expectations |
| `registry_surface_inputs.py` | registry surface source-input expectations |
| `docs_contracts.py` | markdown/date/root/snippet expectations |

## Route

Use `docs/validation/validator_inventory.json` for the machine-readable module
map. Use `docs/validation/VALIDATOR_TOPOLOGY.md` for the human topology map.

## Validation

```bash
python -m unittest tests.test_validator_module_topology tests.test_validate_kag
python scripts/validate_kag.py
```
