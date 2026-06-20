# Agon Parts

`mechanics/agon/parts/` holds active KAG-side Agon sub-mechanics.

Use a part when a payload family has its own source config, generated registry
contract, focused builder, validator, test, and stop-lines. Do not use parts as
topic folders or future parking space.

## Active parts

| Part | Role | Generated output |
| --- | --- | --- |
| `promotion-candidates` | KAG-side candidate registry for Agon-derived pattern families. | `generated/agon_kag_promotion_candidate_registry.min.json` |
| `sophian-threshold-packets` | Candidate-only packet registry for possible Sophian threshold review. | `generated/agon_sophian_kag_packet_registry.min.json` |

Generated outputs stay root published read models. Part-local configs, scripts,
tests, and route docs own the operation that builds and validates them.
