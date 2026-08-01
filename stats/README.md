# aoa-kag local stats port

This directory exposes statistical questions whose domain meaning belongs to
`aoa-kag`. It uses the shared `aoa-stats` measurement grammar without moving
KAG source ownership or generated-evidence authority into the central organ.

## Current reference measurement

| Measurement | Question | Reference value |
| --- | --- | --- |
| `aoa-kag/repo-self-family-pass-ratio` | What fraction of inventoried owners pass the complete canonical repo-self index-family check? | `10 / 24` at source revision `6bb1f5770ca608b14ddec858011e5cf7cd6b14b1` |
| `aoa-kag/owner-local-pr-workflow-wall-time` | What wall time do real hosted owner-local PR workflows require while both local proofs remain blocking? | `198 s` median, `n=1`, workflow blob `41372d185b9ca250b110faf5421d975db8d0c805` |

The reference packet is a census of the owner rows reported by
`generated/repo_local_kag_coverage.min.json`. The coverage read model and its
source contracts remain stronger than this packet.

## Authority

The ratio reports only the current complete-family validation classification.
It does not measure authored knowledge quality, retrieval quality, proof
strength, or live graph readiness. `aoa-stats` may validate and compose the
packet without redefining that ceiling.

The owner-local timing measurement admits only first-attempt hosted PR runs at
one exact workflow source revision. Every admitted run must report the
`owner-local` route, successful source-fast and owner-family proofs,
`full-audit=correctly-not-required`, and a successful typed summary. Failed,
cancelled, rerun, high-impact, mixed, unknown, malformed, stale, unavailable,
or otherwise unprovable runs are excluded rather than converted into a fast
sample. Its eventual distribution is performance telemetry, not proof of
validator strength, future performance, causality, runner cost, or KAG
equivalence.

For this measurement, workflow wall time starts at the GitHub Actions run
`created_at` timestamp and ends when the successful typed `Repo Validation`
job completes. Checkout time is the sum of the eight pinned donor checkout
steps; owner-family and source-fast time use their named step intervals. The
reference packet links each admitted public run and retains the exact workflow
blob identity so later source-only observation updates remain comparable.

## Surfaces

- `port.manifest.json` declares the local question, measurement contract, and
  export.
- `packets/repo-self-family-pass-ratio.reference.json` records the
  evidence-linked reference observation.
- `generated/repo_local_kag_coverage.min.json` is the immediate derived
  evidence route; KAG manifests, schemas, builders, and owner sources remain
  stronger.
