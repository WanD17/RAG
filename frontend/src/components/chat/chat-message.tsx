import { Sparkles, User } from 'lucide-react';
import { SourceCard } from './source-card';
import type { ChatMessage } from '../../types';

interface ChatMessageProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export function ChatMessageItem({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 animate-fade-up ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center
          ${isUser
            ? 'bg-gradient-to-br from-zinc-700 to-zinc-800 ring-1 ring-white/10'
            : 'bg-gradient-to-br from-violet-500 via-fuchsia-500 to-pink-500 shadow-lg shadow-violet-500/30'}`}
      >
        {isUser
          ? <User className="w-4 h-4 text-zinc-300" />
          : <Sparkles className="w-4 h-4 text-white" strokeWidth={2.5} />
        }
      </div>

      <div className={`max-w-[78%] space-y-2 ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap
            ${isUser
              ? 'bg-gradient-to-br from-violet-600 to-fuchsia-600 text-white rounded-tr-md shadow-lg shadow-violet-900/30'
              : 'glass text-zinc-100 rounded-tl-md'}`}
        >
          {message.content || (isStreaming && !message.content && (
            <span className="flex gap-1.5 items-center py-1">
              <span className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
              <span className="w-2 h-2 rounded-full bg-fuchsia-400 animate-pulse" style={{ animationDelay: '0.2s' }} />
              <span className="w-2 h-2 rounded-full bg-pink-400 animate-pulse" style={{ animationDelay: '0.4s' }} />
            </span>
          ))}
          {isStreaming && message.content && (
            <span className="inline-block w-1.5 h-4 bg-gradient-to-b from-violet-400 to-fuchsia-400 ml-0.5 animate-pulse rounded-sm align-middle" />
          )}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="w-full space-y-1.5 pt-1">
            <p className="text-[10px] text-zinc-500 font-semibold px-1 uppercase tracking-widest">Sources</p>
            {message.sources.map((src, i) => (
              <SourceCard key={`${src.document_id}-${src.chunk_index}`} source={src} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
