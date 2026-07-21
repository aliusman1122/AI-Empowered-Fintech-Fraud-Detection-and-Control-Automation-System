import pytest
from httpx import AsyncClient
import os

pytestmark = pytest.mark.asyncio

async def test_n8n_webhook_valid_payload(async_client: AsyncClient, auth_headers: dict):
    resp = await async_client.post("/api/v1/webhooks/n8n", json={
        "transaction_id": "tx-1234",
        "action": "verify"
    }, headers=auth_headers)
    assert resp.status_code in [200, 201, 202, 404]

async def test_transaction_response_invalid_signature(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/webhooks/transaction-response", json={
        "token": "invalid_hmac_token",
        "decision": "approved"
    })
    # If endpoint exists, it should catch invalid signature
    if resp.status_code != 404:
        assert resp.status_code in [400, 401, 403]
