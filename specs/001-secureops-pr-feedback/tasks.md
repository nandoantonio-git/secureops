# Tasks: SecureOps PR Vulnerability Feedback

**Input**: Design documents from `/specs/001-secureops-pr-feedback/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Included because the constitution quality gates, feature spec, and quickstart require reproducible validation for analysis engine behavior, taint analysis, blocking decisions, fallback behavior, and manual override history.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Application code lives under `secureops/app/`
- Tests live under `secureops/tests/`
- Validation fixtures live under `secureops/tests/fixtures/`
- Documentation for this feature remains under `specs/001-secureops-pr-feedback/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Python/FastAPI project structure, local dependencies, and validation fixture layout.

- [x] T001 Create SecureOps source tree directories in `secureops/app/{api,models,db,engine/rules,remediation,github}` and `secureops/tests/{unit,integration,validation,fixtures}`
- [x] T002 Initialize Python 3.12 project metadata and dependencies in `secureops/pyproject.toml`
- [x] T003 [P] Configure pytest test discovery and markers in `secureops/pytest.ini`
- [x] T004 [P] Create application package markers in `secureops/app/__init__.py` and subpackage `__init__.py` files
- [x] T005 [P] Add local environment example for PostgreSQL, gate mode, secondary language, and Ollama fallback in `secureops/.env.example`
- [x] T006 [P] Create controlled fixture directories for Python and secondary-language clean/vulnerable/fallback cases under `secureops/tests/fixtures/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core API, persistence, parser, and domain infrastructure that MUST be complete before user stories can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Define shared enums and constants for analysis status, gate modes, finding status, severity, signal types, and recommendation sources in `secureops/app/models/enums.py`
- [x] T008 [P] Implement FastAPI application factory and health endpoint in `secureops/app/main.py`
- [x] T009 [P] Implement Pydantic settings for database URL, secondary language, gate mode, and Ollama configuration in `secureops/app/config.py`
- [x] T010 Implement PostgreSQL connection/session setup in `secureops/app/db/connection.py`
- [x] T011 Create Alembic migration environment in `secureops/app/db/migrations/`
- [x] T012 Define SQLAlchemy models for PullRequestAnalysis, Finding, RemediationRecommendation, DetectionSignal, GateDecision, LanguageCoverageProfile, LanguageCoverageResult, FindingHistoryEntry, and ValidationScenario in `secureops/app/models/analysis.py`, `secureops/app/models/finding.py`, and `secureops/app/models/remediation.py`
- [x] T013 Implement initial migration for all entities and relationships in `secureops/app/db/migrations/versions/001_initial_secureops_schema.py`
- [x] T014 [P] Implement OpenAPI request/response schemas from `contracts/openapi.yaml` in `secureops/app/api/schemas.py`
- [x] T015 [P] Implement redacted domain error types and API error responses in `secureops/app/api/errors.py`
- [x] T016 Implement Tree-sitter parser adapter for Python and selected secondary language in `secureops/app/engine/parser.py`
- [x] T017 Implement stable finding fingerprint helper in `secureops/app/engine/fingerprint.py`
- [x] T018 [P] Add baseline validation fixtures listed in quickstart.md under `secureops/tests/fixtures/`
- [x] T019 [P] Add API contract tests for `/analyses`, `/findings/{findingId}`, and `/analyses/{analysisId}/gate-decision` in `secureops/tests/integration/test_openapi_contract.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order or in parallel by story.

---

## Phase 3: User Story 1 - Receber feedback acionável no Pull Request (Priority: P1) 🎯 MVP

**Goal**: Analyze a controlled Pull Request and publish actionable finding feedback with cause, evidence, impact, recommended correction, and safe example.

**Independent Test**: Submit or simulate a PR containing a known Python vulnerable fixture and verify each valid finding receives structured, non-generic feedback in the PR review context.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T020 [P] [US1] Add unit tests for reviewed remediation template selection and context adaptation in `secureops/tests/unit/test_remediation_templates.py`
- [x] T021 [P] [US1] Add unit tests for deterministic/template fallback when Ollama is unavailable in `secureops/tests/unit/test_remediation_fallback.py`
- [x] T022 [P] [US1] Add unit tests for Python vulnerable fixture detection and safe fixture non-detection in `secureops/tests/unit/test_python_rules.py`
- [x] T023 [P] [US1] Add integration test for creating an analysis and listing structured findings in `secureops/tests/integration/test_analysis_feedback_flow.py`
- [x] T024 [P] [US1] Add validation test for quickstart Scenario 1 advisory Python PR feedback in `secureops/tests/validation/test_advisory_python_feedback.py`
- [x] T025 [P] [US1] Add validation test for quickstart Scenario 6 Ollama unavailable fallback in `secureops/tests/validation/test_ollama_fallback.py`
- [x] T026 [P] [US1] Add unit tests ensuring PR feedback redacts sensitive evidence such as hardcoded secrets, tokens, credentials, database URLs, and private keys while preserving enough context for actionability in `secureops/tests/unit/test_pr_feedback_redaction.py`

