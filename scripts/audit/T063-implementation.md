Implemented T063 in [findings.py](/workspaces/sec-project/secureops/app/api/findings.py:41). `GET /findings/{findingId}` now returns a normalized detail payload that explicitly includes `history`, and override responses use the same detail serialization after mutating the stored finding.

Verification passed:
- `python -m py_compile secureops/app/api/findings.py`
- `bash scripts/gate.sh secureops/app/api/findings.py`
- `bash scripts/gate.sh`
- `pytest secureops/tests/integration/test_finding_override_api.py -q`

No commit was made.