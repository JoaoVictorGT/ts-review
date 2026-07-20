import json
import logging

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-flash-latest"  # alias Google keeps pointed at their current flash-tier model
FALLBACK_MESSAGE = "Não consegui entender sua pergunta. Você pode reformular ou falar com nosso suporte?"
MAX_COMMENTS_PER_CATEGORY = 6  # defensive cap; upstream generator already caps at 4/side per sentiment

SYSTEM_INSTRUCTION = (
    "You are TrueStay's hotel performance analyst. Answer the hotel manager's "
    "question using ONLY the JSON data provided as context — category scores, "
    "competitor comparisons, regional ranking, quarterly trend, and real guest "
    "review excerpts. Be concise (2-4 sentences), cite concrete numbers from "
    "the data when relevant, and say plainly if the data can't answer the question."
)

_model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    _model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)


def _trim_context(context: dict) -> dict:
    """Drop UI-only fields (icons, internal ids) the model has no use for;
    cap comment arrays defensively. Everything else is kept close to as-is —
    it's already small (a few KB), and the whole point of this feature is
    grounding on real guest text, so trimming further would cost quality
    for no real size/cost benefit at this data scale.
    """
    return {
        "categories": [{"name": c["name"], "insight": c["insight"]} for c in context.get("CATEGORIES", [])],
        "hotel_scores": context.get("HOTEL_ARENA_SCORES", {}),
        "competitors": [{"name": c["name"], "scores": c["scores"]} for c in context.get("COMPETITORS", [])],
        "leaderboard": context.get("LEADERBOARD", []),
        "vulnerabilities": context.get("VULNERABILITIES", []),
        "quarterly_labels": context.get("QUARTERLY_LABELS", []),
        "quarterly_overall": context.get("QUARTERLY_OVERALL", []),
        "quarterly_by_category": context.get("QUARTERLY_BY_CATEGORY", {}),
        "dimension_comments": context.get("DIMENSION_COMMENTS", []),
        "category_comments": {
            name: comments[:MAX_COMMENTS_PER_CATEGORY]
            for name, comments in context.get("CATEGORY_COMMENTS", {}).items()
        },
        "regional_standing": context.get("REGIONAL_STANDING", {}),
        "worst_category": context.get("WORST_CATEGORY", {}),
        "best_category": context.get("BEST_CATEGORY", {}),
    }


def ask(question: str, context: dict) -> str:
    if _model is None:  # GEMINI_API_KEY unset — degrade gracefully, no network call
        return FALLBACK_MESSAGE
    try:
        prompt = f"HOTEL DATA (JSON):\n{json.dumps(_trim_context(context), default=str)}\n\nQUESTION: {question}"
        # Cap total time (including the SDK's own automatic retries) so a
        # transient/rate-limit failure falls back in ~45s, not the 1-2
        # minutes the client's default retry budget can otherwise take.
        response = _model.generate_content(prompt, request_options={"timeout": 45})
        text = (response.text or "").strip()
        return text or FALLBACK_MESSAGE
    except google_exceptions.ResourceExhausted:
        logger.warning("Gemini rate limit/quota exceeded")
        return FALLBACK_MESSAGE
    except google_exceptions.GoogleAPIError:
        logger.exception("Gemini API error")
        return FALLBACK_MESSAGE
    except Exception:
        # response.text's accessor can itself raise (e.g. safety-filtered
        # generations), plus any other unexpected SDK/network failure —
        # ask() must never raise, this is the final safety net.
        logger.exception("Unexpected error calling Gemini")
        return FALLBACK_MESSAGE
