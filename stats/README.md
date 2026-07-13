# aoa-kag local stats port

This directory exposes statistical questions whose domain meaning belongs to
`aoa-kag`. It uses the shared `aoa-stats` measurement grammar without moving
KAG source ownership or generated-evidence authority into the central organ.

## Current reference measurement

| Measurement | Question | Reference value |
| --- | --- | --- |
| `aoa-kag/repo-self-family-pass-ratio` | What fraction of inventoried owners pass the complete canonical repo-self index-family check? | `10 / 24` at source revision `6bb1f5770ca608b14ddec858011e5cf7cd6b14b1` |

The reference packet is a census of the owner rows reported by
`generated/repo_local_kag_coverage.min.json`. The coverage read model and its
source contracts remain stronger than this packet.

## Authority

The ratio reports only the current complete-family validation classification.
It does not measure authored knowledge quality, retrieval quality, proof
strength, or live graph readiness. `aoa-stats` may validate and compose the
packet without redefining that ceiling.

## Surfaces

- `port.manifest.json` declares the local question, measurement contract, and
  export.
- `packets/repo-self-family-pass-ratio.reference.json` records the
  evidence-linked reference observation.
- `generated/repo_local_kag_coverage.min.json` is the immediate derived
  evidence route; KAG manifests, schemas, builders, and owner sources remain
  stronger.
