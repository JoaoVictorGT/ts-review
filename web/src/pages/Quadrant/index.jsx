import { useState } from "react"
import { HOTELS } from "../../data/mockData"
import HotelDot from "./HotelDot"
import HotelDrawer from "./HotelDrawer"

export default function Quadrant() {
  const [openHotelId, setOpenHotelId] = useState(null)
  const openHotel = HOTELS.find((h) => h.id === openHotelId) ?? null

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <div className="mb-10">
        <h1 className="text-3xl font-semibold text-slate-900">TrueStay Quadrant</h1>
        <p className="text-slate-500 mt-2">Daily rate vs. audited performance across 4 dimensions.</p>
      </div>

      <div className="grid lg:grid-cols-[1fr_auto] gap-8 items-start">
        <div className="relative aspect-square bg-slate-50 rounded-xl border border-slate-200 p-8">
          <div className="absolute inset-8 border-l border-b border-dashed border-slate-300" />
          <div className="absolute inset-8 left-1/2 top-8 bottom-8 border-l border-dashed border-slate-300" />
          <div className="absolute inset-8 top-1/2 left-8 right-8 border-t border-dashed border-slate-300" />

          <span className="absolute top-4 left-8 text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Overpriced
          </span>
          <span className="absolute top-4 right-8 text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Premium / Luxury
          </span>
          <span className="absolute bottom-4 left-8 text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Basic Economy
          </span>
          <span className="absolute bottom-4 right-8 text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Value for Money
          </span>

          <span className="absolute left-2 top-1/2 -translate-y-1/2 -rotate-90 text-xs text-slate-400">Price</span>
          <span className="absolute bottom-2 right-1/2 translate-x-1/2 text-xs text-slate-400">Audited quality</span>

          <div className="relative w-full h-full">
            {HOTELS.map((h) => (
              <HotelDot key={h.id} hotel={h} onOpen={setOpenHotelId} />
            ))}
          </div>
        </div>

        <div className="w-full lg:w-72 bg-white border border-slate-200 rounded-xl p-5">
          <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-3">Legend</p>
          <div className="flex items-center gap-2 mb-2 text-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-slate-600">Premium / Luxury</span>
          </div>
          <div className="flex items-center gap-2 mb-2 text-sm">
            <span className="w-2 h-2 rounded-full bg-sky-500" />
            <span className="text-slate-600">Value for Money</span>
          </div>
          <div className="flex items-center gap-2 mb-2 text-sm">
            <span className="w-2 h-2 rounded-full bg-slate-400" />
            <span className="text-slate-600">Basic Economy</span>
          </div>
          <div className="flex items-center gap-2 mb-2 text-sm">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span className="text-slate-600">Overpriced</span>
          </div>
          <p className="text-xs text-slate-400 mt-4 leading-relaxed">Click a hotel on the chart to open the detailed report.</p>
        </div>
      </div>

      {openHotel && <HotelDrawer hotel={openHotel} onClose={() => setOpenHotelId(null)} />}
    </div>
  )
}
