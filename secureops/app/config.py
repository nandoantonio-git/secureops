"""Application settings for SecureOps."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.enums import DEFAULT_GATE_MODE, GateMode


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    database_url: str = Field(
        default="postgresql+psycopg://secureops:secureops@localhost:5432/secureops",
        description="SQLAlchemy-compatible PostgreSQL database URL.",
    )
    secondary_language: str = Field(
        default="javascript",
        description="Secondary language with deterministic minimum coverage.",
    )
    gate_mode: GateMode = Field(
        default=DEFAULT_GATE_MODE,
        description="Default pull request gate behavior.",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the local Ollama service.",
    )
    ollama_model: str = Field(
        default="codellama",
        description="Ollama model used for contextualized remediation.",
    )
    ollama_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        description="Timeout for Ollama requests in seconds.",
    )
    ollama_fallback_enabled: bool = Field(
        default=True,
        description="Use deterministic remediation fallback when Ollama is unavailable.",
    )
    dashboard_frontend_origin: str = Field(
        default="http://localhost:5173",
        description="Allowed CORS origin for the dashboard frontend dev server.",
    )
    github_token: str | None = Field(
        default=None,
        description=(
            "GitHub token used to publish PR comments and commit statuses. "
            "Publishing is skipped (not an error) when this is unset, so the "
            "API keeps working in any environment that isn't wired to a "
            "real GitHub repository."
        ),
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "secureops/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator(
        "database_url",
        "secondary_language",
        "ollama_base_url",
        "ollama_model",
        "dashboard_frontend_origin",
    )
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        """Reject empty string configuration after trimming whitespace."""
        stripped = value.strip()
        if not stripped:
            msg = "value must not be empty"
            raise ValueError(msg)
        return stripped

    @field_validator("secondary_language")
    @classmethod
    def normalize_secondary_language(cls, value: str) -> str:
        """Normalize language keys for parser and rule dispatch."""
        return value.lower()

    @field_validator("ollama_base_url")
    @classmethod
    def normalize_ollama_base_url(cls, value: str) -> str:
        """Avoid duplicated slashes when clients append endpoint paths."""
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()


__all__ = ["Settings", "get_settings", "settings"]
