"""
setup_database.py
Load Brazilian E-Commerce CSVs into SQLite database for SQL analysis.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "dataset"
DB_PATH = Path(__file__).parent / "ecommerce.db"

# CSV file → table name mapping
TABLES = {
    "olist_customers_dataset.csv":              "customers",
    "olist_orders_dataset.csv":                 "orders",
    "olist_order_items_dataset.csv":            "order_items",
    "olist_order_payments_dataset.csv":         "order_payments",
    "olist_order_reviews_dataset.csv":          "order_reviews",
    "olist_products_dataset.csv":               "products",
    "olist_sellers_dataset.csv":                "sellers",
    "olist_geolocation_dataset.csv":            "geolocation",
    "product_category_name_translation.csv":    "category_translation",
}

# Columns to parse as datetime
DATETIME_COLS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_reviews": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}


def load_csv_to_sqlite():
    """Load all CSVs into SQLite, create indexes."""
    # Remove old DB if exists
    if DB_PATH.exists():
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))

    for csv_file, table_name in TABLES.items():
        csv_path = DATA_DIR / csv_file
        if not csv_path.exists():
            print(f"WARNING: {csv_file} not found, skipping.")
            continue

        print(f"Loading {csv_file} -> {table_name}...", end=" ")

        # Read CSV
        df = pd.read_csv(csv_path, encoding="utf-8")

        # Parse datetime columns if applicable
        if table_name in DATETIME_COLS:
            for col in DATETIME_COLS[table_name]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        # Write to SQLite
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"{len(df):,} rows")

    # Create indexes for fast JOINs
    print("\nCreating indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_seller ON order_items(seller_id)",
        "CREATE INDEX IF NOT EXISTS idx_payments_order ON order_payments(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_order ON order_reviews(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(product_category_name)",
        "CREATE INDEX IF NOT EXISTS idx_customers_state ON customers(customer_state)",
        "CREATE INDEX IF NOT EXISTS idx_geolocation_zip ON geolocation(geolocation_zip_code_prefix)",
    ]
    for idx_sql in indexes:
        conn.execute(idx_sql)
    conn.commit()
    print("Indexes created.")

    # Validate
    print("\n--- Table Summary ---")
    cursor = conn.cursor()
    for table_name in TABLES.values():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name:30s} {count:>10,} rows")
        except sqlite3.OperationalError:
            print(f"  {table_name:30s} NOT LOADED")

    conn.close()
    print(f"\nDatabase saved to: {DB_PATH}")


if __name__ == "__main__":
    load_csv_to_sqlite()
