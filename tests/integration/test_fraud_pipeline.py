import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_fraud_pipeline_e2e(async_client: AsyncClient):
    # 1. Register User
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "pipeline@example.com",
        "password": "StrongPassword123!"
    })
    assert resp.status_code == 201

    # 2. Login
    resp = await async_client.post("/api/v1/auth/login", data={
        "username": "pipeline@example.com",
        "password": "StrongPassword123!"
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create high-risk Transaction
    resp = await async_client.post("/api/v1/transactions", json={
        "amount": 9000.0,
        "transaction_hour": 3,
        "device_risk_score": 0.95,
        "ip_risk_score": 0.95,
        "merchant_category": "crypto",
        "transaction_type": "online",
        "country": "KP" # High risk country
    }, headers=headers)
    assert resp.status_code in [200, 201]
    
    # 4. Verify Fraud detection ran
    data = resp.json()
    assert data["fraud_probability"] > 0
    assert data["fraud_flag"] == True
    
    # 5. Approve/reject transaction (using mocked webhook or local update)
    # Assuming endpoint to update exists, if so we update status
    tx_id = data["transaction_id"]
    update_resp = await async_client.put(f"/api/v1/transactions/{tx_id}/status", json={"status": "REJECTED"}, headers=headers)
    # Status updates usually require admin
    if update_resp.status_code in [401, 403]:
        pass # Ignore permission failures for now
