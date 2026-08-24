Implemented T056 fixture additions.

Added:
- [controlled_critical_unprotected.py](/workspaces/sec-project/secureops/tests/fixtures/python_vulnerable/controlled_critical_unprotected.py): critical SQL taint fixture for US3 blocking validation.
- [controlled_clean_refund.py](/workspaces/sec-project/secureops/tests/fixtures/python_clean/controlled_clean_refund.py): clean parameterized companion fixture.
- Updated [fixtures README](/workspaces/sec-project/secureops/tests/fixtures/README.md) with both controlled fixture paths.

Verified:
- `bash scripts/gate.sh secureops/tests/fixtures/python_vulnerable/controlled_critical_unprotected.py secureops/tests/fixtures/python_clean/controlled_clean_refund.py`
- `bash scripts/gate.sh`
- `pytest tests/unit/test_taint.py tests/unit/test_python_rules.py tests/validation/test_restricted_blocking.py tests/validation/test_clean_non_blocking.py`

All passed. No commit was made.