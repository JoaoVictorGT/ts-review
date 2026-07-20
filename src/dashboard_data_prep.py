"""Turn NLP-enriched review data into the aggregated views the TrueStay
dashboard needs — the same shapes currently hand-mocked in
``web/src/data/mockData.js`` (HOTEL_ARENA_SCORES, LEADERBOARD,
DIMENSION_COMMENTS, CATEGORY_COMMENTS, COMPETITORS, VULNERABILITIES).

This is a PROTOTYPE, not the real Phase 3 pipeline. It runs on the 500-row
Colab smoke-test sample (``reviews_enriched_sample.parquet``), which only
covers 2 hotels — enough to prove the transformations produce sane numbers,
not enough for a real leaderboard/quadrant. Point ``INPUT_PATH`` at the full
``reviews_enriched.parquet`` once that finishes running to get real breadth.

Known gaps vs. the mocked website (read before wiring this to real data):

* The mock's "Monthly score trend" is monthly; this data only supports
  QUARTERLY granularity (`quarter` column) — matches the hotel x quarter
  panel decided earlier. The chart will need a label change, not just new data.
* The mock's Quadrant page (price vs. audited quality) has no equivalent
  here — the dataset has no price/rate column. Leave that page mocked, or
  source pricing from elsewhere, until that's resolved.
* The website currently only shows 5 of our 8 aspects (Food, Comfort,
  Cleanliness, Staff, Location — missing Value, Noise, Facilities). This
  script computes all 8; §7 below shows the mismatch with real counts so
  it's a visible decision, not a silent drop.

Run with:
    python src/dashboard_data_prep.py
or paste the body into a new Colab cell after the NLP pipeline cells (same
file, no changes needed — it only depends on pandas).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nlp_pipeline import ASPECT_LEXICON  # noqa: E402  (same-folder import, see sys.path above)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "outputs" / "reviews_enriched_sample.parquet"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "dashboard_data_sample.json"
MOCKDATA_JS_PATH = PROJECT_ROOT / "web" / "src" / "data" / "mockData.js"

# snake_case sub-tag -> readable phrase, for auto-generated insight text.
# Anything missing here falls back to a plain "_" -> " " replace.
SUBTAG_DISPLAY = {
    "dirt_dust": "dirt & dust",
    "housekeeping_general": "housekeeping",
    "checkin_checkout": "check-in/check-out",
    "staff_general": "staff",
    "location_general": "location",
    "distance_center": "distance to the center",
    "transport_access": "transport access",
    "restaurant_service": "restaurant service",
    "drinks_bar": "the bar",
    "food_general": "food",
    "price_too_high": "high prices",
    "hidden_fees": "hidden fees",
    "good_value": "value for money",
    "value_general": "pricing",
    "external_noise": "outside noise",
    "internal_noise": "noise from neighbors",
    "noise_general": "noise",
    "water_quality": "water quality",
    "air_conditioning": "air conditioning",
    "pool_gym_spa": "the pool/gym/spa",
    "bed_mattress": "the bed/mattress",
    "room_size": "room size",
    "sleep_quality": "sleep quality",
}

# All 8 aspects our NLP pipeline scores. The website today only surfaces 5
# (see the module docstring) — WEBSITE_ASPECTS below is that subset.
ASPECTS = ["cleanliness", "staff", "location", "comfort", "food", "value", "noise", "facilities"]
WEBSITE_ASPECTS = ["food", "comfort", "cleanliness", "staff", "location"]

# A 0-10 aspect score below this is treated as a complaint, at/above as a
# compliment. 5.0 is the neutral midpoint _score_from_label already uses in
# nlp_pipeline.py, so this reuses the same cut rather than inventing a new one.
NEGATIVE_THRESHOLD = 5.0


def title(aspect: str) -> str:
    """"value" -> "Value", matching the Title Case category names in mockData.js."""
    return "Value for Money" if aspect == "value" else aspect.capitalize()


# --------------------------------------------------------------------------- #
# 1. Category health per hotel — mirrors HOTEL_ARENA_SCORES
# --------------------------------------------------------------------------- #


def category_scores_by_hotel(df: pd.DataFrame) -> pd.DataFrame:
    """Mean 0-10 score and mention count per aspect, one row per hotel.

    Reviews that never mention an aspect carry NaN in that aspect's score
    column (by design — see nlp_pipeline.py) so `.mean()` correctly ignores
    them instead of treating silence as a neutral 5.
    """
    rows = []
    for hotel, g in df.groupby("Hotel_Name"):
        row = {"Hotel_Name": hotel, "n_reviews": len(g)}
        for aspect in ASPECTS:
            col = g[f"aspect_{aspect}_score"]
            row[f"{aspect}_score"] = round(col.mean(), 2) if col.notna().any() else None
            row[f"{aspect}_mentions"] = int(col.notna().sum())
        rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 2. Overall score + leaderboard — mirrors LEADERBOARD / REGIONAL_STANDING
# --------------------------------------------------------------------------- #


def leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """Rank hotels by mean Reviewer_Score.

    Deliberately the mean of the review-level Reviewer_Score, NOT the
    dataset's static Average_Score column — Average_Score is a hotel-level
    constant (see the Phase 1 data audit) and can't answer "how is this
    hotel doing", which is the whole point of this dashboard.
    """
    board = (
        df.groupby("Hotel_Name")["Reviewer_Score"]
        .agg(overall_score="mean", n_reviews="size")
        .round({"overall_score": 2})
        .sort_values("overall_score", ascending=False)
        .reset_index()
    )
    board.insert(0, "rank", range(1, len(board) + 1))
    return board


# --------------------------------------------------------------------------- #
# 3. Quarterly trend — mirrors MONTHLY_OVERALL / MONTHLY_BY_CATEGORY
#    (quarterly here, not monthly — see module docstring)
# --------------------------------------------------------------------------- #


def quarterly_trend(df: pd.DataFrame, hotel_name: str) -> pd.DataFrame:
    """Overall + per-aspect mean score by quarter, for one hotel."""
    hotel_df = df[df["Hotel_Name"] == hotel_name]
    overall = hotel_df.groupby("quarter")["Reviewer_Score"].mean().round(2)
    trend = pd.DataFrame({"overall": overall})
    for aspect in WEBSITE_ASPECTS:
        trend[aspect] = hotel_df.groupby("quarter")[f"aspect_{aspect}_score"].mean().round(2)
    return trend.reset_index()


# --------------------------------------------------------------------------- #
# 4. Dimension comments summary — mirrors DIMENSION_COMMENTS
# --------------------------------------------------------------------------- #


def dimension_comments(df: pd.DataFrame, hotel_name: str) -> pd.DataFrame:
    """Total mentions and complaint count per aspect, for one hotel."""
    hotel_df = df[df["Hotel_Name"] == hotel_name]
    rows = []
    for aspect in WEBSITE_ASPECTS:
        col = hotel_df[f"aspect_{aspect}_score"]
        total = int(col.notna().sum())
        negative = int((col < NEGATIVE_THRESHOLD).sum())
        rows.append({"name": title(aspect), "total": total, "negative": negative})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 5. Category comment samples — mirrors CATEGORY_COMMENTS
# --------------------------------------------------------------------------- #


def category_comments(df: pd.DataFrame, hotel_name: str, per_side: int = 4) -> dict[str, list[dict]]:
    """Up to `per_side` real positive + negative evidence excerpts per aspect.

    Evidence text comes verbatim from _extract_evidence in nlp_pipeline.py —
    a word-window slice of the actual review, never generated — so these
    "comments" are guaranteed to be real guest text, not invented copy.
    """
    hotel_df = df[df["Hotel_Name"] == hotel_name]
    result: dict[str, list[dict]] = {}
    for aspect in WEBSITE_ASPECTS:
        score_col, evidence_col = f"aspect_{aspect}_score", f"aspect_{aspect}_evidence"
        mentioned = hotel_df[hotel_df[score_col].notna() & (hotel_df[evidence_col] != "")]
        picked = []
        for sentiment, mask in [
            ("positive", mentioned[score_col] >= NEGATIVE_THRESHOLD),
            ("negative", mentioned[score_col] < NEGATIVE_THRESHOLD),
        ]:
            for _, r in mentioned[mask].head(per_side).iterrows():
                picked.append(
                    {
                        "sentiment": sentiment,
                        "text": r[evidence_col],
                        "nationality": str(r["Reviewer_Nationality"]).strip(),
                        "date": r["Review_Date"],
                    }
                )
        result[title(aspect)] = picked
    return result


# --------------------------------------------------------------------------- #
# 6. Competitor gap matrix + vulnerability table
#    — mirrors COMPETITORS/gaps_vs_focus and VULNERABILITIES
# --------------------------------------------------------------------------- #


def competitor_gaps(scores_by_hotel: pd.DataFrame, focus_hotel: str) -> pd.DataFrame:
    """focus_score - competitor_score per aspect, one row per competitor."""
    focus_row = scores_by_hotel[scores_by_hotel["Hotel_Name"] == focus_hotel].iloc[0]
    rows = []
    for _, comp in scores_by_hotel[scores_by_hotel["Hotel_Name"] != focus_hotel].iterrows():
        row = {"competitor": comp["Hotel_Name"]}
        for aspect in WEBSITE_ASPECTS:
            focus_val, comp_val = focus_row[f"{aspect}_score"], comp[f"{aspect}_score"]
            row[title(aspect)] = (
                round(focus_val - comp_val, 2) if pd.notna(focus_val) and pd.notna(comp_val) else None
            )
        rows.append(row)
    return pd.DataFrame(rows)


def find_highlights(evidence_text: str, aspect: str, max_highlights: int = 2) -> list[str]:
    """Which of the aspect's own keywords actually appear in this evidence text.

    Reuses the exact keyword lexicon nlp_pipeline.py already gates aspects on —
    the highlighted phrase is always a literal substring of the real review,
    the same guarantee _extract_evidence relies on. Longer phrases are checked
    first so e.g. "water pressure" wins over a bare "water" if both are present.
    """
    all_keywords = sorted(
        {kw for keywords in ASPECT_LEXICON[aspect].values() for kw in keywords},
        key=len,
        reverse=True,
    )
    lowered = evidence_text.lower()
    found: list[str] = []
    for kw in all_keywords:
        if kw in lowered:
            idx = lowered.find(kw)
            match = evidence_text[idx : idx + len(kw)]
            if match not in found:
                found.append(match)
        if len(found) >= max_highlights:
            break
    return found


def vulnerability_table(df: pd.DataFrame, scores_by_hotel: pd.DataFrame, focus_hotel: str) -> list[dict]:
    """For each competitor, their single weakest aspect + one real negative excerpt."""
    entries = []
    for _, comp in scores_by_hotel[scores_by_hotel["Hotel_Name"] != focus_hotel].iterrows():
        aspect_scores = {a: comp[f"{a}_score"] for a in WEBSITE_ASPECTS if pd.notna(comp[f"{a}_score"])}
        if not aspect_scores:
            continue
        weakest = min(aspect_scores, key=aspect_scores.get)
        comp_df = df[df["Hotel_Name"] == comp["Hotel_Name"]]
        score_col, evidence_col = f"aspect_{weakest}_score", f"aspect_{weakest}_evidence"
        negative = comp_df[(comp_df[score_col] < NEGATIVE_THRESHOLD) & (comp_df[evidence_col] != "")]
        if negative.empty:
            continue
        review_text = negative.iloc[0][evidence_col]
        entries.append(
            {
                "competitor": comp["Hotel_Name"],
                "category": title(weakest),
                "review": review_text,
                "highlights": find_highlights(review_text, weakest),
            }
        )
    return entries


# --------------------------------------------------------------------------- #
# 7. Aspect coverage — how much of the real 8-aspect data the current
#    5-category website is throwing away (see module docstring)
# --------------------------------------------------------------------------- #


def dropped_aspect_coverage(df: pd.DataFrame) -> pd.DataFrame:
    dropped = [a for a in ASPECTS if a not in WEBSITE_ASPECTS]
    rows = []
    for aspect in dropped:
        col = df[f"aspect_{aspect}_score"]
        rows.append({"aspect": title(aspect), "mentions_in_sample": int(col.notna().sum())})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 8. Website-shaped bundle — matches web/src/data/mockData.js's exports
#    exactly, so it can be dropped in with no component code changes
#    (except MONTHLY_* -> QUARTERLY_*, since quarter is the real granularity).
# --------------------------------------------------------------------------- #


def auto_insight(df: pd.DataFrame, hotel_name: str, aspect: str) -> str:
    """One sentence: the single most common complaint sub-tag for this aspect.

    Deterministic — picks from real (sub-tag, count) pairs, never phrased by a
    model — so it can never say something the data doesn't back up.
    """
    hotel_df = df[df["Hotel_Name"] == hotel_name]
    score_col, subtag_col = f"aspect_{aspect}_score", f"aspect_{aspect}_subtags"
    negative = hotel_df[hotel_df[score_col] < NEGATIVE_THRESHOLD]

    counts: Counter[str] = Counter()
    for tags in negative[subtag_col]:
        counts.update(t for t in str(tags).split(";") if t)

    if not counts:
        return f"No major {title(aspect).lower()} complaints in this sample."

    # Prefer a specific sub-tag over the "*_general" catch-all — "check-in/
    # check-out" is an actionable insight, "staff" (from staff_general) just
    # restates the category name.
    specific = {tag: n for tag, n in counts.items() if not tag.endswith("_general")}
    top_subtag, count = Counter(specific or counts).most_common(1)[0]
    display = SUBTAG_DISPLAY.get(top_subtag, top_subtag.replace("_", " "))
    plural = "review" if count == 1 else "reviews"
    return f"Most negative mentions are about {display} ({count} {plural})."


def build_website_data(df: pd.DataFrame, focus_hotel: str) -> dict:
    """Assemble every export mockData.js needs, in its exact shape."""
    scores = category_scores_by_hotel(df)
    board = leaderboard(df)
    trend = quarterly_trend(df, focus_hotel)

    categories = [
        {
            "name": title(a),
            "icon": {"food": "utensils", "comfort": "bed", "cleanliness": "sparkles",
                      "staff": "users", "location": "map-pin"}[a],
            "insight": auto_insight(df, focus_hotel, a),
        }
        for a in WEBSITE_ASPECTS
    ]

    focus_row = scores[scores["Hotel_Name"] == focus_hotel].iloc[0]
    hotel_arena_scores = {title(a): focus_row[f"{a}_score"] for a in WEBSITE_ASPECTS}

    competitors = [
        {
            "id": comp["Hotel_Name"].lower().replace(" ", "_"),
            "name": comp["Hotel_Name"],
            "scores": {title(a): comp[f"{a}_score"] for a in WEBSITE_ASPECTS},
        }
        for _, comp in scores[scores["Hotel_Name"] != focus_hotel].iterrows()
    ]

    focus_quarterly = (
        df[df["Hotel_Name"] == focus_hotel].groupby("quarter")["Reviewer_Score"].mean().sort_index()
    )
    hotel_trend = None
    if len(focus_quarterly) >= 2:
        hotel_trend = "up" if focus_quarterly.iloc[-1] >= focus_quarterly.iloc[0] else "down"

    leaderboard_rows = []
    for _, r in board.iterrows():
        is_focus = r["Hotel_Name"] == focus_hotel
        row = {
            "rank": int(r["rank"]),
            "name": f"{r['Hotel_Name']} (You)" if is_focus else r["Hotel_Name"],
            "score": r["overall_score"],
        }
        if is_focus:
            row["isUser"] = True
            if hotel_trend:
                row["trend"] = hotel_trend
        leaderboard_rows.append(row)

    return {
        "CATEGORIES": categories,
        "HOTEL_ARENA_SCORES": hotel_arena_scores,
        "COMPETITORS": competitors,
        "LEADERBOARD": leaderboard_rows,
        "VULNERABILITIES": vulnerability_table(df, scores, focus_hotel),
        "QUARTERLY_LABELS": trend["quarter"].tolist(),
        "QUARTERLY_OVERALL": trend["overall"].tolist(),
        "QUARTERLY_BY_CATEGORY": {title(a): trend[a].tolist() for a in WEBSITE_ASPECTS},
        "DIMENSION_COMMENTS": dimension_comments(df, focus_hotel).to_dict(orient="records"),
        "CATEGORY_COMMENTS": category_comments(df, focus_hotel),
    }


def write_mockdata_js(website_data: dict, focus_hotel: str, path: Path) -> None:
    """Render web/src/data/mockData.js — same export names as before, real content.

    CATEGORY_COLORS, HOTELS, and QUADRANT_STYLES are NOT regenerated: the
    Quadrant page has no real data source (no price column anywhere in the
    dataset) and stays mocked on purpose — see the header comment below.
    """
    j = lambda obj: json.dumps(obj, indent=2, ensure_ascii=False)  # noqa: E731

    js = f"""\
