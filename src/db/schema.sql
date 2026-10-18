-- Supply Chain Ops Copilot schema
-- sales: real Kaggle Store Item Demand Forecasting rows (when loaded)
-- suppliers / inventory: SYNTHETIC (seeded); never treat as real ops data

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sales (
    date TEXT NOT NULL,
    store INTEGER NOT NULL,
    item INTEGER NOT NULL,
    sales INTEGER NOT NULL,
    PRIMARY KEY (date, store, item)
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
    store INTEGER NOT NULL,
    item INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    unit_cost REAL NOT NULL,
    lead_time_days INTEGER NOT NULL,
    on_hand INTEGER NOT NULL,
    PRIMARY KEY (store, item),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE INDEX IF NOT EXISTS idx_sales_store_item_date ON sales (store, item, date);
CREATE INDEX IF NOT EXISTS idx_inventory_supplier ON inventory (supplier_id);
