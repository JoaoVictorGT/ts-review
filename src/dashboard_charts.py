"""Charts for the dashboard_data_prep.py output — reads
outputs/dashboard_data_sample.json (or the full-dataset version once ready)
and renders the same figures the website's Dashboard page shows, using
matplotlib (works natively in Colab, no extra install needed).

Run with:
    python src/dashboard_charts.py
or paste the body into a new Colab cell right after the dashboard_data_prep
cell (it only depends on matplotlib + json, no repo imports required there).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless — we only save figures, never show() them

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "outputs" / "dashboard_data_sample.json"
FIGURES_DIR = PROJECT_ROOT / "figures"

CATEGORY_COLORS = {
    "Food": "#f97316",
    "Comfort": "#ef4444",
    "Cleanliness": "#06b6d4",
    "Staff": "#8b5cf6",
    "Location": "#22c55e",
}
WEBSITE_ASPECTS = ["Food", "Comfort", "Cleanliness", "Staff", "Location"]


def chart_category_scores(data: dict) -> Path:
    """Bar chart: focus hotel's 0-10 score per category (mirrors the Category Health cards)."""
    focus = data["focus_hotel"]
    row = next(r for r in data["category_scores_by_hotel"] if r["Hotel_Name"] == focus)
    scores = [row[f"{a.lower() if a != 'Value for Money' else 'value'}_score"] for a in WEBSITE_ASPECTS]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(WEBSITE_ASPECTS, scores, color=[CATEGORY_COLORS[a] for a in WEBSITE_ASPECTS])
    ax.axhline(7.0, color="#94a3b8", linestyle="--", linewidth=1, label="Stable threshold (7.0)")
    ax.set_ylim(0, 10)
    ax.set_ylabel("Score (0-10)")
    ax.set_title(f"Category scores — {focus}")
    ax.legend()
    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, score + 0.15, f"{score:.1f}", ha="center", fontsize=10)

    path = FIGURES_DIR / "dashboard_category_scores.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def chart_quarterly_trend(data: dict) -> Path:
    """Line chart: overall + per-category score across quarters (mirrors Monthly Score Trend)."""
    focus = data["focus_hotel"]
    trend = data["quarterly_trend"]
    quarters = [row["quarter"] for row in trend]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(quarters, [row["overall"] for row in trend], color="#2563eb", linewidth=2.5,
             marker="o", label="Overall")
    for aspect in WEBSITE_ASPECTS:
        key = "value" if aspect == "Value for Money" else aspect.lower()
        if all(key in row for row in trend):
            ax.plot(quarters, [row.get(key) for row in trend], color=CATEGORY_COLORS[aspect],
                     linewidth=1.3, alpha=0.7, label=aspect)

    ax.set_ylim(0, 10)
    ax.set_ylabel("Score (0-10)")
    ax.set_title(f"Quarterly score trend — {focus}\n(the website mocks this as monthly; real data is quarterly)")
    ax.legend(loc="lower left", fontsize=8, ncol=3)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    path = FIGURES_DIR / "dashboard_quarterly_trend.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def chart_leaderboard(data: dict) -> Path:
    """Horizontal bar chart: hotels ranked by overall score (mirrors Regional Leaderboard)."""
    board = sorted(data["leaderboard"], key=lambda r: r["rank"], reverse=True)
    names = [f"#{r['rank']} {r['Hotel_Name']}" for r in board]
    scores = [r["overall_score"] for r in board]
    colors = ["#2563eb" if r["Hotel_Name"] == data["focus_hotel"] else "#cbd5e1" for r in board]

    fig, ax = plt.subplots(figsize=(7, 0.6 * len(board) + 1))
    ax.barh(names, scores, color=colors)
    ax.set_xlim(0, 10)
    ax.set_xlabel("Overall score (mean Reviewer_Score)")
    ax.set_title("Leaderboard")
    for i, score in enumerate(scores):
        ax.text(score + 0.1, i, f"{score:.2f}", va="center", fontsize=9)

    path = FIGURES_DIR / "dashboard_leaderboard.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def chart_competitor_gaps(data: dict) -> Path | None:
    """Diverging bar chart: focus hotel's gap vs. each competitor, per category."""
    gaps = data["competitor_gaps"]
    if not gaps:
        return None

    fig, axes = plt.subplots(len(gaps), 1, figsize=(8, 3 * len(gaps)), squeeze=False)
    for ax, comp in zip(axes[:, 0], gaps):
        categories = [c for c in WEBSITE_ASPECTS if comp.get(c) is not None]
        values = [comp[c] for c in categories]
        colors = ["#2563eb" if v >= 0 else "#ef4444" for v in values]
        ax.barh(categories, values, color=colors)
        ax.axvline(0, color="#94a3b8", linewidth=1)
        ax.set_title(f"Gap vs. {comp['competitor']} (positive = focus hotel ahead)")

    path = FIGURES_DIR / "dashboard_competitor_gaps.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    paths = [
        chart_category_scores(data),
        chart_quarterly_trend(data),
        chart_leaderboard(data),
        chart_competitor_gaps(data),
    ]
    for p in paths:
        if p:
            print(f"Saved {p}")


if __name__ == "__main__":
    main()
