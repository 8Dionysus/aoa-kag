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
| `expected_contracts.py` | expected contract data facade |
| `expected/core.py` | repo roots, schema/example paths, allowed values, and shared path sets |
| `expected/registry_contracts.py` | registry boundary, counterpart, provenance, and guardrail expectations |
| `expected/governance_contracts.py` | KAG maturity governance expectations |
| `expected/recurrence_contracts.py` | return-regrounding expectations |
| `expected/technique_contracts.py` | technique-lift expectations |
| `expected/tos_contracts.py` | Tree-of-Sophia route, chunk, retrieval, and adjunct expectations |
| `expected/handoff_contracts.py` | reasoning-handoff expectations |
| `expected/federation_contracts.py` | federation spine, export registry, and memo donor expectations |
| `expected/cross_source_contracts.py` | cross-source node projection expectations |
| `expected/consumer_contracts.py` | tiny consumer bundle and counterpart exposure review expectations |
| `expected/registry_surface_inputs.py` | registry surface source-input expectations |
| `expected/docs_contracts.py` | markdown/date/root/snippet expectations |
| `common.py` | shared validator errors, file readers, markdown helpers, schema helpers |
| `source_refs.py` | source reference resolution |
| `schema_surfaces.py` | JSON schema checks |
| `local_contracts.py` | local route and mechanics-adjacent checks |
| `manifest_contracts.py` | manifest contract facade |
| `manifests/technique_lift.py` | technique-lift manifest checks |
| `manifests/tos_text_chunk_map.py` | ToS text chunk map manifest checks |
| `manifests/tos_retrieval_axis.py` | ToS retrieval axis manifest checks |
| `manifests/tos_zarathustra_route.py` | ToS Zarathustra route manifest checks |
| `manifests/tos_zarathustra_route_retrieval.py` | ToS Zarathustra route retrieval manifest checks |
| `manifests/reasoning_handoff.py` | reasoning-handoff manifest checks |
| `manifests/return_regrounding.py` | return-regrounding manifest checks |
| `manifests/governance.py` | KAG maturity governance manifest checks |
| `manifests/source_owned_export.py` | source-owned export dependency manifest checks |
| `manifests/federation_export_registry.py` | federation export registry manifest checks |
| `manifests/federation_spine.py` | federation spine manifest checks |
| `manifests/cross_source_node_projection.py` | cross-source node projection manifest checks |
| `manifests/tiny_consumer_bundle.py` | tiny consumer bundle manifest checks |
| `manifests/counterpart_federation_exposure_review.py` | counterpart federation exposure review manifest checks |
| `projection_parity.py` | generated/read-model parity facade |
| `projection/registry.py` | registry payload and special registry surface checks |
| `projection/tos_text_chunk_map.py` | ToS text chunk map pack checks |
| `projection/tos_retrieval_axis.py` | ToS retrieval axis pack checks |
| `projection/tos_zarathustra_route.py` | ToS Zarathustra route pack checks |
| `projection/tos_zarathustra_route_retrieval.py` | ToS Zarathustra route retrieval pack checks |
| `projection/reasoning_handoff.py` | reasoning-handoff pack checks |
| `projection/return_regrounding.py` | return-regrounding pack checks |
| `projection/governance.py` | KAG maturity governance pack checks |
| `projection/federation_export_registry.py` | federation export registry pack checks |
| `projection/federation_spine.py` | federation spine pack checks |
| `projection/cross_source_node_projection.py` | cross-source node projection pack checks |
| `projection/tiny_consumer_bundle.py` | tiny consumer bundle pack checks |
| `projection/counterpart_federation_exposure_review.py` | counterpart federation exposure review pack checks |
| `projection/technique.py` | generated text parity and technique-lift pack checks |
| `example_contracts.py` | public example validator facade |
| `examples/tos_examples.py` | Tree-of-Sophia example checks |
| `examples/recurrence_examples.py` | return-regrounding example checks |
| `examples/governance_examples.py` | KAG maturity governance example checks |
| `examples/federation_examples.py` | federation export and KAG export example checks |
| `examples/cross_source_examples.py` | cross-source node projection example checks |
| `examples/tiny_consumer_bundle_examples.py` | tiny consumer bundle example checks |
| `examples/exposure_review_examples.py` | counterpart federation exposure review example checks |
| `examples/bridge_examples.py` | bridge retrieval and bridge envelope example checks |
| `examples/counterpart_examples.py` | counterpart edge and counterpart consumer contract example checks |
| `examples/reasoning_handoff_examples.py` | reasoning-handoff example checks |
| `sibling_readiness.py` | optional source-owned export readiness checks |
| `orchestrator.py` | validate_kag orchestration facade |
| `orchestration/static_surfaces.py` | local, schema, route, and stress surface checks |
| `orchestration/manifests.py` | registry context and manifest contract checks |
| `orchestration/expected_payloads.py` | expected generated payload construction |
| `orchestration/generated_text.py` | generated text parity checks |
| `orchestration/generated_structures.py` | generated structure checks |
| `orchestration/examples.py` | public example checks |
| `orchestration/status.py` | success status output |
| `orchestration/runner.py` | top-level validation flow |

`docs/validation/validator_inventory.json` stores the machine-readable module
map. `config/validation_lanes.json` stores lane commands.

## Consequences

- Validator ownership is visible from the directory tree and inventory.
- Generation imports, expected data, and shared helpers have separate homes.
- Tests patch the module that reads the surface they override.
- Expected contract data has dedicated family modules behind an import facade.
- Manifest checks have dedicated manifest-family modules.
- Generated parity checks have dedicated projection-family modules.
- Public example checks have dedicated surface-family modules.
- Repo-wide validation orchestration has dedicated phase modules.
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