// Data for the TrueStay dashboard — generated by src/dashboard_data_prep.py
// from real NLP-enriched reviews ({focus_hotel} + competitors), NOT hand-mocked.
// Re-run that script to refresh these numbers from a newer dataset; don't
// hand-edit the generated sections below.
//
// CATEGORY_COLORS, HOTELS, and QUADRANT_STYLES are still mocked on purpose —
// the Quadrant page (price vs. audited quality) has no real data source; this
// dataset has no price/rate column at all.

export const CATEGORIES = {j(website_data["CATEGORIES"])}

export const CATEGORY_COLORS = {{
  Food: "#f97316",
  Comfort: "#ef4444",
  Cleanliness: "#06b6d4",
  Staff: "#8b5cf6",
  Location: "#22c55e",
}}

export const HOTEL_ARENA_SCORES = {j(website_data["HOTEL_ARENA_SCORES"])}

export const COMPETITORS = {j(website_data["COMPETITORS"])}

export const LEADERBOARD = {j(website_data["LEADERBOARD"])}

// Derived once, from LEADERBOARD, so every component that needs "how do we
// compare to the region" (Dashboard insight card, Regional Position card,
// the chat agent) reads the same numbers instead of recomputing them.
const _you = LEADERBOARD.find((h) => h.isUser)
const _total = LEADERBOARD.length
const _average = LEADERBOARD.reduce((sum, h) => sum + h.score, 0) / _total

