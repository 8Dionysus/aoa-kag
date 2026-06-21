# Reasoning Handoff

## Mechanic card

Status: active Checkpoint part for KAG reasoning handoff guardrails.

### Trigger

Use this part when reasoning handoff docs, generated handoff packs,
counterpart contract refs, owner-state guardrails, or handoff example posture
changes.

### Local owns

The part owns focused validation and tests that keep reasoning handoff packets
as derived guide-to-source surfaces instead of owner state.

### Stronger owner split

`aoa-playbooks` owns scenario choreography. `aoa-evals` owns artifact verdicts
and proof. `aoa-memo` owns checkpoint-to-memory contracts and durable memory.
`aoa-routing` owns live re-entry. Runtime owners own execution state.

### Inputs

Reasoning handoff docs, reasoning handoff manifest, generated handoff pack,
counterpart consumer contract refs, example guardrail, and stronger owner refs.

### Outputs

Part-local generated handoff pack plus validation result and source-route
failure messages.

### Must not claim

Durable state ownership, memory writeback, proof verdict, route activation,
runtime restart, direct canon authorship, or hidden graph sovereignty.

### Next route

Change the reasoning handoff source doc or manifest first, regenerate when
needed, then run this part's validator. Repo-wide generation and validation
remain compatibility entrypoints that cross-check the part-local surfaces.
