# Exposure Review

This part owns the KAG-local audit route for counterpart federation exposure
review and planned-only counterpart posture.

## Owner Route

- proof owner: `aoa-evals`
- local part: `mechanics/audit/parts/exposure-review/`
- local source controls: `mechanics/audit/parts/exposure-review/manifests/counterpart_federation_exposure_review.json`
- local generated outputs: `mechanics/audit/parts/exposure-review/generated/counterpart_federation_exposure_review*.json`

## Stop-Line

Exposure review keeps counterpart refs visible enough to audit but not active
as generated counterpart payloads, retrieval payloads, routing ownership, or
source replacement.
