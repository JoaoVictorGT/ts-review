import { useState, useRef, useEffect } from "react"
import { MessageCircle, X, Send, Sparkles } from "lucide-react"
import { useAuth } from "../hooks/useAuth"

const GREETING = "Hi! Ask me anything about how your hotel is performing."

export default function ChatWidget() {
  const { session } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState(() => [{ id: "greeting", role: "agent", text: GREETING }])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, open])

  async function handleSend(event) {
    event.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    const userMessage = { id: crypto.randomUUID(), role: "user", text }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setSending(true)

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${session.token}` },
        body: JSON.stringify({ question: text }),
      })
      const body = await res.json()
      const answer = res.ok
        ? body.answer
        : "Não consegui entender sua pergunta. Você pode reformular ou falar com nosso suporte?"
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "agent", text: answer }])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "agent",
          text: "Não consegui entender sua pergunta. Você pode reformular ou falar com nosso suporte?",
        },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="fixed bottom-6 right-6 z-40">
      {open && (
        <div className="mb-3 w-80 sm:w-96 h-[28rem] bg-white border border-slate-200 rounded-xl shadow-xl flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-900 text-white">
            <span className="text-sm font-medium">TrueStay analyst</span>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                {m.role === "agent" && (
                  <div className="w-6 h-6 rounded-lg bg-sky-50 flex items-center justify-center mr-2 shrink-0">
                    <Sparkles className="w-3.5 h-3.5 text-sky-500" />
                  </div>
                )}
                <div
                  className={`max-w-[75%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-blue-600 text-white rounded-br-sm"
                      : "bg-slate-100 text-slate-700 rounded-bl-sm"
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="w-6 h-6 rounded-lg bg-sky-50 flex items-center justify-center mr-2 shrink-0">
                  <Sparkles className="w-3.5 h-3.5 text-sky-500" />
                </div>
                <div className="bg-slate-100 text-slate-400 rounded-xl rounded-bl-sm px-3 py-2 text-sm">
                  Typing…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={handleSend} className="flex items-center gap-2 p-3 border-t border-slate-100">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              disabled={sending}
              className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400 disabled:bg-slate-50"
            />
            <button
              type="submit"
              disabled={sending}
              className="bg-gradient-to-r from-sky-400 to-blue-600 text-white rounded-lg p-2 hover:shadow-md transition-shadow shrink-0 disabled:opacity-50"
              aria-label="Send"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-14 h-14 rounded-full bg-gradient-to-r from-sky-400 to-blue-600 text-white shadow-lg flex items-center justify-center hover:shadow-xl transition-shadow"
        aria-label="Open chat"
      >
        {open ? <X className="w-5 h-5" /> : <MessageCircle className="w-5 h-5" />}
      </button>
    </div>
  )
}
