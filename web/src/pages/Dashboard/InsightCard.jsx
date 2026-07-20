import { Sparkles } from "lucide-react"
import { useDashboardData } from "../../hooks/useDashboardData"

/**
 * A single plain-language takeaway synthesizing the score, the regional
 * standing, and the weakest/strongest category — for guests who won't read
 * the charts below but still need to walk away knowing what to do next.
 */
export default function InsightCard() {
  const { data } = useDashboardData()
  const { HOTEL_ARENA_SCORES, WORST_CATEGORY, BEST_CATEGORY, REGIONAL_STANDING } = data
  const { you, average, delta } = REGIONAL_STANDING
  const isAboveAverage = delta >= 0
  const worstScore = HOTEL_ARENA_SCORES[WORST_CATEGORY.name]
  const bestScore = HOTEL_ARENA_SCORES[BEST_CATEGORY.name]

  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-blue-600 to-sky-500 rounded-xl p-6 mb-10 text-white shadow-sm">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg bg-white/15 flex items-center justify-center shrink-0">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs font-semibold tracking-wider uppercase text-blue-100 mb-1.5">This month's takeaway</p>
          <p className="text-base leading-relaxed max-w-3xl">
            Your overall score is <strong>{you.score.toFixed(2)}</strong> — {isAboveAverage ? "just above" : "just below"}{" "}
            the region's average of <strong>{average.toFixed(2)}</strong>. The biggest opportunity right now is{" "}
            <strong>
              {WORST_CATEGORY.name} ({worstScore != null ? worstScore.toFixed(1) : "—"}/10)
            </strong>
            : {WORST_CATEGORY.insight.toLowerCase()} On the bright side,{" "}
            <strong>
              {BEST_CATEGORY.name} ({bestScore != null ? bestScore.toFixed(1) : "—"}/10)
            </strong>{" "}
            remains your strongest driver of guest satisfaction.
          </p>
        </div>
      </div>
    </div>
  )
}
