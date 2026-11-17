"""Generate SYNTHETIC suppliers and inventory for each store×item.

Uses a FIXED random seed. Assumptions are documented in README.md.
This is NOT real inventory or supplier data — only sales may be from Kaggle.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "supply_chain.db"
SEED = 42

# --- Documented assumptions (see README) ---
N_SUPPLIERS = 8
REGIONS = ["Northeast", "Southeast", "Midwest", "West"]
UNIT_COST_MIN = 2.0
UNIT_COST_MAX = 40.0
LEAD_TIME_CHOICES = [3, 5, 7, 10, 14]
ON_HAND_DAYS_MIN = 3
ON_HAND_DAYS_MAX = 21


def _supplier_rows(rng: np.random.Generator) -> list[tuple[int, str, str]]:
    rows = []
    for i in range(1, N_SUPPLIERS + 1):
        region = REGIONS[(i - 1) % len(REGIONS)]
        rows.append((i, f"Supplier-{i:02d}", region))
    return rows


def generate_inventory(conn: sqlite3.Connection, seed: int = SEED) -> tuple[int, int]:
    """Populate suppliers + inventory tables. Returns (n_suppliers, n_inventory)."""
    rng = np.random.default_rng(seed)

    pairs = pd.read_sql_query(
        "SELECT DISTINCT store, item FROM sales ORDER BY store, item",
        conn,
    )
    if pairs.empty:
        raise ValueError("No sales rows found; load train.csv before synthesizing inventory")

    # Mean daily sales used to scale on-hand (synthetic coverage days × demand)
    demand = pd.read_sql_query(
        """
        SELECT store, item, AVG(sales) AS avg_daily_sales
        FROM sales
        GROUP BY store, item
        """,
        conn,
    )
    demand = demand.merge(pairs, on=["store", "item"], how="right")
    demand["avg_daily_sales"] = demand["avg_daily_sales"].fillna(1.0).clip(lower=0.5)

    suppliers = _supplier_rows(rng)
    conn.execute("DELETE FROM inventory")
    conn.execute("DELETE FROM suppliers")
    conn.executemany(
        "INSERT INTO suppliers (supplier_id, name, region) VALUES (?, ?, ?)",
        suppliers,
    )

    inv_rows: list[tuple[int, int, int, float, int, int]] = []
    for row in demand.itertuples(index=False):
        store = int(row.store)
        item = int(row.item)
        # Deterministic assignment: item maps to a supplier bucket
        supplier_id = int(((item - 1) % N_SUPPLIERS) + 1)
        unit_cost = float(rng.uniform(UNIT_COST_MIN, UNIT_COST_MAX))
        lead_time = int(rng.choice(LEAD_TIME_CHOICES))
        cover_days = float(rng.uniform(ON_HAND_DAYS_MIN, ON_HAND_DAYS_MAX))
        on_hand = max(0, int(round(float(row.avg_daily_sales) * cover_days)))
        inv_rows.append((store, item, supplier_id, round(unit_cost, 2), lead_time, on_hand))

    conn.executemany(
        """
        INSERT INTO inventory (store, item, supplier_id, unit_cost, lead_time_days, on_hand)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        inv_rows,
    )
    conn.commit()
    return len(suppliers), len(inv_rows)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Synthesize inventory/suppliers into SQLite")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)

    if not args.db.is_file():
        raise SystemExit(f"Database not found: {args.db}. Run load_data.py first.")

    conn = sqlite3.connect(args.db)
    try:
        n_sup, n_inv = generate_inventory(conn, seed=args.seed)
        print(f"Seed={args.seed}")
        print(f"Inserted {n_sup} synthetic suppliers, {n_inv} synthetic inventory rows")
        for table in ("suppliers", "inventory", "sales"):
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {n:,} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
