"""Turn NLP-enriched review data into the aggregated views the TrueStay
dashboard needs (HOTEL_ARENA_SCORES, LEADERBOARD, DIMENSION_COMMENTS,
CATEGORY_COMMENTS, COMPETITORS, VULNERABILITIES), and push the result to
Neon Postgres, where the FastAPI backend (see ``api/``) serves it to the
website at runtime.

Defaults to the full NLP-enriched dataset (``data/mockdata/reviews_enriched.csv``,
1492 hotels). Override ``INPUT_PATH``/``FOCUS_HOTEL`` via environment
variables to run against a different file/hotel (e.g. the smaller 500-row
Colab smoke-test sample, ``outputs/reviews_enriched_sample.parquet``, with
focus hotel "Hotel Arena").

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
import math
import os
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
INPUT_PATH = Path(os.environ.get("INPUT_PATH", PROJECT_ROOT / "data" / "mockdata" / "reviews_enriched.csv"))
FOCUS_HOTEL = os.environ.get("FOCUS_HOTEL", "Hilton London Wembley")
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "dashboard_data_sample.json"

# Size of the "competitive set" shown on the dashboard (gap matrix, leaderboard,
# vulnerability table) — capped since the full dataset can have 1000+ hotels.
COMPETITOR_CAP = 5

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


def select_competitors(board: pd.DataFrame, focus_hotel: str, n: int = COMPETITOR_CAP) -> pd.DataFrame:
    """The n hotels whose overall_score is closest to focus_hotel's, excluding itself.

    "Closest score" rather than "all other hotels" — the latter only works
    when the dataset has a handful of hotels (fine for the old 2-hotel
    sample, breaks completely at 1000+ hotels). Ties broken by Hotel_Name
    for a deterministic, reproducible selection.
    """
    focus_score = board.loc[board["Hotel_Name"] == focus_hotel, "overall_score"].iloc[0]
    others = board[board["Hotel_Name"] != focus_hotel].copy()
    others["distance"] = (others["overall_score"] - focus_score).abs()
    return others.sort_values(["distance", "Hotel_Name"]).head(n).drop(columns="distance")


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


def competitor_gaps(scores_by_hotel: pd.DataFrame, focus_hotel: str, competitor_names) -> pd.DataFrame:
    """focus_score - competitor_score per aspect, one row per competitor."""
    focus_row = scores_by_hotel[scores_by_hotel["Hotel_Name"] == focus_hotel].iloc[0]
    rows = []
    for _, comp in scores_by_hotel[scores_by_hotel["Hotel_Name"].isin(competitor_names)].iterrows():
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


def vulnerability_table(
    df: pd.DataFrame, scores_by_hotel: pd.DataFrame, focus_hotel: str, competitor_names
) -> list[dict]:
    """For each competitor, their single weakest aspect + one real negative excerpt."""
    entries = []
    for _, comp in scores_by_hotel[scores_by_hotel["Hotel_Name"].isin(competitor_names)].iterrows():
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


def build_website_data(
    df: pd.DataFrame,
    focus_hotel: str,
    scores: pd.DataFrame | None = None,
    board: pd.DataFrame | None = None,
) -> dict:
    """Assemble every export mockData.js needs, in its exact shape.

    `scores`/`board` can be precomputed once and passed in when calling this
    per-hotel in a loop (e.g. src/backfill_all_hotels.py) — both are cheap to
    compute for one hotel but wasteful to redo unchanged 1492 times.
    """
    if scores is None:
        scores = category_scores_by_hotel(df)
    if board is None:
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

    competitor_names = select_competitors(board, focus_hotel)["Hotel_Name"]

    competitors = [
        {
            "id": comp["Hotel_Name"].lower().replace(" ", "_"),
            "name": comp["Hotel_Name"],
            "scores": {title(a): comp[f"{a}_score"] for a in WEBSITE_ASPECTS},
        }
        for _, comp in scores[scores["Hotel_Name"].isin(competitor_names)].iterrows()
    ]

    focus_quarterly = (
        df[df["Hotel_Name"] == focus_hotel].groupby("quarter")["Reviewer_Score"].mean().sort_index()
    )
    hotel_trend = None
    if len(focus_quarterly) >= 2:
        hotel_trend = "up" if focus_quarterly.iloc[-1] >= focus_quarterly.iloc[0] else "down"

    # Display list: focus hotel + its capped competitor set, NOT the entire
    # board (could be 1000+ rows). Ranks keep their TRUE value from the full
    # `board` (gaps between shown ranks are expected and more honest than
    # renumbering 1..N).
    display_hotels = pd.concat(
        [
            board[board["Hotel_Name"] == focus_hotel],
            board[board["Hotel_Name"].isin(competitor_names)],
        ]
    ).sort_values("rank")

    leaderboard_rows = []
    for _, r in display_hotels.iterrows():
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
        "VULNERABILITIES": vulnerability_table(df, scores, focus_hotel, competitor_names),
        "QUARTERLY_LABELS": trend["quarter"].tolist(),
        "QUARTERLY_OVERALL": trend["overall"].tolist(),
        "QUARTERLY_BY_CATEGORY": {title(a): trend[a].tolist() for a in WEBSITE_ASPECTS},
        "DIMENSION_COMMENTS": dimension_comments(df, focus_hotel).to_dict(orient="records"),
        "CATEGORY_COMMENTS": category_comments(df, focus_hotel),
    }


def compute_derived(website_data: dict, board: pd.DataFrame, focus_hotel: str) -> dict:
    """REGIONAL_STANDING / WORST_CATEGORY / BEST_CATEGORY.

    These used to be derived in JS at module-load time (only possible because
    mockData.js was a synchronous static import). Now that the frontend
    fetches this data at runtime, computing it once here — and shipping it
    pre-derived as part of the stored payload — avoids re-implementing the
    same derivation in every React component that needs it.

    REGIONAL_STANDING's total/average/rank are computed from the FULL `board`
    (every hotel in the dataset), not from website_data["LEADERBOARD"] — that
    list is capped to the focus hotel + its competitor set for display, so
    deriving "total"/"average" from it would silently understate the true
    population (e.g. 6 instead of 1492).
    """
    categories = website_data["CATEGORIES"]
    scores = website_data["HOTEL_ARENA_SCORES"]

    you = next(h for h in website_data["LEADERBOARD"] if h.get("isUser"))
    focus_row = board.loc[board["Hotel_Name"] == focus_hotel].iloc[0]
    total = len(board)
    average = board["overall_score"].mean()
    true_rank = int(focus_row["rank"])

    # Hotels with sparse reviews can have NO mentions of a given aspect —
    # category_scores_by_hotel() marks that None, which pandas silently
    # upcasts to NaN once it's in a DataFrame column. NaN comparisons never
    # raise (they're just always False), so a naive min/max would still
    # "work" but could inconsistently treat a no-data category as the
    # worst/best one. Only consider categories with a real score; fall back
    # to categories[0] in the pathological case where every aspect is
    # unscored (would require a hotel with essentially zero reviews).
    scored_categories = [c for c in categories if pd.notna(scores.get(c["name"]))]
    worst = min(scored_categories, key=lambda c: scores[c["name"]]) if scored_categories else categories[0]
    best = max(scored_categories, key=lambda c: scores[c["name"]]) if scored_categories else categories[0]

    return {
        "REGIONAL_STANDING": {
            "you": you,
            "total": total,
            "average": round(average, 2),
            "delta": round(you["score"] - average, 2),
            "percentBetterThan": round(((total - true_rank) / total) * 100),
        },
        "WORST_CATEGORY": worst,
        "BEST_CATEGORY": best,
    }


def json_safe(obj):
    """Recursively replace float NaN with None.

    pandas .mean() on an all-NaN group (e.g. a quarter where a hotel got zero
    reviews mentioning some aspect) returns NaN, not None — and Python's
    json.dumps emits that as a bare `NaN` token by default, which is not
    valid JSON and Postgres's jsonb column correctly rejects. None/null is
    the correct value here (same "silence isn't a neutral score" convention
    used elsewhere in this file), so convert before serializing.
    """
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    return obj


def push_to_neon(website_data: dict, board: pd.DataFrame, focus_hotel: str, hotel_slug: str) -> None:
    """Upsert the full dashboard payload (website_data + derived values) into
    Neon Postgres. Requires DATABASE_URL in the environment (see api/.env.example
    for the expected format) — load it from a local .env with python-dotenv
    when running this manually.
    """
    import psycopg2
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.environ["DATABASE_URL"]

    payload = json_safe({**website_data, **compute_derived(website_data, board, focus_hotel)})

    with psycopg2.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO hotel_dashboard_data (hotel_slug, focus_hotel_name, data, generated_at)
            VALUES (%s, %s, %s, now())
            ON CONFLICT (hotel_slug) DO UPDATE
              SET focus_hotel_name = EXCLUDED.focus_hotel_name,
                  data = EXCLUDED.data,
                  generated_at = EXCLUDED.generated_at
            """,
            (hotel_slug, focus_hotel, json.dumps(payload, default=str)),
        )
    print(f"Pushed dashboard data for '{focus_hotel}' -> Neon (slug={hotel_slug})")


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


