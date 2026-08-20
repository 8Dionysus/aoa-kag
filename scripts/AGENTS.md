# AGENTS.md

## Guidance for `scripts/`

`scripts/` contains generators, validators, decision-index helpers, and projection helpers for the KAG substrate.

Read `docs/validation/COMMAND_AUTHORITY.md`,
`docs/validation/SCRIPT_TOPOLOGY.md`, and
`docs/validation/script_inventory.json` before adding, moving, or changing a
script's lane, owner, or side-effect posture.

Keep scripts deterministic, repo-relative, and provenance-preserving. Avoid hidden network calls, private corpora, local-only paths, and ambient credentials.

Builder changes must preserve source ownership: manifests and source refs guide derived output; generated projections do not become source truth.

Validator changes should catch provenance loss, source-ref drift, schema mismatch, quarantine bypass, and over-strong maturity claims.

`validate_local_stats_port.py` is only the source-fast adapter to the pinned
`aoa-stats` validator; KAG-local statistical meaning stays under `stats/`.

Full validation command sequences live in `config/validation_lanes.json`.
Use lane entrypoints instead of copying release sequences:

```bash
python scripts/ci_gate.py --mode source-fast
python scripts/ci_gate.py --mode generated
python scripts/ci_release_check.py
python scripts/validate_abyss_machine_kag_registry_bundle.py
```

`ci_release_check.py` is CI-only: it accepts the source-fast omission only
through an exact same-run receipt and otherwise falls back to the complete
`release_check.py` sequence. Do not use it to weaken standalone release
validation or to authorize cross-run reuse.

`scripts/validate_kag.py` exposes `local`, `os-wide`, and full-compatible
scopes. Local phases must not acquire the OS-wide provider sweep implicitly;
the lane manifest owns placement of that blocking audit.

`scripts/impact_routing.py` may only add the full OS-wide audit to the
always-required source-fast and self owner-family proofs. Keep its owner-local
surface an explicit allowlist; invalid, empty, unavailable, or unknown paths
must route to full audit. Its required-summary mode must distinguish a verified
audit from one that was correctly not required.
