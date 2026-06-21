# Source-Owned Export Contract

This part keeps source-owned export ingress bounded enough to cross without
absorbing the source owner.

It requires:

- each declared source-owned export to contain exactly one `primary` source
  input;
- that `primary` input to belong to the export owner;
- supporting inputs to stay supporting and not become ownership transfer;
- the memo donor export to remain registry-visible only until a reviewed owner
  need activates spine or routing visibility;
- memo donor consumption to keep `consumed_by` empty while no live KAG surface
  consumes it;
- memo readiness, durable consequence, retention, recall, and live-ledger
  pressure to route back to `aoa-memo`.

It forbids:

- treating registry visibility as live spine or routing activation;
- treating a memo donor as graph truth, proof, or memory ownership;
- using source-owned exports as replacements for authored source meaning;
- using active legacy `seed`, `wave`, `stub`, or `landing` naming as bridge
  stage semantics.
