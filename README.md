# Supply Chain Ops Copilot

**Status: in progress** — building day by day; full agent evals are not marked passing until you run them with a real DB + `ANTHROPIC_API_KEY`.

Plain-English supply chain questions → Claude API agent (tool use) → SQLite queries, demand forecast, budget-constrained reorder optimization, Excel export.

MVP surface: **FastAPI endpoints only** (no UI).

## Data story (read this)

- **Sales:** from the [Kaggle Store Item Demand Forecasting Challenge](https://www.kaggle.com/c/demand-forecasting-kernels-only) (`train.csv`) when you download it.
- **Inventory, suppliers, unit cost, lead time, on-hand:** **synthetic**, generated with a fixed random seed. They are layered on top of real sales so we can demo planning workflows.
- Never claim inventory or supplier data is real.

CI and unit tests use `tests/fixtures/sample_train.csv` only (a few stores/items/days). That fixture is **not** the Kaggle dataset.

## Architecture

```
question → FastAPI /ask → Claude agent
              ├─ run_sql          → SQLite (mode=ro, SELECT-only)
              ├─ forecast_demand  → lag-7 seasonal / seasonal-level model
              ├─ optimize_reorder → PuLP budget ILP
              └─ export_excel     → openpyxl .xlsx
```

Data path today:
- `load_data.py` loads Kaggle sales into SQLite
- `synth_inventory.py` fills synthetic suppliers + inventory (seed=42)

## Setup (Windows)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Python **≥ 3.11**.

Optional for the agent later:
```bat
set ANTHROPIC_API_KEY=sk-ant-...
```

## Download sales data (Kaggle)

```bat
pip install kaggle
kaggle competitions download -c demand-forecasting-kernels-only -p data/
tar -xf data\demand-forecasting-kernels-only.zip -C data
```

Expect `data\train.csv`. Requires `%USERPROFILE%\.kaggle\kaggle.json`.

If `data\train.csv` is missing, `sc-load` exits with instructions — it will **not** invent a fake full Kaggle dump.

## Load + synthesize

```bat
sc-load          # → data/supply_chain.db , prints row counts
sc-synth         # seed=42 synthetic suppliers + inventory
```

`data/` and `*.db` are gitignored — do not push them.

## Forecast backtest (later day)

```bat
sc-backtest --max-series 20
sc-backtest --store 1 --item 1
```

Metrics printed are **live WAPE / RMSE** from the run. Do not invent accuracy numbers.

**Baseline:** seasonal-naive with **lag-7** (same weekday).  
**Holdout:** last **13 weeks** only, time-ordered. No random splits.

## Reorder optimization (later day)

```bat
sc-optimize --budget 5000 --limit 50
```

- **Objective:** maximize units ordered toward unmet forecast demand.
- **Constraints:** total cost ≤ budget; integer quantities.
- Uses **synthetic** on-hand / unit cost / lead time.

## API (later day)

```bat
set SUPPLY_CHAIN_DB=data\supply_chain.db
sc-api
```

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness + db/key flags |
| POST | `/ask` | Agent (needs `ANTHROPIC_API_KEY`) |
| POST | `/forecast` | Direct forecast (no LLM) |
| POST | `/optimize` | Direct reorder plan (no LLM) |
| POST | `/export` | Write Excel plan (no LLM) |

## Evals (later day)

```bat
sc-evals
sc-evals --live-agent
```

## Tests & CI (later day)

```bat
pytest -q
```

## Docker (later day)

```bat
docker build -t supply-chain-copilot .
docker run --rm -p 8741:8741 -e ANTHROPIC_API_KEY -v "%CD%/data:/app/data" supply-chain-copilot
```

## Synthetic inventory assumptions

Documented for interview honesty. All generated in `synth_inventory.py` with **seed = 42**:

| Assumption | Value / rule |
|------------|----------------|
| RNG seed | `42` (fixed) |
| Suppliers | 8 (`Supplier-01` … `Supplier-08`) |
| Regions | Northeast, Southeast, Midwest, West (round-robin) |
| Supplier assignment | `supplier_id = ((item - 1) % 8) + 1` |
| Unit cost | Uniform draw in `[2.0, 40.0]`, rounded to 2 decimals |
| Lead time (days) | Choice from `{3, 5, 7, 10, 14}` |
| On-hand | `round(avg_daily_sales × cover_days)` with `cover_days ~ U(3, 21)` |
| Avg daily sales | Mean of historical `sales` for that store×item (floor 0.5) |

These are **not** real warehouse snapshots.

## Project layout

```
README.md, .gitignore, pyproject.toml
data/                 # gitignored (train.csv, *.db, exports)
src/db/               # schema, load, synth
src/forecast/         # baseline, model, backtest (later)
src/optimize/         # reorder PuLP (later)
src/agent/            # tools, agent loop (later)
src/api/              # FastAPI (later)
evals/                # questions + harness (later)
tests/                # pytest + fixtures
.github/workflows/    # CI (later)
Dockerfile            # later
```

## What still needs you

1. Keep shipping one honest learned slice per day.
2. Own every GitHub commit.
3. Keep Status **in progress** until live evals pass.
