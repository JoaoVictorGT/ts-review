import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Check } from "lucide-react"
import { useAuth } from "../hooks/useAuth"

const PLANS = [
  {
    id: "starter",
    name: "Starter",
    tagline: "For exploring the public quadrant.",
    price: "$0",
    period: "/mo",
    features: ["Access to the general quadrant", "1 summary report per month", "Email support"],
    cta: "Start for free",
    ctaClass: "bg-slate-900 text-white hover:bg-slate-800",
    highlight: false,
  },
  {
    id: "hotel_partner",
    name: "Hotel Partner",
    tagline: "For corporate travel managers.",
    price: "$1,490",
    period: "/mo",
    features: [
      "Unlimited consolidated reports",
      "Licensed TrueStay seal",
      "Benchmarking vs. competitors",
      "Priority support",
    ],
    cta: "Subscribe to Hotel Partner",
    ctaClass: "bg-gradient-to-r from-sky-400 to-blue-600 text-white shadow-sm hover:shadow-md",
    highlight: true,
  },
  {
    id: "corporate",
    name: "Corporate",
    tagline: "For chains and luxury agencies.",
    price: "Custom pricing",
    period: "",
    features: [
      "Everything in Hotel Partner",
      "Dedicated diagnostic consulting",
      "API integration",
      "Dedicated account manager",
    ],
    cta: "Talk to an expert",
    ctaClass: "bg-slate-900 text-white hover:bg-slate-800",
    highlight: false,
  },
]

export default function Pricing() {
  const { session, setPlan } = useAuth()
  const navigate = useNavigate()
  const [busyPlan, setBusyPlan] = useState(null)

  async function handleCta(plan) {
    if (!session) {
      // Only the free plan has a real signup flow today — the paid tiers
      // have no checkout/payment integration yet, so leave them inert for
      // logged-out visitors rather than pretending to start a subscription.
      if (plan.id === "starter") navigate("/register?from=pricing")
      return
    }
    // Already logged in (e.g. redirected here after registering outside the
    // pricing flow, per Feature 4) — picking any plan here just records the
    // choice and sends them to their dashboard.
    setBusyPlan(plan.id)
    try {
      await setPlan(plan.id)
      navigate("/dashboard")
    } finally {
      setBusyPlan(null)
    }
  }

  return (
    <section className="max-w-6xl mx-auto px-6 py-20">
      <div className="text-center mb-14">
        <h1 className="text-3xl font-semibold text-slate-900">Plans and pricing</h1>
        <p className="text-slate-500 mt-3">Choose the right level of access to TrueStay's hotel intelligence.</p>
      </div>
      <div className="grid md:grid-cols-3 gap-6 items-start">
        {PLANS.map((plan) => (
          <div
            key={plan.name}
            className={`relative bg-white rounded-xl p-8 border shadow-sm ${
              plan.highlight ? "border-2 border-blue-500 shadow-md" : "border-slate-200"
            }`}
          >
            {plan.highlight && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs font-medium rounded-full px-3 py-1">
                Most Popular
              </span>
            )}
            <h3 className="text-slate-900 font-medium">{plan.name}</h3>
            <p className="text-sm text-slate-500 mt-1 mb-6">{plan.tagline}</p>
            <div className="flex items-baseline gap-1 mb-6">
              <span className="text-3xl font-semibold text-slate-900">{plan.price}</span>
              {plan.period && <span className="text-sm text-slate-400">{plan.period}</span>}
            </div>
            <ul className="space-y-3 mb-8 text-sm text-slate-600">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-sky-500 mt-0.5 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            <button
              type="button"
              onClick={() => handleCta(plan)}
              disabled={busyPlan === plan.id}
              className={`w-full text-sm font-medium rounded-lg py-2.5 transition-colors disabled:opacity-50 ${plan.ctaClass}`}
            >
              {busyPlan === plan.id ? "Saving..." : plan.cta}
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}
