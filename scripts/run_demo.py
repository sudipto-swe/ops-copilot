import asyncio
import json
import sys

import httpx

from apps.api.app.agent.ops_agent import OpsAgent
from apps.api.app.llm.client import get_llm_client
from apps.api.app.mcp_server.server import MCPServer
from scripts.inject_fault import inject, reset


async def run_demo():
    print("=========================================================")
    print("        OPS COPILOT — LIVE INCIDENT TRIAGE DEMO         ")
    print("=========================================================\n")

    # Step 1: Ensure services are up and healthy
    print("[1/5] Checking service health...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get("http://localhost:8001/health", timeout=3.0)
            if res.status_code != 200:
                print("Services not running! Please start them via `make up` first.")
                sys.exit(1)
        except httpx.HTTPError:
            print("Services not running! Please start them via `make up` first.")
            sys.exit(1)
    print("  ✓ Services online.")

    # Step 2: Inject real failure
    print("\n[2/5] Injecting production fault: 'crash_loop' into gateway...")
    inject("crash_loop")

    # Step 3: Trigger Incident Alert
    alert = "ALERT [HighSeverity]: Gateway returning HTTP 500 error rate > 50% across edge cluster"
    print(f"\n[3/5] Incoming Alert: {alert}")

    # Step 4: Run Ops Agent Triage
    print("\n[4/5] Ops Copilot Agent starting autonomous investigation...")
    llm = get_llm_client()
    mcp = MCPServer()
    agent = OpsAgent(llm_client=llm, mcp_server=mcp, max_steps=6)

    result = await agent.investigate(alert)

    # Print Agent reasoning trace
    for step in result["scratchpad"]:
        print(f"\n  ➤ Step {step['step_number']}: {step['thought']}")
        if step.get("action"):
            print(f"    Action: {step['action']['name']}({step['action']['arguments']})")
            if step.get("observation"):
                obs_preview = json.dumps(step["observation"])
                if len(obs_preview) > 120:
                    obs_preview = obs_preview[:120] + "...}"
                print(f"    Observation: {obs_preview}")

    # Step 5: Incident Report Verification & Output
    report = result["report"]
    print("\n[5/5] Final SRE Incident Report Generated:")
    print("---------------------------------------------------------")
    print(f"Incident ID        : {report['incident_id']}")
    print(f"Summary            : {report['summary']}")
    print(f"Target Service     : {report['target_service']}")
    print(f"Root Cause         : {report['root_cause_hypothesis']}")
    print(f"Confidence         : {report['confidence'] * 100:.1f}%")
    print(f"Recommended Action : {report['recommended_action']}")
    print("Citations (Logs)   :")
    for log_evidence in report["evidence_logs"]:
        print(f"  • {log_evidence}")
    print("Citations (Metrics):")
    for metric_evidence in report["evidence_metrics"]:
        print(f"  • {metric_evidence}")
    print("---------------------------------------------------------")

    # Step 6: Clean up / reset
    print("\nResetting environment back to healthy state...")
    reset()
    print("Demo complete.\n")

if __name__ == "__main__":
    asyncio.run(run_demo())
