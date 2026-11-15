#!/usr/bin/env bash
set -e

echo "=== Running Ops Copilot Smoke Tests ==="

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

# Ensure services are up
bash scripts/start_services.sh

echo "Verifying health endpoints..."
curl -fsS http://127.0.0.1:8001/health | grep '"status":"ok"' >/dev/null
echo "✓ Gateway is healthy"

curl -fsS http://127.0.0.1:8002/health | grep '"status":"ok"' >/dev/null
echo "✓ Orders is healthy"

curl -fsS http://127.0.0.1:8003/health | grep '"status":"ok"' >/dev/null
echo "✓ Payments is healthy"

curl -fsS http://127.0.0.1:8000/health | grep '"status":"ok"' >/dev/null
echo "✓ Ops Copilot API is healthy"

echo "Verifying Prometheus metrics endpoint..."
curl -fsS http://127.0.0.1:8001/metrics | grep "gateway_requests_total" >/dev/null
echo "✓ Prometheus metrics live on Gateway"

echo "=== Smoke Tests Succeeded ==="
