"""One-time (re-runnable) batch job: compute and push real dashboard data for
EVERY hotel in the full dataset, not just the one focus hotel dashboard_data_prep.py
handles. Needed so the registration flow's hotel search/autocomplete
(GET /hotels/search) can find real hotels, and so anyone who registers
against one immediately sees real historical data instead of an empty
placeholder.

Reuses category_scores_by_hotel/leaderboard/select_competitors/
build_website_data/compute_derived from dashboard_data_prep.py, computing
the expensive population-wide aggregates (scores, board) ONCE and passing
them into build_website_data() for every hotel instead of recomputing per
call.

Run with:
    python src/backfill_all_hotels.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from slugify import slugify

from dashboard_data_prep import (
    INPUT_PATH,
    PROJECT_ROOT,
    category_scores_by_hotel,
    build_website_data,
    compute_derived,
    json_safe,
    leaderboard,
    load_hotel_report,
    load_reviews,
    sanitize_evidence_columns,
)

REPORT_KEYS = ("SCORE_GOALS", "ACTION_PLAN", "ASPECT_DETAILS")


def unique_slug_for(hotel_name: str, used_slugs: set[str]) -> str:
    """slugify(name, separator='_') matches the existing convention
    (hotel_slug='hotel_arena', 'hilton_london_wembley') — python-slugify's
    default separator is '-', which would mix conventions across old/new
    rows. Collisions (two different names slugifying the same way) resolved
    in-memory since we process the whole unique hotel list in one pass.
    """
    base = slugify(hotel_name, separator="_") or "hotel"
    slug, suffix = base, 2
    while slug in used_slugs:
        slug = f"{base}_{suffix}"
        suffix += 1
    used_slugs.add(slug)
    return slug


def main() -> None:
    load_dotenv()
    database_url = os.environ["DATABASE_URL"]

    print(f"Loading {INPUT_PATH} ...")
    df = load_reviews(INPUT_PATH)
    df = sanitize_evidence_columns(df)
    print(f"{len(df)} reviews, {df['Hotel_Name'].nunique()} hotels")

    scores = category_scores_by_hotel(df)
    board = leaderboard(df)
    hotel_names = board["Hotel_Name"].tolist()
    total = len(hotel_names)

    used_slugs: set[str] = set()
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    start = time.time()

    # This script overwrites `data` wholesale (ON CONFLICT DO UPDATE), so any
    # hotel that already has the teammate's score-improvement report merged in
    # (see dashboard_data_prep.py's load_hotel_report()/main()) would silently
    # lose SCORE_GOALS/ACTION_PLAN/ASPECT_DETAILS otherwise. Load the report
    # once and re-merge it here too, so every hotel it covers gets it on every
    # backfill run, not just whichever ones happened to have it before.
    report_path = Path(os.environ.get("HOTEL_REPORT_PATH", PROJECT_ROOT / "data" / "website_hotel_report.json"))
    report_by_slug = load_hotel_report(report_path) if report_path.exists() else {}
    if report_by_slug:
        print(f"Loaded score-improvement report: {len(report_by_slug)} hotels covered.")
    else:
        print(f"No score-improvement report found at {report_path} — SCORE_GOALS/etc. won't be touched this run.")

    # Safety net for any hotel that already has report keys in Neon but isn't
    # in report_by_slug for some reason (e.g. a differently-sourced report) —
    # don't silently wipe those either.
    cur.execute("SELECT hotel_slug, data FROM hotel_dashboard_data WHERE data ?| %s", (list(REPORT_KEYS),))
    preserved_report_data = {
        row_slug: {k: row_data[k] for k in REPORT_KEYS if k in row_data} for row_slug, row_data in cur.fetchall()
    }

    merged_count = 0
    for i, hotel_name in enumerate(hotel_names, start=1):
        website_data = build_website_data(df, hotel_name, scores=scores, board=board)
        payload = json_safe({**website_data, **compute_derived(website_data, board, hotel_name)})
        slug = unique_slug_for(hotel_name, used_slugs)
        report = report_by_slug.get(slug)
        if report:
            payload["SCORE_GOALS"] = report["score_goals"]
            payload["ACTION_PLAN"] = report["action_plan"]
            payload["ASPECT_DETAILS"] = report["aspect_details"]
            merged_count += 1
        elif slug in preserved_report_data:
            payload.update(preserved_report_data[slug])

        cur.execute(
            """
            INSERT INTO hotel_dashboard_data (hotel_slug, focus_hotel_name, data, generated_at)
            VALUES (%s, %s, %s, now())
            ON CONFLICT (hotel_slug) DO UPDATE
              SET focus_hotel_name = EXCLUDED.focus_hotel_name,
                  data = EXCLUDED.data,
                  generated_at = EXCLUDED.generated_at
            """,
            (slug, hotel_name, json.dumps(payload, default=str)),
        )

        if i % 50 == 0 or i == total:
            conn.commit()
            elapsed = time.time() - start
            rate = i / elapsed
            eta = (total - i) / rate if rate > 0 else 0
            print(f"{i}/{total} ({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining) -> {slug}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone. Pushed {total} hotels in {time.time() - start:.0f}s. "
          f"{merged_count} had score-improvement report data merged in.")


if __name__ == "__main__":
    main()
