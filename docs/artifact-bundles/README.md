# OS Abyss Artifact Bundles

This directory declares repo-local artifact bundle inputs for OS Abyss trust
checks over public generated KAG surfaces.

The current release-relevant surface is the generated KAG registry readmodel:

- `kag_registry.bundle.json` describes the ABI subject, release controls, and
  consumer contract for `generated/kag_registry.min.json`.
- The artifact-bundle validator builds, signs, verifies, promotes
  durable release-ready evidence with source and
  host-managed trust-root metadata, materializes the subject store, runs an
  agent-intent trust gate for `aoa-kag`, and adversarially checks the
  ABI/SBOM-lite/SLSA bundle through `abyss-machine` when that package is
  available.
- In portable CI where `abyss_machine` is not installed, the same validator
  checks the repo-local manifest contract, artifact identity parity, subject
  inventory, consumer-path shape, and public-safety scan. Use
  `--require-abyss-machine` for a host lane that must fail unless the full OS
  Abyss artifact-bundle roundtrip runs.

These manifests are not runtime state. They are portable release inputs; local
bundle directories, registry records, subject stores, and sidecars are
generated evidence.
