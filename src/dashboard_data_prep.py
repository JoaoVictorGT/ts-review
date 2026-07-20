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
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "outputs" / "reviews_enriched_sample.parquet"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "dashboard_data_sample.json"

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
        entries.append(
            {
                "competitor": comp["Hotel_Name"],
                "category": title(weakest),
                "review": negative.iloc[0][evidence_col],
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
# Orchestration
# --------------------------------------------------------------------------- #


def main() -> None:
    print(f"Loading {INPUT_PATH} ...")
    df = pd.read_parquet(INPUT_PATH)
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


if __name__ == "__main__":
    main()
