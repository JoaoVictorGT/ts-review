// Canned, keyword-matched replies grounded in the same mock data the rest of
// the dashboard uses — no real LLM/backend yet, but the numbers it quotes are
// real (well, real-mock) and consistent with what's shown elsewhere. Swap
// this for an actual API call once the backend exists; the chat UI itself
// won't need to change.

import { CATEGORIES, HOTEL_ARENA_SCORES, REGIONAL_STANDING, WORST_CATEGORY, BEST_CATEGORY } from "../../data/mockData"

const GREETING =
  "Hi! I'm your TrueStay analyst. Ask me about any category (food, comfort, cleanliness, staff, location), how you compare to the region, or what's driving your score."

function findMentionedCategory(text) {
  const lower = text.toLowerCase()
  return CATEGORIES.find((c) => lower.includes(c.name.toLowerCase()))
}

export function getAgentReply(userText) {
  const lower = userText.toLowerCase()

  const category = findMentionedCategory(userText)
  if (category) {
    const score = HOTEL_ARENA_SCORES[category.name]
    return `${category.name} is currently at ${score.toFixed(1)}/10. ${category.insight}`
  }

  if (/(average|region|competitor|compare|rank)/.test(lower)) {
    const { you, total, average, delta, percentBetterThan } = REGIONAL_STANDING
    const direction = delta >= 0 ? "above" : "below"
    return (
      `You're ranked #${you.rank} of ${total} hotels in the region, ${Math.abs(delta).toFixed(2)} points ` +
      `${direction} the regional average of ${average.toFixed(2)}. That means you're doing better than ` +
      `${percentBetterThan}% of hotels nearby.`
    )
  }

  if (/(worst|risk|problem|weak|improve|wrong)/.test(lower)) {
    const score = HOTEL_ARENA_SCORES[WORST_CATEGORY.name]
    return `Your biggest opportunity right now is ${WORST_CATEGORY.name} (${score.toFixed(1)}/10). ${WORST_CATEGORY.insight}`
  }

  if (/(best|strong|good|driver|well)/.test(lower)) {
    const score = HOTEL_ARENA_SCORES[BEST_CATEGORY.name]
    return `${BEST_CATEGORY.name} is your strongest area (${score.toFixed(1)}/10). ${BEST_CATEGORY.insight}`
  }

  if (/^(hi|hello|hey)\b/.test(lower)) {
    return GREETING
  }

  return (
    "I can help with that — try asking about a specific category (food, comfort, cleanliness, staff, location), " +
    "how you compare to nearby competitors, or what's driving your score up or down."
  )
}

export function createInitialMessage() {
  return { id: crypto.randomUUID(), role: "agent", text: GREETING }
}
