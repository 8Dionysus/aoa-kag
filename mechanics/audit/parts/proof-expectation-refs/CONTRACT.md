# Proof Expectation Refs Contract

This part owns the audit contract for proof refs embedded in KAG maturity
surfaces.

It requires:

- every proof expectation ref to resolve through `aoa-evals`;
- AOA-K surfaces to keep explicit proof refs;
- maturity surfaces to preserve proof ownership outside KAG.

It forbids:

- proof verdict ownership;
- treating named refs as proof completion;
- activation from proof-anchor visibility alone.
