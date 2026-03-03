"""Domain models for tenant policy configuration (YAML shape)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

CapabilityName = Literal[
    "File.Read",
    "File.Write",
    "File.Delete",
    "Shell.Exec",
    "Network.Http",
    "Workspace.Upload",
    "BackendTool.Invoke",
    "LLM.Call",
    "Search.Web",
    "Code.Execute",
]


class CapabilityConfig(BaseModel):
    """Single capability definition in tenant YAML config."""

    name: CapabilityName
    allowed_paths: list[str] | None = None
    blocked_paths: list[str] | None = None
    allowed_commands: list[str] | None = None
    blocked_commands: list[str] | None = None
    allowed_domains: list[str] | None = None
    max_file_size_bytes: int | None = None
    max_output_bytes: int | None = None
    requires_approval: bool | None = None
    approval_rule_id: str | None = None
    allowed_languages: list[str] | None = None
    max_execution_time_seconds: int | None = None
    allow_code_network: bool | None = None


class ApprovalRuleConfig(BaseModel):
    """Approval rule definition in tenant YAML config."""

    approval_rule_id: str
    title: str
    description: str


class LlmPolicyConfig(BaseModel):
    """LLM policy constraints in tenant YAML config."""

    allowed_models: list[str]
    max_input_tokens: int = 200000
    max_output_tokens: int = 16384
    max_session_tokens: int = 1000000


class TenantPolicyConfig(BaseModel):
    """Root shape of a tenant's YAML policy config file."""

    tenant_id: str = "default"
    capabilities: list[CapabilityConfig]
    llm_policy: LlmPolicyConfig
    approval_rules: list[ApprovalRuleConfig] = []
