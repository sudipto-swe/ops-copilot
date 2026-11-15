import httpx
import pytest

from scripts.inject_fault import SERVICE_URLS, load_scenarios


def test_load_scenarios_has_minimum_six():
    scenarios = load_scenarios()
    assert len(scenarios) >= 6
    assert "crash_loop" in scenarios
    assert "oom_simulation" in scenarios
    assert "slow_db" in scenarios

@pytest.mark.asyncio
async def test_inject_crash_loop_and_reset():
    scenarios = load_scenarios()
    sc = scenarios["crash_loop"]
    target_url = SERVICE_URLS[sc["service"]]

    async with httpx.AsyncClient() as client:
        # Inject fault
        inject_resp = await client.post(f"{target_url}/simulate_fault", json={"type": sc["fault_type"]})
        assert inject_resp.status_code == 200

        # Verify unhealthy response
        health_resp = await client.get(f"{target_url}/health")
        assert health_resp.status_code == 500

        # Reset to healthy
        reset_resp = await client.post(f"{target_url}/simulate_fault", json={"type": "healthy", "latency_ms": 0})
        assert reset_resp.status_code == 200

        # Verify healthy
        health_resp2 = await client.get(f"{target_url}/health")
        assert health_resp2.status_code == 200
        assert health_resp2.json()["status"] == "ok"
