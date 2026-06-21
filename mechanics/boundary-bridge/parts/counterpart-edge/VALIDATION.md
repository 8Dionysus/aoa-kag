# Counterpart Edge Validation

Run:

```bash
python scripts/validate_kag.py
python -m unittest discover -s mechanics/boundary-bridge/parts/counterpart-edge/tests -p 'test_*.py'
```

The repo-wide validator owns the current schema/example checks for this part.
Focused part tests protect the planned-only counterpart contract posture.
