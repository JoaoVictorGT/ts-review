import { SlidersHorizontal } from "lucide-react"
import { useDashboardData } from "../../hooks/useDashboardData"

export default function CompetitiveGapMatrix({ activeFilter, selectedCompetitorId, onSelectCompetitor }) {
  const { data } = useDashboardData()
  const { CATEGORIES, HOTEL_ARENA_SCORES, COMPETITORS } = data
  const competitor = COMPETITORS.find((c) => c.id === selectedCompetitorId)
  const gaps = CATEGORIES.map((c) => ({
    name: c.name,
    gap: +(HOTEL_ARENA_SCORES[c.name] - competitor.scores[c.name]).toFixed(1),
  }))
  const maxAbs = Math.max(...gaps.map((g) => Math.abs(g.gap)))

  return (
    <>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase">
          Competitive gap vs. <span className="text-slate-500 normal-case">{competitor.name}</span>
        </p>
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-slate-400" />
          <select
            value={selectedCompetitorId}
            onChange={(e) => onSelectCompetitor(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg pl-3 pr-8 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            {COMPETITORS.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-14">
        <div className="flex flex-col gap-4 relative">
          {gaps.map((g) => {
            const widthPct = (Math.abs(g.gap) / maxAbs) * 48
            const isPositive = g.gap > 0
            const isActive = activeFilter === g.name
            const direction = isPositive ? "ahead of" : "behind"
            const tooltip = `You are ${Math.abs(g.gap).toFixed(1)} points ${direction} ${competitor.name} in this pillar`
            return (
              <div
                key={g.name}
                className={`flex items-center gap-4 ${isActive ? "bg-blue-50/60 -mx-2 px-2 rounded-lg" : ""}`}
              >
                <span className="w-24 shrink-0 text-sm text-slate-600">{g.name}</span>
                <div className="relative flex-1 h-7 group" title={tooltip}>
                  <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-200" />
                  <div
                    className={`absolute top-0.5 h-6 rounded ${isPositive ? "bg-blue-500" : "bg-red-500"} flex items-center transition-all`}
                    style={isPositive ? { left: "50%", width: `${widthPct}%` } : { left: `${50 - widthPct}%`, width: `${widthPct}%` }}
                  >
                    <span className={`text-xs text-white font-medium ${isPositive ? "ml-auto mr-2" : "ml-2"}`}>
                      {isPositive ? "+" : ""}
                      {g.gap.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
        <div className="flex justify-between text-xs text-slate-400 mt-4 pt-4 border-t border-slate-100">
          <span>← Competitor ahead</span>
          <span>Tie</span>
          <span>You ahead →</span>
        </div>
      </div>
    </>
  )
}
