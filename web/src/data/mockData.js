// Mock data for the TrueStay prototype. Every value here mirrors the
// real shape our NLP pipeline (src/nlp_pipeline.py) will eventually produce:
// a 0-10 score per category, closed-vocabulary complaint tags, and verbatim
// review excerpts. Swap this file for a real API/data call once the hotel x
// period panel (Phase 3) is ready — component code should not need to change.

export const CATEGORIES = [
  { name: "Food", icon: "utensils", insight: "Breakfast is well rated, but the buffet loses points on weekends." },
  { name: "Comfort", icon: "bed", insight: "Faulty windows and outside noise dragged the score down." },
  { name: "Cleanliness", icon: "sparkles", insight: "Recurring complaints about bathroom cleanliness over the last 30 days." },
  { name: "Staff", icon: "users", insight: "Front desk praised for friendliness, but check-in tends to run slow." },
  { name: "Location", icon: "map-pin", insight: "Central location is the main driver of guest satisfaction." },
]

export const CATEGORY_COLORS = {
  Food: "#f97316",
  Comfort: "#ef4444",
  Cleanliness: "#06b6d4",
  Staff: "#8b5cf6",
  Location: "#22c55e",
}

export const HOTEL_ARENA_SCORES = { Food: 7.1, Comfort: 5.4, Cleanliness: 6.8, Staff: 7.0, Location: 9.2 }

export const COMPETITORS = [
  { id: "plaza", name: "Competitor Plaza", scores: { Food: 8.9, Comfort: 8.2, Cleanliness: 9.0, Staff: 8.5, Location: 6.0 } },
  { id: "vondelpark", name: "Hotel Vondelpark", scores: { Food: 8.3, Comfort: 7.6, Cleanliness: 8.1, Staff: 7.9, Location: 7.2 } },
  { id: "canalview", name: "Canal View Suites", scores: { Food: 7.8, Comfort: 7.0, Cleanliness: 7.5, Staff: 6.8, Location: 8.0 } },
  { id: "museum", name: "Museumkwartier Hotel", scores: { Food: 7.5, Comfort: 7.8, Cleanliness: 7.9, Staff: 7.6, Location: 7.0 } },
]

export const LEADERBOARD = [
  { rank: 1, name: "Grand Hotel Krasnapolsky", score: 8.90 },
  { rank: 2, name: "Hotel Vondelpark", score: 8.55 },
  { rank: 3, name: "Competitor Plaza", score: 8.12 },
  { rank: 4, name: "Canal View Suites", score: 7.95 },
  { rank: 5, name: "Museumkwartier Hotel", score: 7.70 },
  { rank: 6, name: "Hotel Arena (You)", score: 7.43, isUser: true, trend: "up" },
  { rank: 7, name: "City Central Hotel", score: 7.20 },
  { rank: 8, name: "Amstel Riverside", score: 6.95 },
  { rank: 9, name: "Traveler's Rest", score: 6.40 },
  { rank: 10, name: "Budget Stay Amsterdam", score: 5.80 },
]

// Derived once, from LEADERBOARD, so every component that needs "how do we
// compare to the region" (Dashboard insight card, Regional Position card,
// the chat agent) reads the same numbers instead of recomputing them.
const _you = LEADERBOARD.find((h) => h.isUser)
const _total = LEADERBOARD.length
const _average = LEADERBOARD.reduce((sum, h) => sum + h.score, 0) / _total

export const REGIONAL_STANDING = {
  you: _you,
  total: _total,
  average: _average,
  delta: _you.score - _average,
  percentBetterThan: Math.round(((_total - _you.rank) / _total) * 100),
}

// Derived once, from HOTEL_ARENA_SCORES, so the weakest/strongest category
// (and its existing `insight` copy) can be reused anywhere without
// re-deriving the min/max each time.
export const WORST_CATEGORY = CATEGORIES.reduce((worst, c) =>
  HOTEL_ARENA_SCORES[c.name] < HOTEL_ARENA_SCORES[worst.name] ? c : worst,
)
export const BEST_CATEGORY = CATEGORIES.reduce((best, c) =>
  HOTEL_ARENA_SCORES[c.name] > HOTEL_ARENA_SCORES[best.name] ? c : best,
)

export const VULNERABILITIES = [
  {
    competitor: "Competitor Plaza",
    category: "Location",
    review: "terrible location, way too far from the metro and a nightmare to walk back at night",
    highlights: ["terrible location", "far from the metro"],
  },
  {
    competitor: "Hotel Vondelpark",
    category: "Comfort",
    review: "noisy room and the air conditioning was broken all night",
    highlights: ["noisy room", "air conditioning was broken"],
  },
  {
    competitor: "Canal View Suites",
    category: "Staff",
    review: "check-in took forever and the front desk seemed unable to solve any problems",
    highlights: ["check-in took forever"],
  },
]

