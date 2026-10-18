"use client";

import { useState, FormEvent, useRef, useEffect } from "react";
import * as api from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: api.Citation[];
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<api.Citation | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await api.queryDocuments(question, 5);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, citations: res.citations },
      ]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Query failed";
      setError(msg);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${msg}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] relative">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 mb-4">
        {messages.length === 0 ? (
          <div className="text-slate-500 text-sm">
            Ask a question about your uploaded documents. Answers will cite
            sources with page numbers. Click a citation to view the full source.
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-slate-900/70 border border-slate-800 text-slate-100"
                }`}
              >
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.content}
                </div>
                
                {/* Citations - Clickable */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-700">
                    <p className="text-xs text-slate-400 mb-2 font-medium">
                      Sources (click to view):
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {msg.citations.map((c) => (
                        <button
                          key={c.index}
                          onClick={() => setActiveCitation(c)}
                          className="text-xs text-left bg-slate-950/50 hover:bg-slate-900 border border-slate-700 rounded-lg p-2 transition-colors"
                        >
                          <span className="text-blue-400 font-mono font-bold">
                            [{c.index}]
                          </span>{" "}
                          <span className="text-slate-300">
                            {c.document_filename}
                          </span>
                          {c.page_number && (
                            <span className="text-slate-500">
                              {" "}• page {c.page_number}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-900/70 border border-slate-800 text-slate-400 rounded-2xl px-4 py-3 text-sm">
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your documents..."
          disabled={loading}
          className="flex-1 px-4 py-3 rounded-xl bg-slate-900/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium transition-colors"
        >
          {loading ? "..." : "Send"}
        </button>
      </form>

      {/* Source Viewer Modal */}
      {activeCitation && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" onClick={() => setActiveCitation(null)}>
          <div 
            className="bg-slate-800 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl"
            onClick={(e) => e.stopPropagation()} // Prevent close when clicking inside
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-700">
              <div>
                <h3 className="text-white font-semibold">
                  Source [{activeCitation.index}]
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  {activeCitation.document_filename}
                  {activeCitation.page_number && ` • Page ${activeCitation.page_number}`}
                </p>
              </div>
              <button 
                onClick={() => setActiveCitation(null)}
                className="text-slate-400 hover:text-white bg-slate-700/50 hover:bg-slate-700 rounded-lg p-2 transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="p-6 overflow-y-auto">
              <p className="text-slate-300 text-sm whitespace-pre-wrap leading-relaxed">
                {activeCitation.content}
              </p>
            </div>
            <div className="p-4 border-t border-slate-700 bg-slate-900/50 rounded-b-2xl flex justify-between items-center text-xs text-slate-500">
              <span>Relevance Score: {(activeCitation.score * 100).toFixed(1)}%</span>
              <span>Chunk ID: {activeCitation.chunk_id.slice(0, 8)}...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}