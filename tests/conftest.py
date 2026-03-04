"""Shared fixtures for policy service tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from policy_service.config import Settings
from policy_service.dependencies import get_policy_service
from policy_service.exceptions import ServiceError
from policy_service.models.domain import (
    ApprovalRuleConfig,
    CapabilityConfig,
    LlmPolicyConfig,
    TenantPolicyConfig,
)
from policy_service.repositories.memory import InMemoryPolicyRepository
from policy_service.routes import health, policy_bundles
from policy_service.services.policy_service import PolicyService


@pytest.fixture
def default_config() -> TenantPolicyConfig:
    return TenantPolicyConfig(
        tenant_id="default",
        capabilities=[
            CapabilityConfig(
                name="File.Read",
                allowed_paths=["."],
                max_file_size_bytes=10485760,
            ),
            CapabilityConfig(
                name="File.Write",
                allowed_paths=["."],
                requires_approval=True,
                approval_rule_id="file-write-approval",
            ),
            CapabilityConfig(
                name="Shell.Exec",
                allowed_commands=["git", "python"],
                max_output_bytes=1048576,
            ),
            CapabilityConfig(
                name="Network.Http",
                blocked_domains=["169.254.169.254", "localhost", "127.0.0.1"],
            ),
        ],
        llm_policy=LlmPolicyConfig(
            allowed_models=["claude-sonnet-4-20250514"],
            max_input_tokens=200000,
            max_output_tokens=16384,
            max_session_tokens=1000000,
        ),
        approval_rules=[
            ApprovalRuleConfig(
                approval_rule_id="file-write-approval",
                title="File Write",
                description="Approve file write",
            ),
        ],
    )


@pytest.fixture
def tenant_acme_config() -> TenantPolicyConfig:
    return TenantPolicyConfig(
        tenant_id="acme",
        capabilities=[
            CapabilityConfig(name="File.Read", allowed_paths=["."]),
            CapabilityConfig(name="Shell.Exec", allowed_commands=["git"]),
        ],
        llm_policy=LlmPolicyConfig(
            allowed_models=["claude-haiku-4-20250414"],
            max_input_tokens=100000,
            max_output_tokens=8192,
            max_session_tokens=500000,
        ),
    )


@pytest.fixture
def settings() -> Settings:
    return Settings(env="test", policy_expiry_hours=24, schema_version="1.0")


@pytest.fixture
def repo(
    default_config: TenantPolicyConfig,
    tenant_acme_config: TenantPolicyConfig,
) -> InMemoryPolicyRepository:
    return InMemoryPolicyRepository(
        default_config=default_config,
        tenant_configs={"acme": tenant_acme_config},
    )


@pytest.fixture
def policy_service(repo: InMemoryPolicyRepository, settings: Settings) -> PolicyService:
    return PolicyService(repo, settings)


@pytest.fixture
async def client(policy_service: PolicyService) -> AsyncIterator[AsyncClient]:
    async def _service_error_handler(request: Request, exc: Exception) -> JSONResponse:
        se = (
            exc
            if isinstance(exc, ServiceError)
            else ServiceError(
                "Unknown",
                code="INTERNAL_ERROR",
                status_code=500,
            )
        )
        body: dict[str, Any] = {
            "code": se.code,
            "message": se.message,
            "retryable": se.status_code >= 500,
        }
        return JSONResponse(status_code=se.status_code, content=body)

    app = FastAPI()
    app.include_router(health.router)
    app.include_router(policy_bundles.router)
    app.add_exception_handler(ServiceError, _service_error_handler)

    app.dependency_overrides[get_policy_service] = lambda: policy_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
