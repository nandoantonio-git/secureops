"""Ollama remediation client with timeout and fallback-safe confidence handling."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from app.models.enums import RecommendationConfidence, RecommendationSource, Severity
from app.remediation.templates import RemediationRecommendation


_REQUIRED_RECOMMENDATION_FIELDS = (
    "cause",
    "evidence",
    "impact",
    "recommended_correction",
    "safe_example",
)

_CONFIDENCE_RANK = {
    RecommendationConfidence.LOW: 1,
    RecommendationConfidence.MEDIUM: 2,
    RecommendationConfidence.HIGH: 3,
}


@dataclass(frozen=True)
class OllamaRemediationContext:
    """Finding details sent to Ollama for contextualized remediation text."""

    rule_id: str
    category: Optional[str]
    language: str
    file_path: str
    line_start: int
    evidence: str
    current_severity: str
    sink: Optional[str] = None
    user_input: Optional[str] = None


@dataclass(frozen=True)
class OllamaClientResult:
    """Result of an Ollama remediation attempt."""

    recommendation: Optional[RemediationRecommendation]
    fallback_reason: Optional[str] = None

    @property
    def should_fallback(self) -> bool:
        """Return whether deterministic/template fallback should be used."""

        return self.recommendation is None


class OllamaClient:
    """Small synchronous client for Ollama's local generate API."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        minimum_confidence: RecommendationConfidence = RecommendationConfidence.MEDIUM,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.timeout_seconds = timeout_seconds
        self.minimum_confidence = minimum_confidence

    def generate_remediation(
        self,
        context: OllamaRemediationContext,
    ) -> OllamaClientResult:
        """Generate remediation guidance or return a fallback reason."""

        if not self.base_url or not self.model:
            return OllamaClientResult(
                recommendation=None,
                fallback_reason="ollama_not_configured",
            )

        try:
            payload = self._post_generate(context)
        except TimeoutError:
            return OllamaClientResult(
                recommendation=None,
                fallback_reason="ollama_timeout",
            )
        except OSError:
            return OllamaClientResult(
                recommendation=None,
                fallback_reason="ollama_unavailable",
            )
        except ValueError:
            return OllamaClientResult(
                recommendation=None,
                fallback_reason="ollama_invalid_response",
            )

        recommendation = self._recommendation_from_payload(
            payload,
            current_severity=context.current_severity,
        )
        if recommendation is None:
            return OllamaClientResult(
                recommendation=None,
                fallback_reason="ollama_invalid_response",
            )

        if _confidence_below(
            recommendation.confidence,
            self.minimum_confidence,
        ):
            return OllamaClientResult(
                recommendation=None,
                fallback_reason="ollama_low_confidence",
            )

        return OllamaClientResult(recommendation=recommendation)

    def _post_generate(
        self,
        context: OllamaRemediationContext,
    ) -> Mapping[str, Any]:
        try:
            import httpx
        except ImportError as exc:
            raise OSError("httpx is required for Ollama requests") from exc

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": _build_prompt(context),
                    "stream": False,
                    "format": "json",
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError("Ollama request timed out") from exc
        except httpx.HTTPError as exc:
            raise OSError("Ollama request failed") from exc

        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ValueError("Ollama response must be a JSON object")
        return payload

    def _recommendation_from_payload(
        self,
        payload: Mapping[str, Any],
        *,
        current_severity: str,
    ) -> Optional[RemediationRecommendation]:
        body = _extract_response_body(payload)
        if body is None:
            return None

        confidence = _parse_confidence(body.get("confidence"))
        if confidence is None:
            return None

        values = {}
        for field in _REQUIRED_RECOMMENDATION_FIELDS:
            value = body.get(field)
            if not isinstance(value, str) or not value.strip():
                return None
            values[field] = value.strip()

        suggested_severity, severity_rationale = _parse_severity_suggestion(
            body,
            current_severity=current_severity,
        )

        return RemediationRecommendation(
            cause=values["cause"],
            evidence=values["evidence"],
            impact=values["impact"],
            recommended_correction=values["recommended_correction"],
            safe_example=values["safe_example"],
            generation_source=RecommendationSource.OLLAMA_CONTEXTUALIZED,
            template_id=None,
            confidence=confidence,
            suggested_severity=suggested_severity,
            severity_rationale=severity_rationale,
        )


