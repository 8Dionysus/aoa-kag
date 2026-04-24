# AGENTS.md

## Guidance for `config/`

`config/` holds build, projection, publication, and consumer-support inputs for KAG surfaces.

Config may shape derived projections, but it must not create new source meaning or bypass owner wait states.

Keep config explicit, provenance-aware, and reviewable. Avoid private corpora, hidden embeddings, secret tokens, and local-only assumptions.

When config changes generated projections, rebuild and inspect provenance, source refs, quarantine posture, and maturity governance.

Verify with:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
python scripts/validate_semantic_agents.py
```
