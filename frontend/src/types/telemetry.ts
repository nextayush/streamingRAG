export interface ServiceStatus {
  status: 'up' | 'down';
  url?: string;
  error?: string;
}

export interface QdrantStatus extends ServiceStatus {
  collection?: string;
  points_count?: number;
  vectors_count?: number | null;
  status_collection?: string;
}

export interface Telemetry {
  timestamp: string;
  uptime_seconds: number;
  uptime_human: string;
  version: string;
  engine: {
    ready: boolean;
    collection: string;
    embed_model: string;
    sparse_model: string;
    reranker: string;
    llm: string;
    llm_provider: string;
  };
  ingestion: {
    interval_seconds: number;
    cycles_completed: number;
    last_cycle_at: string | null;
    last_cycle_duration_ms: number | null;
    last_status: string;
    last_market_docs: number;
    last_news_docs: number;
    recent_errors: string[];
    sources: string[];
    marketaux_configured: boolean;
  };
  queries: {
    total: number;
    streamed: number;
    last_at: string | null;
    last_intent: string | null;
    last_duration_ms: number | null;
  };
  infrastructure: {
    qdrant: QdrantStatus;
    redis: ServiceStatus;
  };
  tracked_symbols: string[];
  symbol_count: number;
}
