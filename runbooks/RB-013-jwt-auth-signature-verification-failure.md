# [SYNTHETIC] Runbook: JWT Authentication Signature Failure
**Service**: gateway
**Symptoms**: All incoming client requests return 401 Unauthorized with token verification error.
**Triage**: Verify JWKS public key rotation and clock skew across edge nodes.
**Remediation**: Refresh cached JWKS keys in gateway or rollback faulty key rotation.
**Recommended Action**: rollback
