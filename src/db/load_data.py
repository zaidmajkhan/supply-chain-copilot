"""Load Kaggle Store Item Demand Forecasting train.csv into SQLite.

Expects data/train.csv with columns: date, store, item, sales.
Creates data/supply_chain.db and prints row counts per table.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "data" / "train.csv"
DEFAULT_DB = ROOT / "data" / "supply_chain.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

DOWNLOAD_HELP = """
data/train.csv not found.

Download the Kaggle Store Item Demand Forecasting Challenge training file:

  1. Install Kaggle CLI and place credentials in ~/.kaggle/kaggle.json
  2. Run:
       kaggle competitions download -c demand-forecasting-kernels-only -p data/
       unzip -o data/demand-forecasting-kernels-only.zip -d data/
  3. Ensure data/train.csv exists, then re-run this script.

Or download train.csv manually from the competition page and place it at data/train.csv.

Tests use tests/fixtures/sample_train.csv only — they do not require the full Kaggle file.
""".strip()


def resolve_paths(csv_path: Path | None, db_path: Path | None) -> tuple[Path, Path]:
    return (csv_path or DEFAULT_CSV), (db_path or DEFAULT_DB)


def create_schema(conn: sqlite3.Connection) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()


def load_sales(conn: sqlite3.Connection, csv_path: Path, chunksize: int = 100_000) -> int:
    conn.execute("DELETE FROM sales")
    total = 0
    for chunk in pd.read_csv(csv_path, chunksize=chunksize):
        required = {"date", "store", "item", "sales"}
        missing = required - set(chunk.columns)
        if missing:
            raise ValueError(f"CSV missing columns: {sorted(missing)}")
        chunk = chunk[["date", "store", "item", "sales"]].copy()
        chunk["date"] = pd.to_datetime(chunk["date"]).dt.strftime("%Y-%m-%d")
        chunk.to_sql("sales", conn, if_exists="append", index=False)
        total += len(chunk)
    conn.commit()
    return total


def print_row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    for (name,) in tables:
        n = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        counts[name] = n
        print(f"  {name}: {n:,} rows")
    return counts


def load_database(csv_path: Path, db_path: Path) -> dict[str, int]:
    if not csv_path.is_file():
        print(DOWNLOAD_HELP, file=sys.stderr)
        raise SystemExit(1)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        n_sales = load_sales(conn, csv_path)
        print(f"Loaded {n_sales:,} sales rows from {csv_path}")
        print("Row counts:")
        return print_row_counts(conn)
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Load train.csv into SQLite")
    parser.add_argument("--csv", type=Path, default=None, help="Path to train.csv")
    parser.add_argument("--db", type=Path, default=None, help="Output SQLite path")
    args = parser.parse_args(argv)
    csv_path, db_path = resolve_paths(args.csv, args.db)
    load_database(csv_path, db_path)
    print(f"Database written to {db_path}")


if __name__ == "__main__":
    main()