### Implementation for User Story 1

- [x] T027 [P] [US1] Implement Python deterministic vulnerability rules with code evidence extraction in `secureops/app/engine/rules/python.py`
- [x] T028 [US1] Implement scan orchestration that parses changed files and creates findings in `secureops/app/engine/scan.py`
- [x] T029 [P] [US1] Implement reviewed remediation template catalog for common known patterns in `secureops/app/remediation/templates.py`
- [x] T030 [P] [US1] Implement Ollama client with timeout and low-confidence handling in `secureops/app/remediation/ollama_client.py`
- [x] T031 [US1] Implement deterministic/template fallback recommendation generation in `secureops/app/remediation/fallback.py`
- [x] T032 [US1] Implement remediation service that always returns cause, evidence, impact, correction, and safe example for published findings in `secureops/app/remediation/service.py`
- [x] T033 [US1] Implement analysis creation and retrieval endpoints in `secureops/app/api/analyses.py`
- [x] T034 [US1] Implement finding listing/detail endpoints in `secureops/app/api/findings.py`
- [x] T035 [P] [US1] Implement GitHub PR comment formatter for structured, redacted feedback that includes cause, evidence, impact, correction, and safe example without exposing sensitive values in `secureops/app/github/comments.py`
- [x] T036 [US1] Integrate scan, remediation, persistence, and PR comment formatting in `secureops/app/api/analyses.py`
- [x] T037 [US1] Document local US1 validation command and expected evidence in `secureops/README.md`

**Checkpoint**: User Story 1 is independently functional and testable as the MVP.

---

## Phase 4: User Story 2 - Demonstrar análise em duas linguagens (Priority: P2)

**Goal**: Demonstrate Python deep coverage and one secondary language with minimal but real deterministic coverage and visible limitations.

**Independent Test**: Run controlled vulnerable and safe fixtures in both languages, confirming Python data-flow depth and at least one deterministic secondary-language pattern without implying parity.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T038 [P] [US2] Add unit tests for Python data-flow tracking from untrusted inputs to sensitive sinks in `secureops/tests/unit/test_taint.py`
- [x] T039 [P] [US2] Add unit tests for secondary-language vulnerable and safe fixtures in `secureops/tests/unit/test_secondary_rules.py`
- [x] T040 [P] [US2] Add integration test for language coverage profiles and limitations in `secureops/tests/integration/test_language_coverage.py`
- [x] T041 [P] [US2] Add validation tests for quickstart Scenarios 2 and 3 in `secureops/tests/validation/test_language_depth.py`

### Implementation for User Story 2

- [x] T042 [US2] Implement Python taint analysis from untrusted sources to sensitive sinks in `secureops/app/engine/taint.py`
- [x] T043 [P] [US2] Implement secondary-language deterministic rule coverage in `secureops/app/engine/rules/secondary.py`
- [x] T044 [US2] Integrate taint findings and secondary-language findings into scan orchestration in `secureops/app/engine/scan.py`
- [x] T045 [US2] Implement language coverage profile/result persistence in `secureops/app/models/analysis.py` and `secureops/app/api/analyses.py`
- [x] T046 [US2] Surface asymmetric language limitations in analysis responses and PR feedback in `secureops/app/github/comments.py`
- [x] T047 [US2] Document supported secondary-language rule and known limitations in `secureops/README.md`

**Checkpoint**: User Story 2 demonstrates two-language support with explicit unequal depth.

---

## Phase 5: User Story 3 - Controlar bloqueios de merge com confiança (Priority: P3)

**Goal**: Keep advisory mode as the default and allow blocking only for known critical findings validated by multiple deterministic signals.

**Independent Test**: Use clean and critical vulnerable PR fixtures to verify advisory default, no undue clean-code blocks, and restricted blocking only when deterministic evidence satisfies the configured criteria.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T048 [P] [US3] Add unit tests for deterministic detection-signal eligibility in `secureops/tests/unit/test_gate_eligibility.py`
- [x] T049 [P] [US3] Add integration test for `/analyses/{analysisId}/gate-decision` in advisory and blocking modes in `secureops/tests/integration/test_gate_api.py`
- [x] T050 [P] [US3] Add validation test for quickstart Scenario 4 restricted critical blocking in `secureops/tests/validation/test_restricted_blocking.py`
- [x] T051 [P] [US3] Add validation test for quickstart Scenario 5 clean-code non-blocking in `secureops/tests/validation/test_clean_non_blocking.py`

### Implementation for User Story 3

