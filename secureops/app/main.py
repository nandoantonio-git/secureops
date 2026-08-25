"""FastAPI application entrypoint for SecureOps."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyses import router as analyses_router
from app.api.dashboard import router as dashboard_router
from app.api.errors import register_error_handlers
from app.api.findings import router as findings_router
from app.config import settings


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
    api.include_router(dashboard_router)
    register_error_handlers(api)

    # The dashboard frontend is a separate origin (Vite dev server locally).
    # There is no auth/cookie mechanism anywhere in this API today, so
    # credentials stay disabled -- this only unblocks the browser fetches.
    api.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.dashboard_frontend_origin],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    return api


app = create_app()


__all__ = ["app", "create_app"]
