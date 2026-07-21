import { useDashboardData } from "../../hooks/useDashboardData"

export default function RegionalLeaderboard() {
  const { data } = useDashboardData()
  const { LEADERBOARD, QUARTERLY_LABELS } = data

  if (QUARTERLY_LABELS.length === 0) {
    return (
      <div>
        <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-3">Regional leaderboard</p>
        <div className="bg-white border border-slate-200 rounded-xl p-6 text-sm text-slate-400">
          Ranking available once we have enough reviews for this hotel.
        </div>
      </div>
    )
  }

  return (
    <div>
      <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-3">Regional leaderboard</p>
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <div className="divide-y divide-slate-100">
          {LEADERBOARD.map((h) => {
            if (h.isUser) {
              const arrow =
                h.trend === "up" ? (
                  <span className="text-emerald-600 text-xs font-medium">↑</span>
                ) : h.trend === "down" ? (
                  <span className="text-red-500 text-xs font-medium">↓</span>
                ) : null
              return (
                <div key={h.rank} className="flex items-center gap-4 px-5 py-3.5 bg-blue-50 border-l-4 border-blue-600">
                  <span className="w-6 text-sm font-bold text-blue-700">{h.rank}</span>
                  <span className="flex-1 text-sm font-medium text-slate-900 flex items-center gap-2">
                    {h.name.replace(" (You)", "")}
                    <span className="text-[10px] font-semibold tracking-wide bg-blue-600 text-white rounded-full px-2 py-0.5">
                      YOU
                    </span>
                  </span>
                  <span className="flex items-center gap-1 text-sm font-semibold text-slate-900">
                    {h.score.toFixed(2)} {arrow}
                  </span>
                </div>
              )
            }
            return (
              <div key={h.rank} className="flex items-center gap-4 px-5 py-3.5 bg-white">
                <span className="w-6 text-sm text-slate-400">{h.rank}</span>
                <span className="flex-1 text-sm text-slate-700">{h.name}</span>
                <span className="text-sm text-slate-600">{h.score.toFixed(2)}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
