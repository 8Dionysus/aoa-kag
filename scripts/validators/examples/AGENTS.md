# AGENTS.md

## Applies to

`scripts/validators/examples/`.

## Role

This package contains public example contract validators. The public import
facade is `scripts/validators/example_contracts.py`.

## Function Map

| Surface | Function |
| --- | --- |
| `tos_examples.py` | Tree-of-Sophia example checks |
| `recurrence_examples.py` | return-regrounding example checks |
| `governance_examples.py` | KAG maturity governance example checks |
| `federation_examples.py` | federation export and KAG export example checks |
| `cross_source_examples.py` | cross-source node projection example checks |
| `tiny_consumer_bundle_examples.py` | tiny consumer bundle example checks |
| `exposure_review_examples.py` | counterpart federation exposure review example checks |
| `bridge_examples.py` | bridge retrieval and bridge envelope example checks |
| `counterpart_examples.py` | counterpart edge and counterpart consumer contract example checks |
| `reasoning_handoff_examples.py` | reasoning-handoff example checks |

## Route

Use `docs/validation/validator_inventory.json` for the machine-readable module
map. Use `docs/validation/VALIDATOR_TOPOLOGY.md` for the human topology map.

## Validation

```bash
python -m unittest tests.test_validator_module_topology tests.test_validate_kag
python scripts/validate_kag.py
```
