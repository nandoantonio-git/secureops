# Quickstart: SecureOps PR Vulnerability Feedback

This guide validates the planned MVP end-to-end. It is a runnable validation guide for implementation, not a full implementation script.

## Prerequisites

- Python 3.12 available locally.
- PostgreSQL available locally.
- Tree-sitter grammars available for Python and the selected secondary language.
- Ollama installed and running for local IA-assisted remediation, or fallback mode enabled.
- GitHub repository or local PR fixture harness.
- Controlled fixtures for:
  - Python clean code:
    `secureops/tests/fixtures/python_clean/safe_request_handler.py`
  - Python vulnerable code:
    `secureops/tests/fixtures/python_vulnerable/command_injection.py`
  - Python critical unprotected data-flow case:
    `secureops/tests/fixtures/python_vulnerable/critical_unprotected_data_flow.py`
  - Secondary-language clean code:
    `secureops/tests/fixtures/secondary_clean/safe_dom_update.js`
  - Secondary-language deterministic vulnerable pattern:
    `secureops/tests/fixtures/secondary_vulnerable/dom_xss.js`
  - Ollama unavailable/fallback behavior:
    `secureops/tests/fixtures/python_fallback/unsafe_yaml_load.py`

## Required MVP Configuration

- Default gate mode: `advisory`.
- Optional restricted gate mode: `blocking_enabled`.
- Primary language: Python.
- Secondary language: deterministic minimum coverage only.
- Fine-tuning: disabled for MVP validation.
- Redis/Celery, dashboard-as-core, RBAC/full audit log, and DAST: disabled/out of scope.

## Local Execution Notes

Run commands from the service root unless noted otherwise:

```bash
cd secureops
```

The quickstart scenarios are covered by validation tests that drive the FastAPI
fixture harness directly. They create analysis requests with `content_ref`
pointing at files under `secureops/tests/fixtures/`, then verify findings,
feedback, language coverage, gate decisions, and override history through the
API.

Full quickstart validation:

```bash
python -m pytest tests/validation
```

Focused scenario commands:

```bash
python -m pytest tests/validation/test_advisory_python_feedback.py
python -m pytest tests/validation/test_language_depth.py
python -m pytest tests/validation/test_restricted_blocking.py
python -m pytest tests/validation/test_clean_non_blocking.py
python -m pytest tests/validation/test_ollama_fallback.py
python -m pytest tests/validation/test_manual_override_history.py
```

## Validation Scenario 1: Advisory PR feedback for Python vulnerability

Command:

```bash
cd secureops
python -m pytest tests/validation/test_advisory_python_feedback.py
```

Fixture path:

- `secureops/tests/fixtures/python_vulnerable/command_injection.py`

1. Open or simulate a Pull Request containing the known Python vulnerable fixture.
2. Trigger analysis through the GitHub Actions flow or local PR harness. The
   validation harness posts to `POST /analyses` in `advisory` mode with
   `content_ref` set to the fixture path.
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

Command:

```bash
cd secureops
python -m pytest tests/validation/test_language_depth.py::test_quickstart_scenario_2_python_data_flow_finding
```

Fixture path:

- `secureops/tests/fixtures/python_vulnerable/critical_unprotected_data_flow.py`

1. Run the fixture where untrusted input reaches a sensitive sink without sanitization.
   The validation harness posts to `POST /analyses` in `advisory` mode with
   the fixture mapped to `app/invoices.py`.
2. Confirm the finding includes deterministic rule evidence and data-flow evidence.
3. Confirm remediation points to the unsafe flow and gives a safe pattern.

Expected outcome: Python primary-language depth is demonstrated with data-flow evidence.

## Validation Scenario 3: Secondary-language deterministic coverage

Command:

```bash
cd secureops
python -m pytest tests/validation/test_language_depth.py::test_quickstart_scenario_3_secondary_language_deterministic_coverage
```

Fixture path:

- `secureops/tests/fixtures/secondary_vulnerable/dom_xss.js`

1. Run the secondary-language vulnerable fixture. The validation harness posts
   to `POST /analyses` in `advisory` mode with JavaScript content mapped to
   `web/search.js`.
2. Confirm the language coverage result identifies the secondary language and its limitations.
3. Confirm at least one deterministic secondary-language finding is produced.
4. Confirm the feedback does not imply parity with Python data-flow coverage.

Expected outcome: two-language support is real, visible, and explicitly unequal.

## Validation Scenario 4: Restricted blocking for known critical vulnerability

Command:

```bash
cd secureops
python -m pytest tests/validation/test_restricted_blocking.py
```

Fixture path:

- `secureops/tests/fixtures/python_vulnerable/critical_unprotected_data_flow.py`

1. Enable `blocking_enabled` for a controlled run.
2. Run a Pull Request fixture with a known unprotected critical vulnerability.
   The validation harness posts to `POST /analyses` with `mode` set to
   `blocking_enabled`.
3. Confirm the finding has multiple deterministic signals or deterministic rule plus data-flow evidence.
4. Confirm the gate decision is `blocked`.
5. Confirm no IA-only signal is used as the sole blocking basis.

Expected outcome: blocking happens only for validated critical deterministic evidence.

## Validation Scenario 5: Clean-code non-blocking guarantee

Command:

```bash
cd secureops
python -m pytest tests/validation/test_clean_non_blocking.py
```

Fixture paths:

- `secureops/tests/fixtures/python_clean/safe_request_handler.py`
- `secureops/tests/fixtures/secondary_clean/safe_dom_update.js`

1. Enable `blocking_enabled` for a controlled run.
2. Run clean fixtures for both supported languages. The validation harness posts
   to `POST /analyses` with Python mapped to `app/users.py` and JavaScript
   mapped to `web/profile.js`.
3. Confirm no eligible critical findings are produced.
4. Confirm gate decision is `passed` or advisory, not `blocked`.

Expected outcome: zero undue blocks for clean code.

## Validation Scenario 6: Ollama unavailable fallback

Command:

```bash
cd secureops
python -m pytest tests/validation/test_ollama_fallback.py
```

Fixture path:

- `secureops/tests/fixtures/python_vulnerable/command_injection.py`

Environment forced by the validation test:

- `OLLAMA_BASE_URL=http://127.0.0.1:9`
- `OLLAMA_TIMEOUT_SECONDS=0.001`
- `OLLAMA_FALLBACK_ENABLED=true`

1. Make Ollama unavailable or configure the Ollama adapter to time out.
2. Run a vulnerable fixture covered by a reviewed remediation template. The
   validation harness posts to `POST /analyses` in `advisory` mode with the
   fixture mapped to `app/images.py`.
3. Confirm the platform emits a deterministic/template remediation.
4. Confirm the finding remains structured and safe.
5. Confirm the scan does not fail solely because IA is unavailable.

Expected outcome: AI failure degrades safely into grounded advisory feedback.

## Validation Scenario 7: Manual override and history

Command:

```bash
cd secureops
python -m pytest tests/validation/test_manual_override_history.py
```

Fixture path:

- `secureops/tests/fixtures/python_vulnerable/command_injection.py`

1. Select an existing finding.
2. Change status to `false_positive` or `accepted_risk` with a reason. The
   validation harness posts to `POST /findings/{findingId}/override` with
   `to_value` set to `accepted_risk`.
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
cd secureops
python -m pytest
python -m pytest tests/unit
python -m pytest tests/integration
python -m pytest tests/validation
```

If GitHub Actions integration is not available locally, document the fixture harness command and the safest manual PR dry-run evidence before checkpoint use.