def load_reviews(path: Path) -> pd.DataFrame:
    if path.suffix == ".csv":
        return pd.read_csv(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported input format: {path.suffix} ({path})")


def main() -> None:
    print(f"Loading {INPUT_PATH} ...")
    df = load_reviews(INPUT_PATH)
    df = sanitize_evidence_columns(df)
    print(f"{len(df)} reviews, {df['Hotel_Name'].nunique()} hotels")

    focus_hotel = FOCUS_HOTEL
    assert focus_hotel in df["Hotel_Name"].values, f"{focus_hotel!r} not found in {INPUT_PATH}"
    print(f"\nUsing '{focus_hotel}' as the focus hotel.\n")

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

    competitor_names = select_competitors(board, focus_hotel)["Hotel_Name"]

    gaps = competitor_gaps(scores, focus_hotel, competitor_names)
    print(f"\n=== 6a. Competitor gap matrix (vs {focus_hotel}) ===")
    print(gaps.to_string(index=False) if not gaps.empty else "  (no other hotels in this sample)")

    vulns = vulnerability_table(df, scores, focus_hotel, competitor_names)
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

    hotel_slug = focus_hotel.lower().replace(" ", "_")
    push_to_neon(website_data, board, focus_hotel, hotel_slug)


if __name__ == "__main__":
    main()
