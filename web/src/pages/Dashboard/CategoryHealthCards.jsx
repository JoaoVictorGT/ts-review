import { Utensils, Bed, Sparkles, Users, MapPin } from "lucide-react"
import { useDashboardData } from "../../hooks/useDashboardData"

const ICONS = { utensils: Utensils, bed: Bed, sparkles: Sparkles, users: Users, "map-pin": MapPin }

function getStatus(score) {
  if (score >= 8.5) return { label: "Excellent", badge: "bg-emerald-50 text-emerald-700 border border-emerald-200", bar: "#22c55e", pulse: "" }
  if (score >= 7.0) return { label: "Stable", badge: "bg-amber-50 text-amber-700 border border-amber-200", bar: "#eab308", pulse: "" }
  return { label: "Critical", badge: "bg-red-50 text-red-700 border border-red-200", bar: "#ef4444", pulse: "animate-pulse" }
}

export default function CategoryHealthCards({ activeFilter, onToggleFilter }) {
  const { data } = useDashboardData()
  const { CATEGORIES, HOTEL_ARENA_SCORES } = data
  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-14">
      {CATEGORIES.map((c) => {
        const score = HOTEL_ARENA_SCORES[c.name]
        const hasScore = score != null
        const status = hasScore ? getStatus(score) : null
        const pct = hasScore ? Math.min(100, (score / 10) * 100) : 0
        const isActive = activeFilter === c.name
        const Icon = ICONS[c.icon]
        return (
          <button
            key={c.name}
            type="button"
            onClick={() => onToggleFilter(c.name)}
            className={`text-left bg-white border ${
              isActive ? "border-blue-400 ring-2 ring-blue-100" : "border-slate-200"
            } rounded-xl p-5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer`}
          >
            <div className="flex items-center justify-between mb-4">
              <Icon className="w-5 h-5 text-slate-400" />
              {hasScore ? (
                <span className={`text-xs font-medium rounded-full px-2.5 py-1 ${status.badge} ${status.pulse}`}>
                  {status.label}
                </span>
              ) : (
                <span className="text-xs font-medium rounded-full px-2.5 py-1 bg-slate-50 text-slate-400 border border-slate-200">
                  No data
                </span>
              )}
            </div>
            <p className="text-3xl font-semibold text-slate-900 mb-2">{hasScore ? score.toFixed(1) : "—"}</p>
            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden mb-3">
              <div className="h-full rounded-full" style={{ width: `${pct}%`, background: status?.bar ?? "#cbd5e1" }} />
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              {hasScore ? c.insight : "Not enough guest mentions yet."}
            </p>
            <p className="text-xs font-medium text-slate-400 mt-2">{c.name}</p>
          </button>
        )
      })}
    </div>
  )
}
