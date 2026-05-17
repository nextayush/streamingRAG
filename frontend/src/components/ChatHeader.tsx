'use client';

import { motion } from 'framer-motion';
import { Activity, Bot } from 'lucide-react';

interface ChatHeaderProps {
  onTelemetryToggle: () => void;
  telemetryOpen: boolean;
  engineReady?: boolean;
}

export function ChatHeader({
  onTelemetryToggle,
  telemetryOpen,
  engineReady,
}: ChatHeaderProps) {
  return (
    <header className="app-header">
      <motion.div
        className="logo-mark"
        whileHover={{ scale: 1.05 }}
        transition={{ type: 'spring', stiffness: 400 }}
      >
        <Bot size={20} />
      </motion.div>

      <div className="header-text">
        <h1>Streaming RAG Pro</h1>
        <p>Live market data · Grok · LlamaIndex</p>
      </div>

      <motion.div className="header-actions">
        <span className="header-live">Live</span>
        <button
          type="button"
          className={`header-telemetry-btn ${telemetryOpen ? 'active' : ''}`}
          onClick={onTelemetryToggle}
          aria-label={telemetryOpen ? 'Close telemetry' : 'Open system telemetry'}
          aria-pressed={telemetryOpen}
        >
          <Activity size={18} />
          <span>Telemetry</span>
          <span
            className={`telemetry-status-dot ${engineReady ? 'ready' : 'loading'}`}
            aria-hidden
          />
        </button>
      </motion.div>
    </header>
  );
}
