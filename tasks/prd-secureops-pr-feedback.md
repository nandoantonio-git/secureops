# PRD — SecureOps PR Vulnerability Feedback

**Status**: Formal PRD draft synthesized from Spec Kit artifacts
**Source artifacts**:
- `specs/001-secureops-pr-feedback/spec.md`
- `specs/001-secureops-pr-feedback/plan.md`
- `specs/001-secureops-pr-feedback/tasks.md`
- `.specify/memory/constitution.md` — SecureOps Constitution v2.1.0

**Feature**: `001-secureops-pr-feedback`
**Product**: SecureOps
**Primary user**: Developer receiving security feedback during Pull Request review
**Governance user**: Security Champion / Tech Lead / responsible reviewer
**Academic context**: FIAP Engenharia de Software Projeto Integrador, with CP1/CP2/CP3 and final technical defense

---

## 1. Executive Summary

SecureOps is a PR-first static application security testing platform that analyzes Pull Requests for code vulnerabilities and returns actionable feedback directly in the PR. The product must explain what was found, why it is risky, and how to correct it with concrete, safe guidance — not merely list findings.

The MVP prioritizes trustworthy, teachable findings over broad vulnerability coverage. Python is the primary analysis language and receives complete MVP depth: AST-based parsing, deterministic rules, and supported data-flow tracking from untrusted inputs to sensitive sinks. A second language is mandatory but intentionally narrower: it receives minimal, real, deterministic rule coverage with documented limitations and no parity claim.

A local AI component via Ollama may improve severity classification and remediation wording, but it is not a critical dependency. Every required flow must remain functional, testable, and demonstrable when Ollama is unavailable, low-confidence, or times out by falling back to deterministic or reviewed-template feedback. Fine-tuning via LoRA/QLoRA is a stretch goal only.

Merge blocking starts in advisory mode by default. Automatic blocking may only apply to a restricted subset of critical findings validated by multiple deterministic signals. A finding must never block a PR solely because an AI component judged it critical.

---

## 2. Problem Statement

Development teams often discover security vulnerabilities late in the software lifecycle, when remediation cost and coordination overhead are high. Existing SAST tools can produce noisy findings with limited correction guidance, making developers distrust alerts or defer remediation.

For this project, the problem is not simply “detect more vulnerabilities.” The core product challenge is to generate a smaller set of reliable, understandable, and actionable findings inside the developer workflow, while maintaining enough technical depth to demonstrate SAST robustness, AI innovation, DevSecOps integration, and academic defensibility.

---

## 3. Goals

### 3.1 Product Goals

1. Provide actionable vulnerability feedback directly in Pull Requests.
2. Ensure every published finding includes:
   - cause
   - evidence
   - impact
   - recommended correction
   - safe example or safe pattern
3. Demonstrate deep analysis for Python, including AST parsing and supported data-flow tracking.
4. Demonstrate real support for a second language through limited deterministic coverage.
5. Preserve developer trust by defaulting to advisory feedback and restricting automatic blocking.
6. Keep AI useful but non-critical through deterministic/template fallback.
7. Persist findings and lifecycle changes so repeated analyses can distinguish new, existing, resolved, false-positive, and accepted-risk findings.
8. Produce validation evidence suitable for FIAP checkpoints and technical defense without distorting the product away from the PR-first developer experience.

### 3.2 Academic Goals

1. Show architecture discipline through clear modules, local reproducibility, and explainable state transitions.
2. Demonstrate SAST robustness through AST-based parsing, deterministic rules, Python data-flow analysis, and a controlled validation corpus.
3. Demonstrate AI innovation through local Ollama-assisted severity/remediation with fallback-safe behavior.
4. Demonstrate DevSecOps practice through GitHub Actions-triggered PR analysis and advisory/blocking status publication.
5. Maintain traceability from architecture and product decisions to FIAP evaluation criteria.

---

## 4. Non-Goals / Out of Scope

The following are explicitly outside the MVP critical path:

