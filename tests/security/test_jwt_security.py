import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_expired_jwt(async_client: AsyncClient):
    # Depending on how flexible testing JWT generation is, we simulate invalid
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiZXhwIjoxNTE2MjM5MDIyfQ.invalid"}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401

async def test_missing_jwt(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/auth/me")
    assert resp.status_code == 401

async def test_wrong_algorithm_jwt(async_client: AsyncClient):
    headers = {"Authorization": "Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6MX0."}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
