"""FastAPI dependency providers."""

from __future__ import annotations

from fastapi import Request

from policy_service.services.policy_service import PolicyService


def get_policy_service(request: Request) -> PolicyService:
    return request.app.state.policy_service  # type: ignore[no-any-return]