- [x] T052 [US3] Implement detection signal creation for deterministic rules, data-flow evidence, template matches, and AI-assisted classification in `secureops/app/engine/scan.py`
- [x] T053 [US3] Implement gate decision service enforcing advisory default and deterministic critical-blocking criteria in `secureops/app/api/gate.py`
- [x] T054 [US3] Implement GitHub status/check output for advisory, passed, and blocked decisions in `secureops/app/github/status.py`
- [x] T055 [US3] Integrate gate decision persistence and response schemas in `secureops/app/api/analyses.py` and `secureops/app/api/gate.py`
- [x] T056 [US3] Add controlled critical-unprotected and clean-code validation fixtures in `secureops/tests/fixtures/python_vulnerable/` and `secureops/tests/fixtures/python_clean/`

**Checkpoint**: User Story 3 controls blocking without AI-only authority and with zero undue blocks in clean controlled scenarios.

---

## Phase 6: User Story 4 - Gerenciar ciclo de vida de findings (Priority: P4)

**Goal**: Allow a responsible person to override finding status or automatic assessment and retain minimal visible history.

**Independent Test**: Change a finding status to false positive or accepted risk, confirm the new status is visible, and confirm a history entry records the manual decision.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T057 [P] [US4] Add unit tests for valid and invalid finding lifecycle transitions in `secureops/tests/unit/test_finding_lifecycle.py`
- [x] T058 [P] [US4] Add integration test for `/findings/{findingId}/override` in `secureops/tests/integration/test_finding_override_api.py`
- [x] T059 [P] [US4] Add validation test for quickstart Scenario 7 manual override and history in `secureops/tests/validation/test_manual_override_history.py`

### Implementation for User Story 4

- [x] T060 [US4] Implement finding lifecycle transition validation in `secureops/app/models/finding.py`
- [x] T061 [US4] Implement manual override service with append-only history creation in `secureops/app/api/findings.py`
- [x] T062 [US4] Preserve overridden findings across repeated analyses using stable fingerprints in `secureops/app/engine/fingerprint.py` and `secureops/app/engine/scan.py`
- [x] T063 [US4] Include history entries in finding detail API responses in `secureops/app/api/findings.py`
- [x] T064 [US4] Document manual override validation evidence in `secureops/README.md`

**Checkpoint**: User Story 4 supports minimal governance without introducing full RBAC or audit-log scope.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and checkpoint/defense evidence across implemented stories.

- [x] T065 [P] Update quickstart execution notes with actual commands and fixture paths in `specs/001-secureops-pr-feedback/quickstart.md`
- [x] T066 [P] Add FIAP evaluation traceability notes for architecture, SAST robustness, AI innovation, DevSecOps, and defense evidence in `specs/001-secureops-pr-feedback/plan.md`
- [x] T067 Run full unit, integration, and validation suites with `pytest` from `secureops/`
- [x] T068 Verify controlled corpus results for finding usefulness, clean-code non-blocking, critical blocking, secondary-language coverage, and Ollama fallback in `secureops/tests/validation/`
- [x] T069 Review generated findings for actionability and remove or downgrade any finding lacking cause, evidence, impact, correction, and safe example in `secureops/app/engine/rules/` and `secureops/app/remediation/`
- [x] T070 Document any local verification blocker and safest manual PR dry-run evidence in `secureops/README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - no dependency on other stories; this is the MVP.
- **User Story 2 (P2)**: Can start after Foundational, but integrates naturally with US1 scan/remediation outputs.
- **User Story 3 (P3)**: Can start after Foundational; depends on findings and detection signals from US1/US2 for meaningful end-to-end validation.
- **User Story 4 (P4)**: Can start after Foundational; depends on persisted findings from US1 for realistic validation.

### Within Each User Story

- Tests MUST be written and fail before implementation.
- Models and schemas before services.
- Services before endpoints and GitHub integration.
- Story complete before moving to the next priority unless parallel staffing is available.

---

## Parallel Opportunities

- Setup tasks T003, T004, T005, and T006 can run in parallel.
- Foundational tasks T014, T015, T018, and T019 can run in parallel after base project structure exists.
- Test tasks within each user story can run in parallel because they target different files.
- US2 secondary-language rule work can run in parallel with US2 Python taint tests after parser foundation exists.
- US3 gate API tests and validation tests can run in parallel after gate schemas are known.
- US4 lifecycle and override API tests can run in parallel after finding model fields are defined.

---

## Parallel Example: User Story 1

```bash
# Launch test-writing work for User Story 1 together:
Task: "T020 [P] [US1] Add unit tests for reviewed remediation template selection and context adaptation in secureops/tests/unit/test_remediation_templates.py"
Task: "T021 [P] [US1] Add unit tests for deterministic/template fallback when Ollama is unavailable in secureops/tests/unit/test_remediation_fallback.py"
Task: "T022 [P] [US1] Add unit tests for Python vulnerable fixture detection and safe fixture non-detection in secureops/tests/unit/test_python_rules.py"
Task: "T023 [P] [US1] Add integration test for creating an analysis and listing structured findings in secureops/tests/integration/test_analysis_feedback_flow.py"

