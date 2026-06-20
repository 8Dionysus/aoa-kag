# Owner Downlink

This part owns KAG-to-owner downlink and adoption-consent packets.

## Owns

- adoption boundary, adoption dossier, pattern downlink, and owner signal docs;
- `kag_adoption_boundary`, `kag_pattern_adoption_dossier`,
  `kag_pattern_downlink`, and `kag_to_owner_signal` schema/example contracts;
- focused tests for owner-downlink packet shape.

## Does Not Own

Owner consent itself, owner-local adoption, runtime mutation, or release
execution.
