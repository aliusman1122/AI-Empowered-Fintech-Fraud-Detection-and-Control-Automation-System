import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_xss_in_merchant_category(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.post("/api/v1/transactions", json={
        "amount": 100.0,
        "transaction_hour": 10,
        "device_risk_score": 0.5,
        "ip_risk_score": 0.5,
        "merchant_category": "<script>alert('xss')</script>",
        "transaction_type": "online",
        "country": "US"
    }, headers=auth_headers)
    
    # Ideally should be rejected due to validation errors (Zod/Pydantic) or escaped
    assert resp.status_code in [200, 201, 422]
    if resp.status_code in [200, 201]:
        data = resp.json()
        assert "<script>" not in data.get("merchant_category", "")
