import { useState } from "react"
import { Filter, X } from "lucide-react"
import { REGIONAL_STANDING, COMPETITORS } from "../../data/mockData"
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
  const [activeFilter, setActiveFilter] = useState(null)
  const [selectedCompetitorId, setSelectedCompetitorId] = useState(COMPETITORS[0]?.id)

  function toggleFilter(name) {
    setActiveFilter((prev) => (prev === name ? null : name))
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <div className="flex items-center justify-between mb-10 flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Central Dashboard — Hotel Arena</h1>
          <p className="text-slate-500 mt-2">
            Health by category, competitive gap, score trend, ranking, and guest feedback.
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase">Overall Score</p>
          <p className="text-3xl font-semibold text-slate-900">{REGIONAL_STANDING.you.score.toFixed(2)}</p>
        </div>
      </div>

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
        selectedCompetitorId={selectedCompetitorId}
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
