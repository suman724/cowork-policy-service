"""FastAPI application factory for the Policy Service."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from policy_service.config import Settings
from policy_service.exceptions import ServiceError
from policy_service.repositories.config_file import ConfigFilePolicyRepository
from policy_service.routes import health, policy_bundles
from policy_service.services.policy_service import PolicyService

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()

    log_level = logging.getLevelNamesMapping().get(settings.log_level.upper(), logging.INFO)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )

    repo = ConfigFilePolicyRepository(settings.config_dir)
    app.state.policy_service = PolicyService(repo, settings)

    logger.info("policy_service_started", env=settings.env)
    yield
    logger.info("policy_service_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cowork Policy Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(policy_bundles.router)

    app.add_exception_handler(ServiceError, _service_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)

    return app


async def _service_error_handler(request: Request, exc: Exception) -> JSONResponse:
    se = (
        exc
        if isinstance(exc, ServiceError)
        else ServiceError("Unknown", code="INTERNAL_ERROR", status_code=500)
    )
    body: dict[str, Any] = {
        "code": se.code,
        "message": se.message,
        "retryable": se.status_code >= 500,
    }
    return JSONResponse(status_code=se.status_code, content=body)


async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": "Internal server error", "retryable": True},
    )


app = create_app()