export const REGIONAL_STANDING = {{
  you: _you,
  total: _total,
  average: _average,
  delta: _you.score - _average,
  percentBetterThan: Math.round(((_total - _you.rank) / _total) * 100),
}}

// Derived once, from HOTEL_ARENA_SCORES, so the weakest/strongest category
// (and its existing `insight` copy) can be reused anywhere without
// re-deriving the min/max each time.
export const WORST_CATEGORY = CATEGORIES.reduce((worst, c) =>
  HOTEL_ARENA_SCORES[c.name] < HOTEL_ARENA_SCORES[worst.name] ? c : worst,
)
export const BEST_CATEGORY = CATEGORIES.reduce((best, c) =>
  HOTEL_ARENA_SCORES[c.name] > HOTEL_ARENA_SCORES[best.name] ? c : best,
)

export const VULNERABILITIES = {j(website_data["VULNERABILITIES"])}

// The real dataset only supports QUARTERLY granularity (matches the hotel x
// quarter panel decided for the project) — these used to be mislabeled
// "MONTHLY_*" back when this was hand-mocked with 12 fake months.
export const QUARTERLY_LABELS = {j(website_data["QUARTERLY_LABELS"])}
export const QUARTERLY_OVERALL = {j(website_data["QUARTERLY_OVERALL"])}
export const QUARTERLY_BY_CATEGORY = {j(website_data["QUARTERLY_BY_CATEGORY"])}

