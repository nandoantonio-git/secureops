# Research: SecureOps PR Vulnerability Feedback

## Decision: Python is the primary analysis language

**Rationale**: The constitution requires Python as the primary language with complete MVP coverage, including AST-based parsing and data-flow tracking for supported vulnerability patterns. Concentrating depth in Python makes the PR feedback reliable and defensible.

**Alternatives considered**:
- Equal depth across both languages: rejected because it would weaken finding quality and violate the unequal-coverage MVP scope.
- Secondary language as the primary target: rejected because the constitution explicitly names Python as the primary analysis language.

## Decision: Secondary language receives minimum deterministic coverage only

**Rationale**: The product must demonstrate two-language support, but parity is explicitly out of scope. The secondary language should have real documented rules, fixtures, and visible limitations, without complete taint analysis.

**Alternatives considered**:
- Documentation-only secondary support: rejected because evaluation requires real analysis coverage.
- Full secondary-language taint analysis: rejected as scope expansion that risks Python depth and PR feedback quality.

## Decision: Use Tree-sitter as the AST parsing foundation

**Rationale**: Tree-sitter supports multiple languages and stable source locations needed for PR comments. It keeps the path to language expansion credible while allowing the MVP to remain explicitly asymmetric.

**Alternatives considered**:
- Native Python `ast` only: useful for Python but less aligned with the required two-language parser strategy.
- Regex scanning: rejected because it is too fragile for reliable findings and blocking evidence.

## Decision: Use deterministic rules plus Python-focused data-flow tracking

**Rationale**: Blocking and core findings need deterministic, auditable evidence. Python data-flow tracking supports the strongest MVP demonstration: untrusted input reaching sensitive sinks without sanitization. The secondary language remains rule-based.

**Alternatives considered**:
- AI-first vulnerability discovery: rejected because AI cannot be a critical dependency or sole blocking authority.
- Broad rule catalog before data-flow: rejected because actionable feedback and reliability come before broad coverage.

## Decision: Use FastAPI as the service boundary

**Rationale**: FastAPI provides clear request/response contracts, straightforward validation, and a simple local development path for a Python product. It fits a PR-first API without requiring a full web dashboard.

**Alternatives considered**:
- CLI-only implementation: simpler, but weaker for persisted lifecycle status and manual overrides.
- Full dashboard application first: rejected because dashboard is not the core product experience.

## Decision: Persist analysis state and finding lifecycle in PostgreSQL

**Rationale**: The product needs durable analyses, findings, history, overrides, validation outcomes, and repeated-scan correlation. PostgreSQL is sufficient without adding queue or analytics infrastructure.

**Alternatives considered**:
- Flat files: rejected because lifecycle and override history become weak and hard to query.
- Event store/full audit system: rejected as overbuilt; minimal history satisfies this phase.

## Decision: Use local Ollama with deterministic/template fallback

**Rationale**: Ollama supports local AI-assisted severity and remediation without paid APIs. The constitution requires the product to survive AI failure, so reviewed templates and deterministic fallback are mandatory.

**Alternatives considered**:
- Hosted paid LLM: rejected because required demos/tests must not depend on paid APIs.
- IA-only recommendations: rejected because suggestions must be grounded and fallback-safe.
- Templates only: safe but less contextual; retained as fallback and reviewed baseline.

## Decision: Treat LoRA/QLoRA fine-tuning as stretch goal only

**Rationale**: Fine-tuning can support academic innovation, but it must not become part of the critical MVP path. Required behavior must work with base local Ollama or deterministic fallback.

**Alternatives considered**:
- Mandatory fine-tuning: rejected as high schedule/compute risk and not necessary for the core PR flow.
- Remove AI entirely: rejected because local AI is part of the product differentiation, as long as it is not critical.

## Decision: GitHub Actions drives the PR workflow

**Rationale**: The product promise is direct PR feedback. GitHub Actions is a natural trigger for opened/updated Pull Requests and can publish comments/status while keeping the MVP operationally simple.

**Alternatives considered**:
- Scheduled-only scans: rejected as secondary to the PR-first experience.
- Long-running queue worker first: rejected for MVP; Redis/Celery remains a future scalability option.

## Decision: Advisory mode is default; blocking is restricted

**Rationale**: Merge blocking is high trust. It is allowed only for critical findings validated by multiple deterministic signals and never by isolated AI judgment. This satisfies the constitution and protects developer trust.

**Alternatives considered**:
- Block all high/critical findings: rejected due to false-positive risk.
- AI-determined blocking: rejected as a constitutional violation.

## Decision: Keep Redis/Celery, dashboard core, RBAC/full audit log, and DAST out of this phase

**Rationale**: These are valid future evolutions but do not strengthen the critical PR feedback loop enough to justify MVP dependency. Excluding them reduces complexity and improves checkpoint demonstrability.

**Alternatives considered**:
- Queue-based architecture now: rejected until scan volume/latency demands it.
- Executive dashboard as core: rejected because product value is developer-facing PR feedback.
- Full governance suite: rejected; minimal status history and manual overrides remain required.
- DAST: rejected as outside SAST PR-feedback scope.
