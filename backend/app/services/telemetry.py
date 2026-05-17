"""Aggregate system telemetry for the dashboard."""

import logging
from datetime import datetime

from app.core.config import settings
from app.engine.index import is_engine_ready
from app.services.stocks import STOCK_MAP
from app.services.telemetry_state import get_state, uptime_seconds

logger = logging.getLogger(__name__)


def _check_qdrant() -> dict:
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=settings.QDRANT_URL, timeout=3)
        info = client.get_collection("streaming_rag")
        return {
            "status": "up",
            "url": settings.QDRANT_URL,
            "collection": "streaming_rag",
            "points_count": info.points_count,
            "vectors_count": getattr(info, "vectors_count", None),
            "status_collection": str(info.status),
        }
    except Exception as e:
        logger.debug("Qdrant telemetry failed: %s", e)
        return {
            "status": "down",
            "url": settings.QDRANT_URL,
            "collection": "streaming_rag",
            "error": str(e),
        }


def _check_redis() -> dict:
    try:
        import redis

        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        return {"status": "up", "url": settings.REDIS_URL}
    except Exception as e:
        return {"status": "down", "url": settings.REDIS_URL, "error": str(e)}


def get_telemetry() -> dict:
    state = get_state()
    uptime = uptime_seconds()

    return {
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime, 1),
        "uptime_human": _format_uptime(uptime),
        "version": settings.VERSION,
        "engine": {
            "ready": is_engine_ready(),
            "collection": "streaming_rag",
            "embed_model": "BAAI/bge-base-en-v1.5",
            "sparse_model": "Splade_PP_en_v1",
            "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "llm": settings.GROK_MODEL,
            "llm_provider": "xAI Grok",
        },
        "ingestion": {
            "interval_seconds": 30,
            "cycles_completed": state.ingestion_cycles,
            "last_cycle_at": state.last_ingestion_at,
            "last_cycle_duration_ms": state.last_ingestion_duration_ms,
            "last_status": state.last_ingestion_status,
            "last_market_docs": state.last_ingestion_market_docs,
            "last_news_docs": state.last_ingestion_news_docs,
            "recent_errors": state.last_ingestion_errors,
            "sources": ["yfinance", "MarketAux"],
            "marketaux_configured": bool(
                settings.MARKETAUX_API_KEY
                and settings.MARKETAUX_API_KEY != "your_marketaux_api_key"
            ),
        },
        "queries": {
            "total": state.query_count,
            "streamed": state.stream_count,
            "last_at": state.last_query_at,
            "last_intent": state.last_query_intent,
            "last_duration_ms": state.last_query_ms,
        },
        "infrastructure": {
            "qdrant": _check_qdrant(),
            "redis": _check_redis(),
        },
        "tracked_symbols": list(STOCK_MAP.keys()),
        "symbol_count": len(STOCK_MAP),
    }


def _format_uptime(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"
