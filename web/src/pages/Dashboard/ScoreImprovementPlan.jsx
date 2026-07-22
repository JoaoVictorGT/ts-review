import { useState } from "react"
import { useDashboardData } from "../../hooks/useDashboardData"
import ScoreGoalPlan from "./ScoreGoalPlan"
import AspectDeepDive from "./AspectDeepDive"

// Shared state for the two views, mirroring combined_widget.html's `state`
// object: view is "plan" or the active aspect's key. showPlan() intentionally
// leaves activeGoal untouched so the selected goal tab survives a
// detail -> plan -> detail round-trip; showDetail() always resets activeCause.
export default function ScoreImprovementPlan() {
  const { data } = useDashboardData()
  const { SCORE_GOALS, ASPECT_DETAILS } = data

  const [view, setView] = useState("plan")
  const [activeGoal, setActiveGoal] = useState(() => (SCORE_GOALS ? Object.keys(SCORE_GOALS)[0] : null))
  const [activeCause, setActiveCause] = useState(null)

  // Most hotels don't have report data yet (only the test hotel does, for
  // now) — rather than show an empty-state message, the section just doesn't
  // render, same as it not existing for hotels never covered by the report.
  if (!SCORE_GOALS) return null

  function showPlan() {
    setView("plan")
  }

  function showDetail(aspect) {
    setView(aspect)
    setActiveCause(null)
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 mb-14">
      {view === "plan" ? (
        <ScoreGoalPlan
          scoreGoals={SCORE_GOALS}
          activeGoal={activeGoal}
          onSelectGoal={setActiveGoal}
          onOpenLever={showDetail}
        />
      ) : (
        <AspectDeepDive
          aspect={view}
          details={ASPECT_DETAILS?.[view]}
          activeCause={activeCause}
          onSelectCause={setActiveCause}
          onBack={showPlan}
        />
      )}
    </div>
  )
}
