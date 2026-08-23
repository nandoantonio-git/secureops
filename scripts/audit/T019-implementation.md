Implemented T019 in [test_openapi_contract.py](/workspaces/sec-project/secureops/tests/integration/test_openapi_contract.py:1).

It now covers contract checks for:

- `/analyses`
- `/findings/{findingId}`
- `/analyses/{analysisId}/gate-decision`

Verification passed:

- `python -m py_compile secureops/tests/integration/test_openapi_contract.py`
- `pytest secureops/tests/integration/test_openapi_contract.py` with `3 passed`
- `bash scripts/gate.sh secureops/tests/integration/test_openapi_contract.py`
- `bash scripts/gate.sh`

No commit was created.