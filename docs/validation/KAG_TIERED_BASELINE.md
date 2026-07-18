# Tiered KAG migration baseline

The authoritative migration baseline is the set of 24 immutable owner
`origin/main` refs recorded in
`docs/validation/kag_tiered_baseline.evidence.json`. Every ref exposes a valid
`aoa-repo-local-kag-family-manifest-v3`; together they contain 9,726 shards.

The rollout coverage snapshot embedded in `aoa-kag@47e7587` reported
283,751,563 tracked bytes. Directly summing the final owner manifests at their
recorded refs gives 284,890,209 bytes:

| Owner | Coverage snapshot | Owner manifest | Drift |
| --- | ---: | ---: | ---: |
| `abyss-stack` | 21,724,495 | 21,847,116 | +122,621 |
| `aoa-skills` | 8,477,033 | 9,427,032 | +949,999 |
| `aoa-stats` | 8,072,226 | 8,138,252 | +66,026 |
| **Total** | **283,751,563** | **284,890,209** | **+1,138,646** |

The central coverage file therefore captured earlier values for three owner
families even though their final `origin/main` manifests later carried larger
physical surfaces. The logical rollout facts remain 24/24 v3 and 9,726 shards,
but the live physical baseline is 84.90% of the non-growing 320 MiB ceiling
with 50,654,111 bytes of headroom.

This evidence also establishes why exact OS-wide measurements cannot be owned
by a self-indexed provider coverage file. During the tiered rollout, exact
owner-inclusive totals are produced from immutable owner releases by the
signed OS composition plane.
