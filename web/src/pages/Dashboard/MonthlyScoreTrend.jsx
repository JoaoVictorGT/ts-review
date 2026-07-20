import { useState } from "react"
import { Line } from "react-chartjs-2"
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js"
import { CATEGORY_COLORS } from "../../data/staticDisplayData"
import { useDashboardData } from "../../hooks/useDashboardData"

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler)

const TOGGLE_ACTIVE = "text-xs font-medium rounded-lg px-3 py-1.5 bg-slate-900 text-white transition-colors"
const TOGGLE_INACTIVE = "text-xs font-medium rounded-lg px-3 py-1.5 text-slate-500 hover:bg-slate-200 transition-colors"

export default function MonthlyScoreTrend() {
  const { data } = useDashboardData()
  const { CATEGORIES, QUARTERLY_LABELS, QUARTERLY_OVERALL, QUARTERLY_BY_CATEGORY } = data
  const [view, setView] = useState("overall")
  const [activeDimensions, setActiveDimensions] = useState(new Set(CATEGORIES.map((c) => c.name)))

  function toggleDimension(name) {
    setActiveDimensions((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  const datasets =
    view === "overall"
      ? [
          {
            label: "Overall Score",
            data: QUARTERLY_OVERALL,
            borderColor: "#2563eb",
            backgroundColor: "rgba(37,99,235,0.08)",
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointBackgroundColor: "#2563eb",
          },
        ]
      : CATEGORIES.filter((c) => activeDimensions.has(c.name)).map((c) => ({
          label: c.name,
          data: QUARTERLY_BY_CATEGORY[c.name],
          borderColor: CATEGORY_COLORS[c.name],
          backgroundColor: "transparent",
          tension: 0.35,
          pointRadius: 2,
        }))

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { min: 4, max: 10, grid: { color: "#f1f5f9" }, ticks: { color: "#94a3b8", font: { size: 11 } } },
      x: { grid: { display: false }, ticks: { color: "#94a3b8", font: { size: 11 } } },
    },
    plugins: {
      legend: {
        display: view === "dimension",
        position: "bottom",
        labels: { boxWidth: 8, boxHeight: 8, usePointStyle: true, color: "#475569", font: { size: 11 } },
      },
      tooltip: { mode: "index", intersect: false },
    },
    interaction: { mode: "index", intersect: false },
  }

  return (
    <>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase">Quarterly score trend</p>
        <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
          <button type="button" onClick={() => setView("overall")} className={view === "overall" ? TOGGLE_ACTIVE : TOGGLE_INACTIVE}>
            Overall
          </button>
          <button type="button" onClick={() => setView("dimension")} className={view === "dimension" ? TOGGLE_ACTIVE : TOGGLE_INACTIVE}>
            By Dimension
          </button>
        </div>
      </div>
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-14">
        {view === "dimension" && (
          <div className="flex flex-wrap gap-2 mb-5">
            {CATEGORIES.map((c) => {
              const active = activeDimensions.has(c.name)
              const color = CATEGORY_COLORS[c.name]
              const style = active
                ? { background: `${color}1A`, borderColor: color, color }
                : { background: "#fff", borderColor: "#e2e8f0", color: "#94a3b8" }
              return (
                <button
                  key={c.name}
                  type="button"
                  onClick={() => toggleDimension(c.name)}
                  className="text-xs font-medium rounded-full px-3 py-1.5 border transition-colors"
                  style={style}
                >
                  {c.name}
                </button>
              )
            })}
          </div>
        )}
        <div style={{ height: "260px" }}>
          <Line data={{ labels: QUARTERLY_LABELS, datasets }} options={options} />
        </div>
      </div>
    </>
  )
}
