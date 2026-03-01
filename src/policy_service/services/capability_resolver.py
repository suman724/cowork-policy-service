"""Resolve requested capabilities against tenant policy configuration."""

from __future__ import annotations

from cowork_platform.policy_bundle import Capability

from policy_service.models.domain import CapabilityConfig


def resolve_capabilities(
    tenant_capabilities: list[CapabilityConfig],
    requested: list[str],
) -> list[Capability]:
    """Filter tenant capabilities to the requested subset.

    Returns only capabilities whose name appears in `requested`.
    If `requested` is empty, returns all tenant capabilities.
    """
    available = {cap.name: cap for cap in tenant_capabilities}

    if not requested:
        names = list(available.keys())
    else:
        names = [name for name in requested if name in available]

    return [_to_capability(available[name]) for name in names]


def _to_capability(config: CapabilityConfig) -> Capability:
    """Convert internal config shape to the platform Capability model."""
    return Capability(
        name=config.name,
        allowedPaths=config.allowed_paths,
        blockedPaths=config.blocked_paths,
        allowedCommands=config.allowed_commands,
        blockedCommands=config.blocked_commands,
        allowedDomains=config.allowed_domains,
        maxFileSizeBytes=config.max_file_size_bytes,
        maxOutputBytes=config.max_output_bytes,
        requiresApproval=config.requires_approval,
        approvalRuleId=config.approval_rule_id,
    )
