# Sophian Threshold Packet Contract

The active source config is
`config/sophian-threshold-packet-registry.source.json`.

The active generated read model is
`generated/agon_sophian_kag_packet_registry.min.json` inside this part.

## Payload Rules

- `registry_id` stays `agon.sophian_kag_packet.registry.v1`.
- `review_stage` stays `sophian_threshold`.
- `review_stage_label` stays `Sophian Threshold`.
- `runtime_posture` stays `candidate_only`.
- Every item stays candidate-only and requires review.
- Every item keeps false flags for ToS canonization, direct ToS writes, and
  canon writes.
- Every item keeps forbidden effects for no verdict authority, no durable scar,
  no rank or trust mutation, no automatic canonization, no KAG-as-canon, and no
  hidden SDK write.

## Naming Rule

Historical `seed`, `wave`, and landing wording is not an active contract key
here. Former root names are preserved only through
`mechanics/agon/legacy/INDEX.md`.
