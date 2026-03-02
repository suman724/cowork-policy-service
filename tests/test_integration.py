"""Integration tests for policy service with real YAML config loading.

Tests the full app stack: HTTP routes → service → ConfigFilePolicyRepository → YAML files.
No external infrastructure required (no DynamoDB, no LocalStack).
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from policy_service.config import Settings
from policy_service.main import create_app
from policy_service.repositories.config_file import ConfigFilePolicyRepository
from policy_service.services.policy_service import PolicyService


@pytest.fixture(scope="module")
async def integration_client() -> AsyncIterator[AsyncClient]:
    """Create test client with real ConfigFilePolicyRepository loading YAML config."""
    app = create_app()
    # ASGITransport doesn't trigger lifespan, so set up the service manually
    settings = Settings()
    repo = ConfigFilePolicyRepository(settings.config_dir)
    app.state.policy_service = PolicyService(repo, settings)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.integration
class TestPolicyIntegration:
    async def test_health_endpoint(self, integration_client: AsyncClient) -> None:
        resp = await integration_client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    async def test_get_bundle_default_tenant(self, integration_client: AsyncClient) -> None:
        resp = await integration_client.get(
            "/policy-bundles",
            params={
                "tenantId": "unknown-tenant",
                "userId": "u1",
                "sessionId": "sess-1",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "capabilities" in body
        assert "llmPolicy" in body
        assert len(body["capabilities"]) > 0

    async def test_get_bundle_with_capabilities_filter(
        self, integration_client: AsyncClient
    ) -> None:
        resp = await integration_client.get(
            "/policy-bundles",
            params={
                "tenantId": "default",
                "userId": "u1",
                "sessionId": "sess-1",
                "capabilities": "File.Read,Shell.Exec",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        cap_names = [c["name"] for c in body["capabilities"]]
        assert "File.Read" in cap_names
        assert "Shell.Exec" in cap_names
        assert len(cap_names) == 2

    async def test_get_bundle_all_capabilities(self, integration_client: AsyncClient) -> None:
        resp = await integration_client.get(
            "/policy-bundles",
            params={
                "tenantId": "default",
                "userId": "u1",
                "sessionId": "sess-1",
                "capabilities": "",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        # Default config has 9 capabilities
        assert len(body["capabilities"]) == 9

    async def test_bundle_has_required_fields(self, integration_client: AsyncClient) -> None:
        resp = await integration_client.get(
            "/policy-bundles",
            params={
                "tenantId": "default",
                "userId": "u1",
                "sessionId": "sess-1",
            },
        )
        assert resp.status_code == 200
        body = resp.json()

        assert "schemaVersion" in body
        assert "policyBundleVersion" in body
        assert "expiresAt" in body
        assert "capabilities" in body
        assert "llmPolicy" in body
        assert "approvalRules" in body

        # Version format: YYYY-MM-DD.{8-char hex}
        assert re.match(r"\d{4}-\d{2}-\d{2}\.[a-f0-9]{8}", body["policyBundleVersion"])

    async def test_missing_required_params(self, integration_client: AsyncClient) -> None:
        resp = await integration_client.get("/policy-bundles")
        assert resp.status_code == 422
