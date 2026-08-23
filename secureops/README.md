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

