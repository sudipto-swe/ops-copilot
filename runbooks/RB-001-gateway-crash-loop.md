# [SYNTHETIC] Runbook: Gateway Crash Loop (HTTP 500)
**Service**: gateway
**Symptoms**: /health returns HTTP 500, log indicates 'Fatal startup or runtime exception in core engine'.
**Triage**: Check gateway container logs for recent configuration errors or invalid environment variables.
**Remediation**: Restart the gateway container or rollback the most recent configuration changes.
**Recommended Action**: restart
