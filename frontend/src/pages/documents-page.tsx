import { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshCw, FolderOpen, FileText, CheckCircle2, Loader, AlertCircle } from 'lucide-react';
import { UploadZone } from '../components/documents/upload-zone';
import { DocumentList } from '../components/documents/document-list';
import { listDocuments, uploadDocument, deleteDocument } from '../api/documents-api';
import type { Document } from '../types';

export function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch {
      setError('Failed to load documents.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { void fetchDocuments(); }, [fetchDocuments]);

  useEffect(() => {
    const hasPending = documents.some((d) => d.status === 'pending' || d.status === 'processing');
    if (!hasPending) return;
    const id = setInterval(() => { void fetchDocuments(); }, 2000);
    return () => clearInterval(id);
  }, [documents, fetchDocuments]);

  async function handleUpload(files: File[]) {
    setIsUploading(true);
    setError('');
    try {
      const uploaded = await Promise.all(files.map(uploadDocument));
      setDocuments((prev) => [...uploaded, ...prev]);
    } catch {
      setError('Failed to upload one or more files.');
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm('Delete this document? This cannot be undone.')) return;
    setDeletingId(id);
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch {
      setError('Failed to delete document.');
    } finally {
      setDeletingId(null);
    }
  }

  const stats = useMemo(() => {
    const total = documents.length;
    const completed = documents.filter((d) => d.status === 'completed').length;
    const processing = documents.filter((d) => d.status === 'processing' || d.status === 'pending').length;
    const failed = documents.filter((d) => d.status === 'failed').length;
    return { total, completed, processing, failed };
  }, [documents]);

  const statCards = [
    { label: 'Total', value: stats.total, icon: FileText, color: 'violet', from: 'from-violet-500/15', to: 'to-violet-500/5', border: 'border-violet-500/20', text: 'text-violet-300' },
    { label: 'Completed', value: stats.completed, icon: CheckCircle2, color: 'emerald', from: 'from-emerald-500/15', to: 'to-emerald-500/5', border: 'border-emerald-500/20', text: 'text-emerald-300' },
    { label: 'Processing', value: stats.processing, icon: Loader, color: 'amber', from: 'from-amber-500/15', to: 'to-amber-500/5', border: 'border-amber-500/20', text: 'text-amber-300' },
    { label: 'Failed', value: stats.failed, icon: AlertCircle, color: 'red', from: 'from-red-500/15', to: 'to-red-500/5', border: 'border-red-500/20', text: 'text-red-300' },
  ];

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-6 animate-fade-up">
        <div className="glass-strong rounded-2xl p-6 relative overflow-hidden">
          <div className="absolute -top-20 -right-20 w-60 h-60 rounded-full bg-violet-500/10 blur-3xl pointer-events-none" />
          <div className="absolute -bottom-20 -left-20 w-60 h-60 rounded-full bg-fuchsia-500/10 blur-3xl pointer-events-none" />

          <div className="relative flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 via-fuchsia-500 to-pink-500 flex items-center justify-center shadow-lg shadow-violet-500/40">
                <FolderOpen className="w-6 h-6 text-white" strokeWidth={2} />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Knowledge Base</h2>
                <p className="text-sm text-zinc-400 mt-0.5">Manage documents indexed for semantic search</p>
              </div>
            </div>
            <button
              onClick={fetchDocuments}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm text-zinc-300 bg-white/[0.04] border border-white/10 hover:bg-white/[0.08] transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          <div className="relative grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
            {statCards.map(({ label, value, icon: Icon, from, to, border, text }) => (
              <div key={label} className={`rounded-xl p-4 bg-gradient-to-br ${from} ${to} border ${border}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-zinc-400 font-medium uppercase tracking-wider">{label}</span>
                  <Icon className={`w-4 h-4 ${text}`} />
                </div>
                <div className="text-2xl font-bold text-white tabular-nums">{value}</div>
              </div>
            ))}
          </div>
        </div>

        <UploadZone onUpload={handleUpload} isUploading={isUploading} />

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-300 text-sm rounded-xl px-4 py-3">
            {error}
          </div>
        )}

        <div className="glass-strong rounded-2xl overflow-hidden">
          <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">All Documents</h3>
              <p className="text-xs text-zinc-500 mt-0.5">{stats.total} item{stats.total !== 1 ? 's' : ''}</p>
            </div>
          </div>
          {isLoading
            ? (
              <div className="flex items-center justify-center py-20 text-zinc-500">
                <RefreshCw className="w-5 h-5 animate-spin mr-2 text-violet-400" />
                <span className="text-sm">Loading documents...</span>
              </div>
            )
            : <DocumentList documents={documents} onDelete={handleDelete} deletingId={deletingId} />
          }
        </div>
      </div>
    </div>
  );
}
