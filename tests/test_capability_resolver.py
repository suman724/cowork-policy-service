"""Tests for capability resolver intersection logic."""

from __future__ import annotations

import pytest

from policy_service.models.domain import CapabilityConfig
from policy_service.services.capability_resolver import resolve_capabilities


@pytest.mark.unit
class TestCapabilityResolver:
    def _make_caps(self) -> list[CapabilityConfig]:
        return [
            CapabilityConfig(name="File.Read", allowed_paths=["."]),
            CapabilityConfig(name="File.Write", allowed_paths=["."]),
            CapabilityConfig(name="Shell.Exec", allowed_commands=["git"]),
            CapabilityConfig(name="Network.Http", allowed_domains=["*.github.com"]),
        ]

    def test_returns_requested_subset(self) -> None:
        result = resolve_capabilities(self._make_caps(), ["File.Read", "Shell.Exec"])
        names = [c.name for c in result]
        assert names == ["File.Read", "Shell.Exec"]

    def test_ignores_unknown_capabilities(self) -> None:
        result = resolve_capabilities(self._make_caps(), ["File.Read", "Teleport.Beam"])
        assert len(result) == 1
        assert result[0].name == "File.Read"

    def test_returns_all_when_empty_request(self) -> None:
        result = resolve_capabilities(self._make_caps(), [])
        assert len(result) == 4

    def test_preserves_scope_constraints(self) -> None:
        result = resolve_capabilities(self._make_caps(), ["Shell.Exec"])
        assert result[0].allowedCommands == ["git"]
