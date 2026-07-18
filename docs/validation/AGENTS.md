# AGENTS.md

## Applies to

`docs/validation/`.

## Role

This directory maps validation lanes, command authority, validator posture,
validator inventory, script inventory, lane posture, and failure routes for
`aoa-kag`.

## Inputs

- `config/validation_lanes.json`
- `scripts/validation_lanes.py`
- `scripts/ci_gate.py`
- `docs/validation/VALIDATOR_TOPOLOGY.md`
- `docs/validation/validator_inventory.json`
- `docs/validation/SCRIPT_TOPOLOGY.md`
- `docs/validation/script_inventory.json`
- `docs/validation/kag_tiered_baseline.evidence.json`

## Routes

| Surface | Function |
| --- | --- |
| `config/validation_lanes.json` | command authority |
| `VALIDATOR_TOPOLOGY.md` | validator family map |
| `validator_inventory.json` | validator module inventory |
| `SCRIPT_TOPOLOGY.md` | script family map |
| `script_inventory.json` | script surface inventory |
| `KAG_TIERED_BASELINE.md` | human-readable immutable v3 baseline and drift explanation |
| `kag_tiered_baseline.evidence.json` | schema-checked 24-owner baseline evidence packet |

## Validation

```bash
python -m unittest tests.test_validation_command_authority tests.test_script_topology tests.test_validator_module_topology
python scripts/ci_gate.py --mode source-fast
```

For release-visible lane changes:

```bash
python scripts/release_check.py
```

## Closeout

Report changed lane ids, inventories, focused checks, broader lane checks, and
the next owner route.
