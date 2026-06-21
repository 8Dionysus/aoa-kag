# Sophian Threshold Packet Validation

Run:

```bash
python mechanics/agon/parts/sophian-threshold-packets/scripts/build_sophian_threshold_packet_registry.py --check
python mechanics/agon/parts/sophian-threshold-packets/scripts/validate_sophian_threshold_packet_registry.py
python -m unittest discover -s mechanics/agon/parts/sophian-threshold-packets/tests -p 'test_*.py'
```

The builder may write only this part's
`generated/agon_sophian_kag_packet_registry.min.json` when run without
`--check`.
