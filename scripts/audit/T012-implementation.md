Implemented T012.

Added SQLAlchemy ORM models for all requested core entities:

- [analysis.py](/workspaces/sec-project/secureops/app/models/analysis.py:41): `PullRequestAnalysis`, `GateDecision`, `LanguageCoverageProfile`, `LanguageCoverageResult`, `ValidationScenario`
- [finding.py](/workspaces/sec-project/secureops/app/models/finding.py:38): `Finding`, `DetectionSignal`, `FindingHistoryEntry`
- [remediation.py](/workspaces/sec-project/secureops/app/models/remediation.py:27): `RemediationRecommendation`
- [enums.py](/workspaces/sec-project/secureops/app/models/enums.py:109): added missing coverage and validation scenario enums

Verification passed:

```bash
python3 -m py_compile secureops/app/models/analysis.py secureops/app/models/finding.py secureops/app/models/remediation.py
bash scripts/gate.sh secureops/app/models/analysis.py secureops/app/models/finding.py secureops/app/models/remediation.py
bash scripts/gate.sh
```

Caveat: this container does not have a `python` binary, only `python3`, so I used `python3`. A runtime SQLAlchemy import smoke check could not run because `sqlalchemy` is not installed in the system Python environment. No commit was made.