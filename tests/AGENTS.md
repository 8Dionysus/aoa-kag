# AGENTS.md

## Guidance for `tests/`

`tests/` protects KAG manifests, generated projections, bridge contracts, schemas, examples, and source-policy boundaries.

Tests should expose provenance loss, source-ref drift, projection overreach, quarantine bypass, schema mismatch, and maturity overclaiming.

Do not update expected generated projections without checking manifests, source refs, docs, and the owning source repo.

Keep fixtures public-safe. No private corpora, hidden embeddings, secrets, or unreduced source dumps.

Verify with:

```bash
python -m pytest -q tests
python scripts/validate_semantic_agents.py
```
