import { X, ChevronRight } from "lucide-react"
import { QUADRANT_STYLES } from "../../data/mockData"

export default function HotelDrawer({ hotel, onClose }) {
  if (!hotel) return null
  const style = QUADRANT_STYLES[hotel.quadrant]
  const metrics = [
    ["Food", hotel.food],
    ["Service", hotel.service],
    ["Comfort", hotel.comfort],
    ["Cleaner", hotel.cleaner],
  ]

  return (
    <div className="fixed inset-0 z-40">
      <div className="absolute inset-0 bg-slate-900/30" onClick={onClose} />
      <div className="absolute right-0 top-0 w-full max-w-sm bg-white h-full shadow-xl p-8 overflow-y-auto">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-6 right-6 text-slate-400 hover:text-slate-600"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>
        <div className="w-full h-32 rounded-lg bg-gradient-to-br from-sky-100 to-blue-100 mb-6" />
        <span className={`inline-block text-xs font-medium rounded-full px-3 py-1 mb-3 ${style.badge}`}>
          {style.label}
        </span>
        <h2 className="text-xl font-semibold text-slate-900 mb-1">{hotel.name}</h2>
        <p className="text-sm text-slate-500 mb-8">Average daily rate: ${hotel.price}</p>
        <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-4">Audited performance</p>
        <div>
          {metrics.map(([label, value]) => {
            const pct = Math.round((value / 5) * 100)
            return (
              <div key={label} className="mb-4">
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-slate-600">{label}</span>
                  <span className="text-slate-900 font-medium">{value.toFixed(1)}/5</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-sky-400 to-blue-600"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
        <button
          type="button"
          className="w-full mt-6 flex items-center justify-center gap-2 bg-slate-900 text-white text-sm font-medium rounded-lg py-2.5 hover:bg-slate-800 transition-colors"
        >
          View full report <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
