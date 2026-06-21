# Tiny Consumer Bundle Validation

Run:

```bash
python scripts/generate_kag.py
python scripts/validate_kag.py
python -m unittest discover -s mechanics/boundary-bridge/parts/tiny-consumer-bundle/tests -p 'test_*.py'
```

The repo-wide generator and validator remain compatibility entrypoints while
this part owns the bundle manifest, schemas, example, and generated read models.
