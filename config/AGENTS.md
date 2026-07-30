# AGENTS.md

## Guidance for `config/`

`config/` holds build, projection, publication, and consumer-support inputs for KAG surfaces.

Config may shape derived projections, but it must not create new source meaning or bypass owner wait states.

Keep config explicit, provenance-aware, and reviewable. Avoid private corpora, hidden embeddings, secret tokens, and local-only assumptions.

When config changes generated projections, rebuild and inspect provenance, source refs, quarantine posture, and maturity governance.

Full validation command sequences live in `config/validation_lanes.json`.
The same manifest owns fail-closed impact rules. `source-fast` and the self
owner-family proof remain always required; new or uncertain surfaces default
to the full audit instead of widening the owner-local allowlist implicitly.
It also owns the bounded OS-wide owner-worker policy. Keep registry-order
assembly, a one-worker sequential comparison route, and a hard upper bound;
worker overrides must not bypass owner completeness or packet admission.
Verify with the generated lane, then the source-fast lane:

```bash
python scripts/ci_gate.py --mode generated
python scripts/ci_gate.py --mode source-fast
```
