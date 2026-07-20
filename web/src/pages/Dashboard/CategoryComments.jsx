import { useState } from "react"
import { ThumbsUp, ThumbsDown } from "lucide-react"
import { useDashboardData } from "../../hooks/useDashboardData"

export default function CategoryComments() {
  const { data } = useDashboardData()
  const { CATEGORIES, CATEGORY_COMMENTS } = data
  const [activeCategory, setActiveCategory] = useState("Food")
  const comments = CATEGORY_COMMENTS[activeCategory] ?? []

  return (
    <>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase">Recent guest comments by category</p>
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1.5">
            <ThumbsUp className="w-3.5 h-3.5 text-emerald-500" />
            Positive
          </span>
          <span className="flex items-center gap-1.5">
            <ThumbsDown className="w-3.5 h-3.5 text-red-500" />
            Negative
          </span>
        </div>
      </div>
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-14">
        <div className="flex flex-wrap gap-1 bg-slate-100 rounded-lg p-1 mb-5 w-fit">
          {CATEGORIES.map((c) => {
            const active = activeCategory === c.name
            return (
              <button
                key={c.name}
                type="button"
                onClick={() => setActiveCategory(c.name)}
                className={`text-xs font-medium rounded-md px-3 py-1.5 transition-colors ${
                  active ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {c.name}
              </button>
            )
          })}
        </div>
        <div className="space-y-3">
          {comments.map((c, i) => {
            const isPositive = c.sentiment === "positive"
            const Icon = isPositive ? ThumbsUp : ThumbsDown
            return (
              // eslint-disable-next-line react/no-array-index-key
              <div key={i} className="flex items-start gap-3 border border-slate-100 rounded-lg p-3.5">
                <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${isPositive ? "text-emerald-500" : "text-red-500"}`} />
                <div className="flex-1">
                  <p className="text-sm text-slate-700 leading-relaxed">&quot;{c.text}&quot;</p>
                  <p className="text-xs text-slate-400 mt-1.5">
                    {c.nationality} · {c.date}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </>
  )
}
