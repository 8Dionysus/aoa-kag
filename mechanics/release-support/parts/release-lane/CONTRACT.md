# Release Lane Contract

This part owns the release-support operation contract.

It requires:

- release command storage to remain in `config/validation_lanes.json`;
- `scripts/release_check.py` to remain a stable entrypoint delegated to the
  lane loader;
- release docs to point to the public release entrypoint;
- source-fast to avoid invoking release-only entrypoints.

It forbids:

- duplicating lane command sequences inside docs or release scripts;
- moving release truth into GitHub-only surfaces;
- treating generated parity as source truth.
