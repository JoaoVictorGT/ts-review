"""Data quality audit for the European hotel reviews dataset.

This module performs an exhaustive, production-grade audit of the raw
``Hotel_Reviews.csv`` dataset *before* any cleaning or modeling. It answers
structural, health, distribution, frequency, completeness and integrity
questions and persists a Markdown report plus diagnostic figures.

Design notes
------------
* Comments and documentation are in English (project convention).
* The module is import-safe: every step is a small, typed, documented
  function. ``run_audit`` orchestrates them and returns a results dict so the
  audit can be reused from notebooks or tests.
* Nothing is mutated on the source dataframe; the audit is read-only.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # headless backend: we only save figures, never show them

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = PROJECT_ROOT / "figures"
REPORTS_DIR = PROJECT_ROOT / "reports"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

DATASET_PATH = DATA_DIR / "Hotel_Reviews.csv"

# Placeholder tokens used by Booking.com when a reviewer left a side blank.
NEGATIVE_PLACEHOLDER = "No Negative"
POSITIVE_PLACEHOLDER = "No Positive"

# The six European cities present in this well-known dataset. Used to derive a
# clean ``city`` dimension from the free-text ``Hotel_Address``.
KNOWN_CITIES = ("Amsterdam", "Barcelona", "London", "Milan", "Paris", "Vienna")

# Invisible / problematic characters we explicitly hunt for in text columns.
INVISIBLE_CHARS = {
    "tab": "\t",
    "newline": "\n",
    "carriage_return": "\r",
    "non_breaking_space": "\xa0",
    "zero_width_space": "​",
    "zero_width_nbsp": "﻿",
}

NUMERIC_COLUMNS = [
    "Additional_Number_of_Scoring",
    "Average_Score",
    "Review_Total_Negative_Word_Counts",
    "Total_Number_of_Reviews",
    "Review_Total_Positive_Word_Counts",
    "Total_Number_of_Reviews_Reviewer_Has_Given",
    "Reviewer_Score",
    "lat",
    "lng",
]

LONG_TEXT_COLUMNS = ["Negative_Review", "Positive_Review"]
SHORT_TEXT_COLUMNS = [
    "Hotel_Address",
    "Review_Date",
    "Hotel_Name",
    "Reviewer_Nationality",
    "Tags",
    "days_since_review",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("data_quality")

sns.set_theme(style="whitegrid", palette="deep")


# --------------------------------------------------------------------------- #
# Result container
# --------------------------------------------------------------------------- #


@dataclass
class AuditResult:
    """Collects every finding so the audit is reusable and testable."""

    sections: dict[str, Any] = field(default_factory=dict)
    figures: list[Path] = field(default_factory=list)

    def add(self, name: str, payload: Any) -> None:
        self.sections[name] = payload


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


def load_data(path: Path = DATASET_PATH) -> pd.DataFrame:
    """Load the raw dataset without any implicit cleaning.

    ``low_memory=False`` avoids mixed-type chunk inference on the large text
    columns. We deliberately keep every value as-is (including whitespace) so
    the audit can measure the real state of the data.
    """
    logger.info("Loading dataset from %s", path)
    df = pd.read_csv(path, low_memory=False)
    logger.info("Loaded shape=%s", df.shape)
    return df


# --------------------------------------------------------------------------- #
# 1. Structure overview
# --------------------------------------------------------------------------- #


def structure_overview(df: pd.DataFrame) -> dict[str, Any]:
    """Rows, columns, dtypes, memory footprint and per-column cardinality."""
    logger.info("Section 1: structure overview")
    mem_bytes = df.memory_usage(deep=True).sum()
    cardinality = {col: int(df[col].nunique(dropna=True)) for col in df.columns}
    dtypes = {col: str(dt) for col, dt in df.dtypes.items()}

    return {
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "memory_mb": round(mem_bytes / 1024**2, 2),
        "dtypes": dtypes,
        "cardinality": cardinality,
        "numeric_columns": [c for c in NUMERIC_COLUMNS if c in df.columns],
        "text_columns": [c for c in LONG_TEXT_COLUMNS if c in df.columns],
        "categorical_columns": [c for c in SHORT_TEXT_COLUMNS if c in df.columns],
    }


# --------------------------------------------------------------------------- #
# 2. Health checks (per column)
# --------------------------------------------------------------------------- #


def _count_invisible(series: pd.Series) -> dict[str, int]:
    """Count rows containing each tracked invisible character."""
    s = series.dropna().astype(str)
    counts: dict[str, int] = {}
    for name, ch in INVISIBLE_CHARS.items():
        counts[name] = int(s.str.contains(re.escape(ch), regex=True).sum())
    return counts


def health_checks(df: pd.DataFrame) -> dict[str, Any]:
    """Missing, empty, whitespace and invisible-character diagnostics per column."""
    logger.info("Section 2: health checks")
    n = len(df)
    per_column: dict[str, Any] = {}

    for col in df.columns:
        series = df[col]
        missing = int(series.isna().sum())
        record: dict[str, Any] = {
            "missing": missing,
            "missing_pct": round(100 * missing / n, 4),
        }
        if series.dtype == object:
            s = series.dropna().astype(str)
            record["empty_string"] = int((s == "").sum())
            record["whitespace_only"] = int(s.str.fullmatch(r"\s+").fillna(False).sum())
            record["leading_or_trailing_space"] = int((s != s.str.strip()).sum())
            record["invisible_chars"] = _count_invisible(series)
        per_column[col] = record

    return per_column


# --------------------------------------------------------------------------- #
# 3. Placeholder detection (domain-specific data-quality trap)
# --------------------------------------------------------------------------- #


def placeholder_detection(df: pd.DataFrame) -> dict[str, Any]:
    """Detect Booking.com's 'No Negative' / 'No Positive' sentinel values.

    These are *not* missing values in the pandas sense but they carry no
    textual information and would poison any NLP feature if treated as content.
    """
    logger.info("Section 3: placeholder detection")
    n = len(df)
    neg = df["Negative_Review"].astype(str).str.strip()
    pos = df["Positive_Review"].astype(str).str.strip()

    neg_ph = int((neg == NEGATIVE_PLACEHOLDER).sum())
    pos_ph = int((pos == POSITIVE_PLACEHOLDER).sum())
    both_ph = int(((neg == NEGATIVE_PLACEHOLDER) & (pos == POSITIVE_PLACEHOLDER)).sum())

    return {
        "negative_placeholder": neg_ph,
        "negative_placeholder_pct": round(100 * neg_ph / n, 2),
        "positive_placeholder": pos_ph,
        "positive_placeholder_pct": round(100 * pos_ph / n, 2),
        "both_empty": both_ph,
        "both_empty_pct": round(100 * both_ph / n, 2),
    }


# --------------------------------------------------------------------------- #
# 4. Duplicate analysis
# --------------------------------------------------------------------------- #


def duplicate_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Full-row, review-level and hotel-level duplicate detection."""
    logger.info("Section 4: duplicate analysis")
    full_dupes = int(df.duplicated().sum())

    # A "review" is uniquely identified (as much as this schema allows) by the
    # hotel, the date, the reviewer origin and both text sides.
    review_keys = [
        "Hotel_Name",
        "Review_Date",
        "Reviewer_Nationality",
        "Negative_Review",
        "Positive_Review",
        "Reviewer_Score",
    ]
    review_dupes = int(df.duplicated(subset=review_keys).sum())

    # Hotel identity: same name but conflicting address / coordinates would be
    # an inconsistency; same name+address collapsing to one hotel is expected.
    hotels = df.groupby("Hotel_Name").agg(
        n_addresses=("Hotel_Address", "nunique"),
        n_avg_scores=("Average_Score", "nunique"),
    )
    hotels_multi_address = hotels[hotels["n_addresses"] > 1]
    hotels_multi_score = hotels[hotels["n_avg_scores"] > 1]

    return {
        "full_row_duplicates": full_dupes,
        "review_level_duplicates": review_dupes,
        "unique_hotels": int(df["Hotel_Name"].nunique()),
        "hotels_with_multiple_addresses": int(len(hotels_multi_address)),
        "hotels_with_multiple_avg_scores": int(len(hotels_multi_score)),
        "hotels_multi_score_examples": hotels_multi_score.head(10).to_dict("index"),
    }


