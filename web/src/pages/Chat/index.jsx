import { useState, useRef, useEffect } from "react"
import { Send, Sparkles } from "lucide-react"
import { getAgentReply, createInitialMessage } from "./agentReplies"
import { useDashboardData } from "../../hooks/useDashboardData"

export default function Chat() {
  const { data, loading, error } = useDashboardData()
  const [messages, setMessages] = useState(() => [createInitialMessage()])
  const [input, setInput] = useState("")
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  function handleSend(event) {
    event.preventDefault()
    const text = input.trim()
    if (!text || !data) return

    const userMessage = { id: crypto.randomUUID(), role: "user", text }
    const agentMessage = { id: crypto.randomUUID(), role: "agent", text: getAgentReply(text, data) }
    setMessages((prev) => [...prev, userMessage, agentMessage])
    setInput("")
  }

  if (loading) {
    return <div className="max-w-3xl mx-auto px-6 py-16 text-slate-400">Connecting to your analyst…</div>
  }
  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-16 text-red-500">
        Couldn't load your hotel data: {error.message}
      </div>
    )
  }

  const hotelName = data.REGIONAL_STANDING.you.name.replace(" (You)", "")

  return (
    <div className="max-w-3xl mx-auto px-6 py-10 flex flex-col" style={{ height: "calc(100vh - 64px)" }}>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-slate-900">Talk to your TrueStay analyst</h1>
        <p className="text-slate-500 mt-1">Ask plain-language questions about how {hotelName} is performing.</p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            {m.role === "agent" && (
              <div className="w-8 h-8 rounded-lg bg-sky-50 flex items-center justify-center mr-2 shrink-0">
                <Sparkles className="w-4 h-4 text-sky-500" />
              </div>
            )}
            <div
              className={`max-w-[75%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-blue-600 text-white rounded-br-sm"
                  : "bg-white border border-slate-200 text-slate-700 rounded-bl-sm"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="mt-4 flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about food, comfort, cleanliness, staff, location..."
          className="flex-1 rounded-lg border border-slate-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
        />
        <button
          type="submit"
          className="bg-gradient-to-r from-sky-400 to-blue-600 text-white rounded-lg p-2.5 hover:shadow-md transition-shadow shrink-0"
          aria-label="Send"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  )
}
