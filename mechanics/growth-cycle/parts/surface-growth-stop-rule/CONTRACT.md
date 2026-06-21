# Surface Growth Stop Rule Contract

This part keeps KAG growth posture explicit enough to stop.

It requires:

- net-new `AOA-K-*` growth to remain paused by default;
- `AOA-K-0008` to stay blocked while counterpart activation remains
  planned-contract-only;
- owner wait states to name outward owner dependencies instead of solving them
  inside KAG;
- bounded output contracts to forbid source replacement, routing ownership,
  memory truth ownership, proof ownership, and quarantine shortcuts;
- recovery posture to route through existing regrounding and antifragility
  surfaces.

It forbids:

- treating proof anchors as proof verdicts;
- treating registry visibility as owner acceptance;
- promoting a planned surface by generated-pack drift;
- using active legacy `seed`, `wave`, `stub`, or `landing` naming as a growth
  stage.
