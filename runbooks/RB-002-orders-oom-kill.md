# [SYNTHETIC] Runbook: Orders Service Out of Memory (OOMKilled)
**Service**: orders
**Symptoms**: Container exit code 137 or log 'Process memory exceeded cgroup quota. OOMKilled invoked'.
**Triage**: Inspect memory usage metrics and cgroup limit thresholds. Check for batch order payloads.
**Remediation**: Scale container memory limits or horizontal pod autoscaling.
**Recommended Action**: scale
