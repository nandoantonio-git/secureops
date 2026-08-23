Implemented T033 in [analyses.py](/workspaces/sec-project/secureops/app/api/analyses.py:29):

- Added explicit `PullRequestAnalysis` response models for create/retrieve endpoints.
- Added contract operation IDs: `createAnalysis` and `getAnalysis`.
- Aligned retrieval path parameter with contract name `analysisId` while preserving internal `analysis_id`.

Verification passed:

- `python -m py_compile secureops/app/api/analyses.py`
- `bash scripts/gate.sh secureops/app/api/analyses.py`
- `bash scripts/gate.sh`
- `PYTHONPATH=secureops pytest secureops/tests/integration/test_analysis_feedback_flow.py -q`

No commit was made.