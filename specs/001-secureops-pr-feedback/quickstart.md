# Quickstart: SecureOps PR Vulnerability Feedback

This guide validates the planned MVP end-to-end. It is a runnable validation guide for implementation, not a full implementation script.

## Prerequisites

- Python 3.12 available locally.
- PostgreSQL available locally.
- Tree-sitter grammars available for Python and the selected secondary language.
- Ollama installed and running for local IA-assisted remediation, or fallback mode enabled.
- GitHub repository or local PR fixture harness.
- Controlled fixtures for:
  - Python clean code.
  - Python vulnerable code.
  - Python critical unprotected data-flow case.
  - Secondary-language clean code.
  - Secondary-language deterministic vulnerable pattern.
  - Ollama unavailable/fallback behavior.

## Required MVP Configuration

- Default gate mode: `advisory`.
- Optional restricted gate mode: `blocking_enabled`.
- Primary language: Python.
- Secondary language: deterministic minimum coverage only.
- Fine-tuning: disabled for MVP validation.
- Redis/Celery, dashboard-as-core, RBAC/full audit log, and DAST: disabled/out of scope.

## Validation Scenario 1: Advisory PR feedback for Python vulnerability

1. Open or simulate a Pull Request containing a known Python vulnerable fixture.
2. Trigger analysis through the GitHub Actions flow or local PR harness.
3. Confirm a `PullRequestAnalysis` is recorded as `completed`.
4. Confirm the PR receives feedback containing:
   - cause
   - evidence
   - impact
   - recommended correction
   - safe example
5. Confirm the PR is not blocked in default advisory mode.

Expected outcome: actionable finding is published; merge remains unblocked.

## Validation Scenario 2: Python data-flow finding

1. Run the fixture where untrusted input reaches a sensitive sink without sanitization.
2. Confirm the finding includes deterministic rule evidence and data-flow evidence.
3. Confirm remediation points to the unsafe flow and gives a safe pattern.

Expected outcome: Python primary-language depth is demonstrated with data-flow evidence.

## Validation Scenario 3: Secondary-language deterministic coverage

1. Run the secondary-language vulnerable fixture.
2. Confirm the language coverage result identifies the secondary language and its limitations.
3. Confirm at least one deterministic secondary-language finding is produced.
4. Confirm the feedback does not imply parity with Python data-flow coverage.

Expected outcome: two-language support is real, visible, and explicitly unequal.

## Validation Scenario 4: Restricted blocking for known critical vulnerability

1. Enable `blocking_enabled` for a controlled run.
2. Run a Pull Request fixture with a known unprotected critical vulnerability.
3. Confirm the finding has multiple deterministic signals or deterministic rule plus data-flow evidence.
4. Confirm the gate decision is `blocked`.
5. Confirm no IA-only signal is used as the sole blocking basis.

Expected outcome: blocking happens only for validated critical deterministic evidence.

## Validation Scenario 5: Clean-code non-blocking guarantee

1. Enable `blocking_enabled` for a controlled run.
2. Run clean fixtures for both supported languages.
3. Confirm no eligible critical findings are produced.
4. Confirm gate decision is `passed` or advisory, not `blocked`.

Expected outcome: zero undue blocks for clean code.

## Validation Scenario 6: Ollama unavailable fallback

1. Make Ollama unavailable or configure the Ollama adapter to time out.
2. Run a vulnerable fixture covered by a reviewed remediation template.
3. Confirm the platform emits a deterministic/template remediation.
4. Confirm the finding remains structured and safe.
5. Confirm the scan does not fail solely because IA is unavailable.

Expected outcome: AI failure degrades safely into grounded advisory feedback.

## Validation Scenario 7: Manual override and history

1. Select an existing finding.
2. Change status to `false_positive` or `accepted_risk` with a reason.
3. Confirm the status changes.
4. Confirm a history entry records the change.
5. Re-run analysis and confirm prior human decision remains visible.

Expected outcome: human override is possible and traceable without requiring full RBAC/audit log.

## Success Evidence to Collect

- Valid findings with human usefulness ratings; target: at least 80% useful remediation.
- Clean-code restricted-blocking runs; target: zero undue blocks.
- Critical unprotected fixture run; target: blocked when restricted blocking is enabled.
- Structured finding completeness; target: 100% include cause, evidence, impact, correction, and safe example.
- Blocking traceability; target: 100% tied to deterministic evidence, never IA alone.
- Secondary-language demonstration; target: at least one real deterministic rule with vulnerable and safe fixtures.

## Suggested Verification Commands During Implementation

```bash
pytest
pytest tests/unit
pytest tests/integration
pytest tests/validation
```

If GitHub Actions integration is not available locally, document the fixture harness command and the safest manual PR dry-run evidence before checkpoint use.
