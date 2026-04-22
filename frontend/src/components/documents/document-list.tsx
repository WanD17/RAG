import { Trash2, FileText, Loader2 } from 'lucide-react';
import { DocumentStatusBadge } from './document-status-badge';
import { formatFileSize, formatDate } from '../../lib/utils';
import type { Document } from '../../types';

interface DocumentListProps {
  documents: Document[];
  onDelete: (id: string) => void;
  deletingId: string | null;
}

export function DocumentList({ documents, onDelete, deletingId }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/5 flex items-center justify-center">
          <FileText className="w-6 h-6 text-zinc-600" />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-zinc-300">No documents yet</p>
          <p className="text-xs text-zinc-500 mt-0.5">Upload one to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/5">
            <th className="text-left py-3.5 px-5 font-semibold text-zinc-500 text-xs uppercase tracking-wider">Filename</th>
            <th className="text-left py-3.5 px-4 font-semibold text-zinc-500 text-xs uppercase tracking-wider hidden sm:table-cell">Type</th>
            <th className="text-left py-3.5 px-4 font-semibold text-zinc-500 text-xs uppercase tracking-wider hidden md:table-cell">Size</th>
            <th className="text-left py-3.5 px-4 font-semibold text-zinc-500 text-xs uppercase tracking-wider">Status</th>
            <th className="text-left py-3.5 px-4 font-semibold text-zinc-500 text-xs uppercase tracking-wider hidden lg:table-cell">Uploaded</th>
            <th className="py-3.5 px-4" />
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {documents.map((doc) => (
            <tr key={doc.id} className="hover:bg-white/[0.03] transition-colors">
              <td className="py-3.5 px-5 max-w-[240px]">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500/15 to-fuchsia-500/10 border border-violet-500/20 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-4 h-4 text-violet-300" />
                  </div>
                  <span className="font-medium text-zinc-100 truncate">{doc.filename}</span>
                </div>
              </td>
              <td className="py-3.5 px-4 text-zinc-400 hidden sm:table-cell uppercase text-xs font-mono">{doc.file_type}</td>
              <td className="py-3.5 px-4 text-zinc-400 hidden md:table-cell">{formatFileSize(doc.file_size)}</td>
              <td className="py-3.5 px-4"><DocumentStatusBadge status={doc.status} /></td>
              <td className="py-3.5 px-4 text-zinc-400 hidden lg:table-cell">{formatDate(doc.created_at)}</td>
              <td className="py-3.5 px-4">
                <button
                  onClick={() => onDelete(doc.id)}
                  disabled={deletingId === doc.id}
                  className="p-1.5 rounded-lg text-zinc-500 hover:text-red-300 hover:bg-red-500/10 transition-all disabled:opacity-40"
                  title="Delete document"
                >
                  {deletingId === doc.id
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Trash2 className="w-4 h-4" />
                  }
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
