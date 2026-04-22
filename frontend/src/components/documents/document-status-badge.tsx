import type { Document } from '../../types';

const config: Record<Document['status'], { label: string; classes: string; dot: string }> = {
  pending:    { label: 'Pending',    classes: 'bg-amber-500/10 text-amber-300 border-amber-500/20',   dot: 'bg-amber-400' },
  processing: { label: 'Processing', classes: 'bg-violet-500/10 text-violet-300 border-violet-500/20', dot: 'bg-violet-400 animate-pulse' },
  completed:  { label: 'Completed',  classes: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20', dot: 'bg-emerald-400' },
  failed:     { label: 'Failed',     classes: 'bg-red-500/10 text-red-300 border-red-500/20',         dot: 'bg-red-400' },
};

export function DocumentStatusBadge({ status }: { status: Document['status'] }) {
  const { label, classes, dot } = config[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${classes}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
