import { useState } from "react";
import { askQuestion } from "../../api/qa";
import type { QASource } from "../../types";

interface Props {
  bookId: string;
  sessionId: string;
}

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: QASource[];
}

/** Чат с ответами на основе графа знаний. */
export function QAChat({ bookId, sessionId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  const send = async () => {
    const query = input.trim();
    if (!query || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: query }]);
    setBusy(true);
    try {
      const res = await askQuestion({
        query,
        book_id: bookId,
        session_id: sessionId,
      });
      setMessages((m) => [
        ...m,
        { role: "assistant", text: res.answer, sources: res.sources },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside
      style={{
        width: 360,
        borderLeft: "1px solid #e2e8f0",
        padding: 16,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <h3>Вопрос по учебнику</h3>
      <div style={{ flex: 1, overflowY: "auto" }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 12 }}>
            <b>{m.role === "user" ? "Вы" : "Ассистент"}:</b> {m.text}
            {m.sources && m.sources.length > 0 && (
              <div style={{ fontSize: 12, color: "#64748b" }}>
                Источники: {m.sources.map((s) => s.name).join(", ")}
              </div>
            )}
          </div>
        ))}
        {busy && <p style={{ color: "#64748b" }}>Думаю…</p>}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ваш вопрос…"
          style={{ flex: 1 }}
        />
        <button onClick={send} disabled={busy}>
          →
        </button>
      </div>
    </aside>
  );
}
