from fastapi import HTTPException

from target.common import create_base_app

app = create_base_app("payments")

PAYMENTS_LOG: list[dict] = []

@app.post("/charge")
async def charge(payment: dict):
    if app.state.fault_status == "wrong_service_port":
        app.state.logger.error("Connection refused: payment backend failed to bind on internal port 8003", extra={"service": "payments"})
        raise HTTPException(status_code=502, detail="Port mismatch / backend unreachable")

    if app.state.fault_status == "slow_db":
        import asyncio
        app.state.logger.warning("Slow query detected: SELECT pg_sleep(3.5) on payment_ledger taking > 3000ms", extra={"service": "payments"})
        await asyncio.sleep(1.5)

    charge_record = {
        "payment_id": len(PAYMENTS_LOG) + 1,
        "order_id": payment.get("order_id"),
        "amount": payment.get("amount", 0.0),
        "status": "APPROVED",
    }
    PAYMENTS_LOG.append(charge_record)
    app.state.logger.info(f"Payment processed id={charge_record['payment_id']} amount={charge_record['amount']}", extra={"service": "payments"})
    return charge_record
