# [SYNTHETIC] Runbook: Orders Dependency Down Cascading Failures
**Service**: orders
**Symptoms**: Gateway checkout endpoint fails with downstream unreachable errors.
**Triage**: Check orders service health and pod availability.
**Remediation**: Restart orders service to restore downstream availability.
**Recommended Action**: restart
