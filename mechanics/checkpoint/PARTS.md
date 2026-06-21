# Checkpoint Parts

This file is the active map for KAG checkpoint part pressure.

## What a part means here

A part is a bounded carry or handoff route with source refs, owner refs,
allowed output, stop-lines, and validation.

## Candidate part pressure

| Candidate part | Use when | Current route |
| --- | --- | --- |
| `reasoning-handoff` | KAG packages multi-source handoff guidance. | reasoning handoff manifest, schema, generated pack, docs, examples, tests. |
| `owner-return-packet` | a derived route must point back to owner state before mutation. | return regrounding and owner refs in generated packs. |

## Active part routes

| Active part | Owns | Validation |
| --- | --- | --- |
| `reasoning-handoff` | focused reasoning handoff guardrail, counterpart contract ref, and owner-state stop-line checks | `parts/reasoning-handoff/VALIDATION.md` |

Do not create another `parts/<part>/` until moving the owning artifacts would
make the handoff safer and easier to validate than the current root doc,
manifest, generated, schema, example, or compatibility homes.
