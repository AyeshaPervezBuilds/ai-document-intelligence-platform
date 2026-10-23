"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";
import Chat from "../components/Chat";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const [documents, setDocuments] = useState<api.Document[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => { if (!loading && !user) router.replace("/login"); }, [user, loading, router]);
  useEffect(() => { if (!user) return; loadDocuments(); }, [user]);

  const loadDocuments = async () => {
    setDocsLoading(true);
    try { setDocuments(await api.listDocuments()); }
    catch (err) { setError(err instanceof Error ? err.message : "Failed to load"); }
    finally { setDocsLoading(false); }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    setUploading(true); setError(null);
    try { await api.uploadDocument(file); toast.success(`"${file.name}" uploaded!`); await loadDocuments(); }
    catch (err) { const msg = err instanceof Error ? err.message : "Upload failed"; setError(msg); toast.error(msg); }
    finally { setUploading(false); e.target.value = ""; }
  };

  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); };
  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(false);
    const file = e.dataTransfer.files?.[0]; if (!file) return;
    setUploading(true); setError(null);
    try { await api.uploadDocument(file); toast.success(`"${file.name}" uploaded!`); await loadDocuments(); }
    catch (err) { const msg = err instanceof Error ? err.message : "Upload failed"; setError(msg); toast.error(msg); }
    finally { setUploading(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete?")) return;
    try { await api.deleteDocument(id); setDocuments((d) => d.filter((x) => x.id !== id)); toast.success("Deleted."); }
    catch (err) { toast.error("Delete failed"); }
  };

  if (loading || !user) return <div className="min-h-screen flex items-center justify-center bg-slate-900"><div className="text-slate-400">Loading...</div></div>;

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div><h1 className="text-xl font-bold">Document Intelligence</h1><p className="text-xs text-slate-500">{user.email}</p></div>
          <button onClick={logout} className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm font-medium">Sign Out</button>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && <div className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm">{error}</div>}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className={`lg:col-span-1 bg-slate-800/40 border rounded-2xl p-6 ${isDragging ? "border-blue-500 bg-blue-500/10" : "border-slate-800"}`} onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Documents</h2>
              <label className="cursor-pointer"><input type="file" accept=".pdf,.txt,.docx" onChange={handleUpload} disabled={uploading} className="hidden" /><span className="inline-block px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium">{uploading ? "..." : "+ Upload"}</span></label>
            </div>
            {docsLoading ? <div className="space-y-3 animate-pulse"><div className="h-16 bg-slate-800/80 rounded-lg"></div><div className="h-16 bg-slate-800/80 rounded-lg"></div></div>
            : documents.length === 0 ? <div className="text-center py-10 border-2 border-dashed border-slate-700 rounded-xl"><p className="text-slate-500 text-sm">{isDragging ? "Drop here" : "Drag & drop or Upload"}</p></div>
            : <ul className="space-y-2">{documents.map((doc) => (<li key={doc.id} className="group flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-slate-800"><div className="min-w-0 flex-1"><p className="text-sm font-medium truncate">{doc.filename}</p><p className="text-xs text-slate-500">{doc.status}</p></div><button onClick={() => handleDelete(doc.id)} className="ml-2 opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 text-xs">✕</button></li>))}</ul>}
          </div>
          <div className="lg:col-span-2 bg-slate-800/40 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-lg font-semibold mb-4">Chat</h2>
            <Chat />
          </div>
        </div>
      </main>
    </div>
  );
} 