export const MONTHLY_LABELS = ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
export const MONTHLY_OVERALL = [7.05, 7.10, 7.02, 7.18, 7.25, 7.15, 7.30, 7.28, 7.35, 7.40, 7.38, 7.43]
export const MONTHLY_BY_CATEGORY = {
  Food: [6.90, 6.95, 6.80, 7.00, 7.05, 6.95, 7.00, 7.05, 7.10, 7.05, 7.08, 7.10],
  Comfort: [5.80, 5.70, 5.90, 5.60, 5.50, 5.70, 5.60, 5.50, 5.45, 5.50, 5.42, 5.40],
  Cleanliness: [7.20, 7.10, 7.00, 6.90, 6.95, 6.85, 6.90, 6.80, 6.85, 6.75, 6.80, 6.80],
  Staff: [6.80, 6.85, 6.90, 6.95, 6.90, 6.95, 7.00, 6.98, 7.02, 7.00, 7.05, 7.00],
  Location: [8.90, 8.95, 9.00, 9.05, 9.10, 9.05, 9.10, 9.15, 9.10, 9.18, 9.20, 9.20],
}

export const DIMENSION_COMMENTS = [
  { name: "Food", total: 142, negative: 31 },
  { name: "Comfort", total: 98, negative: 60 },
  { name: "Cleanliness", total: 115, negative: 55 },
  { name: "Staff", total: 130, negative: 23 },
  { name: "Location", total: 176, negative: 7 },
]

export const CATEGORY_COMMENTS = {
  Food: [
    { sentiment: "positive", text: "Breakfast buffet was fantastic, so many fresh options every morning.", nationality: "Germany", date: "Jul 12" },
    { sentiment: "negative", text: "Restaurant service was slow during dinner rush, waited 40 minutes for a table.", nationality: "France", date: "Jul 08" },
    { sentiment: "positive", text: "Loved the coffee corner in the lobby, open 24 hours and always fresh.", nationality: "Spain", date: "Jul 02" },
    { sentiment: "negative", text: "Bar menu is limited and overpriced compared to nearby options.", nationality: "United States", date: "Jun 26" },
  ],
  Comfort: [
    { sentiment: "negative", text: "Could barely sleep, street noise came right through the window all night.", nationality: "United Kingdom", date: "Jul 14" },
    { sentiment: "negative", text: "Air conditioning was broken and the front desk took a day to fix it.", nationality: "Italy", date: "Jul 09" },
    { sentiment: "negative", text: "Bed was comfortable but the room felt cramped for two people.", nationality: "Netherlands", date: "Jul 03" },
    { sentiment: "positive", text: "Pillows and linens were genuinely great, best sleep I've had on a trip.", nationality: "Canada", date: "Jun 29" },
  ],
  Cleanliness: [
    { sentiment: "negative", text: "Bathroom had a lingering smell and the shower drain was slow.", nationality: "Belgium", date: "Jul 13" },
    { sentiment: "negative", text: "Found dust on the shelves and behind the TV, housekeeping missed a spot.", nationality: "Sweden", date: "Jul 07" },
    { sentiment: "positive", text: "Room was spotless on arrival, sheets smelled freshly washed.", nationality: "Portugal", date: "Jul 01" },
    { sentiment: "negative", text: "Towels weren't replaced on day two despite requesting housekeeping.", nationality: "Ireland", date: "Jun 24" },
  ],
  Staff: [
    { sentiment: "positive", text: "Reception team was incredibly friendly and helped us rebook a tour last minute.", nationality: "Australia", date: "Jul 11" },
    { sentiment: "negative", text: "Check-in took over 30 minutes even though we had a reservation confirmed.", nationality: "Germany", date: "Jul 05" },
    { sentiment: "positive", text: "Concierge gave excellent restaurant recommendations, very attentive service.", nationality: "Japan", date: "Jun 30" },
    { sentiment: "positive", text: "Every staff member we met was warm and quick to help with luggage.", nationality: "Brazil", date: "Jun 22" },
  ],
  Location: [
    { sentiment: "positive", text: "Perfectly central, walked to every major sight in under 15 minutes.", nationality: "United States", date: "Jul 15" },
    { sentiment: "positive", text: "Steps from the tram stop, incredibly convenient for getting around the city.", nationality: "France", date: "Jul 10" },
    { sentiment: "positive", text: "Quiet neighborhood but still close to restaurants and nightlife.", nationality: "Spain", date: "Jul 04" },
    { sentiment: "negative", text: "Great location but the surrounding street can get noisy on weekends.", nationality: "Germany", date: "Jun 27" },
  ],
}

// Quadrant page (2x2 price vs. audited-quality scatter). NOTE: uses a
// different 0-5 scale and a slightly different metric set (food/service/
// comfort/cleaner) than the Dashboard's 0-10 scale — a known inconsistency
// inherited from the original mockup, left as-is pending the real data model.
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
