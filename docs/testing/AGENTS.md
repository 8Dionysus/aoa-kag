# AGENTS.md

## Applies to

This card applies to `docs/testing/` and all descendants.

## Role

`docs/testing/` owns the test-home topology map and machine-readable test
inventory for `aoa-kag`.

It documents which boundary each test protects and which execution authority
covers it. It does not store release command sequences.

## Read before editing

Read root `AGENTS.md`, `tests/AGENTS.md`, `docs/testing/TEST_TOPOLOGY.md`,
`docs/testing/test_inventory.json`, `scripts/run_tests.py`, and
`config/validation_lanes.json`.

## Boundaries

- Test inventory entries name focused targets, not executable command
  sequences.
- Root unittest discovery belongs to `scripts/run_tests.py`.
- Release command order belongs in `config/validation_lanes.json`.
- Future mechanic part-local tests should not be added to root discovery until
  a package-local route and lane exist.

## Validation

Run:

```bash
python -m unittest tests.test_test_topology
python scripts/ci_gate.py --mode source-fast
```

## Closeout

Report added, moved, split, folded, or removed test homes; inventory updates;
focused checks run; skipped checks; and the owner route for any failure.
