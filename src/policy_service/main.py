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

    return app


async def _service_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ServiceError)  # noqa: S101
    body: dict[str, Any] = {
        "code": exc.code,
        "message": exc.message,
        "retryable": exc.status_code >= 500,
    }
    return JSONResponse(status_code=exc.status_code, content=body)


app = create_app()