# --------------------------------------------------------------------------- #
# 5. Date & temporal integrity
# --------------------------------------------------------------------------- #


def date_audit(df: pd.DataFrame, today: pd.Timestamp | None = None) -> dict[str, Any]:
    """Parse dates, flag invalid/future ones and cross-check days_since_review."""
    logger.info("Section 5: date & temporal integrity")
    today = today or pd.Timestamp.today().normalize()

    parsed = pd.to_datetime(df["Review_Date"], format="%m/%d/%Y", errors="coerce")
    invalid = int(parsed.isna().sum())
    valid = parsed.dropna()

    # days_since_review is a string like "3 days"; extract the integer.
    dsr = (
        df["days_since_review"]
        .astype(str)
        .str.extract(r"(\d+)")[0]
        .astype("Float64")
    )

    # The scrape reference date is the most recent review (days_since = 0).
    reference_date = valid.max()
    expected_days = (reference_date - parsed).dt.days
    # Consistency: |declared days - expected days| should be ~0.
    diff = (dsr - expected_days).abs()
    inconsistent_days = int((diff > 1).sum())

    return {
        "invalid_dates": invalid,
        "min_date": str(valid.min().date()) if not valid.empty else None,
        "max_date": str(valid.max().date()) if not valid.empty else None,
        "span_days": int((valid.max() - valid.min()).days) if not valid.empty else None,
        "future_dates_vs_today": int((valid > today).sum()),
        "reference_date": str(reference_date.date()) if not valid.empty else None,
        "days_since_review_inconsistent": inconsistent_days,
    }


