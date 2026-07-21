import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_create_transaction_unauthenticated(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/transactions", json={"amount": 100})
    assert resp.status_code == 401

async def test_create_transaction_success(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.post("/api/v1/transactions", json={
        "amount": 1500.0,
        "transaction_hour": 14,
        "device_risk_score": 0.2,
        "ip_risk_score": 0.1,
        "merchant_category": "electronics",
        "transaction_type": "online",
        "country": "US"
    }, headers=auth_headers)
    assert resp.status_code in (200, 201)
    
    data = resp.json()
    assert "transaction_id" in data
    assert "fraud_probability" in data
    assert "status" in data

async def test_get_transactions_paginated(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.get("/api/v1/transactions?skip=0&limit=10", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

async def test_predict_fraud(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.post("/api/v1/transactions/predict", json={
        "amount": 9999.0,
        "transaction_hour": 3,
        "device_risk_score": 0.9,
        "ip_risk_score": 0.9,
        "merchant_category": "crypto",
        "transaction_type": "online",
        "country": "RU"
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "fraud_probability" in data
    assert "fraud_flag" in data
    assert "reason_codes" in data
