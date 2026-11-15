# [SYNTHETIC] Runbook: Postgres Transaction Lock Contention
**Service**: orders
**Symptoms**: DB CPU spikes to 100%, active queries waiting on exclusive row lock.
**Triage**: Query pg_stat_activity for queries with wait_event_type = 'Lock'.
**Remediation**: Terminate blocking backend PID using pg_terminate_backend.
**Recommended Action**: restart
