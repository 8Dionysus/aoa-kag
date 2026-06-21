# Source-Owned Export Validation

Run:

```bash
python mechanics/boundary-bridge/parts/source-owned-export/scripts/validate_source_owned_export.py
python -m unittest discover -s mechanics/boundary-bridge/parts/source-owned-export/tests -p 'test_*.py'
```

For repo-wide compatibility after manifest or generated surface changes, also
run:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
python scripts/validate_mechanics_skeleton.py
```

The repo-wide generated lane still checks full source-owned export parity while
writing this part's local generated registry outputs. This part owns the focused
boundary-bridge operation contract around source-owned donor exports, memo donor
registry-only posture, and owner-primary ingress.
