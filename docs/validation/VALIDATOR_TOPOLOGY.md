# Validator Topology

Validators in `aoa-kag` check provenance-aware KAG contracts: source refs,
manifests, schemas, examples, generated/read-model parity, decision records,
route cards, and mechanics surfaces.

## Lane Map

| Lane | Function |
| --- | --- |
| `source-fast` | read-only source and topology integrity |
| `generated` | generated/read-model parity |
| `release` | release-prep validation |
| `compatibility-canary` | floating sibling compatibility check |
| `advisory` | route inventory for later KAG pressure |

Lane command storage lives in `config/validation_lanes.json`; executable lane
entries are listed in `docs/validation/COMMAND_AUTHORITY.md`.

## validate_kag Shape

`scripts/validate_kag.py` is the repo-wide validation entrypoint. Validator
implementation lives in `scripts/validators/`.

| Module | Function |
| --- | --- |
| `scripts/validators/generation.py` | KAG generation constants and payload builders from the generation package/facade |
| `scripts/validators/expected_contracts.py` | expected contract data facade |
| `scripts/validators/expected/core.py` | repo roots, schema/example paths, allowed values, and shared path sets |
| `scripts/validators/expected/registry_contracts.py` | registry boundary, counterpart, provenance, and guardrail expectations |
| `scripts/validators/expected/governance_contracts.py` | KAG maturity governance expectations |
| `scripts/validators/expected/recurrence_contracts.py` | return-regrounding expectations |
| `scripts/validators/expected/technique_contracts.py` | technique-lift expectations |
| `scripts/validators/expected/tos_contracts.py` | Tree-of-Sophia route, chunk, retrieval, and adjunct expectations |
| `scripts/validators/expected/handoff_contracts.py` | reasoning-handoff expectations |
| `scripts/validators/expected/federation_contracts.py` | federation spine, export registry, and memo donor expectations |
| `scripts/validators/expected/cross_source_contracts.py` | cross-source node projection expectations |
| `scripts/validators/expected/consumer_contracts.py` | tiny consumer bundle and counterpart exposure review expectations |
| `scripts/validators/expected/registry_surface_inputs.py` | registry surface source-input expectations |
| `scripts/validators/expected/docs_contracts.py` | markdown/date/root/snippet expectations |
| `scripts/validators/common.py` | shared validator errors, file readers, markdown helpers, schema helpers |
| `scripts/validators/source_refs.py` | source reference resolution |
| `scripts/validators/schema_surfaces.py` | JSON schema checks |
| `scripts/validators/local_contracts.py` | local route, mechanics skeleton, questbook, antifragility, and ToS tiny-entry checks |
| `scripts/validators/local_kag_subtree.py` | repo-local KAG subtree schema, example, readiness, and record-link checks |
| `scripts/validators/repo_local_kag_index.py` | repo-local source surface index schema, generated index parity, and OS-wide coverage checks |
| `scripts/validators/manifest_contracts.py` | manifest contract facade |
| `scripts/validators/manifests/technique_lift.py` | technique-lift manifest checks |
| `scripts/validators/manifests/tos_text_chunk_map.py` | ToS text chunk map manifest checks |
| `scripts/validators/manifests/tos_retrieval_axis.py` | ToS retrieval axis manifest checks |
| `scripts/validators/manifests/tos_zarathustra_route.py` | ToS Zarathustra route manifest checks |
| `scripts/validators/manifests/tos_zarathustra_route_retrieval.py` | ToS Zarathustra route retrieval manifest checks |
| `scripts/validators/manifests/reasoning_handoff.py` | reasoning-handoff manifest checks |
| `scripts/validators/manifests/return_regrounding.py` | return-regrounding manifest checks |
| `scripts/validators/manifests/governance.py` | KAG maturity governance manifest checks |
| `scripts/validators/manifests/source_owned_export.py` | source-owned export dependency manifest checks |
| `scripts/validators/manifests/federation_export_registry.py` | federation export registry manifest checks |
| `scripts/validators/manifests/federation_spine.py` | federation spine manifest checks |
| `scripts/validators/manifests/cross_source_node_projection.py` | cross-source node projection manifest checks |
| `scripts/validators/manifests/tiny_consumer_bundle.py` | tiny consumer bundle manifest checks |
| `scripts/validators/manifests/counterpart_federation_exposure_review.py` | counterpart federation exposure review manifest checks |
| `scripts/validators/projection_parity.py` | generated/read-model parity facade |
| `scripts/validators/projection/registry.py` | registry payload and special registry surface checks |
| `scripts/validators/projection/tos_text_chunk_map.py` | ToS text chunk map pack checks |
| `scripts/validators/projection/tos_retrieval_axis.py` | ToS retrieval axis pack checks |
| `scripts/validators/projection/tos_zarathustra_route.py` | ToS Zarathustra route pack checks |
| `scripts/validators/projection/tos_zarathustra_route_retrieval.py` | ToS Zarathustra route retrieval pack checks |
| `scripts/validators/projection/reasoning_handoff.py` | reasoning-handoff pack checks |
| `scripts/validators/projection/return_regrounding.py` | return-regrounding pack checks |
| `scripts/validators/projection/governance.py` | KAG maturity governance pack checks |
| `scripts/validators/projection/federation_export_registry.py` | federation export registry pack checks |
| `scripts/validators/projection/federation_spine.py` | federation spine pack checks |
| `scripts/validators/projection/cross_source_node_projection.py` | cross-source node projection pack checks |
| `scripts/validators/projection/tiny_consumer_bundle.py` | tiny consumer bundle pack checks |
| `scripts/validators/projection/counterpart_federation_exposure_review.py` | counterpart federation exposure review pack checks |
| `scripts/validators/projection/technique.py` | generated text parity and technique-lift pack checks |
| `scripts/validators/example_contracts.py` | public example validator facade |
| `scripts/validators/examples/tos_examples.py` | Tree-of-Sophia example checks |
| `scripts/validators/examples/recurrence_examples.py` | return-regrounding example checks |
| `scripts/validators/examples/governance_examples.py` | KAG maturity governance example checks |
| `scripts/validators/examples/federation_examples.py` | federation export and KAG export example checks |
| `scripts/validators/examples/cross_source_examples.py` | cross-source node projection example checks |
| `scripts/validators/examples/tiny_consumer_bundle_examples.py` | tiny consumer bundle example checks |
| `scripts/validators/examples/exposure_review_examples.py` | counterpart federation exposure review example checks |
| `scripts/validators/examples/bridge_examples.py` | bridge retrieval and bridge envelope example checks |
| `scripts/validators/examples/counterpart_examples.py` | counterpart edge and counterpart consumer contract example checks |
| `scripts/validators/examples/reasoning_handoff_examples.py` | reasoning-handoff example checks |
| `scripts/validators/sibling_readiness.py` | optional source-owned export readiness checks |
| `scripts/validators/orchestrator.py` | validate_kag orchestration facade |
| `scripts/validators/orchestration/static_surfaces.py` | local, schema, route, and stress surface checks |
| `scripts/validators/orchestration/manifests.py` | registry context and manifest contract checks |
| `scripts/validators/orchestration/expected_payloads.py` | expected generated payload construction |
| `scripts/validators/orchestration/generated_text.py` | generated text parity checks |
| `scripts/validators/orchestration/generated_structures.py` | generated structure checks |
| `scripts/validators/orchestration/examples.py` | public example checks |
| `scripts/validators/orchestration/status.py` | success status output |
| `scripts/validators/orchestration/runner.py` | top-level validation flow |

The machine-readable module map is
`docs/validation/validator_inventory.json`.

## Mechanics Validators

Mechanic-owned validators stay with their part:

| Part | Validator |
| --- | --- |
| source-owned export | `mechanics/boundary-bridge/parts/source-owned-export/scripts/validate_source_owned_export.py` |
| reasoning handoff | `mechanics/checkpoint/parts/reasoning-handoff/scripts/validate_reasoning_handoff.py` |
| surface-growth stop-rule | `mechanics/growth-cycle/parts/surface-growth-stop-rule/scripts/validate_surface_growth_stop_rule.py` |
| quest store | `mechanics/questbook/parts/quest-store/scripts/validate_quest_store.py` |
| return regrounding | `mechanics/recurrence/parts/return-regrounding/scripts/validate_return_regrounding.py` |

`scripts/run_tests.py` covers root tests and active mechanics part tests.
