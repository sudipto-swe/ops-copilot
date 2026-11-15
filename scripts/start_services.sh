#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

mkdir -p logs .pids

echo "Starting Target Services and Ops Copilot processes..."

# Kill any existing instances
bash scripts/stop_services.sh 2>/dev/null || true

PYTHON=".venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

$PYTHON -m uvicorn target.gateway.main:app --host 127.0.0.1 --port 8001 > logs/gateway.log 2>&1 &
echo $! > .pids/gateway.pid

$PYTHON -m uvicorn target.orders.main:app --host 127.0.0.1 --port 8002 > logs/orders.log 2>&1 &
echo $! > .pids/orders.pid

$PYTHON -m uvicorn target.payments.main:app --host 127.0.0.1 --port 8003 > logs/payments.log 2>&1 &
echo $! > .pids/payments.pid

$PYTHON -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 > logs/api.log 2>&1 &
echo $! > .pids/api.pid

echo "Waiting for services to be ready..."
sleep 2

for port in 8001 8002 8003 8000; do
  curl -s --retry 5 --retry-delay 1 "http://127.0.0.1:${port}/health" > /dev/null && echo "Service on port $port is ready" || echo "Warning: port $port not ready yet"
done

echo "All services started successfully."
