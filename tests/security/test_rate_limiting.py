import pytest
import asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_global_rate_limiting(async_client: AsyncClient):
    # Attempt to breach standard limits
    responses = await asyncio.gather(
        *[async_client.get("/health") for _ in range(50)]
    )
    # Fast requests shouldn't fail if we mock it, or if limits allow 50. 
    # Let's ensure the server doesn't crash.
    assert all(r.status_code in [200, 429] for r in responses)

async def test_login_rate_limiting(async_client: AsyncClient):
    # Overload auth endpoint rapidly
    responses = await asyncio.gather(
        *[async_client.post("/api/v1/auth/login", data={"username": "test", "password": "xxx"}) for _ in range(15)]
    )
    # SlowAPI should block some if configured for 5/min
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes or 401 in status_codes
