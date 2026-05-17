from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from app.engine.index import get_engine, get_query_engine, is_engine_ready
from app.services.query_context import classify_intent
from app.services.live_ingestion import live_ingestion_loop
from app.services.telemetry import get_telemetry
from app.services.telemetry_state import record_query
from pydantic import BaseModel
import uvicorn
import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize the engine in a thread pool (doesn't block the event loop)
    logger.info("⏳ Warming up RAG engine (downloading models on first run)...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, get_engine)
    logger.info("✅ Engine is ready. Starting live ingestion...")

    # 2. THEN start the ingestion loop in the background
    task = asyncio.create_task(live_ingestion_loop())
    yield
    # Cancel the task on shutdown
    task.cancel()

app = FastAPI(title="Streaming RAG Pro", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "engine_ready": is_engine_ready(),
    }


@app.get("/api/telemetry")
async def telemetry():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_telemetry)

@app.post("/api/query")
async def query(request: QueryRequest):
    if not is_engine_ready():
        return JSONResponse(
            status_code=503,
            content={"error": "Engine is still initializing. Please wait a moment and try again."},
        )
    intent = classify_intent(request.query)
    logger.info("Query intent: %s | query: %s", intent.value, request.query[:80])
    engine = get_query_engine(streaming=False, query=request.query)
    started = time.perf_counter()
    response = engine.query(request.query)
    record_query(
        intent=intent.value,
        duration_ms=(time.perf_counter() - started) * 1000,
        streamed=False,
    )
    return {"response": str(response)}

@app.post("/api/stream")
async def stream_query(request: QueryRequest):
    if not is_engine_ready():
        return JSONResponse(
            status_code=503,
            content={"error": "Engine is still initializing. Please wait a moment and try again."},
        )

    intent = classify_intent(request.query)
    logger.info("Query intent: %s | query: %s", intent.value, request.query[:80])
    engine = get_query_engine(streaming=True, query=request.query)

    async def event_generator():
        started = time.perf_counter()
        try:
            response = engine.query(request.query)

            # Stream response tokens
            for token in response.response_gen:
                yield {
                    "event": "message",
                    "data": json.dumps({"token": token}),
                }

            # Send sources at the end
            sources = []
            for source_node in response.source_nodes:
                sources.append({
                    "text": source_node.node.get_content()[:200] + "...",
                    "score": float(source_node.score) if source_node.score else 0,
                    "metadata": source_node.node.metadata,
                })

            yield {
                "event": "sources",
                "data": json.dumps({"sources": sources}),
            }

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

        # Always send done to signal the frontend to stop
        yield {
            "event": "done",
            "data": json.dumps({"status": "completed"}),
        }
        record_query(
            intent=intent.value,
            duration_ms=(time.perf_counter() - started) * 1000,
            streamed=True,
        )

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
