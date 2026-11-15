# [SYNTHETIC] Runbook: Orders DB Connection Pool Exhaustion
**Service**: orders
**Symptoms**: HTTP 503 errors on checkout, log 'FATAL: could not obtain connection from pool: pool exhausted'.
**Triage**: Check active connections vs max_connections limit. Look for unclosed database sessions.
**Remediation**: Scale connection pool size or scale orders replicas to distribute load.
**Recommended Action**: scale
