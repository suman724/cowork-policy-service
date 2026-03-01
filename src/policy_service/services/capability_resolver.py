"""Resolve requested capabilities against tenant policy configuration."""

from __future__ import annotations

import structlog
from cowork_platform.policy_bundle import Capability

from policy_service.models.domain import CapabilityConfig

logger = structlog.get_logger()


def resolve_capabilities(
    tenant_capabilities: list[CapabilityConfig],
    requested: list[str],
) -> list[Capability]:
    """Filter tenant capabilities to the requested subset.

    Returns only capabilities whose name appears in `requested`.
    If `requested` is empty, returns all tenant capabilities.
    """
    available: dict[str, CapabilityConfig] = {cap.name: cap for cap in tenant_capabilities}

    if not requested:
        resolved = list(available.values())
    else:
        resolved = [available[name] for name in requested if name in available]
        unknown = [name for name in requested if name not in available]
        if unknown:
            logger.warning("unknown_capabilities_requested", unknown=unknown)

    return [_to_capability(config) for config in resolved]


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