1. Replacing mature SAST tools such as Semgrep or Bandit.
2. Maximizing vulnerability coverage at the expense of actionability.
3. Full parity between Python and the secondary language.
4. Complete taint analysis for the secondary language.
5. Redis/Celery or queue-based asynchronous architecture as a required MVP dependency.
6. Dashboard or executive analytics as the central product experience.
7. RBAC and full audit log.
8. DAST.
9. Required model training, fine-tuning, or adaptive learning.
10. Paid or externally hosted AI APIs as required validation or demo dependencies.

Optional roadmap/stretch items may include:

- LoRA/QLoRA fine-tuning
- dashboard support views
- queue-backed large-repository processing
- additional languages
- fuller governance/audit features
- DAST or SIEM integrations

---

## 5. Users and Stakeholders

### 5.1 Primary User: Developer

The developer receives PR feedback that identifies security risk and provides concrete remediation guidance. This user needs clear evidence, low noise, and safe suggestions that can be acted on during code review.

### 5.2 Governance User: Security Champion / Tech Lead

This user owns rule governance, severity thresholds, accepted risks, and manual overrides. They need finding lifecycle status, override history, and confidence that blocking behavior is restricted and explainable.

### 5.3 Academic Stakeholders

FIAP professor, evaluators, and project group members review the product for architecture, SAST robustness, AI innovation, DevSecOps practice, and technical defense. They are stakeholders in validation and traceability, not the primary product user.

---

## 6. Core User Journeys

### 6.1 US1 — Receive actionable PR feedback

As a developer, I want to receive a clear explanation of each vulnerability in the Pull Request, so I can understand the risk and fix it without relying on a generic alert list.

Acceptance expectations:

1. Given a Pull Request with a known Python vulnerability, when analysis completes, then the PR receives structured feedback with cause, evidence, impact, concrete correction, and safe example.
2. Given a known vulnerability pattern covered by a reviewed remediation template, when the recommendation is generated, then the correction follows the reviewed model and adapts to the code context.
3. Given sensitive evidence such as hardcoded secrets, tokens, credentials, database URLs, or private keys, when feedback is published to the PR, then the PR feedback redacts sensitive evidence while preserving enough context for actionability.

### 6.2 US2 — Demonstrate two-language analysis

As an evaluator or technical reviewer, I want to verify that SecureOps analyzes two languages with explicitly unequal depth, so the product proves multi-language capability without claiming unsupported parity.

Acceptance expectations:

1. Python receives deterministic rules and supported data-flow tracking.
2. The secondary language receives at least one real deterministic vulnerability rule with vulnerable and safe fixtures.
3. Documentation, PR feedback, and demo material make the unequal coverage visible.

### 6.3 US3 — Control merge blocking safely

As a Security Champion or Tech Lead, I want merge blocking to start consultative and only block critical cases with high-confidence deterministic evidence, so developers are not blocked by fragile or AI-only findings.

Acceptance expectations:

1. Advisory mode is the default and does not block merges.
2. Blocking mode can block only known critical vulnerabilities with multiple deterministic signals.
3. Clean controlled PRs produce zero undue automatic blocks.
4. AI-assisted severity or explanation cannot independently trigger blocking.

### 6.4 US4 — Manage finding lifecycle

As a responsible security reviewer, I want to change finding status and preserve minimal history, so false positives, accepted risks, investigations, and resolutions remain traceable.

Acceptance expectations:

1. Findings support statuses: open, in investigation, resolved, false positive, accepted risk.
2. Manual overrides record who changed what, when, and why.
3. Stable fingerprints preserve overridden findings across repeated analyses.

---

## 7. Functional Requirements

### 7.1 PR Analysis and Feedback

- **FR-001**: The system must analyze Pull Requests and return vulnerability feedback directly in the PR context.
- **FR-002**: The system must generate findings with location, category, severity, evidence, status, and source.
- **FR-003**: Every published finding must include cause, evidence, impact, recommended correction, and safe example.
- **FR-004**: The system must not publish generic or unsupported remediation advice as a concrete correction.
- **FR-005**: The PR feedback formatter must redact sensitive values while preserving actionable context.

