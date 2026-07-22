import { Link } from "react-router-dom"
import { ShieldCheck } from "lucide-react"

export default function Home() {
  return (
    <>
      <div className="relative overflow-hidden">
        <div
          className="absolute inset-0"
          style={{ background: "radial-gradient(circle at 50% 0%, #f8fafc 0%, #ffffff 60%)" }}
        />
        <div className="relative max-w-4xl mx-auto px-6 pt-24 pb-20 text-center">
          <div className="inline-flex items-center gap-2 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-full px-3 py-1 mb-6">
            <ShieldCheck className="w-3.5 h-3.5" /> Independent Hotel Intelligence
          </div>
          <h1 className="text-5xl md:text-6xl font-semibold text-slate-900 leading-tight tracking-tight">
            Intelligence and{" "}
            <span className="bg-gradient-to-r from-sky-400 to-blue-600 bg-clip-text text-transparent">Trust</span>{" "}
            for hotel decisions
          </h1>
          <p className="mt-6 text-lg text-slate-500 max-w-2xl mx-auto">
            Verified reviews. Trusted stays. We rate hotels with rigorous, independent analysis, so
            travel managers can decide with data, not opinions.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              to="/quadrant"
              className="bg-gradient-to-r from-sky-400 to-blue-600 text-white text-sm font-medium rounded-lg px-6 py-3 shadow-sm hover:shadow-md transition-shadow"
            >
              View TrueStay Quadrant
            </Link>
            <Link
              to="/pricing"
              className="text-sm font-medium text-slate-700 border border-slate-200 rounded-lg px-6 py-3 hover:bg-slate-50 transition-colors"
            >
              View plans
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}
