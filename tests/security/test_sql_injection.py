import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_sql_injection_login(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/login", data={
        "username": "admin' OR '1'='1",
        "password": "password"
    })
    assert resp.status_code == 401
    
    resp2 = await async_client.post("/api/v1/auth/login", data={
        "username": "admin@example.com",
        "password": "' OR 1=1 --"
    })
    assert resp2.status_code == 401

async def test_sql_injection_transactions(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.get("/api/v1/transactions?skip=0&limit=10; DROP TABLE users;", headers=auth_headers)
    assert resp.status_code == 422
