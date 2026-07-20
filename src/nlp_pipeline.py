"""GPU-ready NLP feature extraction for the hotel reviews (free local models).

Run this on a machine with a CUDA GPU. It enriches every review with:

* overall sentiment  -> nlptown/bert-base-multilingual-uncased-sentiment (1-5 stars),
  a model fine-tuned on product reviews;
* aspect sentiment   -> yangheng/deberta-v3-base-absa-v1.1, remapped into a 0-10
  score per aspect (0 = most negative, 10 = most positive, NaN = not mentioned),
  plus a verbatim evidence snippet extracted from the review text itself (no
  generation involved, so it cannot invent content).

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
Reviewer_Score, overall stars, and two columns per aspect (``aspect_<name>_score``,
``aspect_<name>_evidence``). This feeds the hotel x quarter panel built later in
``feature_engineering.py``.
"""

from __future__ import annotations

import argparse
import logging
import re
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

# Hotel-relevant aspects. Each aspect has a small set of closed-vocabulary
# SUB-TAGS — this is what makes problems COMPARABLE and COUNTABLE across
# reviews and hotels (e.g. "37 reviews this quarter tagged water_quality"),
# unlike a free-text evidence snippet, which is unique to each review and
# cannot be aggregated. Matching is WORD-BOUNDARY SAFE (see *_PATTERNS below):
# a short keyword like "bar" only matches the standalone word, never a
# substring inside an unrelated word like "barefoot".
ASPECT_LEXICON: dict[str, dict[str, tuple[str, ...]]] = {
    "cleanliness": {
        "smell": ("smell", "smells", "smelly", "smelled", "odour", "odor",
                  "stink", "stinky", "musty"),
        "dirt_dust": ("dirty", "dirtier", "dust", "dusty", "stain", "stains",
                      "stained", "filthy", "grime", "grimy"),
        "mold": ("mould", "mouldy", "mold", "moldy"),
        "hygiene": ("hygiene", "hygienic", "unhygienic"),
        "housekeeping_general": ("clean", "cleaning", "cleaned", "cleaner",
                                  "cleanliness", "tidy", "untidy", "spotless"),
    },
    "staff": {
        "rudeness": ("rude", "unfriendly", "impolite"),
        "helpfulness": ("helpful", "unhelpful", "welcoming", "friendly", "polite"),
        "checkin_checkout": ("reception", "receptionist", "check in",
                              "check out", "checkin", "checkout"),
        "management": ("manager", "managers"),
        "staff_general": ("staff", "employee", "employees", "service"),
    },
    "location": {
        "distance_center": ("central", "centre", "center", "near", "nearby",
                             "close", "distance", "walk", "walking"),
        "transport_access": ("metro", "station", "bus stop", "tram"),
        "surroundings": ("area", "neighbourhood", "neighborhood", "surroundings"),
        "location_general": ("location", "located"),
    },
    "comfort": {
        "bed_mattress": ("bed", "beds", "mattress", "pillow", "pillows"),
        "room_size": ("spacious", "cramped", "room size"),
        "sleep_quality": ("sleep", "sleeping", "comfortable", "uncomfortable",
                           "cozy", "cosy", "comfy"),
    },
    "food": {
        "breakfast": ("breakfast",),
        "restaurant_service": ("restaurant", "meal", "meals", "dinner",
                                "lunch", "buffet"),
        "drinks_bar": ("bar", "bars", "drink", "drinks", "coffee"),
        "food_general": ("food",),
    },
    "value": {
        "price_too_high": ("expensive", "overpriced", "pricey"),
        "hidden_fees": ("hidden fee", "hidden fees", "extra charge",
                         "extra charges", "surcharge"),
        "good_value": ("cheap", "affordable", "worth", "value for money"),
        "value_general": ("price", "prices", "cost", "costs", "money", "value"),
    },
    "noise": {
        "external_noise": ("street noise", "traffic noise", "outside noise"),
        "internal_noise": ("thin walls", "neighbours", "neighbors", "noisy room"),
        "noise_general": ("noise", "noisy", "loud", "quiet", "soundproof", "silent"),
    },
    "facilities": {
        "wifi": ("wifi", "internet", "wi-fi"),
        "water_quality": ("water pressure", "hot water", "cold water",
                           "water quality", "no water", "water"),
        "air_conditioning": ("air conditioning", "ac unit", "aircon"),
        "pool_gym_spa": ("pool", "gym", "spa", "spas"),
        "parking": ("parking",),
        "elevator": ("elevator", "elevators", "lift", "lifts"),
        "bathroom": ("shower", "showers", "bathroom", "bathrooms"),
        "heating": ("heating",),
    },
}


