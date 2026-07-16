# How to run the NLP pipeline on a GPU machine

Extracts overall sentiment (1–5 stars) and, per aspect (cleanliness, staff, location,
comfort, food, value for money, noise, facilities), three columns — a 0–10 score, a
closed-vocabulary sub-tag (e.g. `water_quality`, `wifi`, `rudeness` — comparable/countable
across reviews and hotels), and a verbatim evidence excerpt — for every review, using
**free, local models** (no data leaves the machine).

> No local GPU? Use [`notebooks/nlp_pipeline_colab.ipynb`](../notebooks/nlp_pipeline_colab.ipynb)
> instead — same pipeline, runs on Google Colab's free T4 GPU, no local setup required.

## 1. Prerequisites

- Python 3.10+ and an NVIDIA GPU with CUDA.
- Copy the project to the GPU machine (including `data/Hotel_Reviews.csv`).

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

> Important: install the **CUDA build of PyTorch** matching your GPU (see
> https://pytorch.org). `requirements.txt` requests a generic `torch`; on a GPU
> machine, install the CUDA wheel so it actually uses the card.
> Verify with: `python -c "import torch; print(torch.cuda.is_available())"` → must print `True`.

## 3. Smoke test first (required)

Run on a small sample to confirm the GPU is being used and the model download
(~1GB total, first run only) worked:

```bash
python src/nlp_pipeline.py --sample 500 --batch-size 64
```

Should log `CUDA GPU detected: ...` and save `outputs/reviews_enriched_sample.parquet`.

## 4. Full run

```bash
python src/nlp_pipeline.py --batch-size 128
```

- Tune `--batch-size` to your VRAM (128–256 for 8–12GB GPUs).
- Estimated time: **~1–3h** on a T4/RTX 3060-class GPU (515k reviews).
- Output: `outputs/reviews_enriched.parquet` — one row per review, with
  `overall_stars` plus three columns per aspect:
  - `aspect_<name>_score` — 0–10 float (0 = most negative, 10 = most positive), empty when not mentioned
  - `aspect_<name>_subtags` — `;`-joined closed-vocabulary tags, empty when not mentioned
  - `aspect_<name>_evidence` — verbatim excerpt from the review, empty when not mentioned

## 5. Hand back the result

Bring back `outputs/reviews_enriched.parquet`. From it, the next phase builds the
hotel x quarter panel and its features (runs on CPU).

## Technical notes

- **Aspects** are gated by keyword before running ABSA (`ASPECT_LEXICON` in
  `src/nlp_pipeline.py`), so the model only scores what the review actually
  mentions. Each aspect has a nested set of closed-vocabulary sub-tags — add a
  business-specific one by adding an entry to the relevant aspect's dict.
- Keyword matching is **word-boundary safe** (regex `\bword\b`) — a short
  keyword like `bar` never matches inside an unrelated word like `barefoot`.
- Reviews and (text, aspect) pairs are **de-duplicated** before inference.
- Models used (free):
  - `nlptown/bert-base-multilingual-uncased-sentiment` (overall sentiment)
  - `yangheng/deberta-v3-base-absa-v1.1` (aspect sentiment)