export const DIMENSION_COMMENTS = {j(website_data["DIMENSION_COMMENTS"])}

export const CATEGORY_COMMENTS = {j(website_data["CATEGORY_COMMENTS"])}

// Quadrant page (2x2 price vs. audited-quality scatter) — still 100% mocked,
// see the module header. Also uses a different 0-5 scale and metric set
// (food/service/comfort/cleaner) than the Dashboard's 0-10 scale, inherited
// from the original mockup.
export const HOTELS = [
  {{ id: 1, name: "Grand Azure Palace", quadrant: "premium", x: 82, y: 18, price: 620, food: 4.7, service: 4.9, comfort: 4.8, cleaner: 4.9 }},
  {{ id: 2, name: "Hotel Meridian Bay", quadrant: "premium", x: 74, y: 24, price: 540, food: 4.5, service: 4.6, comfort: 4.7, cleaner: 4.8 }},
  {{ id: 3, name: "The Ivory Court", quadrant: "value", x: 78, y: 74, price: 210, food: 4.4, service: 4.6, comfort: 4.3, cleaner: 4.7 }},
  {{ id: 4, name: "Cedar & Stone Inn", quadrant: "value", x: 70, y: 68, price: 180, food: 4.2, service: 4.5, comfort: 4.2, cleaner: 4.4 }},
  {{ id: 5, name: "Downtown Basic Suites", quadrant: "basic", x: 28, y: 78, price: 95, food: 3.1, service: 3.2, comfort: 3.0, cleaner: 3.4 }},
  {{ id: 6, name: "Traveler's Lodge", quadrant: "basic", x: 22, y: 84, price: 80, food: 2.9, service: 3.0, comfort: 3.1, cleaner: 3.2 }},
  {{ id: 7, name: "Regal Overlook Hotel", quadrant: "overpriced", x: 26, y: 20, price: 480, food: 2.8, service: 3.0, comfort: 3.2, cleaner: 2.9 }},
  {{ id: 8, name: "Marbella Grand", quadrant: "overpriced", x: 34, y: 28, price: 410, food: 3.1, service: 2.9, comfort: 3.0, cleaner: 3.1 }},
]

