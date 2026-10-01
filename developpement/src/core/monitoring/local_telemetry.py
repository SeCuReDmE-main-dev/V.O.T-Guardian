"""Optional local technical metrics; private audit events never use OTLP."""
from __future__ import annotations

import json
import math
import os
import time
from urllib import request
from urllib.parse import urlsplit


COUNTERS = {
    "vot.analysis.total", "vot.twilio.voice_webhook", "vot.twilio.media_event",
    "vot.twilio.websocket_event", "vot.tenebris.compliant", "vot.tenebris.degraded",
}
DURATIONS = {"vot.analysis.latency_ms", "vot.tenebris.destruction_time_ms"}


def local_endpoint(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        return bool(parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "::1"}
                    and parsed.port == 4318 and parsed.path == "/v1/metrics"
                    and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment)
    except (TypeError, ValueError):
        return False


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LocalTelemetry:
    """Fixed metric names, no voice features, prediction, confidence or IDs."""

    def record_metric(self, name: str, value: float, tags=None) -> bool:
        if os.getenv("SECUREDME_OTEL_ENABLED", "").lower() != "true":
            return False
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "http://127.0.0.1:4318/v1/metrics")
        if not local_endpoint(endpoint) or name not in COUNTERS | DURATIONS:
            return False
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return False
        if name in COUNTERS and (not float(value).is_integer() or not 1 <= value <= 1000):
            return False
        if name in DURATIONS and not 0 <= value <= 60000:
            return False
        # No caller-provided tags cross the transport, including hashed IDs.
        timestamp = str(time.time_ns())
        point = {"timeUnixNano": timestamp, "asDouble": float(value)}
        metric = {"name": name, "unit": "ms" if name in DURATIONS else "1"}
        if name in COUNTERS:
            point.update({"asInt": str(int(value)), "startTimeUnixNano": timestamp})
            point.pop("asDouble")
            metric["sum"] = {"aggregationTemporality": 1, "isMonotonic": True, "dataPoints": [point]}
        else:
            metric["gauge"] = {"dataPoints": [point]}
        body = json.dumps({"resourceMetrics": [{
            "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "vot-guardian"}}]},
            "scopeMetrics": [{"scope": {"name": "vot.technical", "version": "1"}, "metrics": [metric]}],
        }]}, separators=(",", ":")).encode("utf-8")
        try:
            opener = request.build_opener(request.ProxyHandler({}), _NoRedirect())
            req = request.Request(endpoint, body, {"Content-Type": "application/json", "Accept": "application/json"}, method="POST")
            with opener.open(req, timeout=0.5) as response:
                raw = response.read(8193)
                if response.status != 200 or len(raw) > 8192:
                    return False
            result = json.loads(raw or b"{}")
            partial = result.get("partialSuccess", {})
            return isinstance(partial, dict) and int(partial.get("rejectedDataPoints", 0)) == 0
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def record_analysis_metrics(self, *, latency_ms: float) -> None:
        self.record_metric("vot.analysis.total", 1)
        self.record_metric("vot.analysis.latency_ms", latency_ms)

    def record_tenebris_metrics(self, *, destruction_time_ms: float, compliance_status: str) -> None:
        self.record_metric("vot.tenebris.destruction_time_ms", destruction_time_ms)
        if compliance_status in {"COMPLIANT", "DEGRADED"}:
            self.record_metric("vot.tenebris." + compliance_status.lower(), 1)

    def get_service_status(self):
        return {"enabled": os.getenv("SECUREDME_OTEL_ENABLED", "").lower() == "true", "transport": "local-otlp-http", "reachability": "not_checked"}