# --------------------------------------------------------------------------- #
# 6. Numeric distributions (skewness, kurtosis, outliers, plots)
# --------------------------------------------------------------------------- #


def _iqr_outliers(series: pd.Series) -> tuple[int, float, float]:
    """Return (#outliers, lower_fence, upper_fence) using the 1.5*IQR rule."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out = int(((series < low) | (series > high)).sum())
    return n_out, float(low), float(high)


def numeric_distributions(df: pd.DataFrame, result: AuditResult) -> dict[str, Any]:
    """Compute distribution stats and render histogram/box/violin grids."""
    logger.info("Section 6: numeric distributions")
    cols = [c for c in NUMERIC_COLUMNS if c in df.columns]
    stats_table: dict[str, Any] = {}

    for col in cols:
        s = df[col].dropna()
        n_out, low, high = _iqr_outliers(s)
        stats_table[col] = {
            "count": int(s.count()),
            "mean": round(float(s.mean()), 4),
            "std": round(float(s.std()), 4),
            "min": round(float(s.min()), 4),
            "median": round(float(s.median()), 4),
            "max": round(float(s.max()), 4),
            "skewness": round(float(stats.skew(s)), 4),
            "kurtosis": round(float(stats.kurtosis(s)), 4),  # excess kurtosis
            "n_outliers_iqr": n_out,
            "outlier_pct": round(100 * n_out / len(s), 2),
            "iqr_fences": [round(low, 2), round(high, 2)],
        }

    _plot_numeric_grid(df, cols, "histograms", result, kind="hist")
    _plot_numeric_grid(df, cols, "boxplots", result, kind="box")
    # Violin + KDE focus on the two scores that matter most analytically.
    _plot_score_detail(df, result)
    return stats_table


def _plot_numeric_grid(
    df: pd.DataFrame, cols: list[str], name: str, result: AuditResult, kind: str
) -> None:
    """Render a grid of histograms or boxplots for all numeric columns."""
    ncols = 3
    nrows = int(np.ceil(len(cols) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 4 * nrows))
    axes = np.atleast_1d(axes).ravel()

    for ax, col in zip(axes, cols):
        s = df[col].dropna()
        if kind == "hist":
            sns.histplot(s, bins=50, kde=True, ax=ax, color="#4C72B0")
        else:
            sns.boxplot(x=s, ax=ax, color="#55A868")
        ax.set_title(col, fontsize=10)
        ax.set_xlabel("")

    for ax in axes[len(cols):]:
        ax.set_visible(False)

    fig.suptitle(f"Numeric {name} — raw dataset", fontsize=14, y=1.01)
    fig.tight_layout()
    path = FIGURES_DIR / f"01_numeric_{name}.png"
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    result.figures.append(path)
    logger.info("  saved %s", path.name)


def _plot_score_detail(df: pd.DataFrame, result: AuditResult) -> None:
    """Violin + KDE for Average_Score (target) and Reviewer_Score."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    sns.violinplot(y=df["Average_Score"].dropna(), ax=axes[0, 0], color="#C44E52")
    axes[0, 0].set_title("Average_Score — violin (TARGET, hotel-level)")

    sns.kdeplot(df["Average_Score"].dropna(), ax=axes[0, 1], fill=True, color="#C44E52")
    axes[0, 1].set_title("Average_Score — KDE")

    sns.violinplot(y=df["Reviewer_Score"].dropna(), ax=axes[1, 0], color="#4C72B0")
    axes[1, 0].set_title("Reviewer_Score — violin (review-level)")

    sns.kdeplot(df["Reviewer_Score"].dropna(), ax=axes[1, 1], fill=True, color="#4C72B0")
    axes[1, 1].set_title("Reviewer_Score — KDE")

    fig.suptitle("Score distributions: hotel-level target vs review-level", fontsize=14)
    fig.tight_layout()
    path = FIGURES_DIR / "01_score_distributions.png"
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    result.figures.append(path)
    logger.info("  saved %s", path.name)


