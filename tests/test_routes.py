"""Tests for HTTP endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestHealthRoutes:
    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async def test_ready(self, client: AsyncClient) -> None:
        resp = await client.get("/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.unit
class TestPolicyBundleRoute:
    async def test_returns_bundle(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/policy-bundles",
            params={
                "tenantId": "default",
                "userId": "user-1",
                "sessionId": "sess-1",
                "capabilities": "File.Read,Shell.Exec",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenantId"] == "default"
        assert data["sessionId"] == "sess-1"
        cap_names = [c["name"] for c in data["capabilities"]]
        assert "File.Read" in cap_names
        assert "Shell.Exec" in cap_names

    async def test_returns_all_caps_when_empty(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/policy-bundles",
            params={
                "tenantId": "default",
                "userId": "user-1",
                "sessionId": "sess-1",
                "capabilities": "",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["capabilities"]) == 4  # test fixture has 4 caps

    async def test_missing_required_params(self, client: AsyncClient) -> None:
        resp = await client.get("/policy-bundles")
        assert resp.status_code == 422
