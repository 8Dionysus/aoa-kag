# Counterpart Edge

## Mechanic card

Status: active Boundary Bridge part for planned counterpart-edge contracts.

### Trigger

Use this part when counterpart consumer contracts, counterpart edge grammar,
planned `AOA-K-0008` examples, or counterpart-ref guardrails change.

### Local owns

The part owns KAG-local counterpart contract docs, schemas, examples, and
validation hooks while keeping `AOA-K-0008` planned.

### Stronger owner split

`Tree-of-Sophia` owns conceptual origin. Source AoA repositories own
operational meaning. `aoa-routing` owns live routing. `aoa-evals` owns proof.
This part owns only derived counterpart grammar and consumer-facing contract
refs.

### Inputs

Counterpart docs, schemas, examples, registry planned status, reasoning
handoff guardrail refs, and exposure-review refs.

### Outputs

Contract/example refs that may be returned by current consumers without
claiming an active generated counterpart payload.

### Must not claim

Identity proof, graph sovereignty, routing authority, federation exposure,
source replacement, or `AOA-K-0008` activation.

### Next route

Change the counterpart contract surface first, then run `scripts/validate_kag.py`
or the focused boundary-bridge tests that cover this part.
