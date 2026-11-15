import argparse
import sys

import httpx
import yaml

SERVICE_URLS = {
    "gateway": "http://localhost:8001",
    "orders": "http://localhost:8002",
    "payments": "http://localhost:8003",
}

def load_scenarios():
    with open("eval/scenarios.yaml") as f:
        return yaml.safe_load(f)["scenarios"]

def inject(scenario_key: str):
    scenarios = load_scenarios()
    if scenario_key not in scenarios:
        print(f"Error: Unknown scenario '{scenario_key}'")
        sys.exit(1)

    scenario = scenarios[scenario_key]
    target_service = scenario["service"]
    fault_type = scenario["fault_type"]
    url = SERVICE_URLS.get(target_service)

    if not url:
        print(f"Error: No URL known for service '{target_service}'")
        sys.exit(1)

    print(f"Injecting fault '{fault_type}' into {target_service} ({url})...")
    payload = {"type": fault_type}
    if fault_type == "slow_db":
        payload["latency_ms"] = 3500

    try:
        resp = httpx.post(f"{url}/simulate_fault", json=payload, timeout=5.0)
        resp.raise_for_status()
        print(f"Successfully injected '{scenario_key}': {scenario['name']}")
    except httpx.HTTPError as e:
        print(f"Failed to inject fault: {e}")
        sys.exit(1)

def reset():
    print("Resetting all services to healthy...")
    for name, url in SERVICE_URLS.items():
        try:
            resp = httpx.post(f"{url}/simulate_fault", json={"type": "healthy", "latency_ms": 0}, timeout=5.0)
            if resp.status_code == 200:
                print(f"✓ {name} reset to healthy")
        except httpx.HTTPError as e:
            print(f"✗ Failed to reset {name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fault Injection Utility")
    parser.add_argument("--scenario", help="Scenario key from eval/scenarios.yaml")
    parser.add_argument("--reset", action="store_true", help="Reset all services to healthy state")
    args = parser.parse_args()

    if args.reset:
        reset()
    elif args.scenario:
        inject(args.scenario)
    else:
        parser.print_help()
