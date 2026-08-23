Implemented T007 in [enums.py](/workspaces/sec-project/secureops/app/models/enums.py:1).

Added shared string-backed enums and constants for:
`AnalysisStatus`, `GateMode`, `FindingStatus`, `Severity`, `SignalType`, `RecommendationSource`, plus related contract enums/defaults needed by upcoming stories.

Verification:
- `python -m py_compile secureops/app/models/enums.py` could not run because `python` is not installed in this container.
- `python3 -m py_compile secureops/app/models/enums.py` passed.
- `bash scripts/gate.sh secureops/app/models/enums.py` passed.
- `bash scripts/gate.sh` passed.

No commit was made.