import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_register_duplicate_email(async_client: AsyncClient):
    # Valid reg
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "unique@example.com",
        "password": "StrongPassword123!"
    })
    assert resp.status_code == 201

    # Dup
    resp2 = await async_client.post("/api/v1/auth/register", json={
        "email": "unique@example.com",
        "password": "StrongPassword123!"
    })
    assert resp2.status_code == 409

async def test_register_weak_password(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "weak"
    })
    assert resp.status_code == 422

async def test_login_success(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json={
        "email": "logintest@example.com",
        "password": "StrongPassword123!"
    })
    
    resp = await async_client.post("/api/v1/auth/login", data={
        "username": "logintest@example.com",
        "password": "StrongPassword123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data

async def test_login_invalid_credentials(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/login", data={
        "username": "nonexistent@example.com",
        "password": "wrong"
    })
    assert resp.status_code == 401

async def test_get_me_unauthenticated(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/auth/me")
    assert resp.status_code == 401

async def test_get_me_authenticated(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"
