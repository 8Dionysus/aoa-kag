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
| `projection_builder` | generated/read-model writers and generation entrypoints |
| `projection_validator_facade` | generated/read-model parity import surface |
| `projection_validator` | generated/read-model parity checks |
| `example_validator_facade` | public example validator import surface |
| `example_validator` | public example payload checks |
| `decision_index_builder` | decision lookup index writer |
| `artifact_bundle_validator` | release artifact bundle check |
| `provider_checkout_tool` | pinned provider checkout materialization |
| `skill_local_contract_tool` | exported skill companion helper |
| `part_local_script_runner` | discovered part-local builder and validator checks |
| `lane_executor`, `lane_loader`, `release_entrypoint`, `test_runner` | lane, release, and test execution |
| `script_route_card` | local route card |
| `projection_helper` | shared generation package modules and compatibility helpers |

## Function Groups

| Function Group | Families |
| --- | --- |
| command authority / lane runners | `lane_executor`, `lane_loader`, `release_entrypoint`, `test_runner`, `part_local_script_runner`, `provider_checkout_tool` |
| generation builders | `projection_builder`, `projection_helper`, `decision_index_builder`, `validator_generation_port` |
| validators | `source_validator`, `validator_entrypoint`, `validator_adapter`, `validator_expected_contracts_facade`, `validator_expected_contracts`, `validator_shared`, `manifest_validator_facade`, `manifest_validator`, `validator_orchestrator_facade`, `validator_orchestration`, `projection_validator_facade`, `projection_validator`, `example_validator_facade`, `example_validator` |
| topology and route inventory | `script_route_card` |
| release / artifact tooling | `artifact_bundle_validator` |
| skill companion helpers | `skill_local_contract_tool` |

## Root Scripts

Root `scripts/*.py` own repo-wide builders, validators, lane execution,
release checks, and test discovery.

`scripts/validate_kag.py` is the entrypoint. The implementation map lives in
`docs/validation/validator_inventory.json`.

`scripts/validators/local_kag_subtree.py` checks the repo-local KAG subtree
contract, example packet, and OS Abyss readiness matrix.

`scripts/generate_kag.py` is the KAG generated-output entrypoint; its
`--check` mode compares generated/read-model parity without writing files.
`scripts/kag_generation.py` is the compatibility facade for existing imports.
The implementation modules live in `scripts/generation/`.

`scripts/generate_repo_local_kag_index.py` builds the repo-local
source/entity/artifact/event index family from the current repository's source,
document, mechanics, command, schema, generated, and receipt surfaces.

`scripts/generate_repo_local_kag_coverage.py` builds
`generated/repo_local_kag_coverage.json` and the minified companion from live
OS Abyss provider roots materialized from the pinned provider registry.

Both repo-local builders support `--check` for parity without writing files.

`scripts/run_part_local_checks.py` discovers active
`mechanics/<package>/parts/<part>/scripts/build_*.py` and `validate_*.py`
surfaces, runs builders with `--check`, and runs validators directly from the
`source-fast` lane.

`scripts/sync_provider_checkouts.py` materializes pinned provider roots from
`manifests/provider_registry.json` under `.deps/` and can run a command with the
same provider-root environment used by repository validation.

## Generation Package

Generation implementation lives under:

```text
scripts/generation/
```

`scripts/generation/AGENTS.md` is the local route card. The package keeps
context, shared helpers, source-reference loading, domain builders, and output
writing separated while preserving the public compatibility surface exported by
`scripts/kag_generation.py`.

## Part-Local Scripts

Mechanic-owned scripts live under:

```text
mechanics/<package>/parts/<part>/scripts/
```

Part-local tests and `scripts/run_tests.py` cover active part scripts.

## Validation

Use `docs/validation/COMMAND_AUTHORITY.md` and the nearest `AGENTS.md` for executable validation commands.
