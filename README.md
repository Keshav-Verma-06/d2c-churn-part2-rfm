# Part 2 Repository — RFM Segmentation & Retention Strategy

**Part 2 Repository. Independent and runnable. Uses only pre-snapshot data (≤ 2025-09-30).**

D2C personal-care brand capstone: customer segmentation with RFM + behavioral signals, retention actions, and budget prioritization (no ML required).

## Snapshot & leakage guardrails

| Rule | Detail |
|------|--------|
| Snapshot date | `2025-09-30` |
| Orders in features | `order_date <= 2025-09-30` only |
| Tickets in features | `ticket_date <= 2025-09-30` only |
| Excluded | Post-snapshot orders, `_DUP` order rows, `churn_next_60d` as a segment input |

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## How to run

```bash
jupyter notebook rfm_segmentation.ipynb
```

The notebook **does not import matplotlib** in the Jupyter kernel. After `segments.csv` is saved, it runs `make_charts.py` with `.venv\Scripts\python.exe` (avoids a broken Anaconda matplotlib install).

Or run everything from the venv:

```bash
.venv\Scripts\python.exe rfm_pipeline.py
.venv\Scripts\python.exe make_charts.py
```

## File structure

| File | Description |
|------|-------------|
| `rfm_segmentation.ipynb` | Main analysis (Phases 1–5, validation) |
| `rfm_pipeline.py` | Scriptable pipeline (same logic as notebook) |
| `make_charts.py` | Builds PNGs in `charts/` (run with `.venv` Python) |
| `segments.csv` | CRM-ready: `customer_id`, `segment_name`, RFM + behavioral columns (2,400 rows) |
| `retention_strategy.md` | Per-segment actions + 500-customer budget plan |
| `manual_review_cases.md` | 10 edge-case customer IDs with reasoning |
| `charts/` | `churn_by_segment.png`, `monetary_by_segment.png`, `recency_frequency_scatter.png` |
| `*.csv` | Provided capstone datasets |

## Segments found (this run)

| Segment | Customers | Churn rate (60d) |
|---------|----------:|------------------:|
| Loyal Customers | 1,429 | 36% |
| At-Risk | 311 | 71% |
| Dormant | 302 | 91% |
| Discount-Sensitive | 189 | 58% |
| Champions | 132 | 5% |
| High-Value Unhappy | 37 | 5% |

**Top retention recommendation:** Prioritize **At-Risk** customers (recency > 129 days, prior frequency ≥ 2) with win-back + free shipping before spending on **Dormant** (91% churn, ₹0 recent spend).

`segments.csv` is **CRM-ready output** — import into your retention tool with `customer_id` as the key.

## Deliverables checklist (rubric)

- [x] `rfm_segmentation.ipynb`
- [x] `segments.csv` (2,400 rows, required columns)
- [x] `retention_strategy.md`
- [x] `manual_review_cases.md` (10 customer IDs)
- [x] ≥3 charts in `charts/`
- [x] `README.md` + `requirements.txt`

## GitHub push (Phase 9)

```bash
git init
git add .
git commit -m "Part 2: RFM Segmentation & Retention Strategy complete"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

Replace `<your-github-repo-url>` with your public repository URL.
