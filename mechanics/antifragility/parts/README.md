# Antifragility Parts

`mechanics/antifragility/parts/` holds active KAG-side degraded-mode
sub-mechanics.

| Part | Role | Contract packets |
| --- | --- | --- |
| `projection-health` | Projection health receipts and source-first stress posture. | part-local `schemas/`, `examples/`, `docs/`, and `tests/` |
| `projection-quarantine` | Quarantine rule set for derived surfaces unsafe to expand. | part-local `docs/` and `tests/` |
| `retrieval-outage-regrounding` | Retrieval-outage recovery tickets and source-first return route. | part-local `schemas/`, `examples/`, `docs/`, and `tests/` |

Root schemas and examples should not be used for active Antifragility part
contracts once the owning part is active.
