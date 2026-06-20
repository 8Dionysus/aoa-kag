# Checkpoint

This package maps the common AoA Checkpoint mechanic into the KAG layer.

## Mechanic card

Status: mapped common-center mechanic; no active part directories yet.

### Trigger

Use this package when KAG carries reasoning handoff, restart, return, or
checkpoint-like references that must remain weaker than owner state.

### Local owns

`aoa-kag` owns derived handoff payload shape, source refs, bounded output
contracts, and return routes to owner repositories.

### Stronger owner split

`Agents-of-Abyss` owns common checkpoint law. `aoa-memo` owns memory writeback.
`aoa-evals` owns proof. `aoa-routing` owns live re-entry. Source owners own
state meaning.

### Inputs

Reasoning handoff manifests, checkpoint-adjacent owner refs, memo/eval refs,
and generated return packs.

### Outputs

Bounded reasoning handoff packs, owner-return hints, and validation-backed
stop-lines.

### Must not claim

Durable state ownership, memory write, proof verdict, route activation, runtime
restart, or source mutation.

### Next route

Start with `PARTS.md`. Create a part only when one checkpoint-shaped handoff
family needs its own local contract and validation.