def _compile_pattern(keywords: tuple[str, ...]) -> "re.Pattern[str]":
    """Word-boundary-safe regex for a list of keywords/phrases (see module docstring)."""
    parts = [
        re.escape(kw) if " " in kw else rf"\b{re.escape(kw)}\b"
        for kw in keywords
    ]
    return re.compile("|".join(parts))


# One pattern per sub-tag, and one merged pattern per aspect (union of its
# sub-tags) reused for the aspect-level gate and the evidence snippet.
SUBTAG_PATTERNS: dict[str, dict[str, "re.Pattern[str]"]] = {
    aspect: {subtag: _compile_pattern(keywords) for subtag, keywords in subtags.items()}
    for aspect, subtags in ASPECT_LEXICON.items()
}
ASPECT_PATTERNS: dict[str, "re.Pattern[str]"] = {
    aspect: _compile_pattern(tuple(kw for keywords in subtags.values() for kw in keywords))
    for aspect, subtags in ASPECT_LEXICON.items()
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
    """Return the aspects whose (merged) keyword pattern matches in a lowercased review."""
    return [aspect for aspect, pattern in ASPECT_PATTERNS.items() if pattern.search(text_lower)]


def detect_subtags(aspect: str, text_lower: str) -> list[str]:
    """Return the closed-vocabulary sub-tags of `aspect` matched in a lowercased review.

    This is the countable/comparable signal — e.g. facilities -> ["water_quality"]
    can be aggregated across every review and hotel, unlike a free-text evidence
    snippet, which is unique per review.
    """
    return [subtag for subtag, pattern in SUBTAG_PATTERNS[aspect].items() if pattern.search(text_lower)]


# Characters of context kept on each side of a keyword match in the evidence
# snippet, and how many non-overlapping snippets to keep per aspect.
EVIDENCE_CONTEXT_CHARS = 45
EVIDENCE_MAX_SNIPPETS = 2


def _score_from_label(label: str, confidence: float) -> float:
    """Map an ABSA label + confidence to a 0-10 scale (0 = most negative, 10 = most positive).

    Deterministic remap of the classifier's own confidence — no separate model,
    nothing invented, just a rescale of a number the model already produced.
    """
    label = label.lower()
    if label == "positive":
        strength = confidence
    elif label == "negative":
        strength = -confidence
    else:  # neutral
        strength = 0.0
    return round(5.0 + 5.0 * strength, 2)


def _extract_evidence(text: str, aspect: str) -> str:
    """Return verbatim context snippet(s) around each aspect keyword hit.

    Audit trail only — not the comparable signal; use detect_subtags for
    anything that needs to be counted or aggregated.
    """
    pattern = ASPECT_PATTERNS[aspect]
    lowered = text.lower()
    snippets: list[str] = []
    last_end = -1
    for m in pattern.finditer(lowered):
        if m.start() < last_end:
            continue
        lo = max(0, m.start() - EVIDENCE_CONTEXT_CHARS)
        hi = min(len(text), m.end() + EVIDENCE_CONTEXT_CHARS)
        snippets.append(text[lo:hi].strip())
        last_end = hi
        if len(snippets) >= EVIDENCE_MAX_SNIPPETS:
            break
    return " (...) ".join(snippets)


def score_aspects(texts: pd.Series, batch_size: int) -> pd.DataFrame:
    """Per mentioned aspect: a 0-10 score, closed-vocabulary sub-tags (comparable
    across reviews), and a verbatim evidence snippet (audit trail only).

    Three columns per aspect — ``aspect_<name>_score`` (float, NaN when not
    mentioned), ``aspect_<name>_subtags`` (";"-joined closed tags, "" when not
    mentioned), ``aspect_<name>_evidence`` (verbatim excerpt, "" when not
    mentioned).
    """
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

    score_cache: dict[tuple[str, str], float] = {}
    subtag_cache: dict[tuple[str, str], str] = {}
    evidence_cache: dict[tuple[str, str], str] = {}
    for (text, aspect), pred in zip(job_list, preds):
        score_cache[(text, aspect)] = _score_from_label(pred["label"], pred["score"])
        subtag_cache[(text, aspect)] = ";".join(detect_subtags(aspect, text.lower()))
        evidence_cache[(text, aspect)] = _extract_evidence(text, aspect)

    # Assemble three columns per aspect.
    result = pd.DataFrame(index=texts.index)
    for aspect in ASPECT_LEXICON:
        result[f"aspect_{aspect}_score"] = [
            score_cache.get((text, aspect)) if aspect in aspects else None
            for text, aspects in zip(texts, mentioned)
        ]
        result[f"aspect_{aspect}_subtags"] = [
            subtag_cache.get((text, aspect), "") if aspect in aspects else ""
            for text, aspects in zip(texts, mentioned)
        ]
        result[f"aspect_{aspect}_evidence"] = [
            evidence_cache.get((text, aspect), "") if aspect in aspects else ""
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
