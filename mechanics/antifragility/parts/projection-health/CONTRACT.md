# Projection Health Contract

This part may define bounded KAG projection-health receipts.

Allowed payload:

- projection family and projection id;
- health state and consumer posture;
- evidence refs, source fallback refs, validator refs, and generated-surface
  refs.

Stop-lines:

- no proof verdict;
- no source repair;
- no runtime repair;
- no hidden regeneration as recovery;
- no widening consumer posture without evidence.
