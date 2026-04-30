import { useCallback, useRef, useState } from 'react';
import type { SourceDocument } from '../types';

interface SSEState {
  answer: string;
  sources: SourceDocument[];
  isStreaming: boolean;
  error: string | null;
  conversationId: string | null;
}

export function useSSE() {
  const [state, setState] = useState<SSEState>({
    answer: '',
    sources: [],
    isStreaming: false,
    error: null,
    conversationId: null,
  });
  const esRef = useRef<EventSource | null>(null);

  const startStream = useCallback((url: string) => {
    if (esRef.current) esRef.current.close();

    setState((prev) => ({ ...prev, answer: '', sources: [], isStreaming: true, error: null }));

    const es = new EventSource(url);
    esRef.current = es;

    es.addEventListener('delta', (e) => {
      try {
        const chunk = JSON.parse(e.data);
        setState((prev) => ({ ...prev, answer: prev.answer + chunk }));
      } catch {
        setState((prev) => ({ ...prev, answer: prev.answer + e.data }));
      }
    });

    es.addEventListener('sources', (e) => {
      try {
        const sources: SourceDocument[] = JSON.parse(e.data);
        setState((prev) => ({ ...prev, sources }));
      } catch {
        // ignore parse errors
      }
    });

    es.addEventListener('done', (e) => {
      try {
        const data = JSON.parse(e.data);
        const convId: string | null = data?.conversation_id ?? null;
        setState((prev) => ({ ...prev, isStreaming: false, conversationId: convId }));
      } catch {
        setState((prev) => ({ ...prev, isStreaming: false }));
      }
      es.close();
    });

    es.onerror = () => {
      setState((prev) => ({
        ...prev,
        isStreaming: false,
        error: 'Connection error. Please try again.',
      }));
      es.close();
    };
  }, []);

  const stopStream = useCallback(() => {
    esRef.current?.close();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  return { ...state, startStream, stopStream };
}
