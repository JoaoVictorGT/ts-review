// Translation/style layer for the Score Improvement Plan widget (ScoreGoalPlan +
// AspectDeepDive), ported from the teammate's reference combined_widget.html.
// EFFORT_KEY/CONFIDENCE_LABEL translate the Ridge-regression report's
// Portuguese values; EFFORT_STYLE uses the site's real Tailwind palette (same
// emerald/amber/red/slate families as CategoryHealthCards.jsx's getStatus())
// instead of the reference widget's inline hex colors.

export const EFFORT_STYLE = {
  low: { label: "low effort", badge: "bg-emerald-50 text-emerald-700", bar: "#22c55e" },
  medium: { label: "medium effort", badge: "bg-amber-50 text-amber-700", bar: "#eab308" },
  high: { label: "high effort", badge: "bg-red-50 text-red-700", bar: "#ef4444" },
  not_actionable: { label: "not actionable", badge: "bg-slate-50 text-slate-500", bar: "#94a3b8" },
  "n/a": { label: "", badge: "bg-slate-50 text-slate-500", bar: "#94a3b8" },
}

// dataset's Portuguese effort_tier values -> EFFORT_STYLE keys above
export const EFFORT_KEY = {
  baixo: "low",
  medio: "medium",
  alto: "high",
  nao_acionavel: "not_actionable",
  "n/a": "n/a",
}

// dataset's Portuguese confidence strings -> English display text
export const CONFIDENCE_LABEL = {
  alta: "high",
  moderada: "moderate",
  baixa: "low",
  "baixa (poucas menções)": "low (few mentions)",
}

export const ASPECT_LABEL = {
  facilities: "Facilities",
  comfort: "Comfort",
  food: "Food",
  staff: "Staff",
  cleanliness: "Cleanliness",
  location: "Location",
  noise: "Noise",
  value: "Value",
}

// Same convention as src/dashboard_data_prep.py's SUBTAG_DISPLAY, extended with
// subtags that only appear in the model report's causes (not in on-site
// auto-insight text) — kept as a separate JS dict since the two live in
// different languages/runtimes.
export const CAUSE_LABEL = {
  bathroom: "Bathroom",
  water_quality: "Water quality",
  heating: "Heating",
  air_conditioning: "Air conditioning",
  wifi: "Wi-Fi",
  parking: "Parking",
  elevator: "Elevator",
  pool_gym_spa: "Pool / gym / spa",
  bed_mattress: "Bed / mattress",
  sleep_quality: "Sleep quality",
  room_size: "Room size",
  checkin_checkout: "Check-in / check-out",
  staff_general: "Staff attitude",
  helpfulness: "Helpfulness",
  rudeness: "Politeness",
  management: "Management",
  breakfast: "Breakfast",
  restaurant_service: "Restaurant service",
  drinks_bar: "Bar / drinks",
  food_general: "Food",
  smell: "Smell",
  dirt_dust: "Dirt / dust",
  mold: "Mold",
  hygiene: "Hygiene",
  housekeeping_general: "Housekeeping",
  distance_center: "Distance to center",
  transport_access: "Transport access",
  surroundings: "Surroundings",
  location_general: "Location",
  price_too_high: "High prices",
  hidden_fees: "Hidden fees",
  good_value: "Value for money",
  value_general: "Pricing",
  external_noise: "Outside noise",
  internal_noise: "Noise from neighbors",
  noise_general: "Noise",
}
