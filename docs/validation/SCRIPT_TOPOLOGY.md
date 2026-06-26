# Script Topology

Scripts in `aoa-kag` provide lane execution, validation, generation, release
checks, and part-local contract tools.

The machine-readable script map is
`docs/validation/script_inventory.json`.

## Inventory Fields

- `path`
- `family`
- `organ_lane`
- `owner_surface`
- `source_truth`
- `reads`
- `writes`
- `side_effects`
- `validation_lane`
- `ci_inclusion`
- `test_target`
- `disposition`

## Families

| Family | Function |
| --- | --- |
| `source_validator` | source, route, decision, mechanics, and source-ref checks |
| `validator_entrypoint` | repo-wide validation CLI |
| `validator_adapter` | validator package import surface |
| `validator_generation_port` | KAG generation constants and payload builders |
| `validator_expected_contracts_facade` | expected contract data import surface |
| `validator_expected_contracts` | expected paths, allowed values, and payload contract data |
| `validator_shared` | shared validator helpers |
| `manifest_validator_facade` | manifest contract import surface |
| `manifest_validator` | manifest source-input and output contract checks |
| `validator_orchestrator_facade` | validate_kag orchestration import surface |
| `validator_orchestration` | validate_kag phase execution |
| `projection_builder` | generated/read-model writers |
| `projection_validator_facade` | generated/read-model parity import surface |
| `projection_validator` | generated/read-model parity checks |
| `example_validator_facade` | public example validator import surface |
| `example_validator` | public example payload checks |
| `decision_index_builder` | decision lookup index writer |
| `artifact_bundle_validator` | release artifact bundle check |
| `skill_local_contract_tool` | exported skill companion helper |
| `lane_executor`, `lane_loader`, `release_entrypoint`, `test_runner` | lane, release, and test execution |
| `script_route_card` | local route card |
| `projection_helper` | shared generation helper |

## Root Scripts

Root `scripts/*.py` own repo-wide builders, validators, lane execution,
release checks, and test discovery.

`scripts/validate_kag.py` is the entrypoint. The implementation map lives in
`docs/validation/validator_inventory.json`.

## Part-Local Scripts

Mechanic-owned scripts live under:

```text
mechanics/<package>/parts/<part>/scripts/
```

Part-local tests and `scripts/run_tests.py` cover active part scripts.

## Validation

```bash
python -m unittest tests.test_script_topology
python scripts/ci_gate.py --mode source-fast
```
