"""FastAPI application entrypoint for SecureOps."""

from fastapi import FastAPI

from app.api.analyses import router as analyses_router
from app.api.errors import register_error_handlers
from app.api.findings import router as findings_router


def create_app() -> FastAPI:
    """Create and configure the SecureOps API application."""
    api = FastAPI(
        title="SecureOps",
        description="PR-first vulnerability feedback service.",
        version="0.1.0",
    )

    @api.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api.include_router(analyses_router)
    api.include_router(findings_router)
    register_error_handlers(api)

    return api


app = create_app()


__all__ = ["app", "create_app"]
