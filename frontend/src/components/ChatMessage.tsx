'use client';

import { motion } from 'framer-motion';
import { Bot, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '@/hooks/useStreaming';

interface ChatMessageProps {
  message: Message;
  index: number;
}

export function ChatMessage({ message, index }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <motion.article
      className={`message ${message.role}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: Math.min(index * 0.03, 0.15) }}
    >
      {!isUser && (
        <motion.div className="message-label">
          <Bot size={14} />
          <span>Assistant</span>
        </motion.div>
      )}

      <motion.div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
        {isUser ? (
          <p className="user-text">{message.content}</p>
        ) : (
          <motion.div className="markdown-content">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </motion.div>
        )}

        {!isUser && message.sources && message.sources.length > 0 && (
          <motion.div className="sources-block">
            <p className="sources-label">Sources</p>
            <motion.div className="sources-list">
              {message.sources.map((source, sIdx) => {
                const meta = source.metadata || {};
                const label = [
                  meta.live ? 'LIVE' : null,
                  meta.source,
                  meta.symbol,
                  meta.sentiment,
                ]
                  .filter(Boolean)
                  .join(' · ') || `Source ${sIdx + 1}`;
                return (
                  <span key={sIdx} className="source-tag" title={source.text}>
                    <FileText size={10} />
                    {label}
                  </span>
                );
              })}
            </motion.div>
          </motion.div>
        )}
      </motion.div>
    </motion.article>
  );
}
