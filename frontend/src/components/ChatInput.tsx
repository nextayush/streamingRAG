'use client';

import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  isStreaming: boolean;
}

export function ChatInput({ value, onChange, onSubmit, isStreaming }: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <form
      className="input-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <textarea
        rows={1}
        placeholder={isStreaming ? 'Analyzing…' : 'Ask about stocks, compare companies, trends…'}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isStreaming}
      />
      <button className="send-button" type="submit" disabled={isStreaming || !value.trim()}>
        {isStreaming ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
      </button>
    </form>
  );
}