### 7.2 Language Coverage

- **FR-006**: The system must support exactly two programming languages in this version.
- **FR-007**: Python must be the primary language and receive deeper analysis.
- **FR-008**: Python analysis must include AST parsing and supported data-flow tracking from untrusted inputs to sensitive sinks.
- **FR-009**: The secondary language must receive minimum real deterministic coverage through documented vulnerability patterns.
- **FR-010**: The system must make language-scope limitations visible and must not imply parity between Python and the secondary language.

### 7.3 Remediation and AI Assistance

- **FR-011**: The system must use reviewed remediation templates for common known patterns.
- **FR-012**: Ollama may augment severity and remediation wording, but deterministic/template fallback must remain available.
- **FR-013**: If Ollama is unavailable, times out, or produces low-confidence output, the system must degrade safely to deterministic/template feedback.
- **FR-014**: Fine-tuning must not be required for MVP correctness, validation, or demonstration.

### 7.4 Advisory and Blocking Behavior

- **FR-015**: The system must distinguish advisory feedback from automatic merge blocking.
- **FR-016**: Advisory mode must be the default.
- **FR-017**: Automatic blocking may only apply to a restricted subset of critical findings validated by multiple deterministic signals.
- **FR-018**: A blocking decision must never depend exclusively on AI-assisted judgment.
- **FR-019**: Clean Pull Requests or Pull Requests without validated critical vulnerabilities must not be blocked.

### 7.5 Finding Lifecycle and Governance

- **FR-020**: Findings must maintain lifecycle status: open, in investigation, resolved, false positive, or accepted risk.
- **FR-021**: A responsible person must be able to manually override finding status or automatic assessment.
- **FR-022**: Manual overrides must retain minimal append-only history.
- **FR-023**: Findings must be preserved across analyses to distinguish new, existing, resolved, and overridden findings.

### 7.6 Validation and Traceability

- **FR-024**: The system must include a controlled validation set covering Python, the secondary language, clean code, critical blocking, and AI fallback scenarios.
- **FR-025**: Analysis-engine, taint-analysis, blocking, and AI-fallback changes must include reproducible local validation evidence.
- **FR-026**: Relevant architecture and validation decisions must remain traceable to FIAP evaluation criteria without changing the product into a checklist-driven demo.

---

## 8. Non-Functional Requirements

### 8.1 Reliability and Safety

- Required flows must work without paid APIs.
- Required flows must survive Ollama unavailability through fallback behavior.
- PR comments must not expose secrets or sensitive source values.
- Blocking must be reversible by returning to advisory behavior.

### 8.2 Explainability

- Every finding must be explainable through deterministic evidence, data-flow evidence, reviewed templates, or a safe combination of those.
- AI output must augment evidence rather than replace source location, rule identity, data-flow evidence, or blocking eligibility.

### 8.3 Testability

- Quality gates must be local and reproducible.
- Rule changes must include vulnerable and safe fixtures when practical.
- Blocking changes must be validated against the controlled corpus.
- AI-dependent behavior must be testable with mocks, deterministic adapters, or fallback mode.

### 8.4 Simplicity

- Implementation should favor clear Python modules and direct functions.
- Avoid unnecessary Clean Architecture, DDD, repository-pattern abstractions, queue infrastructure, or dashboard modules in the MVP.

---

## 9. Technical Architecture

### 9.1 Critical End-to-End Flow

1. Pull Request is opened or updated.
2. GitHub Actions triggers the SecureOps analysis flow.
3. The analysis engine scans changed files.
4. Python files receive AST parsing, deterministic rules, and supported data-flow tracking.
5. Secondary-language files receive deterministic minimum rule coverage.
6. Findings are generated with stable fingerprints and detection signals.
7. Remediation is generated through reviewed templates, local Ollama contextualization, or deterministic fallback.
8. Findings and analysis state are persisted in PostgreSQL.
9. Structured, redacted PR feedback is generated.
10. PR comment/status is published.
11. Gate decision remains advisory by default or blocks only when restricted deterministic criteria are met.

