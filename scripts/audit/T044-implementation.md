T044 is already implemented in `secureops/app/engine/scan.py`: Python scans include taint findings via `detect_python_taint_flows_from_source`, and JavaScript scans include secondary-language findings via `detect_secondary_vulnerabilities_from_source`.

Verification passed:
- `python -m py_compile secureops/app/engine/scan.py`
- `PYTHONPATH=secureops pytest secureops/tests/unit/test_taint.py secureops/tests/unit/test_secondary_rules.py secureops/tests/integration/test_language_coverage.py -q`
- `bash scripts/gate.sh secureops/app/engine/scan.py`
- `bash scripts/gate.sh`

No commit made.