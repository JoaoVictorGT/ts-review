import { useState } from "react"
import { Filter, X } from "lucide-react"
import { useDashboardData } from "../../hooks/useDashboardData"
import InsightCard from "./InsightCard"
import CategoryHealthCards from "./CategoryHealthCards"
import CompetitiveGapMatrix from "./CompetitiveGapMatrix"
import MonthlyScoreTrend from "./MonthlyScoreTrend"
import RegionalLeaderboard from "./RegionalLeaderboard"
import RegionalPosition from "./RegionalPosition"
import CommentsByDimension from "./CommentsByDimension"
import CategoryComments from "./CategoryComments"
import VulnerabilityTable from "./VulnerabilityTable"

export default function Dashboard() {
  const { data, loading, error } = useDashboardData()
  const [activeFilter, setActiveFilter] = useState(null)
  const [selectedCompetitorId, setSelectedCompetitorId] = useState(null)

  function toggleFilter(name) {
    setActiveFilter((prev) => (prev === name ? null : name))
  }

  if (loading) {
    return <div className="max-w-6xl mx-auto px-6 py-16 text-slate-400">Loading dashboard…</div>
  }
  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-16 text-red-500">
        Couldn't load dashboard data: {error.message}
      </div>
    )
  }

  const { REGIONAL_STANDING, COMPETITORS, QUARTERLY_LABELS } = data
  const competitorId = selectedCompetitorId ?? COMPETITORS[0]?.id
  const hotelName = REGIONAL_STANDING.you.name.replace(" (You)", "")
  const hasNoDataYet = QUARTERLY_LABELS.length === 0

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <div className="flex items-center justify-between mb-10 flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Central Dashboard — {hotelName}</h1>
          <p className="text-slate-500 mt-2">
            Health by category, competitive gap, score trend, ranking, and guest feedback.
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase">Overall Score</p>
          <p className="text-3xl font-semibold text-slate-900">{REGIONAL_STANDING.you.score.toFixed(2)}</p>
        </div>
      </div>

      {hasNoDataYet && (
        <div className="mb-6 bg-amber-50 border border-amber-200 text-amber-700 text-sm rounded-lg px-4 py-3">
          We don't have enough guest reviews for {hotelName} yet — the numbers below will fill in as reviews
          come in.
        </div>
      )}

      <InsightCard />

      {activeFilter && (
        <div className="mb-6 flex items-center gap-3 bg-blue-50 border border-blue-100 text-blue-700 text-sm rounded-lg px-4 py-2.5 w-fit">
          <Filter className="w-4 h-4" />
          <span>
            Active filter: <span className="font-medium">{activeFilter}</span>
          </span>
          <button type="button" onClick={() => setActiveFilter(null)} className="ml-2 text-blue-500 hover:text-blue-700">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-3">Category health</p>
      <CategoryHealthCards activeFilter={activeFilter} onToggleFilter={toggleFilter} />

      <CompetitiveGapMatrix
        activeFilter={activeFilter}
        selectedCompetitorId={competitorId}
        onSelectCompetitor={setSelectedCompetitorId}
      />

      <MonthlyScoreTrend />

      <div className="grid lg:grid-cols-2 gap-6 mb-14">
        <RegionalLeaderboard />
        <RegionalPosition />
      </div>

      <CommentsByDimension />
      <CategoryComments />
      <VulnerabilityTable />
    </div>
  )
}
