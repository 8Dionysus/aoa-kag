# AGENTS.md

## Guidance for `scripts/`

`scripts/` contains generators, validators, decision-index helpers, and projection helpers for the KAG substrate.

Read `docs/validation/COMMAND_AUTHORITY.md`,
`docs/validation/SCRIPT_TOPOLOGY.md`, and
`docs/validation/script_inventory.json` before adding, moving, or changing a
script's lane, owner, or side-effect posture.

Keep scripts deterministic, repo-relative, and provenance-preserving. Avoid hidden network calls, private corpora, local-only paths, and ambient credentials.

Builder changes must preserve source ownership: manifests and source refs guide derived output; generated projections do not become source truth.

Validator changes should catch provenance loss, source-ref drift, schema mismatch, quarantine bypass, and over-strong maturity claims.

Full validation command sequences live in `config/validation_lanes.json`.
Use lane entrypoints instead of copying release sequences:

```bash
python scripts/ci_gate.py --mode source-fast
python scripts/ci_gate.py --mode generated
```
