# Surface Growth Stop Rule

## Mechanic card

Status: active Growth Cycle part for KAG maturity and growth pause posture.

### Trigger

Use this part when KAG maturity governance, owner wait states, proof gaps,
pause rules, or `AOA-K-*` surface-growth posture changes.

### Local owns

The part owns the focused validator and tests that keep `aoa-kag` growth
paused unless owner evidence, proof posture, and consumer need justify a new
derived surface.

### Stronger owner split

This part's `manifests/` directory owns source-authored maturity controls.
This part's `generated/` directory owns the maturity read-model payloads.
This part's `schemas/` and `examples/` directories own its public contracts.
`aoa-evals` owns proof verdicts. Neighboring owner repositories own exports,
contracts, and acceptance signals KAG waits for.

### Inputs

Maturity governance docs, owner wait-state docs, proof expectation refs,
manifest controls, generated maturity pack, example payload, and decision
rationale.

### Outputs

Validation result and source-route failure messages. No generated payload is
written by this part.

### Must not claim

Universal progression score, owner acceptance, proof verdict, automatic new
surface creation, release approval, or hidden scheduler authority.

### Next route

Change the manifest or source docs first, regenerate the maturity pack when
needed, then run this part's validator. Repo-wide generated parity remains a
compatibility/read-model check until the builder itself is split.
