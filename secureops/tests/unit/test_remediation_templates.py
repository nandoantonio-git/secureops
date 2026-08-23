"""Unit tests for reviewed remediation template selection."""

from app.models.enums import RecommendationConfidence, RecommendationSource
from app.remediation.templates import (
    RemediationTemplateContext,
    render_template,
    select_template,
)


def _field(value: object, name: str) -> object:
    """Read fields from either dataclass/model instances or dict payloads."""
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def test_selects_reviewed_python_command_injection_template() -> None:
    template = select_template(
        rule_id="python.subprocess.shell_true",
        category="CWE-78",
        language="python",
    )

    assert template is not None
    assert _field(template, "template_id") == "python-command-injection"
    assert _field(template, "language") == "python"
    assert "CWE-78" in _field(template, "categories")


def test_python_command_injection_template_adapts_to_finding_context() -> None:
    template = select_template(
        rule_id="python.subprocess.shell_true",
        category="CWE-78",
        language="python",
    )
    assert template is not None
    context = RemediationTemplateContext(
        file_path="app/images.py",
        line_start=7,
        language="python",
        evidence="subprocess.run(command, shell=True, check=True)",
        sink="subprocess.run",
        user_input="image_path",
    )

    recommendation = render_template(template, context)

    assert _field(recommendation, "generation_source") == (
        RecommendationSource.REVIEWED_TEMPLATE
    )
    assert _field(recommendation, "template_id") == "python-command-injection"
    assert _field(recommendation, "confidence") == RecommendationConfidence.HIGH
    assert "app/images.py:7" in _field(recommendation, "evidence")
    assert "subprocess.run(command, shell=True, check=True)" in _field(
        recommendation,
        "evidence",
    )
    assert "image_path" in _field(recommendation, "cause")
    assert "subprocess.run" in _field(recommendation, "recommended_correction")
    assert "shell=True" not in _field(recommendation, "safe_example")


def test_javascript_dom_xss_template_uses_safe_dom_update() -> None:
    template = select_template(
        rule_id="javascript.dom.inner_html",
        category="CWE-79",
        language="javascript",
    )
    assert template is not None
    context = RemediationTemplateContext(
        file_path="static/search.js",
        line_start=5,
        language="javascript",
        evidence="results.innerHTML = `<strong>${term}</strong>`;",
        sink="innerHTML",
        user_input="q",
    )

    recommendation = render_template(template, context)

    assert _field(template, "template_id") == "javascript-dom-xss"
    assert _field(recommendation, "generation_source") == (
        RecommendationSource.REVIEWED_TEMPLATE
    )
    assert "static/search.js:5" in _field(recommendation, "evidence")
    assert "innerHTML" in _field(recommendation, "evidence")
    assert "q" in _field(recommendation, "cause")
    assert "textContent" in _field(recommendation, "recommended_correction")
    assert "textContent" in _field(recommendation, "safe_example")


def test_unknown_pattern_has_no_reviewed_template() -> None:
    assert (
        select_template(
            rule_id="python.style.line_length",
            category=None,
            language="python",
        )
        is None
    )
