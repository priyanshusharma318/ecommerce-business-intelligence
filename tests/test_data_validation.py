"""
Tests for data validation, missing file detection, referential integrity,
and SQL schema compliance.
"""

import pytest
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

from src.data_loader import DataLoader
from src.data_cleaning import DataCleaner
from src.config import SQL_DIR


def test_data_loader_missing_files_detection(tmp_path):
    loader = DataLoader(raw_data_dir=tmp_path)
    # Since tmp_path is empty, is_dataset_ready should be False
    assert not loader.is_dataset_ready()
    missing = loader.get_missing_files()
    assert len(missing) == 9

    # Create one mock file
    (tmp_path / "olist_orders_dataset.csv").touch()
    assert len(loader.get_missing_files()) == 8


def test_referential_integrity_audit():
    cleaner = DataCleaner()

    # Create intentional foreign key violations
    orders_df = pd.DataFrame({"order_id": ["o1", "o2"], "customer_id": ["c1", "c999_missing"]})
    customers_df = pd.DataFrame({"customer_id": ["c1"]})
    items_df = pd.DataFrame({
        "order_id": ["o1", "o888_missing"],
        "product_id": ["p1", "p777_missing"],
        "seller_id": ["s1", "s666_missing"],
    })
    products_df = pd.DataFrame({"product_id": ["p1"]})
    sellers_df = pd.DataFrame({"seller_id": ["s1"]})

    data_bundle = {
        "orders": orders_df,
        "customers": customers_df,
        "order_items": items_df,
        "products": products_df,
        "sellers": sellers_df,
    }

    violations = cleaner.validate_referential_integrity(data_bundle)

    assert violations["orders_to_customers_orphans"] == 1
    assert violations["items_to_orders_orphans"] == 1
    assert violations["items_to_products_orphans"] == 1
    assert violations["items_to_sellers_orphans"] == 1


def test_sql_schema_syntax_and_tables_creation():
    """Verify that 01_database_schema.sql executes cleanly and creates expected tables."""
    schema_path = SQL_DIR / "01_database_schema.sql"
    assert schema_path.is_file(), "Schema file must exist"

    # Use an in-memory SQLite engine to test DDL statements
    engine = create_engine("sqlite:///:memory:")

    with open(schema_path, "r", encoding="utf-8") as f:
        ddl_text = f.read()

    statements = [stmt.strip() for stmt in ddl_text.split(";") if stmt.strip()]

    with engine.begin() as conn:
        for stmt in statements:
            if stmt.upper().startswith("CREATE SCHEMA") or stmt.upper().startswith("SET "):
                continue
            conn.execute(text(stmt))

    # Assert created tables in database
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result.fetchall()]

    expected_tables = [
        "product_category_translation", "geolocation", "customers", "products",
        "sellers", "orders", "order_items", "order_payments", "order_reviews",
        "dim_date", "dim_customer", "dim_product", "dim_seller", "dim_geography", "fact_sales"
    ]
    for tbl in expected_tables:
        assert tbl in tables, f"Expected table '{tbl}' was not found in schema"
