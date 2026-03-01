"""GET /policy-bundles endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from policy_service.dependencies import get_policy_service
from policy_service.services.policy_service import PolicyService

router = APIRouter(tags=["policy"])


@router.get("/policy-bundles")
async def get_policy_bundle(
    tenant_id: str = Query(alias="tenantId"),
    user_id: str = Query(alias="userId"),
    session_id: str = Query(alias="sessionId"),
    capabilities: str = Query(default="", description="Comma-separated capability names"),
    service: PolicyService = Depends(get_policy_service),
) -> dict[str, Any]:
    cap_list = [c.strip() for c in capabilities.split(",") if c.strip()] if capabilities else []

    bundle = service.generate_bundle(
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        capabilities=cap_list,
    )
    result: dict[str, Any] = bundle.model_dump(mode="json")
    return result
