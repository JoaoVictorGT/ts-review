"""GPU-ready NLP feature extraction for the hotel reviews (free local models).

Run this on a machine with a CUDA GPU. It enriches every review with:

* overall sentiment  -> nlptown/bert-base-multilingual-uncased-sentiment (1-5 stars),
  a model fine-tuned on product reviews;
* aspect sentiment   -> yangheng/deberta-v3-base-absa-v1.1 (positive/negative/neutral),
  a free aspect-based sentiment (ABSA) model.

Both models are free and run fully locally (no API, no data leaves the machine).

Aspect gating
-------------
The ABSA model invents a sentiment even for aspects a review never mentions
(verified: "location" scored Positive on a sentence that didn't mention it).
So we only score an aspect when one of its keywords appears in the review — the
keyword lexicon in ``ASPECT_LEXICON`` is the gate. Extend it with any
business-specific aspect the managers care about.

Efficiency
----------
* Reviews are de-duplicated before inference (~16% are exact duplicates).
* Aspect jobs are de-duplicated on (text, aspect) so repeated phrasings are
  scored once.
* Inference is batched; the batch size is tunable for the target GPU.

Usage
-----
    python src/nlp_pipeline.py --sample 500     # quick smoke test first!
    python src/nlp_pipeline.py                   # full corpus
    python src/nlp_pipeline.py --batch-size 128  # tune for your GPU

Output
------
``outputs/reviews_enriched.parquet`` — one row per review with identifiers,
Reviewer_Score, overall stars, and one sentiment column per aspect. This feeds
the hotel x quarter panel built later in ``feature_engineering.py``.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
import torch
from tqdm import tqdm
from transformers import pipeline

from text_cleaning import (
    NEGATIVE_PLACEHOLDER,
    POSITIVE_PLACEHOLDER,
    clean_review_side,
    combined_clean_text,
)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "Hotel_Reviews.csv"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

OVERALL_MODEL = "nlptown/bert-base-multilingual-uncased-sentiment"
ABSA_MODEL = "yangheng/deberta-v3-base-absa-v1.1"

# Hotel-relevant aspects and the keywords that "unlock" ABSA scoring for them.
# Keys become column names; extend freely with business-specific aspects.
ASPECT_LEXICON: dict[str, tuple[str, ...]] = {
    "cleanliness": ("clean", "dirty", "dust", "hygien", "spotless", "filthy",
                    "stain", "smell", "tidy", "mould", "mold"),
    "staff": ("staff", "reception", "service", "receptionist", "employee",
              "rude", "friendly", "helpful", "polite", "welcoming", "manager"),
    "location": ("location", "located", "central", "centre", "center", "near",
                 "close", "walk", "metro", "station", "distance", "area"),
    "comfort": ("comfortable", "comfy", "bed", "mattress", "pillow", "sleep",
                "cozy", "cosy", "spacious", "room size"),
    "food": ("breakfast", "food", "restaurant", "meal", "dinner", "coffee",
             "buffet", "lunch", "bar", "drink"),
    "value": ("price", "expensive", "cheap", "value", "worth", "cost",
              "overpriced", "money", "affordable"),
    "noise": ("noise", "noisy", "loud", "quiet", "soundproof", "silent"),
    "facilities": ("wifi", "internet", "pool", "gym", "spa", "parking",
                   "elevator", "lift", "air conditioning", "shower",
                   "bathroom", "heating"),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nlp_pipeline")


# --------------------------------------------------------------------------- #
# Inference helpers
# --------------------------------------------------------------------------- #


def _device() -> int:
    """Return 0 for the first CUDA GPU, -1 for CPU."""
    if torch.cuda.is_available():
        logger.info("CUDA GPU detected: %s", torch.cuda.get_device_name(0))
        return 0
    logger.warning("No GPU found — running on CPU (much slower).")
    return -1


def _classify_batched(clf, inputs: list, batch_size: int, desc: str) -> list[dict]:
    """Run a transformers pipeline over inputs in progress-tracked batches."""
    out: list[dict] = []
    for i in tqdm(range(0, len(inputs), batch_size), desc=desc):
        out.extend(clf(inputs[i : i + batch_size], truncation=True, batch_size=batch_size))
    return out


# --------------------------------------------------------------------------- #
# Step 1 — overall review sentiment (1-5 stars)
# --------------------------------------------------------------------------- #


def score_overall_sentiment(texts: pd.Series, batch_size: int) -> pd.Series:
    """Predict 1-5 star sentiment per review, de-duplicating identical texts."""
    logger.info("Overall sentiment: loading %s", OVERALL_MODEL)
    clf = pipeline("sentiment-analysis", model=OVERALL_MODEL, device=_device())

    unique = texts[texts.str.len() > 0].drop_duplicates()
    logger.info("Scoring %d unique non-empty texts", len(unique))
    preds = _classify_batched(clf, unique.tolist(), batch_size, "overall")

    # "4 stars" -> 4
    stars = {t: int(p["label"].split()[0]) for t, p in zip(unique, preds)}
    return texts.map(lambda t: stars.get(t))


# --------------------------------------------------------------------------- #
# Step 2 — aspect-based sentiment (keyword-gated ABSA)
# --------------------------------------------------------------------------- #


def detect_aspects(text_lower: str) -> list[str]:
    """Return the aspects whose keywords appear in a lowercased review."""
    return [
        aspect
        for aspect, keywords in ASPECT_LEXICON.items()
        if any(kw in text_lower for kw in keywords)
    ]


def score_aspects(texts: pd.Series, batch_size: int) -> pd.DataFrame:
    """Score each mentioned aspect per review; unmentioned -> 'not_mentioned'."""
    logger.info("Aspect sentiment: loading %s", ABSA_MODEL)
    absa = pipeline("text-classification", model=ABSA_MODEL, device=_device())

    lowered = texts.str.lower()
    mentioned = lowered.map(detect_aspects)

    # Build de-duplicated (text, aspect) jobs — repeated phrasings scored once.
    jobs: set[tuple[str, str]] = set()
    for text, aspects in zip(texts, mentioned):
        for aspect in aspects:
            jobs.add((text, aspect))
    job_list = sorted(jobs)
    logger.info("ABSA jobs after de-duplication: %d", len(job_list))

    inputs = [{"text": t, "text_pair": a} for t, a in job_list]
    preds = _classify_batched(absa, inputs, batch_size, "aspects")
    cache = {job: p["label"].lower() for job, p in zip(job_list, preds)}

    # Assemble one column per aspect.
    result = pd.DataFrame(index=texts.index)
    for aspect in ASPECT_LEXICON:
        result[f"aspect_{aspect}"] = [
            cache.get((text, aspect), "not_mentioned") if aspect in aspects else "not_mentioned"
            for text, aspects in zip(texts, mentioned)
        ]
    result["n_aspects_mentioned"] = mentioned.map(len).values
    return result


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def run(sample: int | None = None, batch_size: int = 64) -> pd.DataFrame:
    """Enrich reviews with overall + aspect sentiment and persist the result."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    cols = [
        "Hotel_Name", "Review_Date", "Reviewer_Score",
        "Reviewer_Nationality", "Positive_Review", "Negative_Review", "Tags",
    ]
    logger.info("Loading dataset (sample=%s)", sample)
    df = pd.read_csv(DATASET_PATH, usecols=cols, low_memory=False)
    if sample:
        df = df.sample(n=sample, random_state=42).reset_index(drop=True)

    # Identifiers + time key for the panel.
    df["review_id"] = df.index
    df["quarter"] = (
        pd.to_datetime(df["Review_Date"], format="%m/%d/%Y", errors="coerce")
        .dt.to_period("Q")
        .astype(str)
    )

    text = combined_clean_text(df)

    df["overall_stars"] = score_overall_sentiment(text, batch_size)
    aspects = score_aspects(text, batch_size)

    enriched = pd.concat(
        [
            df[["review_id", "Hotel_Name", "Review_Date", "quarter",
                "Reviewer_Nationality", "Reviewer_Score", "Tags", "overall_stars"]],
            aspects,
        ],
        axis=1,
    )

    out_path = OUTPUTS_DIR / ("reviews_enriched_sample.parquet" if sample
                              else "reviews_enriched.parquet")
    enriched.to_parquet(out_path, index=False)
    logger.info("Saved %d enriched reviews -> %s", len(enriched), out_path)

    # Quick sanity summary.
    for aspect in ASPECT_LEXICON:
        counts = enriched[f"aspect_{aspect}"].value_counts().to_dict()
        logger.info("  %-12s %s", aspect, counts)
    return enriched


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=int, default=None,
                        help="Run on a random N-row sample (smoke test).")
    parser.add_argument("--batch-size", type=int, default=64,
                        help="Inference batch size (raise for bigger GPUs).")
    args = parser.parse_args()
    run(sample=args.sample, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
