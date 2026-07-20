import { TrendingUp, TrendingDown } from "lucide-react"
import { useDashboardData } from "../../hooks/useDashboardData"

export default function RegionalPosition() {
  const { data } = useDashboardData()
  const { you, total, average, delta, percentBetterThan } = data.REGIONAL_STANDING
  const { WORST_CATEGORY, BEST_CATEGORY } = data
  const isAboveAverage = delta >= 0
  const isTopHalf = percentBetterThan >= 50
  const hotelName = you.name.replace(" (You)", "")
  const trendPhrase =
    you.trend === "up" ? "trending upward" : you.trend === "down" ? "trending downward" : "holding steady"
  const narrative = `${hotelName} is ${trendPhrase} overall, with ${BEST_CATEGORY.name} its strongest category and ${WORST_CATEGORY.name} its biggest opportunity for improvement.`

  return (
    <div>
      <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-3">Regional position</p>
      <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col justify-center">
        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-4xl font-semibold text-slate-900">#{you.rank}</span>
          <span className="text-sm text-slate-400">of {total} hotels</span>
        </div>

        <div
          className={`inline-flex w-fit items-center gap-1 text-xs font-medium rounded-full px-2.5 py-1 mb-3 border ${
            isTopHalf
              ? "text-emerald-700 bg-emerald-50 border-emerald-200"
              : "text-amber-700 bg-amber-50 border-amber-200"
          }`}
        >
          {isTopHalf ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          Better than {percentBetterThan}% of hotels in the region
        </div>

        <div className="flex items-baseline gap-1.5 mb-4 text-sm">
          <span className="text-slate-500">Regional average:</span>
          <span className="font-medium text-slate-700">{average.toFixed(2)}</span>
          <span className={`font-medium ${isAboveAverage ? "text-emerald-600" : "text-red-600"}`}>
            ({isAboveAverage ? "+" : ""}
            {delta.toFixed(2)} {isAboveAverage ? "above" : "below"} average)
          </span>
        </div>

        <p className="text-sm text-slate-500 leading-relaxed">{narrative}</p>
      </div>
    </div>
  )
}
