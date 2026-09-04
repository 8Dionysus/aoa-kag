# Promotion Candidate Contract

The active source config is
`config/promotion-candidate-registry.source.json`.

The active generated read model is
`generated/agon_kag_promotion_candidate_registry.min.json` inside this part.

## Payload Rules

- `registry_id` stays `agon.kag_promotion_candidates.registry.v1`.
- `review_stage` stays `kag_promotion_path`.
- `review_stage_label` stays `KAG Promotion Path`.
- `runtime_posture` stays `candidate_only`.
- Every item stays `candidate_only`, `non_authority`, `not_canon`, and
  `owner_retained`.
- Every item keeps stop-lines for no verdict authority, no durable scar, no rank
  or trust mutation, no direct ToS promotion, no KAG canonization, and no source
  truth replacement.

## Naming Rule

Historical `seed` and `wave` wording is not an active contract key here. Former
root names are preserved only through the [historical Agon index](https://github.com/8Dionysus/aoa-kag/blob/14ee1e33e43749d23c557b3ef526eca7edb36196/mechanics/agon/legacy/INDEX.md).
