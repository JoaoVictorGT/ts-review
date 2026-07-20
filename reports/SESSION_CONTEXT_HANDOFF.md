# Session Context Handoff

Snapshot of where the TrueStay project stands, written to resume work on a
different machine without re-explaining everything. Read this top to bottom
before touching anything.

## 1. What this project is

**TrueStay** — hotel review analytics. Two halves:

- **Data/NLP pipeline** (`src/`, Python) — audits, cleans, and enriches the
  [515K Hotel Reviews Europe](https://www.kaggle.com/datasets/jiashenliu/515k-hotel-reviews-data-in-europe)
  Kaggle dataset with sentiment/aspect scoring.
- **Web app** (`web/`, React + Vite) — the product UI, currently running on
  data generated FROM the pipeline's output (not live yet, no backend).

## 2. Repository / Git — READ THIS FIRST

- **Remote changed this session.** `origin` now points to
  `https://github.com/JoaoVictorGT/ts-review.git` — the team decided to
  abandon the old repo (`Nuriae/hotelReviews`, still exists on GitHub, just
  not used anymore).
- All 5 local branches were pushed to the new repo: `main`,
  `README/docs-fixes`, `feature/nlp-pipeline-audit`, `pipeline-fixes`,
  `web-structure/front`. `main` is the default branch there.
- Working on `main` directly right now (no active feature branch).
- **Uncommitted changes as of this snapshot** (see §5 for why):
  ```
  M notebooks/nlp_pipeline_colab.ipynb
  M outputs/dashboard_data_sample.json
  M src/dashboard_data_prep.py
  M web/src/data/mockData.js
  M web/src/pages/Dashboard/MonthlyScoreTrend.jsx
  M web/src/pages/Dashboard/index.jsx
  ```
  These are all verified working now (see §4) — safe to review and commit.

## 3. NLP pipeline status

- **Phase 1 (data audit)** and **Phase 2 (text cleaning strategy)**: done.
  Reports in `reports/01_data_audit.md`, `reports/RUN_NLP_ON_GPU.md`.
- **`src/nlp_pipeline.py`**: enriches reviews with overall sentiment (1-5
  stars) and, per aspect (cleanliness, staff, location, comfort, food, value,
  noise, facilities), THREE columns: `aspect_<name>_score` (0-10),
  `aspect_<name>_subtags` (closed-vocabulary, countable — e.g.
  `water_quality`), `aspect_<name>_evidence` (verbatim excerpt).
- **`notebooks/nlp_pipeline_colab.ipynb`**: self-contained Colab version (no
  repo dependency, just needs `Hotel_Reviews.csv` on Google Drive). Mirrors
  `src/nlp_pipeline.py` exactly — keep them in sync when editing either.

### Bugs found and fixed this session (all confirmed fixed, tested)

1. **Word-boundary matching** — keyword gating used raw substring checks, so
   `"bar"` (food aspect) falsely matched inside `"barefoot"`. Fixed with
   `\bword\b` regex in both `src/nlp_pipeline.py` and the notebook.
2. **Missing sub-tags** — aspects only had a free-text evidence snippet, not
   countable across reviews. Added `aspect_<name>_subtags` (closed
   vocabulary, e.g. `water_quality`, `rudeness`) to both files.
3. **`NameError: _score_from_label`** — a refactor accidentally dropped this
   function's definition while keeping its call site. Broke the ENTIRE
   pipeline (`score_aspects` crashed every run). Fixed in both files, this
   one had already been merged to the old repo's `main` before being caught.
4. **Stray backslash in repaired contractions** (found THIS session, just
   fixed) — the notebook's `CONTRACTION_FIXES` dict used raw-string
   replacements like `r"\1n\'t"`, which in Python is NOT `\1n't` — the `\'`
   inside a raw string keeps its literal backslash, so every fixed
   contraction came out as `didn\'t` instead of `didn't` (backslash baked
   into the text). `src/nlp_pipeline.py`'s companion `text_cleaning.py` was
   ALWAYS correct — only the notebook's inlined copy had this bug. Root
   cause fixed in the notebook (verified via `ast.parse` + a live regex
   test — see the exact repro in this session's transcript). Added a
   `sanitize_evidence_columns()` cleanup pass in `dashboard_data_prep.py` so
   ALREADY-corrupted data (see §5) doesn't ship broken text without needing
   a full Colab re-run.

**Open follow-up**: the 500-row Colab sample (`outputs/reviews_enriched_sample.parquet`,
already committed) was generated BEFORE bug #4's fix. The sanitizer patches
the evidence text for the website, but the underlying sample file itself
still has the bug baked in. Not urgent (sanitizer covers it), but worth
regenerating the sample from Colab next time it's convenient, now that the
notebook is fixed. A **full** run (515k rows) should only happen after this
fix, or it'll bake the same corruption into the whole dataset.

## 4. Web app status (`web/`)

React + Vite, React Router, Tailwind v4. Pages: Home, Pricing, Login,
Dashboard (the core analytics screen), Chat (keyword-matched canned agent,
no real LLM yet), Quadrant (price vs. quality scatter — **100% mocked, no
real data source exists for it, no price column anywhere in the dataset**).

Run it: `cd web && npm install && npm run dev` → http://localhost:5173.
Full details in `web/README.md`.

### Just happened: mockData.js is being wired to REAL data

`web/src/data/mockData.js` used to be 100% hand-typed mock data. This
session it became **generated** by `src/dashboard_data_prep.py`, from the
real 500-row Colab sample (`outputs/reviews_enriched_sample.parquet`, 2
hotels: **Hotel Arena** 405 reviews, **K K Hotel George** 95 reviews).

Decisions already made (don't re-litigate — user confirmed all three):

- **Leaderboard/competitors: only real data**, even though that means just 2
  hotels instead of the old mock's 10. No fake filler hotels.
- **Quadrant page stays 100% mocked** — no price data exists to make it real.
- **Category "insight" text is auto-generated** from the data (picks the
  hotel's most common NEGATIVE sub-tag per category, e.g. *"Most negative
  mentions are about check-in/check-out (30 reviews)."*) — prefers specific
  sub-tags over the generic `*_general` catch-alls (fixed mid-session: the
  first version said "Staff: ... about staff", circular and useless; now
  correctly picks `checkin_checkout` instead of `staff_general`).

What `dashboard_data_prep.py` now does end-to-end (`python src/dashboard_data_prep.py`):
loads the sample → sanitizes the backslash bug → computes category scores,
leaderboard, quarterly trend, dimension comments, category comment samples,
competitor gaps, vulnerability table (with real highlighted keywords) →
writes `web/src/data/mockData.js` directly (same export names as before —
`CATEGORIES`, `HOTEL_ARENA_SCORES`, `COMPETITORS`, `LEADERBOARD`,
`VULNERABILITIES`, `DIMENSION_COMMENTS`, `CATEGORY_COMMENTS` — component code
does NOT need to change). `CATEGORY_COLORS`, `HOTELS`, `QUADRANT_STYLES` are
NOT regenerated (Quadrant stays mocked, see above).

**Naming change, now fully wired (fixed this session)**: `MONTHLY_LABELS`/
`MONTHLY_OVERALL`/`MONTHLY_BY_CATEGORY` were renamed to `QUARTERLY_*` in the
generated file (real data only supports quarterly granularity — matches the
hotel × quarter panel decision). `web/src/pages/Dashboard/MonthlyScoreTrend.jsx`
was updated to import `QUARTERLY_*` and its UI label changed from "Monthly
score trend" to "Quarterly score trend".

**Second real bug found and fixed during verification**:
`web/src/pages/Dashboard/index.jsx` hardcoded
`useState("plaza")` as the default `selectedCompetitorId` — a leftover from
the old hand-mocked data that had multiple competitors including one named
"plaza". The real `COMPETITORS` array now has exactly one entry
(`id: "k_k_hotel_george"`), so `COMPETITORS.find(c => c.id === "plaza")`
returned `undefined` and `CompetitiveGapMatrix.jsx` crashed on
`competitor.scores[...]` (confirmed via a real React error-boundary warning
in the browser console). Fixed by deriving the default dynamically:
`useState(COMPETITORS[0]?.id)`.

### Verification status: DONE, confirmed clean

Both of the above are fixed and confirmed working end-to-end in a real
browser (Claude Code's preview tooling, `npm run dev` on port 5173):

- `mockData.js` stray-backslash check: ran an unambiguous Python
  `content.count(chr(92)+chr(39))` — **0 occurrences**. The earlier "503"
  from a bash grep was confirmed to be a shell-escaping artifact, not a real
  bug.
- Home page (`/`): loads clean, no console errors, no Gartner references.
- Dashboard page: loads clean, no console errors. Confirmed rendering real
  data — overall score 7.84, category health cards with real auto-generated
  insight text (e.g. "Most negative mentions are about smell (12 reviews)"
  for Cleanliness), competitive gap matrix vs. K K Hotel George, quarterly
  trend chart, 2-hotel leaderboard, regional position with real average
  (8.08), guest comments by dimension sorted worst→best, real verbatim
  comment excerpts (no stray backslashes visible), competitor vulnerability
  table.
- Chat page (`/chat`): loads clean, no console errors.
- (Screenshot capture via the browser tool timed out in this environment —
  an unrelated tooling issue, not an app bug. Text-based verification
  (`get_page_text`, `read_console_messages`) was used instead and is
  sufficient — no visual/CSS changes were made this pass.)

## 5. Auto-generated companion artifacts (also uncommitted)

- `outputs/dashboard_data_sample.json` — the same computed data as
  `mockData.js`, in plain JSON (useful for the Colab notebook's own
  charting cells, see `notebooks/nlp_pipeline_colab.ipynb` sections 11-12).
- `figures/dashboard_*.png` — matplotlib charts from `src/dashboard_charts.py`
  (category scores, quarterly trend, leaderboard, competitor gaps),
  generated from the same real sample. Already committed in an earlier
  commit on this branch.

## 6. TODO / next steps, roughly in order

1. ~~Finish verifying `mockData.js` is clean~~ — DONE, confirmed 0 stray backslashes.
2. ~~Fix `MonthlyScoreTrend.jsx` import~~ — DONE, uses `QUARTERLY_*` now.
3. ~~Run the dev server and click through Dashboard/Chat/Home~~ — DONE. Also
   found and fixed a second real bug in the process (`index.jsx`'s hardcoded
   `"plaza"` competitor default, see §4). Not yet run: `npm run build` /
   `npm run lint` as a final static check (recommended before committing,
   quick to do).
4. Decide (still open, was asked once and dismissed): which HTML artifact
   should reflect this real-data milestone — `reports/session_summary.html`,
   the live website itself, or a new standalone report? See this session's
   earlier discussion for the 3 framed options.
5. Commit the pending changes (§2) — verification is done, safe to commit
   once `npm run build`/`lint` pass.
6. When convenient: re-run the Colab notebook's smoke test (now bug-fixed)
   to get a clean 500-row sample without the backslash issue baked in, then
   re-run `dashboard_data_prep.py` against that.
7. Longer-term / already decided but not started: FastAPI + Neon Postgres
   backend (see earlier project memory / conversation — DB choice already
   made, API layer not built), Phase 3 feature engineering (hotel × quarter
   panel) on the FULL 515k dataset once a clean full run exists.

## 7. Quick reference — where things live

```
src/data_quality.py          Phase 1 audit
src/panel_feasibility.py     quarter vs semester statistical feasibility
src/text_cleaning.py         text normalization (CORRECT — notebook's copy had the bug)
src/nlp_pipeline.py          local/GPU enrichment pipeline
src/dashboard_data_prep.py   real sample -> web/src/data/mockData.js generator
src/dashboard_charts.py      matplotlib charts from the same real sample
notebooks/nlp_pipeline_colab.ipynb        self-contained Colab pipeline (sections 1-10b enrichment, 11-12 dashboard data+charts)
notebooks/exploratory/                    earlier exploratory notebook (unrelated to the pipeline)
outputs/reviews_enriched_sample.parquet   the real 500-row sample (committed)
outputs/dashboard_data_sample.json        computed aggregates from that sample
web/src/data/mockData.js                  now generated, not hand-typed (see §4)
web/README.md                             how to run the web app
reports/RUN_NLP_ON_GPU.md                 how to run the pipeline locally on GPU
```
