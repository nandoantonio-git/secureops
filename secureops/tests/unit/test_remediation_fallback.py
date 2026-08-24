"""Unit tests for deterministic remediation fallback behavior."""

from app.models.enums import RecommendationConfidence, RecommendationSource
from app.remediation.fallback import (
    RemediationFallbackContext,
    build_fallback_recommendation,
)


def _field(value: object, name: str) -> object:
    """Read fields from either dataclass/model instances or dict payloads."""
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def test_ollama_unavailable_uses_reviewed_template_when_pattern_matches() -> None:
    context = RemediationFallbackContext(
        rule_id="python.subprocess.shell_true",
        category="CWE-78",
        language="python",
        file_path="app/images.py",
        line_start=7,
        evidence="subprocess.run(command, shell=True, check=True)",
        sink="subprocess.run",
        user_input="image_path",
        fallback_reason="ollama_unavailable",
    )

    recommendation = build_fallback_recommendation(context)

    assert _field(recommendation, "generation_source") == (
        RecommendationSource.REVIEWED_TEMPLATE
    )
    assert _field(recommendation, "template_id") == "python-command-injection"
    assert _field(recommendation, "confidence") == RecommendationConfidence.HIGH
    assert "app/images.py:7" in _field(recommendation, "evidence")
    assert "image_path" in _field(recommendation, "cause")
    assert "shell=True" not in _field(recommendation, "safe_example")


def test_ollama_unavailable_uses_reviewed_yaml_template() -> None:
    context = RemediationFallbackContext(
        rule_id="python.yaml.unsafe_load",
        category="CWE-502",
        language="python",
        file_path="tests/fixtures/python_fallback/unsafe_yaml_load.py",
        line_start=7,
        evidence="yaml.load(raw_yaml, Loader=yaml.Loader)",
        sink="yaml.load",
        user_input="raw_yaml",
        fallback_reason="ollama_unavailable",
    )

    recommendation = build_fallback_recommendation(context)

    assert _field(recommendation, "generation_source") == (
        RecommendationSource.REVIEWED_TEMPLATE
    )
    assert _field(recommendation, "template_id") == "python-unsafe-yaml-load"
    assert _field(recommendation, "confidence") == RecommendationConfidence.HIGH
    assert "ollama_unavailable" in _field(recommendation, "evidence")
    assert "yaml.load(raw_yaml, Loader=yaml.Loader)" in _field(
        recommendation,
        "evidence",
    )
    assert "raw_yaml" in _field(recommendation, "cause")
    assert "yaml.safe_load" in _field(recommendation, "recommended_correction")
    assert "yaml.safe_load" in _field(recommendation, "safe_example")


def test_disabled_fallback_returns_no_local_recommendation() -> None:
    context = RemediationFallbackContext(
        rule_id="python.yaml.unsafe_load",
        category="CWE-502",
        language="python",
        file_path="tests/fixtures/python_fallback/unsafe_yaml_load.py",
        line_start=7,
        evidence="yaml.load(raw_yaml, Loader=yaml.Loader)",
        fallback_reason="ollama_unavailable",
        fallback_enabled=False,
    )

    assert build_fallback_recommendation(context) is None
