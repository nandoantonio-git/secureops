Implemented T058 by adding [test_finding_override_api.py](/workspaces/sec-project/secureops/tests/integration/test_finding_override_api.py:1).

The new integration test creates an analysis, selects a finding, posts to `/findings/{findingId}/override`, and asserts the status changes to `false_positive` with a visible history entry.

Verification:
- `python -m py_compile secureops/tests/integration/test_finding_override_api.py` passed
- `bash scripts/gate.sh secureops/tests/integration/test_finding_override_api.py` passed
- `bash scripts/gate.sh` passed
- Targeted pytest is red as expected for TDD: endpoint currently returns `404` because T061 implementation is not present yet.