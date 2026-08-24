Implemented [test_clean_non_blocking.py](/workspaces/sec-project/secureops/tests/validation/test_clean_non_blocking.py).

It adds quickstart Scenario 5 validation for clean Python and JavaScript fixtures under `blocking_enabled`, asserting:
- analysis completes
- both files are analyzed
- no findings are produced
- gate decision is `passed`
- no blocking findings exist

Verification passed:
- Pre-change `python -m py_compile ...` failed because the file was missing
- `python -m py_compile secureops/tests/validation/test_clean_non_blocking.py`
- `pytest secureops/tests/validation/test_clean_non_blocking.py -q`
- `bash scripts/gate.sh secureops/tests/validation/test_clean_non_blocking.py`
- `bash scripts/gate.sh`

No commit was made. The worktree already contains unrelated modified/untracked files; I left those untouched.