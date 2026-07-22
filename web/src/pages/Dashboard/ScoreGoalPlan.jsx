import { EFFORT_STYLE, EFFORT_KEY, CONFIDENCE_LABEL, ASPECT_LABEL, CAUSE_LABEL } from "../../data/aspectDeepDiveLabels"

export default function ScoreGoalPlan({ scoreGoals, activeGoal, onSelectGoal, onOpenLever }) {
  const goal = scoreGoals[activeGoal]
  const combo = goal.combo || []
  const maxContribution = Math.max(...combo.map((x) => x.contribution), 0.0001)

  return (
    <div>
      <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-1">Score improvement plan</p>
      <p className="text-sm text-slate-500 mb-4">How many points do you want to add to the predicted score?</p>

      <div className="flex gap-2 mb-5">
        {Object.keys(scoreGoals).map((g) => (
          <button
            key={g}
            type="button"
            onClick={() => onSelectGoal(g)}
            className={`flex-1 rounded-lg border py-2 text-sm transition-colors ${
              g === activeGoal
                ? "bg-slate-900 text-white border-slate-900 font-semibold"
                : "bg-transparent text-slate-500 border-slate-300 hover:border-slate-400"
            }`}
          >
            {g}
          </button>
        ))}
      </div>

      {goal.fully_achievable ? (
        <div className="bg-emerald-50 rounded-lg px-4 py-3 mb-4">
          <p className="text-sm font-semibold text-emerald-700">Goal achievable</p>
          <p className="text-sm text-emerald-700">
            Predicted score: <b>{goal.predicted_target_score}</b> · touching {combo.length} area
            {combo.length > 1 ? "s" : ""}
          </p>
        </div>
      ) : (
        <div className="bg-amber-50 rounded-lg px-4 py-3 mb-4">
          <p className="text-sm font-semibold text-amber-700">
            Partially achievable — only +{goal.achieved_delta.toFixed(2)}
          </p>
          <p className="text-sm text-amber-700">
            Even maxing out every area, the predicted score reaches <b>{goal.predicted_target_score}</b>
          </p>
        </div>
      )}

      <div>
        {combo.map((x) => {
          const style = EFFORT_STYLE[EFFORT_KEY[x.effort_tier] || "n/a"]
          const width = Math.round((x.contribution / maxContribution) * 100)
          return (
            <button
              key={x.aspect}
              type="button"
              onClick={() => onOpenLever(x.aspect)}
              className="w-full text-left border border-slate-200 rounded-lg px-4 py-3 mb-2 bg-white hover:border-slate-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-900">{ASPECT_LABEL[x.aspect] || x.aspect}</span>
                  <span className="text-xs text-slate-400">
                    {x.current_score.toFixed(1)} → {x.target_score.toFixed(1)}
                  </span>
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-lg ${style.badge}`}>{style.label}</span>
              </div>
              <div className="flex items-center gap-2.5 mb-2">
                <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${width}%`, background: style.bar }} />
                </div>
                <span className="text-xs text-slate-500 min-w-[90px] text-right">
                  +{x.contribution.toFixed(2)} to score
                </span>
              </div>
              <p className="text-sm text-slate-500">
                top cause: <b className="text-slate-900">{CAUSE_LABEL[x.top_cause] || x.top_cause || "—"}</b> ·{" "}
                {x.n_mentions} mentions · confidence: {CONFIDENCE_LABEL[x.confidence] || x.confidence}{" "}
                <span className="text-blue-600">· view details →</span>
              </p>
            </button>
          )
        })}
      </div>

      <p className="text-xs text-slate-400 leading-relaxed mt-4">
        Correlational model estimate, not a causal guarantee. Effort is an editorial judgment call, not real cost
        data. Click a lever to see what's driving it.
      </p>
    </div>
  )
}
