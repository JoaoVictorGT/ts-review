"""Text-quality audit and (later) cleaning pipeline for the review free-text.

Phase 2 delivers the *diagnostic* only: it measures how dirty the two free-text
columns are so we can choose a cleaning strategy with eyes open. The actual
cleaning / normalization functions will be added once the strategy is approved.

Key domain fact about this dataset
----------------------------------
During scraping, punctuation and apostrophes were stripped from the review
text. The dominant defect is therefore NOT random misspelling but broken
contractions and lost punctuation, e.g. "I don t like" / "it s" / "can not".
That distinction drives the cleaning strategy (cheap deterministic repair vs
expensive full LLM rewriting).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "Hotel_Reviews.csv"

NEGATIVE_PLACEHOLDER = "No Negative"
POSITIVE_PLACEHOLDER = "No Positive"
TEXT_COLUMNS = ["Negative_Review", "Positive_Review"]

# Isolated lowercase remnants left behind when apostrophes were stripped
# ("don t", "it s", "we re", "i ve", "they ll", "i m", "he d").
BROKEN_CONTRACTION = re.compile(r"\b(?:t|s|re|ve|ll|m|d)\b")
NON_ASCII = re.compile(r"[^\x00-\x7f]")
EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF]",
    flags=re.UNICODE,
)
MULTISPACE = re.compile(r"\s{2,}")
ALLCAPS_WORD = re.compile(r"\b[A-Z]{3,}\b")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("text_cleaning")


def _is_placeholder(series: pd.Series, placeholder: str) -> pd.Series:
    """Boolean mask of content-free placeholder rows for a text column."""
    return series.astype(str).str.strip() == placeholder


def diagnose_column(series: pd.Series, placeholder: str) -> dict[str, object]:
    """Compute text-quality metrics for one free-text column (real content only)."""
    n_total = len(series)
    s = series.astype(str)

    ph_mask = s.str.strip() == placeholder
    content = s[~ph_mask].str.strip()
    n_content = len(content)

    # Length distribution on real content only.
    char_len = content.str.len()
    word_len = content.str.split().map(len)

    # Approximate LLM token budget: ~1.3 tokens per whitespace word for English.
    approx_tokens = word_len.sum() * 1.3

    def pct(mask_sum: int) -> float:
        return round(100 * mask_sum / n_content, 2) if n_content else 0.0

    broken = int(content.str.contains(BROKEN_CONTRACTION).sum())
    non_ascii = int(content.str.contains(NON_ASCII).sum())
    emoji = int(content.str.contains(EMOJI).sum())
    multispace = int(content.str.contains(MULTISPACE).sum())
    allcaps = int(content.str.contains(ALLCAPS_WORD).sum())
    very_short = int((word_len <= 2).sum())
    duplicates = int(content.duplicated().sum())

    return {
        "n_total": n_total,
        "placeholder_rows": int(ph_mask.sum()),
        "placeholder_pct": round(100 * int(ph_mask.sum()) / n_total, 2),
        "content_rows": n_content,
        "chars_median": float(char_len.median()),
        "chars_p90": float(char_len.quantile(0.9)),
        "words_median": float(word_len.median()),
        "words_mean": round(float(word_len.mean()), 1),
        "words_p90": float(word_len.quantile(0.9)),
        "approx_total_tokens_millions": round(approx_tokens / 1e6, 1),
        "broken_contractions_rows": broken,
        "broken_contractions_pct": pct(broken),
        "non_ascii_rows": non_ascii,
        "non_ascii_pct": pct(non_ascii),
        "emoji_rows": emoji,
        "emoji_pct": pct(emoji),
        "multispace_rows": multispace,
        "multispace_pct": pct(multispace),
        "allcaps_word_rows": allcaps,
        "allcaps_word_pct": pct(allcaps),
        "very_short_rows(<=2_words)": very_short,
        "very_short_pct": pct(very_short),
        "duplicate_content_rows": duplicates,
        "unique_content_rows": n_content - duplicates,
    }


def sample_dirty_examples(series: pd.Series, placeholder: str, k: int = 5) -> list[str]:
    """Return a few real examples showing the de-punctuation artifact."""
    s = series.astype(str).str.strip()
    content = s[(s != placeholder) & s.str.contains(BROKEN_CONTRACTION)]
    return content.head(k).str[:200].tolist()


# --------------------------------------------------------------------------- #
# Deterministic normalization (cleaning "Camada 0" — free, no model needed)
# --------------------------------------------------------------------------- #

# High-value broken-contraction repairs (punctuation stripped during scraping).
# This mainly helps human readability; the transformer models are robust to the
# raw form, so it is optional for modeling.
CONTRACTION_FIXES: dict[str, str] = {
    r"\bcan not\b": "cannot",
    r"\b(do|does|did|is|was|are|were|has|have|had|would|should|could|"
    r"wo|ca|ai|must|need|might)n t\b": r"\1n't",
    r"\bit s\b": "it's",
    r"\bthat s\b": "that's",
    r"\bthere s\b": "there's",
    r"\bhe s\b": "he's",
    r"\bshe s\b": "she's",
    r"\bwhat s\b": "what's",
    r"\blet s\b": "let's",
    r"\bi m\b": "I'm",
    r"\b(i|we|they|you) ve\b": r"\1've",
    r"\b(i|we|they|you|it|he|she) ll\b": r"\1'll",
    r"\b(i|we|they|you|he|she|it) d\b": r"\1'd",
    r"\b(we|they|you) re\b": r"\1're",
}
_COMPILED_FIXES = [(re.compile(p, re.IGNORECASE), r) for p, r in CONTRACTION_FIXES.items()]


def fix_broken_contractions(text: str) -> str:
    """Repair de-punctuated contractions ('don t' -> \"don't\")."""
    for pattern, repl in _COMPILED_FIXES:
        text = pattern.sub(repl, text)
    return text


def normalize_text(text: str) -> str:
    """Strip, collapse internal whitespace and repair contractions."""
    text = MULTISPACE.sub(" ", str(text).strip())
    return fix_broken_contractions(text)


def clean_review_side(series: pd.Series, placeholder: str) -> pd.Series:
    """Normalize a review column and turn content-free placeholders into ''."""
    s = series.astype(str).str.strip()
    s = s.mask(s == placeholder, "")
    return s.map(lambda t: normalize_text(t) if t else "")


def combined_clean_text(df: pd.DataFrame) -> pd.Series:
    """Join the cleaned positive and negative sides into one review text.

    A single review can praise one aspect and criticise another across the two
    fields, so we concatenate both sides and let the aspect model disambiguate.
    """
    pos = clean_review_side(df["Positive_Review"], POSITIVE_PLACEHOLDER)
    neg = clean_review_side(df["Negative_Review"], NEGATIVE_PLACEHOLDER)
    return (pos + " . " + neg).str.strip(" .").str.replace(r"\s+", " ", regex=True)


def run() -> None:
    """Diagnose both free-text columns and print a compact report."""
    logger.info("Loading text columns")
    df = pd.read_csv(DATASET_PATH, usecols=TEXT_COLUMNS, low_memory=False)

    for col, ph in zip(TEXT_COLUMNS, [NEGATIVE_PLACEHOLDER, POSITIVE_PLACEHOLDER]):
        logger.info("Diagnosing %s", col)
        report = diagnose_column(df[col], ph)
        print(f"\n===== {col} =====")
        for key, value in report.items():
            print(f"  {key:32s}: {value}")
        print("  examples (de-punctuation artifact):")
        for ex in sample_dirty_examples(df[col], ph, k=3):
            print(f"    - {ex!r}")


if __name__ == "__main__":
    run()
