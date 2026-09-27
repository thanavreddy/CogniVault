"use client";

import { FormEvent, useState } from "react";
import { Send } from "lucide-react";
import { api, type ChatResponse } from "@/lib/api-client";

type Message = { role: "user" | "assistant"; content: string; sources?: ChatResponse["sources"] };

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); if (!question.trim()) return;
    const current = question.trim(); setQuestion(""); setMessages((items) => [...items, { role: "user", content: current }]); setBusy(true);
    try { const response = await api.chat(current); setMessages((items) => [...items, { role: "assistant", content: response.answer, sources: response.sources }]); }
    catch (error) { setMessages((items) => [...items, { role: "assistant", content: error instanceof Error ? error.message : "The request failed." }]); }
    finally { setBusy(false); }
  };
  return <section className="mx-auto flex min-h-[calc(100vh-10rem)] max-w-3xl flex-col gap-6"><div><p className="text-sm font-medium text-primary">Ask your files</p><h1 className="mt-2 text-4xl font-semibold tracking-tight">Chat</h1><p className="mt-2 text-muted-foreground">Answers are grounded in the chunks indexed from your local documents.</p></div><div className="flex-1 space-y-4 rounded-lg border bg-card p-5">{messages.length === 0 && <p className="text-sm text-muted-foreground">Index a document, then ask a question about it.</p>}{messages.map((message, index) => <div key={index} className={`rounded-lg p-4 ${message.role === "user" ? "ml-10 bg-primary text-primary-foreground" : "mr-10 bg-muted"}`}><p className="whitespace-pre-wrap text-sm">{message.content}</p>{message.sources && message.sources.length > 0 && <div className="mt-4 border-t border-current/20 pt-3 text-xs"><p className="mb-1 font-semibold">Sources</p>{message.sources.map((source, sourceIndex) => <p key={`${source.filename}-${sourceIndex}`}>• {source.filename} · chunk {source.chunk_id}</p>)}</div>}</div>)}</div><form onSubmit={submit} className="flex gap-2"><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about your documents..." className="min-w-0 flex-1 rounded-md border bg-card px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary" /><button disabled={busy || !question.trim()} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-3 text-sm text-primary-foreground disabled:opacity-50"><Send size={16} /> Send</button></form></section>;
}
