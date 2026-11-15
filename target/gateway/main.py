import os

import httpx

from target.common import create_base_app

app = create_base_app("gateway")

ORDERS_URL = os.getenv("ORDERS_URL", "http://localhost:8002")
PAYMENTS_URL = os.getenv("PAYMENTS_URL", "http://localhost:8003")

@app.get("/api/v1/status")
async def get_system_status():
    app.state.logger.info("Checking downstream services status", extra={"service": "gateway"})
    downstreams = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            res = await client.get(f"{ORDERS_URL}/health")
            downstreams["orders"] = "up" if res.status_code == 200 else f"error_{res.status_code}"
        except httpx.HTTPError as e:
            downstreams["orders"] = f"unreachable: {e!s}"

        try:
            res = await client.get(f"{PAYMENTS_URL}/health")
            downstreams["payments"] = "up" if res.status_code == 200 else f"error_{res.status_code}"
        except httpx.HTTPError as e:
            downstreams["payments"] = f"unreachable: {e!s}"

    return {"service": "gateway", "downstreams": downstreams}

@app.post("/api/v1/checkout")
async def checkout(order: dict):
    req_id = "req-checkout-1"
    app.state.logger.info(f"Processing checkout for user {order.get('user_id')}", extra={"service": "gateway", "request_id": req_id})
    async with httpx.AsyncClient(timeout=3.0) as client:
        # Step 1: Create Order
        res_order = await client.post(f"{ORDERS_URL}/orders", json=order)
        if res_order.status_code != 200:
            app.state.logger.error("Order creation failed in orders service", extra={"service": "gateway", "request_id": req_id})
            return {"error": "Failed to create order", "downstream": "orders"}, 502

        # Step 2: Charge Payment
        res_pay = await client.post(f"{PAYMENTS_URL}/charge", json={"order_id": order.get("id", 1), "amount": order.get("amount", 100)})
        if res_pay.status_code != 200:
            app.state.logger.error("Payment authorization failed", extra={"service": "gateway", "request_id": req_id})
            return {"error": "Payment failed", "downstream": "payments"}, 502

    return {"status": "success", "order": res_order.json(), "payment": res_pay.json()}
