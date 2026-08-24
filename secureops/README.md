# SecureOps

SecureOps is a PR-first vulnerability feedback service. Local validation for
US1 exercises advisory Python PR feedback and safe remediation fallback when
Ollama is unavailable.

## US1 Local Validation

Run the US1 validation suite from the `secureops/` project root:

```bash
cd secureops
python -m pytest tests/validation/test_advisory_python_feedback.py tests/validation/test_ollama_fallback.py
```

The command validates the implemented US1 quickstart scenarios:

- Scenario 1, advisory Python PR feedback: a vulnerable Python PR fixture
  creates a completed advisory analysis with at least one structured finding.
- Scenario 6, Ollama unavailable fallback: an unavailable Ollama endpoint still
  produces reviewed-template remediation instead of failing the scan.

Expected evidence from a passing run:

- Both validation tests pass.
- The advisory analysis response has `status` set to `completed`, `mode` set to
  `advisory`, and `findings_count` of at least `1`.
- Published findings include `cause`, `evidence`, `impact`,
  `recommended_correction`, and `safe_example`.
- Findings include at least one deterministic detection signal.
- The default advisory gate decision is `advisory_only` with no blocking
  findings.
- Ollama fallback remediation uses `generation_source` of `reviewed_template`,
  `template_id` of `python-command-injection`, and `confidence` of `high`.

## US2 Language Coverage

SecureOps supports two analysis languages with intentionally unequal depth:

- Python is the primary language. Its coverage level is `deep`, with
  deterministic rules and data-flow evidence for supported taint patterns.
- JavaScript is the selected secondary language. Its coverage level is
  `minimal_deterministic`, with deterministic rule matches only.

The JavaScript parser is selected for `.js`, `.jsx`, `.mjs`, and `.cjs` files,
or for changed files whose language is reported as `javascript`, `js`, or
`node`.

### Supported Secondary-Language Rule

The supported US2 secondary-language rule is `javascript.dom.inner_html`.
It reports a high-severity `CWE-79` finding with source
`secondary_language_rule` when a changed JavaScript file assigns potentially
unsafe content to a DOM `innerHTML` sink.

The rule emits exact source evidence and file/line location when the JavaScript
file parses successfully. Analysis responses and PR feedback also include a
JavaScript coverage result showing `minimal_deterministic` coverage and the
number of JavaScript files analyzed.

The underlying deterministic JavaScript matcher also recognizes related sink
families such as `outerHTML`, `insertAdjacentHTML`, `document.write`,
`document.writeln`, `eval`, `Function`, and string-code `setTimeout` or
`setInterval`. The supported US2 profile, validation fixture, and advertised
secondary-language contract are limited to `javascript.dom.inner_html`.

### Known Secondary-Language Limitations

- JavaScript does not have data-flow tracking in this MVP.
- JavaScript coverage is not parity with Python data-flow analysis.
- Secondary-language findings are deterministic sink matches; they do not prove
  full source-to-sink exploitability or sanitizer correctness.
- Unsupported languages, TypeScript files, and JavaScript files that cannot be
  parsed are skipped rather than analyzed.
- Coverage is limited to the changed files supplied to an analysis request.

## US4 Manual Override Validation

Run the US4 manual override validation from the `secureops/` project root:

```bash
cd secureops
python -m pytest tests/validation/test_manual_override_history.py
```

The command validates quickstart Scenario 7:

- A manual-validation analysis creates a finding for the controlled vulnerable
  Python fixture.
- A reviewer posts to `/findings/{findingId}/override` with `changed_by`,
  `change_type`, `to_value`, and `reason`.
- The overridden finding response shows the new status, such as
  `accepted_risk`, and returns visible `history`.
- The latest history entry records who changed the finding, what changed, the
  previous value, the new value, the reason, and `created_at`.
- Re-running the same analysis preserves the prior human decision and visible
  history on the matching stable fingerprint.

Expected evidence from a passing run:

- `tests/validation/test_manual_override_history.py` passes.
- The override response status is `200`.
- The finding status changes from `open` to the requested override value.
- The append-only history entry includes `changed_by`, `change_type`,
  `from_value`, `to_value`, `reason`, and `created_at`.
- A repeated analysis keeps the override visible for the same finding
  fingerprint.

This is the intended US4 governance scope for this phase: minimal visible
manual override history without full RBAC or a full audit-log subsystem.

## Release-Readiness Verification Notes

Local evidence collected on 2026-08-23:

```bash
cd secureops
python -m pytest tests/validation
```

Result: `7 passed in 0.63s` under the local `Python 3.9.2` interpreter.

The validation suite is the safest manual PR dry-run available in this
workspace because it exercises the FastAPI PR fixture harness without
publishing to a real repository. It covers:

- Advisory Python PR feedback with structured findings and an `advisory_only`
  gate decision.
- Python data-flow evidence for a known unprotected critical fixture.
- Secondary JavaScript deterministic coverage with explicit non-parity notes.
- Restricted blocking for critical deterministic evidence.
- Clean Python and JavaScript fixtures that remain non-blocking.
- Ollama-unavailable fallback to reviewed remediation templates.
- Manual finding override history that survives a repeated analysis.

The manual dry-run evidence to capture for a checkpoint review is:

- `POST /analyses` returns `202` and a completed analysis for the controlled PR
  fixture payloads.
- `GET /analyses/{analysisId}/findings` returns structured remediation fields:
  `cause`, `evidence`, `impact`, `recommended_correction`, and `safe_example`.
- `GET /analyses/{analysisId}/feedback` returns the redacted PR comment body
  that would be posted to GitHub.
- `GET /analyses/{analysisId}/gate-decision` returns `advisory_only` in default
  advisory mode, `blocked` only for the restricted critical fixture, and
  `passed` for clean-code restricted runs.
- `POST /findings/{findingId}/override` returns visible append-only history for
  a reviewer status change.

Local verification blockers remaining before a live release dry run:

- This workspace has no live GitHub Pull Request, GitHub Actions runner
  context, or publishing credentials, so PR comment/status publication was not
  exercised against GitHub. The local substitute is the fixture harness plus
  generated feedback, gate-decision, commit-status, and check-run payloads.
- The repository quickstart names Python 3.12 as the target local prerequisite,
  but this workspace only exposes `Python 3.9.2`. The validation suite passed
  here, but strict Python 3.12 parity should be rerun in a matching environment.
