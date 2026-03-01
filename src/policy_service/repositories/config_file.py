"""YAML-file-based policy repository for Phase 1.

Reads policy configurations from YAML files on disk at startup.
"""

from __future__ import annotations

from pathlib import Path

import structlog
import yaml

from policy_service.exceptions import PolicyConfigError
from policy_service.models.domain import TenantPolicyConfig

logger = structlog.get_logger()


class ConfigFilePolicyRepository:
    """Loads tenant configs from YAML files in a config directory.

    Convention:
      - config/{tenant_id}_policy.yaml  → tenant-specific config
      - config/default_policy.yaml      → fallback for unknown tenants
    """

    def __init__(self, config_dir: str) -> None:
        self._configs: dict[str, TenantPolicyConfig] = {}
        self._default: TenantPolicyConfig | None = None
        self._load(config_dir)

    def _load(self, config_dir: str) -> None:
        config_path = Path(config_dir)
        if not config_path.is_dir():
            raise PolicyConfigError(f"Config directory not found: {config_dir}")

        default_file = config_path / "default_policy.yaml"
        if not default_file.exists():
            raise PolicyConfigError(f"Default policy file not found: {default_file}")

        self._default = self._parse_file(default_file)
        logger.info("loaded_default_policy", config_dir=config_dir)

        for yaml_file in config_path.glob("*_policy.yaml"):
            if yaml_file.name == "default_policy.yaml":
                continue
            tenant_id = yaml_file.name.removesuffix("_policy.yaml")
            self._configs[tenant_id] = self._parse_file(yaml_file)
            logger.info("loaded_tenant_policy", tenant_id=tenant_id)

    @staticmethod
    def _parse_file(path: Path) -> TenantPolicyConfig:
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return TenantPolicyConfig.model_validate(data)
        except Exception as exc:
            raise PolicyConfigError(f"Failed to parse {path}: {exc}") from exc

    def get_tenant_config(self, tenant_id: str) -> TenantPolicyConfig | None:
        return self._configs.get(tenant_id)

    def get_default_config(self) -> TenantPolicyConfig:
        assert self._default is not None  # noqa: S101
        return self._default