export const QUADRANT_STYLES = {{
  premium: {{ label: "Premium / Luxury", badge: "bg-emerald-50 text-emerald-700 border border-emerald-200", dot: "bg-emerald-500" }},
  value: {{ label: "Value for Money", badge: "bg-sky-50 text-sky-700 border border-sky-200", dot: "bg-sky-500" }},
  basic: {{ label: "Basic Economy", badge: "bg-slate-50 text-slate-600 border border-slate-200", dot: "bg-slate-400" }},
  overpriced: {{ label: "Overpriced", badge: "bg-amber-50 text-amber-700 border border-amber-200", dot: "bg-amber-500" }},
}}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(js, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def sanitize_evidence_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip a stray backslash the Colab notebook used to insert before
    repaired contractions ("didn\\'t" instead of "didn't") — a bug in its
    CONTRACTION_FIXES dict, now fixed at the source. Datasets generated before
    that fix still carry the corrupted text, so clean it here rather than
    requiring a full Colab re-run. Harmless no-op on already-clean data.
    """
    for aspect in ASPECTS:
        col = f"aspect_{aspect}_evidence"
        if col in df.columns:
            df[col] = df[col].str.replace("\\'", "'", regex=False)
    return df


def main() -> None:
    print(f"Loading {INPUT_PATH} ...")
    df = pd.read_parquet(INPUT_PATH)
    df = sanitize_evidence_columns(df)
    print(f"{len(df)} reviews, {df['Hotel_Name'].nunique()} hotels: "
          f"{df['Hotel_Name'].value_counts().to_dict()}")

    focus_hotel = df["Hotel_Name"].value_counts().idxmax()
    print(f"\nUsing '{focus_hotel}' as the focus hotel (most reviews in this sample).\n")

    scores = category_scores_by_hotel(df)
    print("=== 1. Category scores by hotel ===")
    print(scores.to_string(index=False))

    board = leaderboard(df)
    print("\n=== 2. Leaderboard ===")
    print(board.to_string(index=False))

    trend = quarterly_trend(df, focus_hotel)
    print(f"\n=== 3. Quarterly trend — {focus_hotel} ===")
    print(trend.to_string(index=False))

    dim_comments = dimension_comments(df, focus_hotel)
    print(f"\n=== 4. Dimension comments — {focus_hotel} ===")
    print(dim_comments.to_string(index=False))

    comments = category_comments(df, focus_hotel)
    print(f"\n=== 5. Category comment samples — {focus_hotel} ===")
    for aspect_name, items in comments.items():
        print(f"  {aspect_name}: {len(items)} example(s)")

    gaps = competitor_gaps(scores, focus_hotel)
    print(f"\n=== 6a. Competitor gap matrix (vs {focus_hotel}) ===")
    print(gaps.to_string(index=False) if not gaps.empty else "  (no other hotels in this sample)")

    vulns = vulnerability_table(df, scores, focus_hotel)
    print(f"\n=== 6b. Vulnerability table ===")
    for v in vulns:
        print(f"  {v['competitor']} — weakest: {v['category']} — \"{v['review'][:80]}...\"")

    coverage = dropped_aspect_coverage(df)
    print("\n=== 7. Aspects the website currently drops (Value, Noise, Facilities) ===")
    print(coverage.to_string(index=False))

    dashboard_data = {
        "focus_hotel": focus_hotel,
        "category_scores_by_hotel": scores.to_dict(orient="records"),
        "leaderboard": board.to_dict(orient="records"),
        "quarterly_trend": trend.to_dict(orient="records"),
        "dimension_comments": dim_comments.to_dict(orient="records"),
        "category_comments": comments,
        "competitor_gaps": gaps.to_dict(orient="records"),
        "vulnerabilities": vulns,
        "dropped_aspect_coverage": coverage.to_dict(orient="records"),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(dashboard_data, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved combined result -> {OUTPUT_PATH}")

    print("\n=== 8. Website data bundle ===")
    website_data = build_website_data(df, focus_hotel)
    for aspect, cat in zip(WEBSITE_ASPECTS, website_data["CATEGORIES"]):
        print(f"  {cat['name']}: {cat['insight']}")
    write_mockdata_js(website_data, focus_hotel, MOCKDATA_JS_PATH)
    print(f"\nWrote real data -> {MOCKDATA_JS_PATH}")


if __name__ == "__main__":
    main()
