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


@pytest.mark.unit
class TestBrowserPolicyGeneration:
    """Tests for browser capability inclusion/exclusion based on tenant config and environment."""

    def test_browser_capabilities_included_for_desktop(self, policy_service: PolicyService) -> None:
        """Desktop session with browser-enabled tenant gets Browser.* capabilities."""
        bundle = policy_service.generate_bundle(
            tenant_id="browser-corp",
            user_id="user-1",
            session_id="sess-1",
            capabilities=[],
            execution_environment="desktop",
        )
        cap_names = {cap.name for cap in bundle.capabilities}
        assert "Browser.Navigate" in cap_names
        assert "Browser.Interact" in cap_names
        assert "Browser.Extract" in cap_names
        assert "Browser.Submit" in cap_names
        assert "Browser.Download" in cap_names

    def test_browser_capabilities_excluded_for_sandbox(self, policy_service: PolicyService) -> None:
        """Sandbox session never gets Browser.* capabilities."""
        bundle = policy_service.generate_bundle(
            tenant_id="browser-corp",
            user_id="user-1",
            session_id="sess-1",
            capabilities=[],
            execution_environment="sandbox",
        )
        cap_names = {cap.name for cap in bundle.capabilities}
        assert "Browser.Navigate" not in cap_names
        assert "Browser.Interact" not in cap_names
        assert "Browser.Submit" not in cap_names
        # Non-browser capabilities should still be present
        assert "File.Read" in cap_names
        assert "Shell.Exec" in cap_names

    def test_browser_capabilities_absent_when_not_configured(
        self, policy_service: PolicyService
    ) -> None:
        """Default tenant config has no browser capabilities."""
        bundle = policy_service.generate_bundle(
            tenant_id="default",
            user_id="user-1",
            session_id="sess-1",
            capabilities=[],
            execution_environment="desktop",
        )
        cap_names = {cap.name for cap in bundle.capabilities}
        assert not any(name.startswith("Browser.") for name in cap_names)

    def test_browser_domain_scopes_in_bundle(self, policy_service: PolicyService) -> None:
        """Browser.Navigate includes allowedDomains and blockedDomains."""
        bundle = policy_service.generate_bundle(
            tenant_id="browser-corp",
            user_id="user-1",
            session_id="sess-1",
            capabilities=["Browser.Navigate"],
            execution_environment="desktop",
        )
        nav_cap = next(c for c in bundle.capabilities if c.name == "Browser.Navigate")
        assert nav_cap.allowedDomains == ["*.atlassian.net", "github.com"]
        assert nav_cap.blockedDomains == ["*.gambling.com"]

    def test_browser_approval_rules_included(self, policy_service: PolicyService) -> None:
        """Browser approval rules included when browser capabilities are resolved."""
        bundle = policy_service.generate_bundle(
            tenant_id="browser-corp",
            user_id="user-1",
            session_id="sess-1",
            capabilities=["Browser.Submit", "Browser.Download"],
            execution_environment="desktop",
        )
        rule_ids = {r.approvalRuleId for r in bundle.approvalRules}
        assert "browser-submit-approval" in rule_ids
        assert "browser-download-approval" in rule_ids

    def test_default_execution_environment_is_desktop(self, policy_service: PolicyService) -> None:
        """Default execution_environment is desktop — browser caps included if configured."""
        bundle = policy_service.generate_bundle(
            tenant_id="browser-corp",
            user_id="user-1",
            session_id="sess-1",
            capabilities=[],
        )
        cap_names = {cap.name for cap in bundle.capabilities}
        assert "Browser.Navigate" in cap_names
