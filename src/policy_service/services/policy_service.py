"""Core business logic: assemble a PolicyBundle for a session."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cowork_platform.policy_bundle import ApprovalRule, LlmPolicy, PolicyBundle

from policy_service.config import Settings
from policy_service.exceptions import ValidationError
from policy_service.models.domain import ApprovalRuleConfig, TenantPolicyConfig
from policy_service.repositories.base import PolicyRepository
from policy_service.services.capability_resolver import resolve_capabilities


class PolicyService:
    def __init__(self, repo: PolicyRepository, settings: Settings) -> None:
        self._repo = repo
        self._settings = settings

    def generate_bundle(
        self,
        *,
        tenant_id: str,
        user_id: str,
        session_id: str,
        capabilities: list[str],
    ) -> PolicyBundle:
        if not tenant_id or not user_id or not session_id:
            raise ValidationError("tenantId, userId, and sessionId are required")

        config = self._repo.get_tenant_config(tenant_id)
        if config is None:
            config = self._repo.get_default_config()

        resolved = resolve_capabilities(config.capabilities, capabilities)

        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=self._settings.policy_expiry_hours)
        version = now.strftime("%Y-%m-%d") + ".1"

        return PolicyBundle(
            policyBundleVersion=version,
            schemaVersion=self._settings.schema_version,
            tenantId=tenant_id,
            userId=user_id,
            sessionId=session_id,
            expiresAt=expires_at,
            capabilities=resolved,
            llmPolicy=_to_llm_policy(config),
            approvalRules=_to_approval_rules(config.approval_rules),
        )


def _to_llm_policy(config: TenantPolicyConfig) -> LlmPolicy:
    return LlmPolicy(
        allowedModels=config.llm_policy.allowed_models,
        maxInputTokens=config.llm_policy.max_input_tokens,
        maxOutputTokens=config.llm_policy.max_output_tokens,
        maxSessionTokens=config.llm_policy.max_session_tokens,
    )


def _to_approval_rules(rules: list[ApprovalRuleConfig]) -> list[ApprovalRule]:
    return [
        ApprovalRule(
            approvalRuleId=r.approval_rule_id,
            title=r.title,
            description=r.description,
        )
        for r in rules
    ]
