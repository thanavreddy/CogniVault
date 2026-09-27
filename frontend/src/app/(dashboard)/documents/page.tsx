"use client";

import { FormEvent, useEffect, useState } from "react";
import { FileText, RefreshCw, Trash2, Upload } from "lucide-react";
import { api, type Document } from "@/lib/api-client";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const loadDocuments = async () => setDocuments(await api.documents.list());
  useEffect(() => { void loadDocuments(); }, []);

  const upload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("file") as HTMLInputElement;
    if (!input.files?.[0]) return;
    setBusy(true);
    try { await api.documents.upload(input.files[0]); input.value = ""; setMessage("Document added."); await loadDocuments(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Upload failed."); }
    finally { setBusy(false); }
  };
  const index = async (filename?: string) => {
    setBusy(true);
    try { const result = await api.documents.index(filename); setMessage(`${result.chunks} chunks indexed.`); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Indexing failed."); }
    finally { setBusy(false); }
  };
  const remove = async (filename: string) => { await api.documents.remove(filename); setDocuments((current) => current.filter((document) => document.filename !== filename)); };

  return <section className="space-y-8">
    <div><p className="text-sm font-medium text-primary">Local knowledge base</p><h1 className="mt-2 text-4xl font-semibold tracking-tight">Documents</h1><p className="mt-2 text-muted-foreground">Files stay in <code>data/documents</code>. Index them into Qdrant when they change.</p></div>
    <form onSubmit={upload} className="flex flex-wrap items-center gap-3 rounded-lg border bg-card p-5"><input name="file" type="file" accept=".pdf,.docx,.txt,.md,.markdown" required className="block flex-1 text-sm" /><button disabled={busy} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"><Upload size={16} /> Add document</button><button type="button" disabled={busy} onClick={() => void index()} className="inline-flex items-center gap-2 rounded-md border px-4 py-2 text-sm disabled:opacity-50"><RefreshCw size={16} /> Index all</button></form>
    {message && <p className="text-sm text-muted-foreground">{message}</p>}
    <div className="divide-y rounded-lg border bg-card">{documents.length === 0 ? <p className="p-6 text-sm text-muted-foreground">No documents yet.</p> : documents.map((document) => <div key={document.filename} className="flex items-center gap-4 p-4"><FileText className="text-primary" size={20} /><div className="min-w-0 flex-1"><p className="truncate font-medium">{document.filename}</p><p className="text-xs text-muted-foreground">{document.file_type.toUpperCase()} · {Math.ceil(document.size / 1024)} KB</p></div><button title="Index this document" onClick={() => void index(document.filename)} className="rounded-md p-2 text-muted-foreground hover:bg-muted"><RefreshCw size={16} /></button><button title="Delete this document" onClick={() => void remove(document.filename)} className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-destructive"><Trash2 size={16} /></button></div>)}</div>
  </section>;
}
