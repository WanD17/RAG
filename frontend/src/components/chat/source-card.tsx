import { FileText } from 'lucide-react';
import type { SourceDocument } from '../../types';

interface SourceCardProps {
  source: SourceDocument;
  index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
  const scorePct = Math.round(source.score * 100);
  const scoreColor = scorePct > 80 ? 'text-emerald-300' : scorePct > 60 ? 'text-violet-300' : 'text-zinc-400';

  return (
    <div className="group flex gap-3 p-3 glass rounded-xl text-sm hover:bg-white/[0.06] transition-all">
      <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 border border-violet-500/30 text-violet-200 flex items-center justify-center text-xs font-bold">
        {index + 1}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 mb-1">
          <FileText className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />
          <span className="font-medium text-zinc-200 truncate">{source.filename}</span>
          <span className={`text-xs ml-auto flex-shrink-0 font-semibold ${scoreColor}`}>
            {scorePct}%
          </span>
        </div>
        <p className="text-zinc-400 text-xs line-clamp-2 leading-relaxed">{source.content}</p>
      </div>
    </div>
  );
}
