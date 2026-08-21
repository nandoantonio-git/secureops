# Data Model: SecureOps PR Vulnerability Feedback

## Entity: PullRequestAnalysis

Represents one scan of a Pull Request or controlled validation scenario.

### Fields

- `id`: unique analysis identifier
- `repository`: repository owner/name or canonical key
- `pull_request_number`: PR number, optional for manual validation
- `commit_sha`: analyzed commit
- `trigger`: `pull_request`, `manual_validation`
- `mode`: `advisory`, `blocking_enabled`
- `status`: `requested`, `running`, `completed`, `failed`
- `started_at`: timestamp
- `completed_at`: timestamp, optional
- `failure_reason`: redacted failure summary, optional

### Relationships

- Has many `Finding`
- Has many `LanguageCoverageResult`

### Validation Rules

- `repository`, `commit_sha`, `trigger`, and `mode` are required.
- `mode` defaults to `advisory`.
- Failures must record redacted reasons only.

### State Transitions

- `requested` → `running` → `completed`
- `requested` → `running` → `failed`

## Entity: Finding

Represents one vulnerability report tied to code location and evidence.

### Fields

- `id`: unique finding identifier
- `analysis_id`: parent analysis identifier
- `repository`: repository key
- `file_path`: source-relative path
- `line_start`: starting line
- `line_end`: ending line, optional
- `language`: `python` or selected secondary language
- `rule_id`: deterministic rule identifier
- `category`: vulnerability category, preferably CWE-style
- `severity`: `critical`, `high`, `medium`, `low`, `info`
- `status`: `open`, `in_investigation`, `resolved`, `false_positive`, `accepted_risk`
- `source`: `primary_language_rule`, `primary_language_taint`, `secondary_language_rule`, `validation_fixture`
- `fingerprint`: stable identity across scans
- `created_at`: timestamp
- `updated_at`: timestamp

### Relationships

- Belongs to `PullRequestAnalysis`
- Has one `RemediationRecommendation`
- Has many `DetectionSignal`
- Has many `FindingHistoryEntry`

### Validation Rules

- Location, language, rule, severity, status, and evidence are required for any published finding.
- Blocking eligibility requires `severity = critical` and multiple deterministic signals.
- IA-assisted classification cannot make a finding blocking-eligible by itself.
- Every published finding must have structured remediation.

### State Transitions

- `open` → `in_investigation`
- `open` → `resolved`
- `open` → `false_positive`
- `open` → `accepted_risk`
- `in_investigation` → `resolved`
- `in_investigation` → `false_positive`
- `in_investigation` → `accepted_risk`
- `false_positive` → `open` if materially different evidence appears
- `accepted_risk` → `open` if policy or evidence changes

## Entity: RemediationRecommendation

Structured explanation and safe correction attached to a finding.

### Fields

- `id`: unique recommendation identifier
- `finding_id`: parent finding
- `cause`: why the issue exists
- `evidence`: concrete code-level evidence, redacted where needed
- `impact`: why it is risky
- `recommended_correction`: concrete recommended change
- `safe_example`: safe code or safe pattern example
- `generation_source`: `reviewed_template`, `ollama_contextualized`, `deterministic_fallback`
- `template_id`: reviewed template identifier, optional
- `confidence`: `high`, `medium`, `low`

### Validation Rules

- Published recommendations require cause, evidence, impact, correction, and safe example.
- Low-confidence AI output must fall back to a reviewed template or advisory deterministic feedback.
- Common known vulnerability patterns should prefer reviewed templates.

## Entity: DetectionSignal

Independent evidence supporting a finding or blocking decision.

### Fields

- `id`: unique signal identifier
- `finding_id`: parent finding
- `signal_type`: `deterministic_rule`, `data_flow`, `template_match`, `ai_assisted_classification`
- `deterministic`: boolean
- `summary`: concise evidence summary
- `created_at`: timestamp

### Validation Rules

- Blocking eligibility requires at least two deterministic signals or one deterministic rule plus deterministic data-flow evidence for the configured critical pattern.
- `ai_assisted_classification` may enrich explanation or severity review but never independently satisfies blocking eligibility.

## Entity: GateDecision

Represents advisory/pass/block outcome for a Pull Request analysis.

### Fields

- `id`: unique decision identifier
- `analysis_id`: parent analysis
- `mode`: `advisory`, `blocking_enabled`
- `decision`: `advisory_only`, `passed`, `blocked`
- `reasons`: human-readable explanations
- `blocking_finding_ids`: finding identifiers used for blocking
- `created_at`: timestamp

### Validation Rules

- `advisory` mode always produces `advisory_only` or `passed`, never `blocked`.
- `blocked` requires at least one eligible critical finding.
- Reasons must identify deterministic evidence, not AI-only judgment.

## Entity: LanguageCoverageProfile

Declared support level for each language.

### Fields

- `id`: unique profile identifier
- `language`: language name
- `role`: `primary`, `secondary`
- `coverage_level`: `deep`, `minimal_deterministic`
- `supports_data_flow`: boolean
- `supported_rule_ids`: list of rule identifiers
- `limitations`: visible scope limitations

### Validation Rules

- Exactly one primary profile and one secondary profile are required.
- Primary profile must be Python and support data-flow tracking for claimed patterns.
- Secondary profile must include at least one deterministic vulnerability pattern with vulnerable and safe fixtures.
- Reports and PR feedback must not imply parity unless implemented and validated.

## Entity: LanguageCoverageResult

Per-analysis result for language coverage.

### Fields

- `id`: unique result identifier
- `analysis_id`: parent analysis
- `language`: analyzed language
- `files_seen`: count
- `files_analyzed`: count
- `rules_applied`: count
- `limitations`: skipped reasons or visible limitations

## Entity: FindingHistoryEntry

Append-only record of status changes and manual overrides.

### Fields

- `id`: unique history identifier
- `finding_id`: parent finding
- `changed_by`: responsible person or system actor
- `change_type`: `status_change`, `severity_override`, `risk_acceptance`, `reopen`
- `from_value`: previous value
- `to_value`: new value
- `reason`: justification
- `created_at`: timestamp

### Validation Rules

- Manual overrides require `changed_by`, `change_type`, `to_value`, and `reason`.
- History entries are append-only.
- Decision history is minimal traceability, not full RBAC/audit log.

## Entity: ValidationScenario

Controlled PR or fixture case with expected behavior.

### Fields

- `id`: unique scenario identifier
- `name`: scenario name
- `language`: Python or secondary language
- `case_type`: `clean`, `valid_finding`, `critical_unprotected`, `false_positive_guard`, `ollama_unavailable`
- `expected_findings`: expected rule identifiers
- `expected_blocking_outcome`: `not_blocked`, `blocked`
- `reviewer_usefulness_rating`: optional human review result

### Validation Rules

- Clean scenarios expect no blocking.
- Critical unprotected scenarios expect blocking only when restricted blocking is enabled and deterministic evidence is sufficient.
- Usefulness ratings feed the 80% success criterion.