### 9.2 Planned Stack

- **Language**: Python 3.12
- **API**: FastAPI
- **Validation schemas**: Pydantic
- **Persistence**: PostgreSQL
- **Database migrations**: Alembic or equivalent
- **Parsing**: Tree-sitter for Python and selected secondary language
- **Testing**: pytest
- **AI assistance**: local Ollama
- **CI/PR workflow**: GitHub Actions

### 9.3 Proposed Source Layout

```text
secureops/
├── app/
│   ├── main.py
│   ├── api/
│   ├── models/
│   ├── db/
│   ├── engine/
│   │   ├── parser.py
│   │   ├── scan.py
│   │   ├── taint.py
│   │   └── rules/
│   ├── remediation/
│   └── github/
├── tests/
│   ├── fixtures/
│   ├── unit/
│   ├── integration/
│   └── validation/
├── pyproject.toml
└── README.md
```

---

## 10. Data Model Summary

### PullRequestAnalysis

Represents a scan run for a PR or manual validation scenario. Tracks repository, PR number, commit SHA, trigger, mode, status, timing, and failure reason.

### Finding

Represents a vulnerability report tied to code location. Includes language, rule, category, severity, lifecycle status, source, fingerprint, remediation, detection signals, and history.

### RemediationRecommendation

Stores structured correction guidance: cause, evidence, impact, recommended correction, safe example, generation source, template ID, and confidence.

### DetectionSignal

Represents independent evidence such as deterministic rule match, data-flow evidence, template match, or AI-assisted classification. Blocking eligibility depends on deterministic evidence, not isolated AI classification.

### GateDecision

Represents advisory, passed, or blocked outcome for an analysis. Blocking decisions must cite eligible critical findings and deterministic reasons.

### LanguageCoverageProfile / LanguageCoverageResult

Represent declared language support and per-analysis coverage outcomes, including visible limitations.

### FindingHistoryEntry

Append-only record of manual status changes, risk acceptance, severity override, or reopen events.

### ValidationScenario

Controlled scenario used to validate clean cases, valid findings, critical blocking, false-positive guards, and AI fallback.

---

## 11. Success Metrics

1. At least 80% of valid findings in the validation set have their correction rated useful by human reviewers.
2. Clean-code validation scenarios produce zero undue automatic merge blocks.
3. A known unprotected critical vulnerability is blocked when restricted blocking is enabled.
4. 100% of published findings include cause, evidence, impact, correction, and safe example.
5. 100% of automatic blocking decisions are traceable to deterministic evidence and are not based solely on AI.
6. Validation set demonstrates both languages: Python deep coverage and at least one real secondary-language deterministic rule.
7. Manual overrides preserve visible history.

Open note: the exact rubric and reviewer process for the 80% usefulness metric remains intentionally unformalized pending group decision.

---

## 12. Validation Plan

### 12.1 Required Fixture Classes

- Python clean code
- Python vulnerable code
- Python critical unprotected data-flow case
- Secondary-language clean code
- Secondary-language deterministic vulnerable pattern
- Ollama unavailable/fallback case

### 12.2 Required Validation Scenarios

1. Advisory PR feedback for Python vulnerability.
2. Python data-flow finding from untrusted input to sensitive sink.
3. Secondary-language deterministic coverage.
4. Restricted blocking for known critical vulnerability.
5. Clean-code non-blocking guarantee.
6. Ollama unavailable fallback.
7. Manual override and history.

### 12.3 Quality Gates

- Tests must be written before implementation for each story area.
- Analysis-engine changes require vulnerable and safe fixtures.
- Taint-analysis changes require expected vulnerable flow and safe/non-vulnerable guard when practical.
- Blocking changes require controlled-corpus validation and false-positive reasoning.
- AI fallback must be validated locally without paid APIs.

---

## 13. Implementation Phases

### Phase 1 — Setup

Initialize Python project structure, pytest, environment example, and fixture directories.

