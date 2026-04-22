import { useCallback, useRef, useState } from 'react';
import type { SourceDocument } from '../types';

interface SSEState {
  answer: string;
  sources: SourceDocument[];
  isStreaming: boolean;
  error: string | null;
}

export function useSSE() {
  const [state, setState] = useState<SSEState>({
    answer: '',
    sources: [],
    isStreaming: false,
    error: null,
  });
  const esRef = useRef<EventSource | null>(null);

  const startStream = useCallback((url: string) => {
    if (esRef.current) esRef.current.close();

    setState({ answer: '', sources: [], isStreaming: true, error: null });

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

    es.addEventListener('done', () => {
      setState((prev) => ({ ...prev, isStreaming: false }));
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
