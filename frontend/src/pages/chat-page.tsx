import { useEffect, useRef, useState } from 'react';
import { Sparkles, Lightbulb, FileSearch, Zap } from 'lucide-react';
import { ChatMessageItem } from '../components/chat/chat-message';
import { ChatInput } from '../components/chat/chat-input';
import { useSSE } from '../hooks/use-sse';
import { buildStreamUrl } from '../api/rag-api';
import { generateId } from '../lib/utils';
import type { ChatMessage } from '../types';

const suggestions = [
  { icon: Lightbulb, text: 'What is in my knowledge base?', hint: 'Explore your documents' },
  { icon: FileSearch, text: 'Summarize the key points from my latest uploads', hint: 'Quick overview' },
  { icon: Zap, text: 'Find information about a specific topic', hint: 'Targeted search' },
];

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { answer, sources, isStreaming, error, conversationId, startStream, stopStream } = useSSE();
  const bottomRef = useRef<HTMLDivElement>(null);
  const streamingIdRef = useRef<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, answer]);

  useEffect(() => {
    if (!isStreaming && streamingIdRef.current && answer) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === streamingIdRef.current
            ? { ...m, content: answer, sources }
            : m
        )
      );
      streamingIdRef.current = null;
    }
  }, [isStreaming, answer, sources]);

  useEffect(() => {
    if (streamingIdRef.current && answer) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === streamingIdRef.current ? { ...m, content: answer } : m
        )
      );
    }
  }, [answer]);

  function handleSend(text: string) {
    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    const assistantId = generateId();
    streamingIdRef.current = assistantId;

    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    startStream(buildStreamUrl(text, conversationId ?? undefined));
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-[55vh] gap-8 animate-fade-up">
              <div className="relative">
                <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-violet-500 via-fuchsia-500 to-pink-500 flex items-center justify-center shadow-2xl shadow-violet-500/50">
                  <Sparkles className="w-10 h-10 text-white" strokeWidth={2} />
                </div>
                <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-violet-500 to-pink-500 blur-2xl opacity-50 animate-pulse-glow -z-10" />
              </div>
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold gradient-text tracking-tight">How can I help today?</h2>
                <p className="text-zinc-400 text-sm">Ask anything about your uploaded documents</p>
              </div>
              <div className="grid sm:grid-cols-3 gap-3 w-full max-w-2xl">
                {suggestions.map(({ icon: Icon, text, hint }) => (
                  <button
                    key={text}
                    onClick={() => handleSend(text)}
                    className="glass rounded-2xl p-4 text-left hover:bg-white/[0.06] transition-all group border-transparent hover:border-violet-500/30"
                  >
                    <Icon className="w-5 h-5 text-violet-400 mb-2 group-hover:scale-110 transition-transform" />
                    <div className="text-sm text-zinc-200 font-medium line-clamp-2">{text}</div>
                    <div className="text-xs text-zinc-500 mt-1">{hint}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <ChatMessageItem
              key={msg.id}
              message={msg}
              isStreaming={isStreaming && msg.id === streamingIdRef.current}
            />
          ))}

          {error && (
            <div className="text-center text-sm text-red-300 bg-red-500/10 rounded-xl px-4 py-3 border border-red-500/30">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <ChatInput onSend={handleSend} onStop={stopStream} isStreaming={isStreaming} />
    </div>
  );
}