### Phase 2 — Foundational Infrastructure

Implement shared enums, FastAPI app, settings, PostgreSQL connection, migrations, database models, OpenAPI schemas, parser adapter, fingerprinting, baseline fixtures, and API contract tests.

### Phase 3 — US1 MVP: Actionable PR Feedback

Implement Python deterministic rules, scan orchestration, remediation templates, Ollama adapter, deterministic fallback, remediation service, analysis/finding endpoints, redacted PR comment formatting, and US1 validation documentation.

### Phase 4 — US2: Two-Language Support

Implement Python data-flow analysis, secondary-language deterministic rule coverage, language coverage persistence, visible limitation messaging, and documentation.

### Phase 5 — US3: Restricted Blocking

Implement detection-signal eligibility, advisory/blocking gate service, GitHub status output, gate decision persistence, and clean/critical validation fixtures.

### Phase 6 — US4: Finding Lifecycle

Implement lifecycle transition validation, manual override service, append-only history, stable-fingerprint override preservation, and finding detail history output.

### Phase 7 — Polish and Defense Evidence

Update quickstart commands, FIAP traceability notes, full validation evidence, actionability review, local verification blockers, and PR dry-run evidence.

---

## 14. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Findings are too noisy or vague | Developer distrust | Prioritize actionability, require structured explanations, downgrade/remove weak findings |
| Blocking creates false positives | PR workflow disruption | Advisory default, restricted deterministic blocking, clean-code validation |
| AI is unavailable or low quality | Demo or workflow failure | Deterministic/template fallback, no required fine-tuning |
| Secondary language appears fake | Evaluation risk | Provide real deterministic rule, safe/vulnerable fixtures, visible limitations |
| Scope expands into dashboard/queues/RBAC/DAST | MVP delay | Keep these explicitly out of phase; document as roadmap only |
| Sensitive evidence leaks in PR comments | Security failure | Redaction task and tests for secrets/tokens/credentials/URLs/private keys |
| Academic traceability becomes product distortion | Poor product coherence | Keep PR-first developer experience as product core and link decisions to FIAP criteria separately |

---

## 15. Open Decisions

1. Exact secondary language selection: plan recommends JavaScript/TypeScript, but the product requirement is “one secondary language with deterministic minimum coverage.”
2. Human-review rubric for the 80% usefulness metric: intentionally pending group decision.
3. Exact first vulnerability classes for Python data-flow and secondary-language deterministic coverage.
4. Exact controlled corpus size for checkpoint demonstration.

---

## 16. Release Readiness Criteria

The MVP is ready for checkpoint/demo use when:

1. US1 works independently with actionable redacted PR feedback.
2. Python vulnerable and safe fixtures pass expected analysis outcomes.
3. Ollama-unavailable fallback produces safe structured remediation.
4. Secondary-language deterministic rule is demonstrated with safe and vulnerable fixtures.
5. Restricted blocking correctly blocks a known critical case and does not block clean controlled cases.
6. Manual override and history are demonstrated.
7. Validation evidence is reproducible locally without paid APIs.
8. FIAP traceability notes are available for architecture, SAST robustness, AI innovation, DevSecOps, and defense.

---

## 17. Appendix: Traceability to Constitution v2.1.0

### I. Actionable Feedback Before Broad Coverage

Covered by structured finding requirements, reviewed remediation templates, redacted PR feedback, and actionability review tasks.

### II. Automatic Blocking Is Earned, Not Default

Covered by advisory default, restricted deterministic blocking, clean-code validation, and no IA-only blocking rule.

### III. Two Languages With Explicitly Unequal Coverage

Covered by Python primary depth and secondary-language deterministic minimum coverage with visible limitations.

### IV. Academic Traceability Without Product Distortion

Covered by FIAP traceability tasks while preserving PR-first developer workflow as the product core.

### V. AI Components Are Never an Isolated Critical Dependency

Covered by Ollama fallback requirements, template/deterministic recommendation generation, and local validation without paid APIs.
