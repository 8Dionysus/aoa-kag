# AGENTS.md

## Guidance for `tests/`

`tests/` protects KAG manifests, generated projections, bridge contracts, schemas, examples, decision indexes, and source-policy boundaries.

Read `docs/testing/TEST_TOPOLOGY.md` and
`docs/testing/test_inventory.json` before adding, moving, splitting, or folding
test files.

Tests should expose provenance loss, source-ref drift, projection overreach, quarantine bypass, schema mismatch, and maturity overclaiming.

Do not update expected generated projections without checking manifests, source refs, docs, and the owning source repo.

Keep fixtures public-safe. No private corpora, hidden embeddings, secrets, or unreduced source dumps.

Full validation command sequences live in `config/validation_lanes.json`.
Use the test runner or lane entrypoint:

```bash
python scripts/run_tests.py
python scripts/ci_gate.py --mode source-fast
```
