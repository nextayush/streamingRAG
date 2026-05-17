'use client';

import { useEffect, useState } from 'react';
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
  Zap,
} from 'lucide-react';
import type { Telemetry } from '@/types/telemetry';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart
} from 'recharts';

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

  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    if (data) {
      setHistory(prev => {
        const timeStr = new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        if (prev.length > 0 && prev[prev.length - 1].time === timeStr) return prev;
        
        const next = [...prev, {
          time: timeStr,
          embedMs: data.ingestion.last_cycle_embed_ms || 0,
          totalDuration: data.ingestion.last_cycle_duration_ms || 0,
          queryLatency: data.queries.last_duration_ms || 0,
        }];
        return next.slice(-20);
      });
    }
  }, [data]);

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
            className="telemetry-panel-full"
            initial={{ y: '50px', opacity: 0, scale: 0.98 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: '50px', opacity: 0, scale: 0.98 }}
            transition={{ type: 'spring', damping: 28, stiffness: 320 }}
          >
            <header className="telemetry-header">
              <motion.div className="telemetry-title-row">
                <motion.div className="telemetry-title-icon">
                  <Activity size={24} />
                </motion.div>
                <motion.div>
                  <h2>Command Center Telemetry</h2>
                  <p>Live AI Pipeline &amp; Infrastructure Monitoring</p>
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

            <motion.div className="telemetry-body-grid">
              {error && !data ? (
                <motion.div className="telemetry-error" style={{ gridColumn: '1 / -1' }}>
                  <AlertCircle size={18} />
                  <span>{error}</span>
                </motion.div>
              ) : null}

              {data ? (
                <>
                  <div className="telemetry-sidebar">
                    <section className="telemetry-section">
                      <h3>System Health</h3>
                      <motion.div className="status-row">
                        <StatusPill ok={engineOk} label="RAG Engine" />
                        <StatusPill ok={qdrantOk} label="Qdrant" />
                        <StatusPill ok={redisOk} label="Redis" />
                      </motion.div>
                    </section>

                    <section className="telemetry-section">
                      <h3>Core Metrics</h3>
                      <motion.div className="metric-grid-1col">
                        <MetricCard icon={<Clock size={18} />} label="Uptime" value={data.uptime_human} />
                        <MetricCard
                          icon={<BarChart3 size={18} />}
                          label="Total Queries"
                          value={data.queries.total}
                          sub={`${data.queries.streamed} streamed`}
                        />
                        <MetricCard
                          icon={<Radio size={18} />}
                          label="Ingestion Cycles"
                          value={data.ingestion.cycles_completed}
                          sub={`every ${data.ingestion.interval_seconds}s`}
                        />
                        <MetricCard
                          icon={<Database size={18} />}
                          label="Vector Points"
                          value={data.infrastructure.qdrant.points_count?.toLocaleString() ?? '—'}
                          sub={data.infrastructure.qdrant.collection}
                        />
                      </motion.div>
                    </section>

                    <section className="telemetry-section">
                      <h3>Engine Configuration</h3>
                      <dl className="detail-list">
                        <DetailRow label="LLM">
                          {data.engine.llm} <span className="muted">({data.engine.llm_provider})</span>
                        </DetailRow>
                        <DetailRow label="Embeddings">{data.engine.embed_model}</DetailRow>
                        <DetailRow label="Reranker">{data.engine.reranker}</DetailRow>
                      </dl>
                    </section>
                  </div>

                  <div className="telemetry-main">
                    <div className="telemetry-charts">
                      <section className="telemetry-section chart-section">
                        <h3><Zap size={14} /> Ingestion Performance (Live)</h3>
                        <div className="chart-container">
                          <ResponsiveContainer width="100%" height={250}>
                            <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                              <defs>
                                <linearGradient id="colorEmbed" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                              <XAxis dataKey="time" stroke="#a1a1aa" fontSize={11} tickMargin={10} />
                              <YAxis stroke="#a1a1aa" fontSize={11} />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                                itemStyle={{ color: '#fafafa', fontSize: '13px' }}
                                labelStyle={{ color: '#a1a1aa', fontSize: '12px', marginBottom: '4px' }}
                              />
                              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                              <Area type="monotone" name="Total Cycle (ms)" dataKey="totalDuration" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorTotal)" />
                              <Area type="monotone" name="Embed/Vectorize (ms)" dataKey="embedMs" stroke="#3b82f6" fillOpacity={1} fill="url(#colorEmbed)" />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      </section>

                      <section className="telemetry-section chart-section">
                        <h3><Activity size={14} /> Query Latency (Live)</h3>
                        <div className="chart-container">
                          <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                              <XAxis dataKey="time" stroke="#a1a1aa" fontSize={11} tickMargin={10} />
                              <YAxis stroke="#a1a1aa" fontSize={11} />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                                itemStyle={{ color: '#fafafa', fontSize: '13px' }}
                                labelStyle={{ color: '#a1a1aa', fontSize: '12px', marginBottom: '4px' }}
                              />
                              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                              <Line type="monotone" name="Latency (ms)" dataKey="queryLatency" stroke="#22c55e" strokeWidth={2} dot={{ r: 4, fill: '#18181b', stroke: '#22c55e', strokeWidth: 2 }} />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </section>
                    </div>

                    <div className="telemetry-details-grid">
                      <section className="telemetry-section info-card">
                        <h3>Latest Ingestion</h3>
                        <dl className="detail-list">
                          <DetailRow label="Time">{formatTime(data.ingestion.last_cycle_at)}</DetailRow>
                          <DetailRow label="Status">
                            <span className={`ingest-status ingest-${data.ingestion.last_status}`}>
                              {data.ingestion.last_status}
                            </span>
                          </DetailRow>
                          <DetailRow label="Docs Indexed">
                            {data.ingestion.last_market_docs} market · {data.ingestion.last_news_docs} news
                          </DetailRow>
                          <DetailRow label="Total Time">
                            {data.ingestion.last_cycle_duration_ms != null ? `${data.ingestion.last_cycle_duration_ms} ms` : '—'}
                          </DetailRow>
                          <DetailRow label="Embed Time">
                            {data.ingestion.last_cycle_embed_ms != null ? `${data.ingestion.last_cycle_embed_ms} ms` : '—'}
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

                      <section className="telemetry-section info-card">
                        <h3>Tracked Symbols ({data.symbol_count})</h3>
                        <motion.div className="symbol-chips" style={{ maxHeight: '140px', overflowY: 'auto' }}>
                          {data.tracked_symbols.map((s) => (
                            <span key={s} className="symbol-chip">
                              {s}
                            </span>
                          ))}
                        </motion.div>
                      </section>
                    </div>
                  </div>
                </>
              ) : null}
            </motion.div>
            
            {data && (
              <p className="telemetry-footer" style={{ padding: '16px', borderTop: '1px solid var(--border)' }}>
                Streaming RAG Pro v{data.version} · Last updated {new Date(data.timestamp).toLocaleTimeString()}
              </p>
            )}
          </motion.aside>
        </>
      ) : null}
    </AnimatePresence>
  );
}
