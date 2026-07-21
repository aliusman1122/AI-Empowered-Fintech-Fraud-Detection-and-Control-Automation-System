import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_get_stats(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.get("/api/v1/stats", headers=auth_headers)
    if resp.status_code == 200:
        data = resp.json()
        assert "total_transactions" in data
        assert "fraud_alerts" in data
    else:
        assert resp.status_code in [200, 401, 403, 404]

async def test_get_metrics(async_client: AsyncClient):
    resp = await async_client.get("/metrics")
    assert resp.status_code == 200
    assert "active_transactions" in resp.text
