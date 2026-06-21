# Release Lane Validation

Run:

```bash
python -m unittest discover -s mechanics/release-support/parts/release-lane/tests -p 'test_*.py'
```

For release-facing changes, also run:

```bash
python scripts/release_check.py
```
