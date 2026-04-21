# Recurrence projection inputs for KAG

`aoa-kag` may consume recurrence projections as regrounding inputs.

Allowed generated candidates:

- `generated/recurrence_regrounding_pack.min.json`
- `generated/donor_refresh_obligations.min.json`

The projection should point toward stronger owner/source refs when derived substrate confidence weakens. It must not turn KAG into source truth, proof authority, routing owner, memory owner, canon author, or hidden graph sovereign.
