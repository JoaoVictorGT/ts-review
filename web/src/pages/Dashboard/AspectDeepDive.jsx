import { useEffect } from "react"
import { EFFORT_STYLE, EFFORT_KEY, ASPECT_LABEL, CAUSE_LABEL } from "../../data/aspectDeepDiveLabels"

const BACK_BUTTON_CLASS =
  "border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-500 mb-3 hover:border-slate-400"

export default function AspectDeepDive({ aspect, details, activeCause, onSelectCause, onBack }) {
  const causes = details?.causes ?? []

  // Mirrors combined_widget.html's renderDetail(): whenever the aspect (or its
  // causes) change, auto-select the first cause if nothing valid is selected —
  // keeps the evidence panel from ever showing a stale/blank selection.
  useEffect(() => {
    if (!details) return
    if (!causes.some((c) => c.cause === activeCause)) {
      onSelectCause(causes.length ? causes[0].cause : null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aspect, details])

  // Guard: a lever can point at an aspect with no matching aspect_details entry
  // (report doesn't cover every aspect for every hotel). Rather than crash on
  // details.n_complaints/.causes, show a short "not available yet" message —
  // the section is still reachable and "Back to plan" always works.
  if (!details) {
    return (
      <div>
        <button type="button" onClick={onBack} className={BACK_BUTTON_CLASS}>
          ← Back to plan
        </button>
        <p className="text-sm text-slate-500">No detailed data available for {ASPECT_LABEL[aspect] || aspect} yet.</p>
      </div>
    )
  }

  const maxN = Math.max(...causes.map((c) => c.n), 1)
  const activeCauseData = causes.find((c) => c.cause === activeCause)

  return (
    <div>
      <button type="button" onClick={onBack} className={BACK_BUTTON_CLASS}>
        ← Back to plan
      </button>

      <div className="flex items-baseline justify-between mb-0.5">
        <span className="text-lg font-semibold text-slate-900">{ASPECT_LABEL[aspect] || aspect}</span>
        <span className="text-sm text-slate-500">
          {details.n_complaints} of {details.n_mentions} mentions are complaints
        </span>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        What guests specifically complain about — click a cause to see the reviews.
      </p>

      <div>
        {causes.map((c) => {
          const on = c.cause === activeCause
          const width = Math.round((c.n / maxN) * 100)
          const bar = EFFORT_STYLE[EFFORT_KEY[c.effort_tier] || "n/a"].bar
          return (
            <button
              key={c.cause}
              type="button"
              onClick={() => onSelectCause(c.cause)}
              className={`w-full text-left rounded-lg px-2.5 py-2 mb-1 border ${
                on ? "bg-white border-slate-300" : "bg-transparent border-transparent"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-sm text-slate-900 ${on ? "font-semibold" : "font-normal"}`}>
                  {CAUSE_LABEL[c.cause] || c.cause}
                </span>
                <span className="text-xs text-slate-500">
                  {c.n} · {c.pct_of_complaints}%
                </span>
              </div>
              <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${width}%`, background: bar }} />
              </div>
            </button>
          )
        })}
      </div>

      <div className="border-t border-slate-200 my-4" />

      {activeCauseData ? (
        <>
          <p className="text-sm text-slate-500 mb-2.5">
            <b className="text-slate-900">{CAUSE_LABEL[activeCauseData.cause] || activeCauseData.cause}</b> —{" "}
            {activeCauseData.evidence.length} review example{activeCauseData.evidence.length > 1 ? "s" : ""}
          </p>
          {activeCauseData.evidence.length ? (
            activeCauseData.evidence.map((quote, i) => (
              <div key={i} className="border border-slate-200 rounded-lg px-3.5 py-2.5 mb-2 bg-white">
                <span className="text-sm text-slate-500 leading-relaxed">&quot;{quote}&quot;</span>
              </div>
            ))
          ) : (
            <p className="text-sm text-slate-400">No verbatim excerpt available for this cause.</p>
          )}
        </>
      ) : (
        <p className="text-sm text-slate-500">No causes recorded.</p>
      )}

      <p className="text-xs text-slate-400 leading-relaxed mt-4">
        A single review can mention more than one cause, so percentages add up to more than 100%. Excerpts are
        verbatim from the original reviews.
      </p>
    </div>
  )
}
