'use client';

import { useState, useRef, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Bot } from 'lucide-react';
import { useStreaming } from '@/hooks/useStreaming';
import { useTelemetry } from '@/hooks/useTelemetry';
import { API_BASE } from '@/lib/api';
import { ChatHeader } from '@/components/ChatHeader';
import { ChatMessage } from '@/components/ChatMessage';
import { ChatInput } from '@/components/ChatInput';
import { SuggestedPrompts } from '@/components/SuggestedPrompts';
import { TelemetryPanel } from '@/components/TelemetryPanel';

export default function Home() {
  const [input, setInput] = useState('');
  const [telemetryOpen, setTelemetryOpen] = useState(false);
  const { messages, sendMessage, isStreaming } = useStreaming(`${API_BASE}/api/stream`);
  const { data: telemetry, loading, error, refresh } = useTelemetry(true, telemetryOpen ? 3000 : 10000);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = () => {
    if (!input.trim() || isStreaming) return;
    sendMessage(input);
    setInput('');
  };

  const showTyping =
    isStreaming && messages.length > 0 && !messages[messages.length - 1].content;

  return (
    <main className="app-shell">
      <div className="bg-accent" aria-hidden />

      <ChatHeader
        onTelemetryToggle={() => setTelemetryOpen((o) => !o)}
        telemetryOpen={telemetryOpen}
        engineReady={telemetry?.engine.ready}
      />

      <div className="chat-scroll" ref={scrollRef}>
        <AnimatePresence mode="wait">
          {messages.length === 0 ? (
            <motion.div
              key="empty"
              className="empty-state"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <motion.div className="empty-icon">
                <Bot size={48} strokeWidth={1.5} />
              </motion.div>
              <h2>Ask about the market</h2>
              <p>Real-time prices, news, and analysis for major tickers.</p>
              <SuggestedPrompts onSelect={sendMessage} disabled={isStreaming} />
            </motion.div>
          ) : (
            <motion.div
              key="messages"
              className="messages-list"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              {messages.map((msg, idx) => (
                <ChatMessage key={idx} message={msg} index={idx} />
              ))}
              {showTyping && (
                <article className="message assistant">
                  <motion.div className="message-bubble assistant-bubble">
                    <motion.div className="typing-indicator">
                      <span className="dot" />
                      <span className="dot" />
                      <span className="dot" />
                    </motion.div>
                  </motion.div>
                </article>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <footer className="chat-footer">
        <ChatInput
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          isStreaming={isStreaming}
        />
      </footer>

      <TelemetryPanel
        open={telemetryOpen}
        onClose={() => setTelemetryOpen(false)}
        data={telemetry}
        loading={loading}
        error={error}
        onRefresh={refresh}
      />
    </main>
  );
}
