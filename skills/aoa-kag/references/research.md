# Research mode

Use this mode for one bounded question that requires several AoA owners,
comparison of competing claims, hypothesis testing, or synthesis across
canonical sources.

1. State the question, owner scope, claim classes, and stopping condition.
2. Call `kag_discover` only when the relevant owners or available retrieval
   routes are unknown. Respect its page and traversal bounds and keep its
   projection timestamp.
3. Search each claim with the narrowest owner and path signals available.
   Refine a noisy claim once; do not turn the task into a catalog sweep.
4. Read the canonical owner resource behind every claim used in the result.
   Follow explicit supersession to the current owner source. Separate
   supporting, contradicting, unresolved, stale, and unavailable evidence.
5. Use `kag_traverse` only when a relationship is part of the hypothesis. Read
   the endpoint owner sources before interpreting the path.
6. Explain degraded or fallback-backed traces before using them. A
   source-unavailable owner contributes only a `partial_snapshot`; a later
   successful read does not erase prior degradation or prove current owner-ref
   parity.
7. Synthesize what the owner sources jointly support, what they conflict on,
   and which stronger owner or proof route must decide the remainder.

Do not convert retrieval ranking into consensus, a repeated assertion into
proof, or a KAG synthesis into memory, routing, role, playbook, runtime, or
source authority. Stop after the bounded question is answered or the missing
evidence is named.
