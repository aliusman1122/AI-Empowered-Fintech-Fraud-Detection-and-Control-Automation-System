import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_get_health(async_client: AsyncClient):
    resp = await async_client.get("/health")
    # depending on trailing slashes or router definitions
    if resp.status_code == 404:
        resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

async def test_get_ready(async_client: AsyncClient):
    resp = await async_client.get("/ready")
    if resp.status_code == 404:
        resp = await async_client.get("/api/v1/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["checks"]["db"] == "ok"
    assert data["checks"]["redis"] == "ok"
