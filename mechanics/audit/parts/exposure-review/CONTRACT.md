# Exposure Review Contract

This part owns the operation contract for AOA-K-0008 review posture.

It requires:

- counterpart consumer surfaces to remain planned;
- federation exposure review to keep stable reviewed-surface order;
- tiny consumer bundle deferred counterpart refs to point at the review;
- federation spine and cross-source projection to forbid counterpart leakage.

It forbids:

- silent federation exposure;
- generated counterpart payload inference;
- routing ownership;
- source replacement;
- planned surface activation without a stronger owner gate.
