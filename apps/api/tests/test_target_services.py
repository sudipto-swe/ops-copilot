import httpx
import pytest

from target.gateway.main import app as gateway_app
from target.orders.main import app as orders_app
from target.payments.main import app as payments_app


@pytest.mark.asyncio
async def test_gateway_health():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway_app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["service"] == "gateway"

@pytest.mark.asyncio
async def test_orders_health_and_metrics():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=orders_app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200

        metrics_resp = await client.get("/metrics")
        assert metrics_resp.status_code == 200
        assert "orders_requests_total" in metrics_resp.text

@pytest.mark.asyncio
async def test_payments_health():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=payments_app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
