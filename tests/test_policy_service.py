"""Tests for PolicyService bundle generation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from policy_service.exceptions import ValidationError
from policy_service.services.policy_service import PolicyService


@pytest.mark.unit
class TestBundleGeneration:
    def test_generates_bundle_with_all_fields(self, policy_service: PolicyService) -> None:
        bundle = policy_service.generate_bundle(
            tenant_id="default",
            user_id="user-1",
            session_id="sess-1",
            capabilities=["File.Read"],
        )
        assert bundle.tenantId == "default"
        assert bundle.userId == "user-1"
        assert bundle.sessionId == "sess-1"
        assert bundle.schemaVersion == "1.0"
        assert len(bundle.capabilities) == 1
        assert bundle.capabilities[0].name == "File.Read"
        assert bundle.llmPolicy.allowedModels == ["claude-sonnet-4-20250514"]

    def test_bundle_expiry(self, policy_service: PolicyService) -> None:
        before = datetime.now(UTC)
        bundle = policy_service.generate_bundle(
            tenant_id="default",
            user_id="user-1",
            session_id="sess-1",
            capabilities=[],
        )
        after = datetime.now(UTC)

        expected_min = before + timedelta(hours=24)
        expected_max = after + timedelta(hours=24)
        assert expected_min <= bundle.expiresAt <= expected_max

    def test_bundle_version_format(self, policy_service: PolicyService) -> None:
        bundle = policy_service.generate_bundle(
            tenant_id="default",
            user_id="user-1",
            session_id="sess-1",
            capabilities=[],
        )
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        assert bundle.policyBundleVersion.startswith(f"{today}.")
        # Suffix should be an 8-char hex string (UUID-based)
        suffix = bundle.policyBundleVersion.split(".", maxsplit=3)[-1]
        assert len(suffix) == 8
        int(suffix, 16)  # validates it's a hex string

    def test_falls_back_to_default_config(self, policy_service: PolicyService) -> None:
        bundle = policy_service.generate_bundle(
            tenant_id="unknown-tenant",
            user_id="user-1",
            session_id="sess-1",
            capabilities=["File.Read"],
        )
        assert bundle.tenantId == "unknown-tenant"
        assert len(bundle.capabilities) == 1

    def test_uses_tenant_specific_config(self, policy_service: PolicyService) -> None:
        bundle = policy_service.generate_bundle(
            tenant_id="acme",
            user_id="user-1",
            session_id="sess-1",
            capabilities=[],
        )
        assert bundle.llmPolicy.allowedModels == ["claude-haiku-4-20250414"]
        assert len(bundle.capabilities) == 2

    def test_validation_error_on_missing_fields(self, policy_service: PolicyService) -> None:
        with pytest.raises(ValidationError, match="required"):
            policy_service.generate_bundle(
                tenant_id="",
                user_id="user-1",
                session_id="sess-1",
                capabilities=[],
            )
