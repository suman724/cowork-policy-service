"""Tests for YAML config loading."""

from __future__ import annotations

import pytest

from policy_service.exceptions import PolicyConfigError
from policy_service.repositories.config_file import ConfigFilePolicyRepository


@pytest.mark.unit
class TestConfigLoading:
    def test_loads_default_config(self) -> None:
        repo = ConfigFilePolicyRepository("config")
        config = repo.get_default_config()
        assert config.tenant_id == "default"
        assert len(config.capabilities) == 9

    def test_raises_on_missing_directory(self) -> None:
        with pytest.raises(PolicyConfigError, match="not found"):
            ConfigFilePolicyRepository("/nonexistent/path")

    def test_raises_on_missing_default_file(self, tmp_path: object) -> None:
        with pytest.raises(PolicyConfigError, match="Default policy file not found"):
            ConfigFilePolicyRepository(str(tmp_path))
