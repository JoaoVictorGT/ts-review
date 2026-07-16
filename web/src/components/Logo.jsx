import { Star, Check } from "lucide-react"

export default function Logo({ light = false }) {
  return (
    <span className="flex items-center gap-2">
      <span className="relative w-7 h-7 flex items-center justify-center">
        <Star className="w-7 h-7 text-sky-400" strokeWidth={1.75} />
        <Check className="w-3.5 h-3.5 text-blue-600 absolute" strokeWidth={3} />
      </span>
      <span className={`text-lg font-semibold tracking-tight ${light ? "text-white" : "text-slate-900"}`}>
        TrueStay
      </span>
    </span>
  )
}
