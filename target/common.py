import json
import logging
import sys
import time
from typing import Any

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": getattr(record, "service", "unknown"),
            "logger": record.name,
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_service_logging(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger

def create_base_app(service_name: str) -> FastAPI:
    app = FastAPI(title=f"Synthetic {service_name.capitalize()} Service", version="0.1.0")
    logger = setup_service_logging(service_name)

    # Prometheus metrics
    REQUEST_COUNT = Counter(
        f"{service_name}_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )
    REQUEST_LATENCY = Histogram(
        f"{service_name}_request_duration_seconds",
        "HTTP request latency in seconds",
        ["endpoint"],
    )

    # In-memory fault state for reproducible simulations
    app.state.service_name = service_name
    app.state.logger = logger
    app.state.fault_status = "healthy"
    app.state.latency_ms = 0
    app.state.error_rate = 0.0

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", f"req-{int(time.time()*1000)}")
        request.state.request_id = req_id

        # Simulating injected latency if set
        if getattr(app.state, "latency_ms", 0) > 0:
            import asyncio
            await asyncio.sleep(app.state.latency_ms / 1000.0)

        # Simulating crash/error if in error fault state (except for management/health endpoints)
        if (
            getattr(app.state, "fault_status", "healthy") == "crash_loop"
            and request.url.path not in ["/simulate_fault", "/metrics"]
        ):
            logger.error(
                "Fatal startup or runtime exception in core engine",
                extra={"service": service_name, "request_id": req_id},
            )
            REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=500).inc()
            return Response(
                content=json.dumps({"error": "Service Crashed / Internal Error"}),
                status_code=500,
                media_type="application/json",
            )

        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
            REQUEST_COUNT.labels(
                method=request.method, endpoint=request.url.path, status=response.status_code
            ).inc()
            response.headers["X-Request-ID"] = req_id
            return response
        except Exception as exc:
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
            REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=500).inc()
            logger.error(
                f"Unhandled error processing {request.url.path}: {exc}",
                extra={"service": service_name, "request_id": req_id},
            )
            raise

    @app.get("/health")
    async def health():
        if getattr(app.state, "fault_status", "healthy") == "crash_loop":
            return Response(
                content=json.dumps({"status": "unhealthy", "service": service_name}),
                status_code=500,
                media_type="application/json",
            )
        return {"status": "ok", "service": service_name}

    @app.get("/ready")
    async def ready():
        if getattr(app.state, "fault_status", "healthy") != "healthy":
            return Response(
                content=json.dumps({"status": "not_ready", "reason": app.state.fault_status}),
                status_code=503,
                media_type="application/json",
            )
        return {"ready": True, "service": service_name}

    @app.get("/metrics")
    async def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/simulate_fault")
    async def simulate_fault(data: dict[str, Any]):
        fault_type = data.get("type", "healthy")
        app.state.fault_status = fault_type
        app.state.latency_ms = data.get("latency_ms", 0)
        logger.warning(
            f"Fault state updated to '{fault_type}' (latency={app.state.latency_ms}ms)",
            extra={"service": service_name, "request_id": "sys-fault-inject"},
        )
        return {"status": "applied", "service": service_name, "fault": fault_type}

    return app
