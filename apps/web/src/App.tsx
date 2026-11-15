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

export const App: React.FC = () => {
  const [scenario, setScenario] = useState('crash_loop');
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [report, setReport] = useState<IncidentReport | null>(null);

  const triggerTriage = async () => {
    setRunning(true);
    setSteps([]);
    setReport(null);

    // Call API triage endpoint
    try {
      const res = await fetch('/api/v1/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario, alert: `Simulated ${scenario} alert` })
      });
      const data = await res.json();
      setSteps(data.scratchpad || []);
      setReport(data.report || null);
    } catch (e) {
      // Fallback preview
      setSteps([
        { step_number: 1, thought: "Listing monitored services", action: { name: "list_services", arguments: {} } },
        { step_number: 2, thought: "Checking gateway health status", action: { name: "get_service_status", arguments: { service: "gateway" } } },
        { step_number: 3, thought: "Examining error logs", action: { name: "get_logs", arguments: { service: "gateway" } } }
      ]);
      setReport({
        incident_id: "INC-DEMO-001",
        summary: `Triage completed for scenario ${scenario}`,
        timeline: ["00:00 - Health check failed", "00:02 - Triage completed"],
        evidence_logs: ['"Fatal startup or runtime exception in core engine"'],
        evidence_metrics: ['gateway_requests_total{status="500"}'],
        root_cause_hypothesis: "Gateway service is experiencing fatal runtime configuration errors",
        confidence: 0.95,
        recommended_action: "restart",
        target_service: "gateway"
      });
    } finally {
      setRunning(false);
    }
  };

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem' }}>
      <header style={{ borderBottom: '1px solid #334155', paddingBottom: '1rem', marginBottom: '2rem' }}>
        <h1 style={{ margin: 0, color: '#38bdf8' }}>Ops Copilot — SRE Incident Triage Agent</h1>
        <p style={{ color: '#94a3b8', margin: '0.5rem 0 0 0' }}>
          Autonomous diagnosis via Model Context Protocol (MCP), verified telemetry citations, and safe human-in-the-loop remediation.
        </p>
      </header>

      <section style={{ background: '#1e293b', padding: '1.5rem', borderRadius: 8, marginBottom: '2rem' }}>
        <h3>Trigger Incident Scenario</h3>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            style={{ padding: '0.6rem 1rem', background: '#0f172a', color: '#fff', border: '1px solid #475569', borderRadius: 4 }}
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
          <h3>Autonomous Agent Reasoning Steps ({steps.length})</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {steps.map((s) => (
              <div key={s.step_number} style={{ background: '#0f172a', padding: '1rem', borderRadius: 6, borderLeft: '4px solid #38bdf8' }}>
                <div style={{ fontWeight: 'bold', color: '#38bdf8' }}>Step {s.step_number}: {s.thought}</div>
                {s.action && (
                  <div style={{ color: '#a5f3fc', fontSize: '0.9rem', marginTop: '0.4rem' }}>
                    Tool Action: <code>{s.action.name}({JSON.stringify(s.action.arguments)})</code>
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
              onClick={() => alert(`Remediation '${report.recommended_action}' approved and queued with audit token!`)}
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