# Launch independent implementation work after tests are in place:
Task: "T027 [P] [US1] Implement Python deterministic vulnerability rules with code evidence extraction in secureops/app/engine/rules/python.py"
Task: "T029 [P] [US1] Implement reviewed remediation template catalog for common known patterns in secureops/app/remediation/templates.py"
Task: "T030 [P] [US1] Implement Ollama client with timeout and low-confidence handling in secureops/app/remediation/ollama_client.py"
```

## Parallel Example: User Story 2

```bash
Task: "T038 [P] [US2] Add unit tests for Python data-flow tracking from untrusted inputs to sensitive sinks in secureops/tests/unit/test_taint.py"
Task: "T039 [P] [US2] Add unit tests for secondary-language vulnerable and safe fixtures in secureops/tests/unit/test_secondary_rules.py"
Task: "T043 [P] [US2] Implement secondary-language deterministic rule coverage in secureops/app/engine/rules/secondary.py"
```

## Parallel Example: User Story 3

```bash
Task: "T048 [P] [US3] Add unit tests for deterministic detection-signal eligibility in secureops/tests/unit/test_gate_eligibility.py"
Task: "T049 [P] [US3] Add integration test for /analyses/{analysisId}/gate-decision in advisory and blocking modes in secureops/tests/integration/test_gate_api.py"
Task: "T050 [P] [US3] Add validation test for quickstart Scenario 4 restricted critical blocking in secureops/tests/validation/test_restricted_blocking.py"
```

## Parallel Example: User Story 4

```bash
Task: "T057 [P] [US4] Add unit tests for valid and invalid finding lifecycle transitions in secureops/tests/unit/test_finding_lifecycle.py"
Task: "T058 [P] [US4] Add integration test for /findings/{findingId}/override in secureops/tests/integration/test_finding_override_api.py"
Task: "T059 [P] [US4] Add validation test for quickstart Scenario 7 manual override and history in secureops/tests/validation/test_manual_override_history.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. STOP and validate US1 independently with `pytest tests/unit/test_remediation_templates.py tests/unit/test_remediation_fallback.py tests/unit/test_python_rules.py tests/integration/test_analysis_feedback_flow.py tests/validation/test_advisory_python_feedback.py tests/validation/test_ollama_fallback.py` from `secureops/`.
5. Use US1 evidence for the first PR-first product demonstration.

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready.
2. Add User Story 1 → actionable PR feedback MVP.
3. Add User Story 2 → two-language and Python data-flow demonstration.
4. Add User Story 3 → restricted deterministic blocking.
5. Add User Story 4 → lifecycle and manual override governance.
6. Complete Polish → checkpoint/defense evidence and full validation corpus.

### Parallel Team Strategy

With four to five contributors:

1. Team completes Setup + Foundational together.
2. Once Foundational is complete:
   - Contributor A: US1 remediation and PR feedback.
   - Contributor B: US2 Python taint and secondary language rules.
   - Contributor C: US3 deterministic gate decisions.
   - Contributor D: US4 lifecycle overrides and history.
   - Contributor E, if available: validation corpus, docs, and FIAP traceability evidence.
3. Integrate by story checkpoints, preserving advisory-first behavior and deterministic fallback.

---

## Notes

- [P] tasks use different files or can be written independently without depending on incomplete task outputs.
- [US1] through [US4] labels map directly to spec.md user stories.
- Constitution-critical quality gates are captured in test and validation tasks for analysis engine, taint analysis, blocking, and AI fallback.
- Do not add Redis/Celery, dashboard-as-core, RBAC/full audit log, DAST, or required fine-tuning in this phase.
- Commit after each completed phase or independently validated user story.


---

## Phase 8: Convergence

- [x] T071 [CRITICAL] Implement an authenticated, mock-testable GitHub PR publishing path that posts the generated redacted feedback comment and commit status/check output directly into the Pull Request context per FR-001, FR-006, and plan: critical MVP flow (missing)
- [x] T072 [HIGH] Add a GitHub Actions pull_request/dry-run workflow or fixture-backed CI entrypoint that dispatches SecureOps analysis and surfaces the generated comment/status evidence per plan: GitHub Actions dispatch and PR workflow validation (missing)
- [x] T073 [MEDIUM] Implement real AI-assisted severity re-classification via Ollama (suggested_severity + rationale on the remediation recommendation, surfaced in the API and PR comment, accepted only through the existing US4 override mechanism -- never auto-applied, never a blocking-eligible signal) per plan: AI innovation and Constitution Principle II/V
