"""Statistical feasibility of the hotel x quarter panel.

The core question is not "how many rows" but "how reliable is each quarterly
mean". A quarterly satisfaction score computed from few reviews is dominated by
sampling noise and would make the panel model chase randomness.

We answer it with a variance decomposition:

* ``sigma_within``    -> review-level noise inside a single hotel-quarter cell
                         (pooled within-cell standard deviation of Reviewer_Score).
* ``signal_var``      -> the *real* quarter-to-quarter variance of a hotel's
                         satisfaction, after removing sampling noise.
* ``reliability(n)``  -> signal_var / (signal_var + sigma_within**2 / n), i.e. the
                         fraction of a quarterly mean (built from n reviews) that
                         reflects real movement rather than noise. This is a
                         classic reliability / signal-to-noise ratio in [0, 1].

A threshold ``n`` is "sufficient" when reliability is comfortably high (>= 0.70)
while still retaining enough cells and hotels to model trajectories.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "Hotel_Reviews.csv"
FIGURES_DIR = PROJECT_ROOT / "figures"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("panel_feasibility")

# Candidate minimum-reviews-per-cell thresholds to evaluate.
THRESHOLDS = [5, 10, 15, 20, 30, 50]
# Minimum number of dense quarters a hotel needs to have a "trajectory".
MIN_DENSE_QUARTERS = 3


def build_cells(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate reviews into hotel x quarter cells with n / mean / var."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["Review_Date"], format="%m/%d/%Y", errors="coerce")
    df["quarter"] = df["date"].dt.to_period("Q")
    cells = df.groupby(["Hotel_Name", "quarter"]).agg(
        n=("Reviewer_Score", "size"),
        mean=("Reviewer_Score", "mean"),
        var=("Reviewer_Score", "var"),  # sample variance, NaN when n == 1
    )
    return cells.reset_index()


def estimate_variance_components(cells: pd.DataFrame) -> dict[str, float]:
    """Decompose observed quarterly variation into signal vs sampling noise."""
    # Review-level noise inside a cell: pooled within-cell variance, weighted by
    # (n - 1) degrees of freedom. Cells with n == 1 contribute no variance info.
    usable = cells.dropna(subset=["var"])
    weights = usable["n"] - 1
    sigma_within_sq = float(np.average(usable["var"], weights=weights))

    # Observed variance of quarterly means within a hotel (only hotels that have
    # several dense quarters, so the variance is meaningfully estimated).
    dense = cells[cells["n"] >= 10]
    per_hotel = dense.groupby("Hotel_Name")["mean"].agg(["var", "count", "mean"])
    per_hotel = per_hotel[per_hotel["count"] >= MIN_DENSE_QUARTERS].dropna()
    observed_var = float(per_hotel["var"].mean())

    # Mean sampling variance carried by those quarterly means.
    mean_inv_n = float((1.0 / dense["n"]).mean())
    sampling_var = sigma_within_sq * mean_inv_n

    # Signal = observed variation minus the sampling noise it contains.
    signal_var = max(observed_var - sampling_var, 0.0)

    return {
        "sigma_within": float(np.sqrt(sigma_within_sq)),
        "sigma_within_sq": sigma_within_sq,
        "observed_quarterly_var": observed_var,
        "sampling_var_at_10plus": sampling_var,
        "signal_var": signal_var,
        "signal_std": float(np.sqrt(signal_var)),
        "n_hotels_with_trajectory": int(len(per_hotel)),
    }


def reliability(n: int, signal_var: float, sigma_within_sq: float) -> float:
    """Fraction of a quarterly mean (from n reviews) that is real signal."""
    se_sq = sigma_within_sq / n
    return signal_var / (signal_var + se_sq) if (signal_var + se_sq) > 0 else 0.0


def threshold_table(cells: pd.DataFrame, comp: dict[str, float]) -> pd.DataFrame:
    """For each candidate threshold: surviving cells/hotels, SE and reliability."""
    rows = []
    total_cells = len(cells)
    for k in THRESHOLDS:
        kept = cells[cells["n"] >= k]
        hotels_traj = (
            kept.groupby("Hotel_Name").size().pipe(lambda s: (s >= MIN_DENSE_QUARTERS).sum())
        )
        se = np.sqrt(comp["sigma_within_sq"] / k)
        rel = reliability(k, comp["signal_var"], comp["sigma_within_sq"])
        rows.append(
            {
                "min_reviews_per_cell": k,
                "cells_kept": int(len(kept)),
                "cells_kept_pct": round(100 * len(kept) / total_cells, 1),
                "hotels_with_>=3_dense_quarters": int(hotels_traj),
                "SE_of_quarterly_mean": round(float(se), 3),
                "reliability": round(float(rel), 3),
            }
        )
    return pd.DataFrame(rows)


def plot_feasibility(cells: pd.DataFrame, table: pd.DataFrame) -> Path:
    """Two-panel figure: cell-size distribution and reliability/coverage trade-off."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    axes[0].hist(cells["n"], bins=range(0, 200, 5), color="#4C72B0", edgecolor="white")
    axes[0].axvline(10, color="#C44E52", linestyle="--", label="threshold = 10")
    axes[0].axvline(20, color="#DD8452", linestyle="--", label="threshold = 20")
    axes[0].set_title("Reviews per hotel-quarter cell")
    axes[0].set_xlabel("reviews in the cell")
    axes[0].set_ylabel("number of cells")
    axes[0].legend()

    ax2 = axes[1]
    ax2.plot(table["min_reviews_per_cell"], table["reliability"], "o-",
             color="#55A868", label="reliability (signal share)")
    ax2.axhline(0.70, color="grey", linestyle=":", label="reliability = 0.70")
    ax2.set_xlabel("minimum reviews per cell (threshold)")
    ax2.set_ylabel("reliability", color="#55A868")
    ax2.set_ylim(0, 1)

    ax3 = ax2.twinx()
    ax3.plot(table["min_reviews_per_cell"], table["cells_kept_pct"], "s--",
             color="#8172B3", label="% cells kept")
    ax3.set_ylabel("% of cells retained", color="#8172B3")
    ax3.set_ylim(0, 100)
    ax2.set_title("Reliability vs coverage trade-off")

    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="center right")

    fig.suptitle("Panel feasibility: is each quarterly score reliable enough?", fontsize=14)
    fig.tight_layout()
    path = FIGURES_DIR / "02_panel_feasibility.png"
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return path


def run() -> None:
    """Compute and report the panel feasibility analysis."""
    logger.info("Loading columns for feasibility analysis")
    df = pd.read_csv(
        DATASET_PATH,
        usecols=["Hotel_Name", "Review_Date", "Reviewer_Score"],
        low_memory=False,
    )
    cells = build_cells(df)
    comp = estimate_variance_components(cells)
    table = threshold_table(cells, comp)
    fig_path = plot_feasibility(cells, table)

    logger.info("Variance components: %s", comp)
    print("\n=== Reviews per hotel-quarter cell ===")
    print(cells["n"].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(1).to_string())
    print("\n=== Signal vs noise ===")
    print(f"  review-level noise (sigma_within):        {comp['sigma_within']:.3f}")
    print(f"  real quarterly signal std (signal_std):   {comp['signal_std']:.3f}")
    print("\n=== Threshold trade-off ===")
    print(table.to_string(index=False))
    print(f"\nFigure saved: figures/{fig_path.name}")


if __name__ == "__main__":
    run()
