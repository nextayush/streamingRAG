"""In-process telemetry counters for the /api/telemetry endpoint."""

import time
from dataclasses import dataclass, field
from datetime import datetime

_start_time = time.time()


@dataclass
class TelemetryState:
    ingestion_cycles: int = 0
    last_ingestion_at: str | None = None
    last_ingestion_duration_ms: float | None = None
    last_ingestion_status: str = "pending"
    last_ingestion_market_docs: int = 0
    last_ingestion_news_docs: int = 0
    last_ingestion_errors: list[str] = field(default_factory=list)
    query_count: int = 0
    stream_count: int = 0
    last_query_at: str | None = None
    last_query_intent: str | None = None
    last_query_ms: float | None = None


_state = TelemetryState()


def uptime_seconds() -> float:
    return time.time() - _start_time


def record_ingestion_cycle(
    *,
    duration_ms: float,
    status: str,
    market_docs: int,
    news_docs: int,
    errors: list[str] | None = None,
) -> None:
    _state.ingestion_cycles += 1
    _state.last_ingestion_at = datetime.now().isoformat()
    _state.last_ingestion_duration_ms = round(duration_ms, 1)
    _state.last_ingestion_status = status
    _state.last_ingestion_market_docs = market_docs
    _state.last_ingestion_news_docs = news_docs
    _state.last_ingestion_errors = (errors or [])[-5:]


def record_query(*, intent: str, duration_ms: float, streamed: bool) -> None:
    _state.query_count += 1
    if streamed:
        _state.stream_count += 1
    _state.last_query_at = datetime.now().isoformat()
    _state.last_query_intent = intent
    _state.last_query_ms = round(duration_ms, 1)


def get_state() -> TelemetryState:
    return _state