# --------------------------------------------------------------------------- #
# 7. Frequency analysis (hotel / temporal / geographic concentration)
# --------------------------------------------------------------------------- #


def _derive_city(address: pd.Series) -> pd.Series:
    """Map each free-text address to one of the six known cities."""
    result = pd.Series(pd.NA, index=address.index, dtype="object")
    for city in KNOWN_CITIES:
        mask = address.str.contains(rf"\b{city}\b", case=False, na=False)
        result = result.mask(mask, city)
    return result


def _derive_country(address: pd.Series) -> pd.Series:
    """The country is the trailing token(s) of the address (UK is two words)."""
    country = address.str.strip().str.extract(r"(United Kingdom|\w+)\s*$")[0]
    return country


def frequency_analysis(df: pd.DataFrame, result: AuditResult) -> dict[str, Any]:
    """Distribution of reviews across hotels, time and geography."""
    logger.info("Section 7: frequency analysis")
    reviews_per_hotel = df.groupby("Hotel_Name").size()

    parsed = pd.to_datetime(df["Review_Date"], format="%m/%d/%Y", errors="coerce")
    per_year = parsed.dt.year.value_counts().sort_index()
    per_month = parsed.dt.to_period("M").value_counts().sort_index()

    city = _derive_city(df["Hotel_Address"])
    country = _derive_country(df["Hotel_Address"])
    nationality = df["Reviewer_Nationality"].astype(str).str.strip()

    # Concentration: share of reviews held by the top hotels.
    top10_share = round(
        100 * reviews_per_hotel.sort_values(ascending=False).head(10).sum() / len(df), 2
    )

    thin_hotels = reviews_per_hotel[reviews_per_hotel < 30]

    _plot_frequency(reviews_per_hotel, per_year, city, nationality, result)

    return {
        "reviews_per_hotel": {
            "min": int(reviews_per_hotel.min()),
            "median": float(reviews_per_hotel.median()),
            "mean": round(float(reviews_per_hotel.mean()), 1),
            "max": int(reviews_per_hotel.max()),
        },
        "hotels_below_30_reviews": int((reviews_per_hotel < 30).sum()),
        "hotels_below_50_reviews": int((reviews_per_hotel < 50).sum()),
        "thin_hotel_examples": thin_hotels.sort_values().head(10).to_dict(),
        "top10_hotels_review_share_pct": top10_share,
        "reviews_per_year": {int(k): int(v) for k, v in per_year.items()},
        "reviews_per_month_head": {str(k): int(v) for k, v in per_month.head(6).items()},
        "reviews_by_city": {str(k): int(v) for k, v in city.value_counts().items()},
        "city_missing": int(city.isna().sum()),
        "reviews_by_country": {
            str(k): int(v) for k, v in country.value_counts().head(10).items()
        },
        "top_nationalities": {
            str(k): int(v) for k, v in nationality.value_counts().head(10).items()
        },
        "distinct_nationalities": int(nationality.nunique()),
    }


