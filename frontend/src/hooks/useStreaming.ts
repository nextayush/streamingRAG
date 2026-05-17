import { useState, useCallback } from 'react';

export interface Source {
  text: string;
  score: number;
  metadata: any;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export const useStreaming = (url: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(async (query: string) => {
    setIsStreaming(true);

    const userMessage: Message = { role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);

    const assistantMessage: Message = { role: 'assistant', content: '' };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorMsg = 'Something went wrong. Please try again.';
        try {
          const errBody = await response.json();
          errorMsg = errBody.error || errorMsg;
        } catch {}

        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1].content = `⚠️ ${errorMsg}`;
          return newMessages;
        });
        return;
      }

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();

          if (trimmed.startsWith('event: ')) {
            const eventType = trimmed.slice(7);
            if (eventType === 'done') {
              reader.cancel();
              return;
            }
            continue;
          }

          if (!trimmed.startsWith('data: ')) continue;

          try {
            const data = JSON.parse(trimmed.slice(6));

            if (data.token) {
              assistantContent += data.token;
              setMessages(prev => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1].content = assistantContent;
                return newMessages;
              });
            } else if (data.sources) {
              setMessages(prev => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1].sources = data.sources;
                return newMessages;
              });
            } else if (data.error) {
              setMessages(prev => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1].content =
                  `⚠️ ${data.error}`;
                return newMessages;
              });
            }
          } catch (e) {
          }
        }
      }
    } catch (error: any) {
      const errorMsg = error?.name === 'AbortError'
        ? '⚠️ Request timed out. Please try again.'
        : '⚠️ Could not connect to the backend. Please make sure it is running on http://localhost:8000';

      setMessages(prev => {
        const newMessages = [...prev];
        if (newMessages.length > 0) {
          newMessages[newMessages.length - 1].content = errorMsg;
        }
        return newMessages;
      });
    } finally {
      setIsStreaming(false);
    }
  }, [url]);

  return { messages, sendMessage, isStreaming };
};
