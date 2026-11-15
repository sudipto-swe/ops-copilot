# [SYNTHETIC] Runbook: Node Disk Pressure and Pod Eviction
**Service**: gateway
**Symptoms**: Pods marked as Failed / Evicted due to NodeHasDiskPressure condition.
**Triage**: Check ephemeral storage usage, dangling container images, and log files.
**Remediation**: Clean container log archives, prune unused images, and scale node disk volume.
**Recommended Action**: scale
