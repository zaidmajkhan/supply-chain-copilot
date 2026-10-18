# Component explainers

Short interview notes: what each piece does, why it exists, and one alternative we rejected.

## DB load (`src/db/load_data.py`)

Loads Kaggle `train.csv` into SQLite with a clear schema and prints row counts. We keep the database under `data/` so large files stay gitignored. Rejected stuffing a fake full Kaggle dump into the repo — CI uses a tiny fixture CSV instead.

## Synthetic inventory (`src/db/synth_inventory.py`)

Generates suppliers, unit cost, lead time, and on-hand for every store×item with a **fixed seed (42)** so demos are reproducible. Needed because the Kaggle set is sales-only. Rejected random unseeded synth — interviewers cannot reproduce results.

## Forecast baseline + model (`src/forecast/`)

Seasonal-naive **lag-7** (weekday seasonality on daily data) plus a slightly better seasonal×moving-average blend. Holdout is the **last 13 weeks**, time-ordered only. Metrics are **WAPE and RMSE** (never MAPE). Rejected random train/test splits and MAPE (blows up near zeros).

## Reorder optimization (`src/optimize/reorder.py`)

PuLP ILP: maximize units ordered toward forecast gap subject to a budget and `order_qty ≤ need`. Interview-explainable CBC solve. Rejected OR-Tools for this MVP (heavier install; PuLP is enough for a budget knapsack-style reorder).

## Agent (`src/agent/`)

Claude tool-use loop with four tools: `run_sql`, `forecast_demand`, `optimize_reorder`, `export_excel`. SQL is URI `mode=ro` plus keyword guards. System prompt forces data honesty (synthetic inventory). Rejected letting the model invent numbers without tools.

## API (`src/api/main.py`)

FastAPI MVP: `/health`, `/ask`, plus direct `/forecast`, `/optimize`, `/export` for testing without the LLM. Missing `ANTHROPIC_API_KEY` returns HTTP 400 with a clear message. Rejected building a UI for the portfolio slice — endpoints demonstrate the full path.

## Evals (`evals/`)

30+ questions with `tools_expected` and fixture SQL `expected` rows where computable. Live agent scoring is opt-in (`--live-agent`) and needs an API key. Rejected hardcoding fake agent accuracy in the README.

## CI (`.github/workflows/ci.yml`)

Install + pytest on push/PR with no API key and no Kaggle file. Keeps the portfolio honest: structural correctness is gated; model quality is measured when you run evals locally.
