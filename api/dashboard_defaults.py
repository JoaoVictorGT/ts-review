"""Placeholder /dashboard payload for a brand-new, self-registered hotel with
no real review data yet ("não encontrei minha acomodação" during signup).

Matches every key/type of the real payload (src/dashboard_data_prep.py's
build_website_data + compute_derived) with zeros/empty collections instead of
None/null anywhere the frontend's existing rendering code assumes a number
(e.g. .toFixed() calls with no null-guard) — so a brand-new account's first
dashboard visit doesn't crash before the frontend's own "no data yet" guard
even runs.
"""

# name/icon pairs must match CategoryHealthCards.jsx's ICONS map exactly.
CATEGORY_META = [
    ("Food", "utensils"),
    ("Comfort", "bed"),
    ("Cleanliness", "sparkles"),
    ("Staff", "users"),
    ("Location", "map-pin"),
]


def empty_dashboard_data(hotel_name: str) -> dict:
    categories = [
        {"name": name, "icon": icon, "insight": "No guest feedback yet — check back once reviews come in."}
        for name, icon in CATEGORY_META
    ]
    names = [c["name"] for c in categories]
    you = {"rank": 1, "name": f"{hotel_name} (You)", "score": 0, "isUser": True}

    return {
        "CATEGORIES": categories,
        "HOTEL_ARENA_SCORES": {name: 0 for name in names},
        "COMPETITORS": [],
        "LEADERBOARD": [you],
        "VULNERABILITIES": [],
        "QUARTERLY_LABELS": [],
        "QUARTERLY_OVERALL": [],
        "QUARTERLY_BY_CATEGORY": {name: [] for name in names},
        "DIMENSION_COMMENTS": [{"name": name, "total": 0, "negative": 0} for name in names],
        "CATEGORY_COMMENTS": {name: [] for name in names},
        "REGIONAL_STANDING": {"you": you, "total": 1, "average": 0, "delta": 0, "percentBetterThan": 0},
        "WORST_CATEGORY": categories[0],
        "BEST_CATEGORY": categories[0],
    }
