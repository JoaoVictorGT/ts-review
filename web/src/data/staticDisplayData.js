// Static, hand-maintained display data — NOT generated, NOT fetched from the API.
// Everything else (CATEGORIES, HOTEL_ARENA_SCORES, LEADERBOARD, etc.) now comes
// from the FastAPI backend at runtime; see web/src/hooks/useDashboardData.js.
//
// CATEGORY_COLORS, HOTELS, and QUADRANT_STYLES are mocked on purpose — the
// Quadrant page (price vs. audited quality) has no real data source; this
// dataset has no price/rate column at all.

export const CATEGORY_COLORS = {
  Food: "#f97316",
  Comfort: "#ef4444",
  Cleanliness: "#06b6d4",
  Staff: "#8b5cf6",
  Location: "#22c55e",
}

// Quadrant page (2x2 price vs. audited-quality scatter) — still 100% mocked.
// Also uses a different 0-5 scale and metric set (food/service/comfort/cleaner)
// than the Dashboard's 0-10 scale, inherited from the original mockup.
export const HOTELS = [
  { id: 1, name: "Grand Azure Palace", quadrant: "premium", x: 82, y: 18, price: 620, food: 4.7, service: 4.9, comfort: 4.8, cleaner: 4.9 },
  { id: 2, name: "Hotel Meridian Bay", quadrant: "premium", x: 74, y: 24, price: 540, food: 4.5, service: 4.6, comfort: 4.7, cleaner: 4.8 },
  { id: 3, name: "The Ivory Court", quadrant: "value", x: 78, y: 74, price: 210, food: 4.4, service: 4.6, comfort: 4.3, cleaner: 4.7 },
  { id: 4, name: "Cedar & Stone Inn", quadrant: "value", x: 70, y: 68, price: 180, food: 4.2, service: 4.5, comfort: 4.2, cleaner: 4.4 },
  { id: 5, name: "Downtown Basic Suites", quadrant: "basic", x: 28, y: 78, price: 95, food: 3.1, service: 3.2, comfort: 3.0, cleaner: 3.4 },
  { id: 6, name: "Traveler's Lodge", quadrant: "basic", x: 22, y: 84, price: 80, food: 2.9, service: 3.0, comfort: 3.1, cleaner: 3.2 },
  { id: 7, name: "Regal Overlook Hotel", quadrant: "overpriced", x: 26, y: 20, price: 480, food: 2.8, service: 3.0, comfort: 3.2, cleaner: 2.9 },
  { id: 8, name: "Marbella Grand", quadrant: "overpriced", x: 34, y: 28, price: 410, food: 3.1, service: 2.9, comfort: 3.0, cleaner: 3.1 },
]

export const QUADRANT_STYLES = {
  premium: { label: "Premium / Luxury", badge: "bg-emerald-50 text-emerald-700 border border-emerald-200", dot: "bg-emerald-500" },
  value: { label: "Value for Money", badge: "bg-sky-50 text-sky-700 border border-sky-200", dot: "bg-sky-500" },
  basic: { label: "Basic Economy", badge: "bg-slate-50 text-slate-600 border border-slate-200", dot: "bg-slate-400" },
  overpriced: { label: "Overpriced", badge: "bg-amber-50 text-amber-700 border border-amber-200", dot: "bg-amber-500" },
}
