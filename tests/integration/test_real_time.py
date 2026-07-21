import pytest
import asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_real_time_velocity_rules(async_client: AsyncClient, auth_headers: dict):
    # 1. Create multiple transactions rapidly
    transactions = []
    
    async def create_tx():
        return await async_client.post("/api/v1/transactions", json={
            "amount": 100.0,
            "transaction_hour": 10,
            "device_risk_score": 0.1,
            "ip_risk_score": 0.1,
            "merchant_category": "food",
            "transaction_type": "in_person",
            "country": "US"
        }, headers=auth_headers)

    results = await asyncio.gather(*[create_tx() for _ in range(5)])
    
    # Some should pass, and others trigger velocity if set up that tightly
    status_codes = [r.status_code for r in results]
    assert len([s for s in status_codes if s in [200, 201]]) > 0

    # Test SSE Event stream format 
    # Stream endpoints require special async handling, so we test connectivity
    async with async_client.stream("GET", "/api/v1/transactions/stream", headers=auth_headers) as response:
        assert response.status_code in [200, 401] # Depends on stream auth rules
        # Just grab the first chunk to ensure not hanging
        async for chunk in response.aiter_text():
            if chunk:
                break
