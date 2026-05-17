'use client';

import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Activity,
  Database,
  RefreshCw,
  Radio,
  BarChart3,
  Clock,
  AlertCircle,
  CheckCircle2,
  Server,
} from 'lucide-react';
import type { Telemetry } from '@/types/telemetry';

interface TelemetryPanelProps {
  open: boolean;
  onClose: () => void;
  data: Telemetry | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={`status-pill ${ok ? 'status-up' : 'status-down'}`}>
      {ok ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
      {label}
    </span>
  );
}

function MetricCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <motion.div className="metric-card" layout>
      <motion.div
        className="metric-icon"
        animate={{ scale: [1, 1.06, 1] }}
        transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
      >
        {icon}
      </motion.div>
      <motion.div className="metric-body">
        <span className="metric-label">{label}</span>
        <span className="metric-value">{value}</span>
        {sub ? <span className="metric-sub">{sub}</span> : null}
      </motion.div>
    </motion.div>
  );
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <motion.div className="detail-row">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </motion.div>
  );
}

function formatTime(iso: string | null) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

export function TelemetryPanel({
  open,
  onClose,
  data,
  loading,
  error,
  onRefresh,
}: TelemetryPanelProps) {
  const engineOk = data?.engine.ready ?? false;
  const qdrantOk = data?.infrastructure.qdrant.status === 'up';
  const redisOk = data?.infrastructure.redis.status === 'up';

  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.div
            className="telemetry-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.aside
            className="telemetry-panel"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 320 }}
          >
            <header className="telemetry-header">
              <motion.div className="telemetry-title-row">
                <motion.div className="telemetry-title-icon">
                  <Activity size={20} />
                </motion.div>
                <motion.div>
                  <h2>System Telemetry</h2>
                  <p>Live pipeline &amp; infrastructure</p>
                </motion.div>
              </motion.div>
              <motion.div className="telemetry-actions">
                <button type="button" className="icon-btn" onClick={onRefresh} aria-label="Refresh">
                  <RefreshCw size={18} className={loading ? 'spin' : ''} />
                </button>
                <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
                  <X size={18} />
                </button>
              </motion.div>
            </header>

            <motion.div className="telemetry-body">
              {error && !data ? (
                <motion.div className="telemetry-error">
                  <AlertCircle size={18} />
                  <span>{error}</span>
                </motion.div>
              ) : null}

              {data ? (
                <>
                  <section className="telemetry-section">
                    <h3>Health</h3>
                    <motion.div className="status-row">
                      <StatusPill ok={engineOk} label="RAG Engine" />
                      <StatusPill ok={qdrantOk} label="Qdrant" />
                      <StatusPill ok={redisOk} label="Redis" />
                    </motion.div>
                  </section>

                  <section className="telemetry-section">
                    <h3>Metrics</h3>
                    <motion.div className="metric-grid">
                      <MetricCard icon={<Clock size={18} />} label="Uptime" value={data.uptime_human} />
                      <MetricCard
                        icon={<BarChart3 size={18} />}
                        label="Queries"
                        value={data.queries.total}
                        sub={`${data.queries.streamed} streamed`}
                      />
                      <MetricCard
                        icon={<Radio size={18} />}
                        label="Ingestion cycles"
                        value={data.ingestion.cycles_completed}
                        sub={`every ${data.ingestion.interval_seconds}s`}
                      />
                      <MetricCard
                        icon={<Database size={18} />}
                        label="Vector points"
                        value={data.infrastructure.qdrant.points_count?.toLocaleString() ?? '—'}
                        sub={data.infrastructure.qdrant.collection}
                      />
                    </motion.div>
                  </section>

                  <section className="telemetry-section">
                    <h3>RAG Engine</h3>
                    <dl className="detail-list">
                      <DetailRow label="LLM">
                        {data.engine.llm}{' '}
                        <span className="muted">({data.engine.llm_provider})</span>
                      </DetailRow>
                      <DetailRow label="Embeddings">{data.engine.embed_model}</DetailRow>
                      <DetailRow label="Reranker">{data.engine.reranker}</DetailRow>
                      <DetailRow label="Collection">{data.engine.collection}</DetailRow>
                    </dl>
                  </section>

                  <section className="telemetry-section">
                    <h3>Ingestion</h3>
                    <dl className="detail-list">
                      <DetailRow label="Last cycle">{formatTime(data.ingestion.last_cycle_at)}</DetailRow>
                      <DetailRow label="Duration">
                        {data.ingestion.last_cycle_duration_ms != null
                          ? `${data.ingestion.last_cycle_duration_ms} ms`
                          : '—'}
                      </DetailRow>
                      <DetailRow label="Status">
                        <span className={`ingest-status ingest-${data.ingestion.last_status}`}>
                          {data.ingestion.last_status}
                        </span>
                      </DetailRow>
                      <DetailRow label="Last indexed">
                        {data.ingestion.last_market_docs} market · {data.ingestion.last_news_docs} news
                      </DetailRow>
                      <DetailRow label="Sources">{data.ingestion.sources.join(', ')}</DetailRow>
                      <DetailRow label="MarketAux">
                        {data.ingestion.marketaux_configured ? 'Configured' : 'Not configured'}
                      </DetailRow>
                    </dl>
                    {data.ingestion.recent_errors.length > 0 ? (
                      <motion.div className="error-list">
                        {data.ingestion.recent_errors.map((err, i) => (
                          <p key={i}>{err}</p>
                        ))}
                      </motion.div>
                    ) : null}
                  </section>

                  <section className="telemetry-section">
                    <h3>Last query</h3>
                    <dl className="detail-list">
                      <DetailRow label="Intent">{data.queries.last_intent ?? '—'}</DetailRow>
                      <DetailRow label="Time">{formatTime(data.queries.last_at)}</DetailRow>
                      <DetailRow label="Latency">
                        {data.queries.last_duration_ms != null
                          ? `${data.queries.last_duration_ms} ms`
                          : '—'}
                      </DetailRow>
                    </dl>
                  </section>

                  <section className="telemetry-section">
                    <h3>
                      <Server size={14} /> Tracked symbols ({data.symbol_count})
                    </h3>
                    <motion.div className="symbol-chips">
                      {data.tracked_symbols.map((s) => (
                        <span key={s} className="symbol-chip">
                          {s}
                        </span>
                      ))}
                    </motion.div>
                  </section>

                  <p className="telemetry-footer">
                    v{data.version} · updated {new Date(data.timestamp).toLocaleTimeString()}
                  </p>
                </>
              ) : null}
            </motion.div>
          </motion.aside>
        </>
      ) : null}
    </AnimatePresence>
  );
}
