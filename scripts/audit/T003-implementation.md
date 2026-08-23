Implemented T003 by adding [secureops/pytest.ini](/workspaces/sec-project/secureops/pytest.ini:1) with pytest discovery for `tests/`, standard `test_*.py`/`Test*`/`test_*` patterns, strict marker validation, and `unit`, `integration`, and `validation` markers.

Verification:
`bash scripts/gate.sh secureops/pytest.ini` passed.

I also tried `pytest --markers` from `secureops/`, but `pytest` is not installed in the current environment. No commit was made.