def _plot_frequency(
    reviews_per_hotel: pd.Series,
    per_year: pd.Series,
    city: pd.Series,
    nationality: pd.Series,
    result: AuditResult,
) -> None:
    """Four-panel figure summarising volume concentration."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    sns.histplot(reviews_per_hotel, bins=50, ax=axes[0, 0], color="#4C72B0")
    axes[0, 0].set_title("Reviews per hotel — distribution")
    axes[0, 0].set_xlabel("reviews per hotel")

    per_year.plot(kind="bar", ax=axes[0, 1], color="#55A868")
    axes[0, 1].set_title("Reviews per year")

    city.value_counts().plot(kind="bar", ax=axes[1, 0], color="#C44E52")
    axes[1, 0].set_title("Reviews per city")
    axes[1, 0].tick_params(axis="x", rotation=45)

    nationality.value_counts().head(12).plot(kind="barh", ax=axes[1, 1], color="#8172B3")
    axes[1, 1].set_title("Top 12 reviewer nationalities")
    axes[1, 1].invert_yaxis()

    fig.suptitle("Frequency & concentration analysis", fontsize=14)
    fig.tight_layout()
    path = FIGURES_DIR / "01_frequency_analysis.png"
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    result.figures.append(path)
    logger.info("  saved %s", path.name)


# --------------------------------------------------------------------------- #
# 8. Completeness (column & hotel level)
# --------------------------------------------------------------------------- #


def completeness_report(df: pd.DataFrame) -> dict[str, Any]:
    """Column-level and hotel-level completeness, plus geo-missing hotels."""
    logger.info("Section 8: completeness")
    n = len(df)
    per_column = {
        col: round(100 * df[col].notna().sum() / n, 2) for col in df.columns
    }

    # Hotels missing coordinates cannot be geolocated on the MVP map.
    geo_missing = df[df["lat"].isna() | df["lng"].isna()]["Hotel_Name"].nunique()

    return {
        "column_completeness_pct": per_column,
        "rows_missing_coordinates": int((df["lat"].isna() | df["lng"].isna()).sum()),
        "hotels_missing_coordinates": int(geo_missing),
    }


# --------------------------------------------------------------------------- #
# 9. Target-specific integrity (leakage / granularity check)
# --------------------------------------------------------------------------- #


def target_integrity(df: pd.DataFrame) -> dict[str, Any]:
    """Critical check: is Average_Score constant within each hotel?

    If ``Average_Score`` is a single value per hotel it is a *hotel-level*
    attribute, not a review-level one. Modeling it from review-level rows would
    (a) massively duplicate the target (pseudo-replication) and (b) invite
    leakage from other hotel-level aggregates. This function quantifies that.
    """
    logger.info("Section 9: target integrity / granularity")
    per_hotel_unique = df.groupby("Hotel_Name")["Average_Score"].nunique()
    hotels_varying = int((per_hotel_unique > 1).sum())

    n_unique_target = int(df["Average_Score"].nunique())
    n_hotels = int(df["Hotel_Name"].nunique())

    # Relationship between the review-level score and the hotel-level average.
    hotel_mean_reviewer = df.groupby("Hotel_Name")["Reviewer_Score"].mean()
    hotel_avg = df.groupby("Hotel_Name")["Average_Score"].first()
    corr = float(hotel_mean_reviewer.corr(hotel_avg))

    return {
        "unique_average_score_values": n_unique_target,
        "n_hotels": n_hotels,
        "hotels_with_varying_average_score": hotels_varying,
        "is_hotel_level_constant": hotels_varying == 0,
        "corr_avg_score_vs_mean_reviewer_score": round(corr, 4),
        "average_score_value_range": [
            round(float(df["Average_Score"].min()), 2),
            round(float(df["Average_Score"].max()), 2),
        ],
    }


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def _fmt(obj: Any, indent: int = 0) -> str:
    """Render a nested dict/list as readable indented Markdown-ish text."""
    pad = "  " * indent
    if isinstance(obj, dict):
        lines = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}- **{k}**:")
                lines.append(_fmt(v, indent + 1))
            else:
                lines.append(f"{pad}- **{k}**: {v}")
        return "\n".join(lines)
    if isinstance(obj, list):
        return "\n".join(f"{pad}- {item}" for item in obj)
    return f"{pad}{obj}"


def write_report(result: AuditResult, path: Path) -> None:
    """Persist the full audit as a Markdown report."""
    logger.info("Writing report to %s", path)
    lines = [
        "# Data Audit Report — Hotel_Reviews.csv",
        "",
        "Auditoria automatizada gerada por `src/data_quality.py`. "
        "Read-only sobre o dataset bruto (sem limpeza).",
        "",
    ]
    titles = {
        "structure": "1. Estrutura",
        "health": "2. Health checks (por coluna)",
        "placeholders": "3. Placeholders de texto ('No Negative' / 'No Positive')",
        "duplicates": "4. Duplicados",
        "dates": "5. Datas & integridade temporal",
        "numeric": "6. Distribuições numéricas (skew/kurtosis/outliers)",
        "frequency": "7. Frequência & concentração",
        "completeness": "8. Completude",
        "target": "9. Integridade da target (Average_Score)",
    }
    for key, title in titles.items():
        if key in result.sections:
            lines.append(f"## {title}")
            lines.append(_fmt(result.sections[key]))
            lines.append("")

    if result.figures:
        lines.append("## Figuras geradas")
        for fig in result.figures:
            lines.append(f"- `figures/{fig.name}`")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def run_audit(path: Path = DATASET_PATH) -> AuditResult:
    """Run every audit section and persist report + figures."""
    for directory in (FIGURES_DIR, REPORTS_DIR, OUTPUTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    df = load_data(path)
    result = AuditResult()

    result.add("structure", structure_overview(df))
    result.add("health", health_checks(df))
    result.add("placeholders", placeholder_detection(df))
    result.add("duplicates", duplicate_analysis(df))
    result.add("dates", date_audit(df))
    result.add("numeric", numeric_distributions(df, result))
    result.add("frequency", frequency_analysis(df, result))
    result.add("completeness", completeness_report(df))
    result.add("target", target_integrity(df))

    write_report(result, REPORTS_DIR / "01_data_audit.md")
    logger.info("Audit complete: %d figures, report saved.", len(result.figures))
    return result


if __name__ == "__main__":
    run_audit()
