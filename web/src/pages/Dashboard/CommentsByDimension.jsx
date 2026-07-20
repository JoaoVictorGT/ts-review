import { useDashboardData } from "../../hooks/useDashboardData"

export default function CommentsByDimension() {
  const { data } = useDashboardData()
  // Worst (highest % negative) first, so the categories needing the most
  // attention surface at the top of the widget.
  const SORTED_BY_WORST = [...data.DIMENSION_COMMENTS].sort(
    (a, b) => b.negative / b.total - a.negative / a.total,
  )
  return (
    <>
      <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-3">Guest comments by dimension</p>
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-14">
        <div className="flex items-center gap-4 mb-6 text-xs text-slate-500">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            Positive mentions
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
            Complaints
          </span>
        </div>
        {SORTED_BY_WORST.map((d) => {
          const negPct = Math.round((d.negative / d.total) * 100)
          const posWidth = 100 - negPct
          return (
            <div key={d.name} className="mb-4 last:mb-0">
              <div className="flex justify-between text-sm mb-1.5 flex-wrap gap-1">
                <span className="text-slate-700 font-medium">{d.name}</span>
                <span className="text-slate-500">
                  {d.negative} complaints <span className="text-slate-400">/ {d.total} mentions</span> ·{" "}
                  <span className={`${negPct >= 40 ? "text-red-600" : "text-slate-400"} font-medium`}>
                    {negPct}% negative
                  </span>
                </span>
              </div>
              <div className="h-2.5 w-full rounded-full overflow-hidden flex">
                <div className="h-full bg-emerald-400" style={{ width: `${posWidth}%` }} />
                <div className="h-full bg-red-400" style={{ width: `${negPct}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}
