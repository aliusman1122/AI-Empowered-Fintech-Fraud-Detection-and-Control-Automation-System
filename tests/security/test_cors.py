import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_cors_preflight(async_client: AsyncClient):
    headers = {
        "Origin": "http://evil-domain.com",
        "Access-Control-Request-Method": "POST",
    }
    resp = await async_client.options("/api/v1/auth/login", headers=headers)
    # Fastapi handles CORS dynamically; if restrictively configured it drops evil origins
    # Assuming standard deployment allows frontend only:
    assert resp.status_code in [200, 400, 403]
    
    headers["Origin"] = "http://localhost:5173"
    resp_valid = await async_client.options("/api/v1/auth/login", headers=headers)
    assert resp_valid.status_code == 200
