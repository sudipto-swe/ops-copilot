# [SYNTHETIC] Runbook: Payments Slow Database Queries & Latency Spike
**Service**: payments
**Symptoms**: Payment authorization requests exceed 3000ms SLA, query log shows 'SELECT pg_sleep' or lock wait.
**Triage**: Identify slow queries on payment_ledger table. Check connection saturation.
**Remediation**: Restart connection pooler, kill hung long-running queries, or restart payments service.
**Recommended Action**: restart
