Implemented T040 by adding [test_language_coverage.py](/workspaces/sec-project/secureops/tests/integration/test_language_coverage.py:1).

The new integration test posts a mixed Python/JavaScript analysis and asserts:
- declared coverage profiles for `python` and `javascript`
- Python as `primary` / `deep` with data-flow support
- JavaScript as `secondary` / `minimal_deterministic` with explicit no-parity limitations
- per-analysis language coverage results and rule counts

Verification:
- `python -m py_compile secureops/tests/integration/test_language_coverage.py` passed
- `bash scripts/gate.sh secureops/tests/integration/test_language_coverage.py` passed
- Targeted pytest is red as intended for TDD: it fails with `KeyError: 'language_coverage_profiles'`, which T045 is expected to implement.