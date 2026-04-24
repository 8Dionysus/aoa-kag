# AGENTS.md

## Guidance for `scripts/`

`scripts/` contains generators, validators, and projection helpers for the KAG substrate.

Keep scripts deterministic, repo-relative, and provenance-preserving. Avoid hidden network calls, private corpora, local-only paths, and ambient credentials.

Builder changes must preserve source ownership: manifests and source refs guide derived output; generated projections do not become source truth.

Validator changes should catch provenance loss, source-ref drift, schema mismatch, quarantine bypass, and over-strong maturity claims.

Verify with:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
python scripts/validate_semantic_agents.py
```
