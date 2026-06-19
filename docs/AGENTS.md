# AGENTS.md

## Guidance for `docs/`

`docs/` explains the KAG model, boundaries, source policy, bridge contracts, regrounding, proof expectations, quarantine, decision rationale, and consumer guides.

Docs may define derived-substrate doctrine, but source repositories still own authored meaning and `aoa-evals` owns proof claims.

Keep provenance, source refs, maturity stop-rules, quarantine posture, and regrounding requirements explicit.

When docs change a bridge or consumer path, check manifests, generated projections, schemas, examples, and the source owner named by the path.

Full validation command sequences live in `config/validation_lanes.json`.
Verify with the nearest lane:

```bash
python scripts/ci_gate.py --mode source-fast
```
