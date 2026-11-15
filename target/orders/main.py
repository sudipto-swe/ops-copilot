
from fastapi import HTTPException

from target.common import create_base_app

app = create_base_app("orders")

# Synthetic in-memory orders DB
ORDERS_DB: list[dict] = []

@app.get("/orders")
async def list_orders():
    app.state.logger.info(f"Listing orders count={len(ORDERS_DB)}", extra={"service": "orders"})
    return {"orders": ORDERS_DB}

@app.post("/orders")
async def create_order(order: dict):
    if app.state.fault_status == "db_connection_pool_exhausted":
        app.state.logger.error("FATAL: could not obtain connection from pool within 5000ms: pool exhausted (max_connections=20)", extra={"service": "orders"})
        raise HTTPException(status_code=503, detail="Database pool exhausted")

    if app.state.fault_status == "oom_simulation":
        app.state.logger.critical("Process memory exceeded cgroup quota (limit 128MB, current 129MB). OOMKilled invoked.", extra={"service": "orders"})
        raise HTTPException(status_code=500, detail="OOM Killed")

    new_order = {"id": len(ORDERS_DB) + 1, "items": order.get("items", []), "user_id": order.get("user_id", 101)}
    ORDERS_DB.append(new_order)
    app.state.logger.info(f"Created order id={new_order['id']}", extra={"service": "orders"})
    return new_order
