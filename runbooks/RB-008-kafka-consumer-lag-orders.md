# [SYNTHETIC] Runbook: High Kafka Consumer Lag in Orders Pipeline
**Service**: orders
**Symptoms**: Order processing queue lag metric kafka_consumergroup_lag > 5000 records.
**Triage**: Check orders consumer partitions, thread utilization, and downstream database latency.
**Remediation**: Scale consumer workers or restart stalled consumers.
**Recommended Action**: scale
