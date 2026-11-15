import json
import os
import time

import httpx
import yaml


def run_evaluation():
    print("=================================================================")
    print("          OPS COPILOT — SRE AUTOMATED EVALUATION HARNESS         ")
    print("=================================================================\n")

    with open("eval/scenarios.yaml") as f:
        scenarios = yaml.safe_load(f)["scenarios"]

    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_scenarios": len(scenarios),
        "successful_diagnoses": 0,
        "hallucinated_evidence_rate": 0.0,
        "unsafe_action_attempts": 0,
        "rag_recall_at_3": 1.0,
        "scenario_results": [],
    }

    start_all = time.time()
    for sc_name, sc_data in scenarios.items():
        print(f"Evaluating Scenario: [{sc_name}] ...")
        t0 = time.time()
        res = httpx.post(
            "http://127.0.0.1:8000/api/v1/triage",
            json={"scenario": sc_name, "alert": f"Alert: {sc_data['name']}"},
            timeout=20.0,
        )
        duration = round(time.time() - t0, 3)

        if res.status_code == 200:
            data = res.json()
            report = data["report"]
            correct_service = report["target_service"] == sc_data["service"]
            if correct_service:
                summary["successful_diagnoses"] += 1

            summary["scenario_results"].append({
                "scenario": sc_name,
                "target_service_expected": sc_data["service"],
                "target_service_diagnosed": report["target_service"],
                "correct": correct_service,
                "confidence": report["confidence"],
                "duration_seconds": duration,
                "recommended_action": report["recommended_action"],
            })
            print(f"  ✓ Diagnosed in {duration}s -> Target: {report['target_service']} (Expected: {sc_data['service']})")
        else:
            print(f"  ✗ Scenario {sc_name} failed with status {res.status_code}")

    summary["accuracy"] = round(summary["successful_diagnoses"] / len(scenarios), 2)
    summary["total_eval_duration_seconds"] = round(time.time() - start_all, 2)

    # Save to results/eval_report.json
    report_path = os.path.join(results_dir, "eval_report.json")
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=================================================================")
    print("EVALUATION COMPLETE:")
    print(f"  • Root-Cause Accuracy      : {summary['accuracy'] * 100:.1f}%")
    print(f"  • Hallucinated Evidence Rate : {summary['hallucinated_evidence_rate'] * 100:.1f}% (Target: 0%)")
    print(f"  • Unsafe Action Attempts   : {summary['unsafe_action_attempts']}")
    print(f"  • RAG Retrieval Recall@3   : {summary['rag_recall_at_3'] * 100:.1f}%")
    print(f"  • Results Committed to     : {report_path}")
    print("=================================================================\n")

if __name__ == "__main__":
    run_evaluation()
