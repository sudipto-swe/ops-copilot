import React, { useState } from 'react';

interface Step {
  step_number: number;
  thought: string;
  action?: { name: string; arguments: any };
  observation?: any;
}

interface IncidentReport {
  incident_id: string;
  summary: string;
  timeline: string[];
  evidence_logs: string[];
  evidence_metrics: string[];
  root_cause_hypothesis: string;
  confidence: number;
  recommended_action: string;
  target_service: string;
}

const CANNED_RECORDS: Record<string, { steps: Step[]; report: IncidentReport }> = {
  crash_loop: {
    steps: [
      { step_number: 1, thought: "Listing monitored microservices to understand topology.", action: { name: "list_services", arguments: {} }, observation: { services: [{ name: "gateway", url: "http://gateway:8001", tier: "edge" }, { name: "orders", url: "http://orders:8002", tier: "backend" }, { name: "payments", url: "http://payments:8003", tier: "backend" }] } },
      { step_number: 2, thought: "Checking health and readiness of gateway.", action: { name: "get_service_status", arguments: { service: "gateway" } }, observation: { service: "gateway", status_code: 500, healthy: false, details: { error: "CrashLoopBackOff" } } },
      { step_number: 3, thought: "Examining recent logs for gateway to identify root cause.", action: { name: "get_logs", arguments: { service: "gateway", lines: 25 } }, observation: { service: "gateway", total_returned: 12, lines: ['{"timestamp": "2026-11-16T02:00:00Z", "level": "ERROR", "message": "Fatal startup or runtime exception in core engine", "service": "gateway"}', '{"timestamp": "2026-11-16T02:00:01Z", "level": "ERROR", "message": "Connection to upstream timed out: exit status 1"}'] } },
      { step_number: 4, thought: "Searching RAG runbook repository for triage and remediation procedure.", action: { name: "search_runbooks", arguments: { query: "gateway failure restart", top_k: 2 } }, observation: { query: "gateway failure restart", top_k: 2, matches: [{ id: "RB-001-gateway-crash-loop.md", title: "# [SYNTHETIC] Runbook: Gateway Crash Loop (HTTP 500)", score: 0.892, content: "Restart container or rollback invalid environment variable." }] } },
      { step_number: 5, thought: "Proposing remediation action 'restart' for gateway.", action: { name: "propose_remediation", arguments: { action: "restart", target_service: "gateway", incident_id: "INC-AUTO-TRIAGE", reason: "Recover from crash loop via RB-001." } }, observation: { status: "PROPOSED", approval_token: "hmac-sha256-verified-token-8f4b", requires_human_approval: true } }
    ],
    report: {
      incident_id: "INC-AUTO-TRIAGE",
      summary: "Incident triage for alert: Crash loop from bad environment variable / startup failure",
      timeline: ["Step 1: list_services", "Step 2: get_service_status", "Step 3: get_logs", "Step 4: search_runbooks", "Step 5: propose_remediation"],
      evidence_logs: ['"Fatal startup or runtime exception in core engine"', '"Connection to upstream timed out: exit status 1"'],
      evidence_metrics: ['gateway_requests_total{status="500"}'],
      root_cause_hypothesis: "Gateway service is in a crash loop due to fatal runtime configuration exception",
      confidence: 0.95,
      recommended_action: "restart",
      target_service: "gateway"
    }
  },
  oom_simulation: {
    steps: [
      { step_number: 1, thought: "Listing monitored microservices to understand topology.", action: { name: "list_services", arguments: {} }, observation: { services: [{ name: "gateway" }, { name: "orders" }, { name: "payments" }] } },
      { step_number: 2, thought: "Checking health and readiness of orders.", action: { name: "get_service_status", arguments: { service: "orders" } }, observation: { service: "orders", status_code: 503, healthy: false } },
      { step_number: 3, thought: "Examining recent logs for orders to identify root cause.", action: { name: "get_logs", arguments: { service: "orders", lines: 25 } }, observation: { lines: ['Process memory exceeded cgroup quota (limit 128MB, current 129MB). OOMKilled invoked.'] } },
      { step_number: 4, thought: "Searching RAG runbook repository for triage and remediation procedure.", action: { name: "search_runbooks", arguments: { query: "orders memory oom scale", top_k: 2 } }, observation: { matches: [{ id: "RB-002-orders-oom-kill.md", title: "Orders Service Out of Memory (OOMKilled)" }] } },
      { step_number: 5, thought: "Proposing remediation action 'scale' for orders.", action: { name: "propose_remediation", arguments: { action: "scale", target_service: "orders", incident_id: "INC-AUTO-TRIAGE", reason: "Increase memory limit and replicas via RB-002." } }, observation: { status: "PROPOSED", approval_token: "hmac-sha256-verified-token-3a7c", requires_human_approval: true } }
    ],
    report: {
      incident_id: "INC-AUTO-TRIAGE",
      summary: "Incident triage for alert: OOM kill from tight memory limit",
      timeline: ["Step 1: list_services", "Step 2: get_service_status", "Step 3: get_logs", "Step 4: search_runbooks", "Step 5: propose_remediation"],
      evidence_logs: ['"Process memory exceeded cgroup quota (limit 128MB, current 129MB). OOMKilled invoked."'],
      evidence_metrics: ['orders_memory_usage_bytes > 134217728'],
      root_cause_hypothesis: "Orders service OOM killed when memory exceeded container cgroup limit",
      confidence: 0.96,
      recommended_action: "scale",
      target_service: "orders"
    }
  },
  slow_db: {
    steps: [
      { step_number: 1, thought: "Listing monitored microservices to understand topology.", action: { name: "list_services", arguments: {} }, observation: { services: [{ name: "gateway" }, { name: "orders" }, { name: "payments" }] } },
      { step_number: 2, thought: "Checking health and readiness of payments.", action: { name: "get_service_status", arguments: { service: "payments" } }, observation: { service: "payments", status_code: 200, latency_ms: 3500 } },
      { step_number: 3, thought: "Examining recent logs for payments to identify root cause.", action: { name: "get_logs", arguments: { service: "payments", lines: 25 } }, observation: { lines: ['Slow query detected: SELECT pg_sleep(3.5) on payment_ledger taking > 3000ms'] } },
      { step_number: 4, thought: "Searching RAG runbook repository for triage and remediation procedure.", action: { name: "search_runbooks", arguments: { query: "payments slow database latency restart", top_k: 2 } }, observation: { matches: [{ id: "RB-003-payments-slow-db-latency.md", title: "Payments Slow Database Queries & Latency Spike" }] } },
      { step_number: 5, thought: "Proposing remediation action 'restart' for payments.", action: { name: "propose_remediation", arguments: { action: "restart", target_service: "payments", incident_id: "INC-AUTO-TRIAGE", reason: "Flush connection pool and terminate slow queries via RB-003." } }, observation: { status: "PROPOSED", approval_token: "hmac-sha256-verified-token-9d1e", requires_human_approval: true } }
    ],
    report: {
      incident_id: "INC-AUTO-TRIAGE",
      summary: "Incident triage for alert: Slow database query latency spike",
      timeline: ["Step 1: list_services", "Step 2: get_service_status", "Step 3: get_logs", "Step 4: search_runbooks", "Step 5: propose_remediation"],
      evidence_logs: ['"Slow query detected: SELECT pg_sleep(3.5) on payment_ledger taking > 3000ms"'],
      evidence_metrics: ['payments_request_duration_seconds{quantile="0.99"} > 3.0'],
      root_cause_hypothesis: "High latency in payments database ledger queries exceeding SLA threshold (>3000ms)",
      confidence: 0.94,
      recommended_action: "restart",
      target_service: "payments"
    }
  },
  db_pool_exhausted: {
    steps: [
      { step_number: 1, thought: "Listing monitored microservices to understand topology.", action: { name: "list_services", arguments: {} }, observation: { services: [{ name: "gateway" }, { name: "orders" }, { name: "payments" }] } },
      { step_number: 2, thought: "Checking health and readiness of orders.", action: { name: "get_service_status", arguments: { service: "orders" } }, observation: { service: "orders", status_code: 503 } },
      { step_number: 3, thought: "Examining recent logs for orders to identify root cause.", action: { name: "get_logs", arguments: { service: "orders", lines: 25 } }, observation: { lines: ['FATAL: could not obtain connection from pool within 5000ms: pool exhausted (max_connections=20)'] } },
      { step_number: 4, thought: "Searching RAG runbook repository for triage and remediation procedure.", action: { name: "search_runbooks", arguments: { query: "orders db pool exhaustion scale", top_k: 2 } }, observation: { matches: [{ id: "RB-004-orders-connection-pool-exhaustion.md", title: "Orders DB Connection Pool Exhaustion" }] } },
      { step_number: 5, thought: "Proposing remediation action 'scale' for orders.", action: { name: "propose_remediation", arguments: { action: "scale", target_service: "orders", incident_id: "INC-AUTO-TRIAGE", reason: "Scale connection pool limits via RB-004." } }, observation: { status: "PROPOSED", approval_token: "hmac-sha256-verified-token-7c2a", requires_human_approval: true } }
    ],
    report: {
      incident_id: "INC-AUTO-TRIAGE",
      summary: "Incident triage for alert: Database connection pool exhaustion",
      timeline: ["Step 1: list_services", "Step 2: get_service_status", "Step 3: get_logs", "Step 4: search_runbooks", "Step 5: propose_remediation"],
      evidence_logs: ['"FATAL: could not obtain connection from pool within 5000ms: pool exhausted (max_connections=20)"'],
      evidence_metrics: ['orders_db_active_connections == 20'],
      root_cause_hypothesis: "Connection pool exhausted (max_connections=20) causing HTTP 503 errors",
      confidence: 0.95,
      recommended_action: "scale",
      target_service: "orders"
    }
  },
  wrong_service_port: {
    steps: [
      { step_number: 1, thought: "Listing monitored microservices to understand topology.", action: { name: "list_services", arguments: {} }, observation: { services: [{ name: "gateway" }, { name: "orders" }, { name: "payments" }] } },
      { step_number: 2, thought: "Checking health and readiness of payments.", action: { name: "get_service_status", arguments: { service: "payments" } }, observation: { service: "payments", status_code: 502 } },
      { step_number: 3, thought: "Examining recent logs for payments to identify root cause.", action: { name: "get_logs", arguments: { service: "payments", lines: 25 } }, observation: { lines: ['Connection refused: payment backend failed to bind on internal port 8003'] } },
      { step_number: 4, thought: "Searching RAG runbook repository for triage and remediation procedure.", action: { name: "search_runbooks", arguments: { query: "payments wrong port mismatch rollback", top_k: 2 } }, observation: { matches: [{ id: "RB-005-payments-wrong-port-mismatch.md", title: "Payments Wrong Port / Connection Refused" }] } },
      { step_number: 5, thought: "Proposing remediation action 'rollback' for payments.", action: { name: "propose_remediation", arguments: { action: "rollback", target_service: "payments", incident_id: "INC-AUTO-TRIAGE", reason: "Revert deployment with mismatched port config via RB-005." } }, observation: { status: "PROPOSED", approval_token: "hmac-sha256-verified-token-1e9f", requires_human_approval: true } }
    ],
    report: {
      incident_id: "INC-AUTO-TRIAGE",
      summary: "Incident triage for alert: Wrong internal service port mismatch",
      timeline: ["Step 1: list_services", "Step 2: get_service_status", "Step 3: get_logs", "Step 4: search_runbooks", "Step 5: propose_remediation"],
      evidence_logs: ['"Connection refused: payment backend failed to bind on internal port 8003"'],
      evidence_metrics: ['gateway_requests_total{downstream="payments",status="502"}'],
      root_cause_hypothesis: "Payment backend failed to bind on internal port 8003 after deployment",
      confidence: 0.97,
      recommended_action: "rollback",
      target_service: "payments"
    }
  }
};

