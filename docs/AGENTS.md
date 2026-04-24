# AGENTS.md

## Guidance for `docs/`

`docs/` explains the KAG model, boundaries, source policy, bridge contracts, regrounding, proof expectations, quarantine, and consumer guides.

Docs may define derived-substrate doctrine, but source repositories still own authored meaning and `aoa-evals` owns proof claims.

Keep provenance, source refs, maturity stop-rules, quarantine posture, and regrounding requirements explicit.

When docs change a bridge or consumer path, check manifests, generated projections, schemas, examples, and the source owner named by the path.

Verify with:

```bash
python scripts/validate_kag.py
python scripts/validate_semantic_agents.py
```
