# AGENTS.md

## Guidance for `.agents/skills/`

`.agents/skills/` is an agent-facing companion surface for KAG-layer maintenance.

It may help agents inspect manifests, generated projections, bridge contracts, and source-policy docs, but it must not turn derived structures into source truth.

Source repositories keep authored meaning. `aoa-kag` keeps provenance-aware derived substrate built from those truths.

Do not hand-edit exported companion files before changing the owning source, manifest, schema, builder, or docs surface.

Keep everything public-safe: no private corpora, secrets, hidden embeddings, unreduced source dumps, or local-only paths.

Verify with:

```bash
python scripts/validate_kag.py
python scripts/validate_semantic_agents.py
```