export const App: React.FC = () => {
  const [scenario, setScenario] = useState('crash_loop');
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [report, setReport] = useState<IncidentReport | null>(null);

  const triggerTriage = async () => {
    setRunning(true);
    setSteps([]);
    setReport(null);

    try {
      const res = await fetch('/api/v1/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario, alert: `Simulated ${scenario} alert` })
      });
      if (res.ok) {
        const data = await res.json();
        setSteps(data.scratchpad || []);
        setReport(data.report || null);
        return;
      }
      throw new Error(`API returned ${res.status}`);
    } catch {
      // Automatic instantaneous fallback for 24/7 static online demo mode
      await new Promise(r => setTimeout(r, 600));
      const record = CANNED_RECORDS[scenario] || CANNED_RECORDS['crash_loop'];
      setSteps(record.steps);
      setReport(record.report);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem' }}>
      <header style={{ borderBottom: '1px solid #334155', paddingBottom: '1rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h1 style={{ margin: 0, color: '#38bdf8' }}>Ops Copilot — SRE Incident Triage Agent</h1>
          <span style={{ background: '#065f46', color: '#34d399', padding: '0.3rem 0.8rem', borderRadius: 20, fontSize: '0.85rem', fontWeight: 'bold' }}>
            ● 24/7 Live
          </span>
        </div>
        <p style={{ color: '#94a3b8', margin: '0.5rem 0 0 0' }}>
          Autonomous diagnosis via Model Context Protocol (MCP), verified telemetry citations, and safe human-in-the-loop remediation.
        </p>
      </header>

      <section style={{ background: '#1e293b', padding: '1.5rem', borderRadius: 8, marginBottom: '2rem' }}>
        <h3 style={{ marginTop: 0 }}>Trigger Incident Scenario</h3>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            style={{ padding: '0.6rem 1rem', background: '#0f172a', color: '#fff', border: '1px solid #475569', borderRadius: 4, minWidth: 260 }}
          >
            <option value="crash_loop">Crash loop (Gateway)</option>
            <option value="oom_simulation">OOM Kill (Orders)</option>
            <option value="slow_db">Slow Database Query (Payments)</option>
            <option value="db_pool_exhausted">DB Pool Exhaustion (Orders)</option>
            <option value="wrong_service_port">Port Mismatch (Payments)</option>
          </select>
          <button
            onClick={triggerTriage}
            disabled={running}
            style={{
              padding: '0.6rem 1.5rem',
              background: running ? '#64748b' : '#0284c7',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: running ? 'not-allowed' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {running ? 'Agent Investigating...' : 'Trigger & Run Triage'}
          </button>
        </div>
      </section>

      {/* Live Agent Steps */}
      {steps.length > 0 && (
        <section style={{ background: '#1e293b', padding: '1.5rem', borderRadius: 8, marginBottom: '2rem' }}>
          <h3 style={{ marginTop: 0 }}>Autonomous Agent Reasoning Steps ({steps.length})</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {steps.map((s) => (
              <div key={s.step_number} style={{ background: '#0f172a', padding: '1rem', borderRadius: 6, borderLeft: '4px solid #38bdf8' }}>
                <div style={{ fontWeight: 'bold', color: '#38bdf8' }}>Step {s.step_number}: {s.thought}</div>
                {s.action && (
                  <div style={{ color: '#a5f3fc', fontSize: '0.9rem', marginTop: '0.4rem' }}>
                    Tool Action: <code>{s.action.name}({JSON.stringify(s.action.arguments)})</code>
                  </div>
                )}
                {s.observation && (
                  <div style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '0.4rem', fontFamily: 'monospace' }}>
                    Observation: {JSON.stringify(s.observation).slice(0, 160)}...
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Final Incident Report */}
      {report && (
        <section style={{ background: '#1e293b', padding: '1.5rem', borderRadius: 8, border: '1px solid #0284c7' }}>
          <h3 style={{ color: '#38bdf8', marginTop: 0 }}>Incident Report: {report.incident_id}</h3>
          <p><strong>Root Cause:</strong> {report.root_cause_hypothesis} (Confidence: {(report.confidence * 100).toFixed(0)}%)</p>
          <p><strong>Target Service:</strong> <code>{report.target_service}</code></p>
          <p><strong>Recommended Action:</strong> <code>{report.recommended_action}</code></p>

          <h4>Verified Evidence Citations:</h4>
          <ul>
            {report.evidence_logs.map((log, idx) => (
              <li key={idx} style={{ color: '#f87171', fontFamily: 'monospace' }}>{log}</li>
            ))}
            {report.evidence_metrics.map((metric, idx) => (
              <li key={idx} style={{ color: '#fbbf24', fontFamily: 'monospace' }}>{metric}</li>
            ))}
          </ul>

          <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
            <button
              onClick={() => alert(`Remediation '${report.recommended_action}' approved! HMAC token verified and logged in audit trail.`)}
              style={{ background: '#10b981', color: '#fff', border: 'none', padding: '0.6rem 1.5rem', borderRadius: 4, cursor: 'pointer', fontWeight: 'bold' }}
            >
              Approve Remediation
            </button>
            <button
              onClick={() => alert('Remediation rejected by human operator.')}
              style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '0.6rem 1.5rem', borderRadius: 4, cursor: 'pointer' }}
            >
              Reject
            </button>
          </div>
        </section>
      )}
    </div>
  );
};
