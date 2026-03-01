"""Repository protocol for policy configuration access."""

from __future__ import annotations

from typing import Protocol

from policy_service.models.domain import TenantPolicyConfig


class PolicyRepository(Protocol):
    """Interface for accessing tenant policy configurations."""

    def get_tenant_config(self, tenant_id: str) -> TenantPolicyConfig | None:
        """Return the policy config for a specific tenant, or None if not found."""
        ...

    def get_default_config(self) -> TenantPolicyConfig:
        """Return the default policy config (always available)."""
        ...