def build_ollama_client(settings: Any) -> OllamaClient:
    """Create an Ollama client from the application settings object."""

    return OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )


def generate_remediation(
    *,
    settings: Any,
    context: OllamaRemediationContext,
) -> OllamaClientResult:
    """Convenience wrapper for callers that do not need to keep a client."""

    return build_ollama_client(settings).generate_remediation(context)


def _extract_response_body(payload: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    response_body = payload.get("response", payload)
    if isinstance(response_body, Mapping):
        return response_body
    if not isinstance(response_body, str):
        return None

    try:
        parsed = json.loads(response_body)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, Mapping):
        return None
    return parsed


def _parse_confidence(value: Any) -> Optional[RecommendationConfidence]:
    if isinstance(value, RecommendationConfidence):
        return value
    if not isinstance(value, str):
        return None

    normalized = value.strip().lower()
    for confidence in RecommendationConfidence:
        if confidence.value == normalized:
            return confidence
    return None


def _confidence_below(
    actual: RecommendationConfidence,
    minimum: RecommendationConfidence,
) -> bool:
    return _CONFIDENCE_RANK[actual] < _CONFIDENCE_RANK[minimum]


def _parse_severity_suggestion(
    body: Mapping[str, Any],
    *,
    current_severity: str,
) -> tuple[Optional[Severity], Optional[str]]:
    """Return (suggested_severity, rationale), or (None, None).

    A malformed or missing suggestion is never an error -- this is an
    optional enrichment on top of an already-valid recommendation, not a
    required field. Agreement with the deterministic rule's severity (or an
    unparseable value) also comes back as (None, None): there is nothing for
    a reviewer to act on either way.
    """

    raw_value = body.get("suggested_severity")
    if not isinstance(raw_value, str):
        return None, None

    normalized = raw_value.strip().lower()
    suggested = next(
        (severity for severity in Severity if severity.value == normalized),
        None,
    )
    if suggested is None or suggested.value == current_severity:
        return None, None

    rationale = body.get("severity_rationale")
    rationale_text = rationale.strip() if isinstance(rationale, str) else None
    return suggested, rationale_text or None


def _build_prompt(context: OllamaRemediationContext) -> str:
    details = {
        "rule_id": context.rule_id,
        "category": context.category,
        "language": context.language,
        "file_path": context.file_path,
        "line_start": context.line_start,
        "evidence": context.evidence,
        "current_severity": context.current_severity,
        "sink": context.sink,
        "user_input": context.user_input,
    }
    return (
        "Generate concise secure-code remediation as JSON only. "
        "Required keys: cause, evidence, impact, recommended_correction, "
        "safe_example, confidence. Confidence must be high, medium, or low. "
        "Do not invent evidence beyond the finding details.\n"
        "Also assess whether current_severity looks right for this specific "
        "occurrence, given the evidence and where the tainted value actually "
        "goes. Add two optional keys: suggested_severity (one of critical, "
        "high, medium, low, info -- omit or repeat current_severity if you "
        "agree with it) and severity_rationale (one sentence, only when "
        "suggested_severity differs from current_severity). This is always a "
        "suggestion for a human reviewer, never applied automatically -- do "
        "not let it change cause/evidence/impact/recommended_correction.\n"
        f"Finding: {json.dumps(details, sort_keys=True)}"
    )


__all__ = [
    "OllamaClient",
    "OllamaClientResult",
    "OllamaRemediationContext",
    "build_ollama_client",
    "generate_remediation",
]
