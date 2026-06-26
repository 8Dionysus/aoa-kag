# AGENTS.md

## Applies to

`scripts/validators/manifests/`.

## Role

This package contains source manifest contract validators. The public import
facade is `scripts/validators/manifest_contracts.py`.

## Function Map

| Surface | Function |
| --- | --- |
| `technique_lift.py` | technique-lift manifest checks |
| `tos_text_chunk_map.py` | ToS text chunk map manifest checks |
| `tos_retrieval_axis.py` | ToS retrieval axis manifest checks |
| `tos_zarathustra_route.py` | ToS Zarathustra route manifest checks |
| `tos_zarathustra_route_retrieval.py` | ToS Zarathustra route retrieval manifest checks |
| `reasoning_handoff.py` | reasoning-handoff manifest checks |
| `return_regrounding.py` | return-regrounding manifest checks |
| `governance.py` | KAG maturity governance manifest checks |
| `source_owned_export.py` | source-owned export dependency manifest checks |
| `federation_export_registry.py` | federation export registry manifest checks |
| `federation_spine.py` | federation spine manifest checks |
| `cross_source_node_projection.py` | cross-source node projection manifest checks |
| `tiny_consumer_bundle.py` | tiny consumer bundle manifest checks |
| `counterpart_federation_exposure_review.py` | counterpart federation exposure review manifest checks |

## Route

Use `docs/validation/validator_inventory.json` for the machine-readable module
map. Use `docs/validation/VALIDATOR_TOPOLOGY.md` for the human topology map.

## Validation

```bash
python -m unittest tests.test_validator_module_topology tests.test_validate_kag
python scripts/validate_kag.py
```
