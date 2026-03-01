"""In-memory policy repository for unit tests."""

from __future__ import annotations

from policy_service.models.domain import TenantPolicyConfig


class InMemoryPolicyRepository:
    """Simple dict-backed repository for testing."""

    def __init__(
        self,
        default_config: TenantPolicyConfig,
        tenant_configs: dict[str, TenantPolicyConfig] | None = None,
    ) -> None:
        self._default = default_config
        self._configs = dict(tenant_configs) if tenant_configs else {}

    def get_tenant_config(self, tenant_id: str) -> TenantPolicyConfig | None:
        return self._configs.get(tenant_id)

    def get_default_config(self) -> TenantPolicyConfig:
        return self._default
