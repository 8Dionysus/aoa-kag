# Reasoning Handoff Pack

This document records the first multi-source generated reasoning handoff pack in
`aoa-kag`.

It keeps `AOA-P-0008` and `AOA-P-0009` legible as bounded runtime-to-KAG
handoff capsules without promoting `aoa-kag` into a routing, memory, eval, or
canon owner.

## Purpose

This wave is intentionally narrow:

- materialize a reviewable `reasoning_handoff_pack`
- keep `AOA-K-0007` and `AOA-K-0008` planned rather than silently activating
  them
- normalize handoff metadata across playbooks, eval hooks, memo contracts, and
  KAG guardrails
- preserve guidance-to-source posture instead of inventing a new owner layer

That planned posture is intentional, not a missing implementation step:

- no downstream consumer contract depends on `AOA-K-0007` or `AOA-K-0008` yet
- federation exposure remains deferred
- the current job is to make the bridge readable before promotion is considered

## Source inputs

The current pack reads bounded donor surfaces from:

- `docs/REASONING_HANDOFF.md` in `aoa-kag`
- `PLAYBOOK.md` for `AOA-P-0008` and `AOA-P-0009` in `aoa-playbooks`
- `artifact_to_verdict_hook` fixtures and schema in `aoa-evals`
- `checkpoint_to_memory_contract`, `inquiry_checkpoint`, and witness trace
  surfaces in `aoa-memo`
- runtime artifact schemas in `aoa-agents`

Those inputs are declared in `manifests/reasoning_handoff_pack.json`.

## What the pack materializes

For each reference scenario, the generated pack keeps:

- one `playbook_ref` back to the scenario-owned source surface
- a role-aware `artifact_spine` with verification, continuity, supporting, and
  optional trace surfaces kept distinct
- an `eval_bridge` that names bundle refs, verification surface, trace
  sidecars, and current report expectation
- a `memo_bridge` that keeps writeback targets and memo contract refs explicit
- `authoritative_refs`, `return_contract`, and `boundary_guardrails` that
  preserve source-first ownership

## What the pack does not do

This wave does not:

- activate `AOA-K-0007` or `AOA-K-0008`
- move routing policy into `aoa-kag`
- turn runtime artifacts into memo truth
- turn eval bridge metadata into verdict ownership
- turn canon-facing deltas into canon authorship
- inline example payload bodies as a replacement for stronger source surfaces

## Regeneration posture

Use:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
```

If the donor repositories are not checked out beside `aoa-kag`, point the
scripts at them with:

- `AOA_PLAYBOOKS_ROOT`
- `AOA_EVALS_ROOT`
- `AOA_MEMO_ROOT`
- `AOA_AGENTS_ROOT`
