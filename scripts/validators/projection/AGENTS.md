# AGENTS.md

## Applies to

`scripts/validators/projection/`.

## Role

This package contains generated/read-model parity validators for KAG projection
families. `scripts/validators/projection_parity.py` is the import facade.

## Function Map

| Surface | Function |
| --- | --- |
| `registry.py` | registry payload and special registry surface checks |
| `tos_text_chunk_map.py` | ToS text chunk map pack checks |
| `tos_retrieval_axis.py` | ToS retrieval axis pack checks |
| `tos_zarathustra_route.py` | ToS Zarathustra route pack checks |
| `tos_zarathustra_route_retrieval.py` | ToS Zarathustra route retrieval pack checks |
| `reasoning_handoff.py` | reasoning-handoff pack checks |
| `return_regrounding.py` | return-regrounding pack checks |
| `governance.py` | KAG maturity governance pack checks |
| `federation_export_registry.py` | federation export registry pack checks |
| `federation_spine.py` | federation spine pack checks |
| `cross_source_node_projection.py` | cross-source node projection pack checks |
| `tiny_consumer_bundle.py` | tiny consumer bundle pack checks |
| `counterpart_federation_exposure_review.py` | counterpart federation exposure review pack checks |
| `technique.py` | generated text parity and technique-lift pack checks |

## Route

Use `docs/validation/validator_inventory.json` for the machine-readable module
map. Use `docs/validation/VALIDATOR_TOPOLOGY.md` for the human topology map.

## Validation

```bash
python -m unittest tests.test_validator_module_topology tests.test_validate_kag
python scripts/validate_kag.py
```
