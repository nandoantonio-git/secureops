"""Shared enum values for SecureOps domain models and API schemas."""

from enum import Enum, unique


@unique
class DomainEnum(str, Enum):
    """String-backed enum base for persisted and API-facing values."""

    def __str__(self) -> str:
        return self.value


@unique
class AnalysisStatus(DomainEnum):
    """Lifecycle states for a pull request analysis."""

    REQUESTED = "requested"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@unique
class AnalysisTrigger(DomainEnum):
    """Supported analysis entry points."""

    PULL_REQUEST = "pull_request"
    MANUAL_VALIDATION = "manual_validation"


@unique
class GateMode(DomainEnum):
    """Configured gate behavior for an analysis."""

    ADVISORY = "advisory"
    BLOCKING_ENABLED = "blocking_enabled"


@unique
class GateDecisionStatus(DomainEnum):
    """Possible outcomes emitted by the PR gate."""

    ADVISORY_ONLY = "advisory_only"
    PASSED = "passed"
    BLOCKED = "blocked"


@unique
class FindingStatus(DomainEnum):
    """Lifecycle states for a vulnerability finding."""

    OPEN = "open"
    IN_INVESTIGATION = "in_investigation"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED_RISK = "accepted_risk"


@unique
class Severity(DomainEnum):
    """Normalized finding severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@unique
class FindingSource(DomainEnum):
    """Engine source that produced a finding."""

    PRIMARY_LANGUAGE_RULE = "primary_language_rule"
    PRIMARY_LANGUAGE_TAINT = "primary_language_taint"
    SECONDARY_LANGUAGE_RULE = "secondary_language_rule"
    VALIDATION_FIXTURE = "validation_fixture"


@unique
class SignalType(DomainEnum):
    """Independent evidence types used to support a finding."""

    DETERMINISTIC_RULE = "deterministic_rule"
    DATA_FLOW = "data_flow"
    TEMPLATE_MATCH = "template_match"
    AI_ASSISTED_CLASSIFICATION = "ai_assisted_classification"


@unique
class RecommendationSource(DomainEnum):
    """How a remediation recommendation was generated."""

    REVIEWED_TEMPLATE = "reviewed_template"
    OLLAMA_CONTEXTUALIZED = "ollama_contextualized"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"


@unique
class RecommendationConfidence(DomainEnum):
    """Confidence levels for remediation recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@unique
class LanguageCoverageRole(DomainEnum):
    """Declared role for a supported analysis language."""

    PRIMARY = "primary"
    SECONDARY = "secondary"


@unique
class LanguageCoverageLevel(DomainEnum):
    """Depth of analysis available for a supported language."""

    DEEP = "deep"
    MINIMAL_DETERMINISTIC = "minimal_deterministic"


@unique
class FindingChangeType(DomainEnum):
    """Manual finding history event types."""

    STATUS_CHANGE = "status_change"
    SEVERITY_OVERRIDE = "severity_override"
    RISK_ACCEPTANCE = "risk_acceptance"
    REOPEN = "reopen"


@unique
class ValidationCaseType(DomainEnum):
    """Controlled validation fixture categories."""

    CLEAN = "clean"
    VALID_FINDING = "valid_finding"
    CRITICAL_UNPROTECTED = "critical_unprotected"
    FALSE_POSITIVE_GUARD = "false_positive_guard"
    OLLAMA_UNAVAILABLE = "ollama_unavailable"


@unique
class ExpectedBlockingOutcome(DomainEnum):
    """Expected gate behavior for a validation scenario."""

    NOT_BLOCKED = "not_blocked"
    BLOCKED = "blocked"


DEFAULT_GATE_MODE = GateMode.ADVISORY
DEFAULT_ANALYSIS_STATUS = AnalysisStatus.REQUESTED
DEFAULT_FINDING_STATUS = FindingStatus.OPEN

SEVERITY_ORDER: tuple[Severity, ...] = (
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
    Severity.INFO,
)

DETERMINISTIC_SIGNAL_TYPES: tuple[SignalType, ...] = (
    SignalType.DETERMINISTIC_RULE,
    SignalType.DATA_FLOW,
    SignalType.TEMPLATE_MATCH,
)

AI_ASSISTED_SIGNAL_TYPES: tuple[SignalType, ...] = (
    SignalType.AI_ASSISTED_CLASSIFICATION,
)
