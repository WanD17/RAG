import { type DragEvent, useRef, useState } from 'react';
import { UploadCloud, Loader2, FileType } from 'lucide-react';

const ACCEPTED = '.pdf,.docx,.txt,.md';
const ACCEPTED_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/markdown'];

interface UploadZoneProps {
  onUpload: (files: File[]) => void;
  isUploading: boolean;
}

export function UploadZone({ onUpload, isUploading }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function filterValid(files: FileList | null): File[] {
    if (!files) return [];
    return Array.from(files).filter(
      (f) => ACCEPTED_TYPES.includes(f.type) || ACCEPTED.split(',').some((ext) => f.name.endsWith(ext))
    );
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const valid = filterValid(e.dataTransfer.files);
    if (valid.length) onUpload(valid);
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !isUploading && inputRef.current?.click()}
      className={`relative glass gradient-border rounded-2xl p-10 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all overflow-hidden
        ${dragging ? 'bg-violet-500/10 scale-[1.01]' : 'hover:bg-white/[0.04]'}
        ${isUploading ? 'pointer-events-none opacity-70' : ''}`}
    >
      {dragging && (
        <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 via-fuchsia-500/5 to-pink-500/10 pointer-events-none" />
      )}

      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => { const valid = filterValid(e.target.files); if (valid.length) onUpload(valid); e.target.value = ''; }}
      />

      <div className="relative">
        <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all
          ${isUploading || dragging
            ? 'bg-gradient-to-br from-violet-500 via-fuchsia-500 to-pink-500 shadow-xl shadow-violet-500/40'
            : 'bg-white/[0.04] border border-white/10'}`}
        >
          {isUploading
            ? <Loader2 className="w-7 h-7 text-white animate-spin" />
            : <UploadCloud className={`w-7 h-7 transition-colors ${dragging ? 'text-white' : 'text-zinc-400'}`} strokeWidth={2} />
          }
        </div>
        {(isUploading || dragging) && (
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-violet-500 to-pink-500 blur-xl opacity-60 -z-10 animate-pulse-glow" />
        )}
      </div>

      <div className="text-center space-y-1">
        <p className="text-base font-semibold text-zinc-100">
          {isUploading ? 'Uploading...' : dragging ? 'Drop to upload' : 'Drop files here or click to upload'}
        </p>
        <div className="flex items-center justify-center gap-1.5 text-xs text-zinc-500">
          <FileType className="w-3.5 h-3.5" />
          <span>PDF, DOCX, TXT, MD supported</span>
        </div>
      </div>
    </div>
  );
}
