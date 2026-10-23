"""
Sentry Agent Tracing & Diagnostics Module for EventPilot AI.
Provides clean telemetry initialization, span instrumentation for AI workflows,
and in-memory local diagnostics for latency/error metrics.
"""

import time
import logging
from typing import Dict, Any, Optional
from collections import deque
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from backend.config import settings

logger = logging.getLogger("eventpilot.observability")

# In-memory diagnostics ring buffer for development monitoring (keeps last 50 runs)
_DIAGNOSTICS_HISTORY = deque(maxlen=50)

def init_sentry() -> bool:
    """Initialize Sentry SDK if SENTRY_DSN is configured."""
    if not settings.SENTRY_DSN:
        logger.info("SENTRY_DSN not provided. Sentry telemetry is disabled.")
        return False

    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            send_default_pii=False,  # Privacy safe: don't harvest personal data
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
            ],
            _experiments={
                "enable_metrics": True,
            }
        )
        logger.info(f"Sentry SDK initialized successfully for environment '{settings.SENTRY_ENVIRONMENT}'")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Sentry SDK: {e}")
        return False

class AISpanContext:
    """
    Context manager that creates a Sentry span if Sentry is active,
    and logs duration and outcome to local diagnostics.
    """
    def __init__(self, op: str, description: str, data: Optional[Dict[str, Any]] = None):
        self.op = op
        self.description = description
        self.data = data or {}
        self.span = None
        self.start_time = 0.0
        self.duration = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        if settings.SENTRY_DSN:
            try:
                self.span = sentry_sdk.start_span(op=self.op, description=self.description)
                self.span.__enter__()
                for k, v in self.data.items():
                    # Set tags and data safely
                    self.span.set_data(k, v)
            except Exception as e:
                logger.debug(f"Could not start Sentry span: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = round((time.perf_counter() - self.start_time) * 1000, 2)
        if self.span:
            try:
                if exc_type is not None:
                    self.span.set_status("internal_error")
                    self.span.set_data("error.message", str(exc_val))
                else:
                    self.span.set_status("ok")
                self.span.set_data("duration_ms", self.duration)
                self.span.__exit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass
        return False  # Do not suppress exceptions

def record_diagnostics_event(
    event_name: str,
    outcome: str,
    duration_ms: float,
    model_identifier: str,
    provider: str,
    token_usage: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
):
    """Record run metrics to local in-memory buffer."""
    _DIAGNOSTICS_HISTORY.append({
        "timestamp": time.time(),
        "event_name": event_name,
        "outcome": outcome,
        "duration_ms": duration_ms,
        "model": model_identifier,
        "provider": provider,
        "tokens": token_usage,
        "error": error
    })

def get_diagnostics_summary() -> Dict[str, Any]:
    """Return local observed workflow metrics for development inspection."""
    total_runs = len(_DIAGNOSTICS_HISTORY)
    if total_runs == 0:
        return {
            "total_runs": 0,
            "success_rate_percent": 100.0,
            "avg_duration_ms": 0.0,
            "recent_events": [],
            "sentry_enabled": bool(settings.SENTRY_DSN),
            "sentry_environment": settings.SENTRY_ENVIRONMENT
        }

    durations = [h["duration_ms"] for h in _DIAGNOSTICS_HISTORY]
    successes = sum(1 for h in _DIAGNOSTICS_HISTORY if h["outcome"] == "success")
    
    return {
        "total_runs": total_runs,
        "success_rate_percent": round((successes / total_runs) * 100, 1),
        "avg_duration_ms": round(sum(durations) / total_runs, 2),
        "min_duration_ms": min(durations),
        "max_duration_ms": max(durations),
        "recent_events": list(_DIAGNOSTICS_HISTORY)[-10:],
        "sentry_enabled": bool(settings.SENTRY_DSN),
        "sentry_environment": settings.SENTRY_ENVIRONMENT
    }
