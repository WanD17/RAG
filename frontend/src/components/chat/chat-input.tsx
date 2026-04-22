import { type KeyboardEvent, useRef, useState } from 'react';
import { Send, Square } from 'lucide-react';

interface ChatInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, onStop, isStreaming, disabled }: ChatInputProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setText('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleInput() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }

  return (
    <div className="px-4 py-4">
      <div className="max-w-3xl mx-auto">
        <div className="glass-strong gradient-border rounded-2xl p-2 flex items-end gap-2 shadow-xl shadow-black/30">
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Ask a question about your documents..."
            disabled={disabled}
            className="flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none disabled:opacity-50"
          />
          <button
            onClick={isStreaming ? onStop : handleSend}
            disabled={!isStreaming && (!text.trim() || !!disabled)}
            className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all
              ${isStreaming
                ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30 border border-red-500/40'
                : 'btn-primary text-white disabled:opacity-30 disabled:cursor-not-allowed disabled:shadow-none'}`}
          >
            {isStreaming
              ? <Square className="w-3.5 h-3.5 fill-current" />
              : <Send className="w-4 h-4" strokeWidth={2.5} />
            }
          </button>
        </div>
        <p className="text-center text-[10px] text-zinc-600 mt-2 tracking-wide">Press <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-400 font-mono">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-400 font-mono">Shift+Enter</kbd> for new line</p>
      </div>
    </div>
  );
}
