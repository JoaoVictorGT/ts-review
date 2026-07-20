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

import psycopg2
from dotenv import load_dotenv
from slugify import slugify

from dashboard_data_prep import (
    INPUT_PATH,
    category_scores_by_hotel,
    build_website_data,
    compute_derived,
    json_safe,
    leaderboard,
    load_reviews,
    sanitize_evidence_columns,
)


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

    for i, hotel_name in enumerate(hotel_names, start=1):
        website_data = build_website_data(df, hotel_name, scores=scores, board=board)
        payload = json_safe({**website_data, **compute_derived(website_data, board, hotel_name)})
        slug = unique_slug_for(hotel_name, used_slugs)

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
    print(f"\nDone. Pushed {total} hotels in {time.time() - start:.0f}s.")


if __name__ == "__main__":
    main()
