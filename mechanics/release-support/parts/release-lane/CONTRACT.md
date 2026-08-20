# Release Lane Contract

This part owns the release-support operation contract.

It requires:

- release command storage to remain in `config/validation_lanes.json`;
- `scripts/release_check.py` to remain a stable entrypoint delegated to the
  lane loader;
- `scripts/ci_release_check.py` to select the CI continuation only after exact
  same-run receipt acceptance and otherwise execute the complete release lane;
- release docs to point to the public release entrypoint;
- source-fast to avoid invoking release-only entrypoints.

It forbids:

- duplicating lane command sequences inside docs or release scripts;
- moving release truth into GitHub-only surfaces;
- using a handoff receipt across runs or to omit generated, OS-wide,
  artifact-bundle, or cleanliness proof;
- treating generated parity as source truth.
