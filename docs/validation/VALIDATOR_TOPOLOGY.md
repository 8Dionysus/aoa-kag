# Validator Topology

Validators in `aoa-kag` check provenance-aware KAG contracts: source refs,
manifests, schemas, examples, generated/read-model parity, decision records,
route cards, and mechanics surfaces.

## Lane Map

| Lane | Function | Entry |
| --- | --- | --- |
| `source-fast` | read-only source and topology integrity | `python scripts/ci_gate.py --mode source-fast` |
| `generated` | generated/read-model parity | `python scripts/ci_gate.py --mode generated` |
| `release` | release-prep validation | `python scripts/release_check.py` |
| `compatibility-canary` | floating sibling compatibility check | `python scripts/ci_gate.py --mode compatibility-canary` |
| `advisory` | route inventory for later KAG pressure | `python scripts/ci_gate.py --mode advisory` |

Lane command storage lives in `config/validation_lanes.json`.

## validate_kag Shape

`scripts/validate_kag.py` is the repo-wide validation entrypoint. Validator
implementation lives in `scripts/validators/`.

| Module | Function |
| --- | --- |
| `scripts/validators/generation.py` | KAG generation constants and payload builders |
| `scripts/validators/expected_contracts.py` | expected paths, allowed values, and payload contract data |
| `scripts/validators/common.py` | shared validator errors, file readers, markdown helpers, schema helpers |
| `scripts/validators/source_refs.py` | source reference resolution |
| `scripts/validators/schema_surfaces.py` | JSON schema checks |
| `scripts/validators/local_contracts.py` | local route, mechanics skeleton, questbook, antifragility, and ToS tiny-entry checks |
| `scripts/validators/manifest_contracts.py` | manifest source-input and output contract checks |
| `scripts/validators/projection_parity.py` | generated/read-model parity checks |
| `scripts/validators/example_contracts.py` | public example payload checks |
| `scripts/validators/sibling_readiness.py` | optional source-owned export readiness checks |
| `scripts/validators/orchestrator.py` | call order and status output |

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
