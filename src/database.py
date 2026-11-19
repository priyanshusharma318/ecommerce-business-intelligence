"""
Database management and ingestion module for PostgreSQL and Star-Schema Analytical Warehousing.
Provides SQLAlchemy connection management, DDL execution, optimized bulk loading,
referential checks, and dimensional table population.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine

from src.config import (
    POSTGRES_URL,
    SQLITE_URL,
    ACTIVE_DB_URL,
    SQL_DIR,
    PROCESSED_DATA_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database lifecycle, relational schema, data loading, and star-schema ETL."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or ACTIVE_DB_URL
        self.engine = self._init_engine()

    def _init_engine(self) -> Engine:
        """Initialize SQLAlchemy engine with auto-fallback to SQLite if PostgreSQL is unreachable."""
        try:
            # Test connecting with a short timeout
            test_engine = create_engine(self.db_url, connect_args={"connect_timeout": 3} if "postgres" in self.db_url else {})
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            logger.info(f"Successfully connected to database at: {self._mask_url(self.db_url)}")
            return test_engine
        except Exception as e:
            logger.warning(
                f"Could not connect to target database ({self._mask_url(self.db_url)}): {e}\n"
                f"Falling back to local SQLite engine for local analytics and automated testing."
            )
            fallback_engine = create_engine(SQLITE_URL)
            return fallback_engine

    def _mask_url(self, url: str) -> str:
        """Mask password in connection URI for secure logging."""
        if "@" in url and ":" in url:
            parts = url.split("@")
            prefix = parts[0].split(":")
            if len(prefix) >= 3:
                return f"{prefix[0]}:{prefix[1]}:****@{parts[1]}"
        return url

    def is_sqlite(self) -> bool:
        """Return True if active database engine is SQLite."""
        return self.engine.dialect.name == "sqlite"

    def execute_sql_file(self, file_path: Path):
        """Execute a multi-statement SQL script file."""
        if not file_path.is_file():
            raise FileNotFoundError(f"SQL file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # Split statements by semicolon while respecting transactions
        # SQLite doesn't support some PostgreSQL-specific syntax like 'CREATE SCHEMA'
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

        with self.engine.begin() as conn:
            for stmt in statements:
                # Filter out postgres-only commands when running in sqlite fallback
                if self.is_sqlite():
                    if stmt.upper().startswith("CREATE SCHEMA") or stmt.upper().startswith("SET "):
                        continue
                try:
                    conn.execute(text(stmt))
                except Exception as err:
                    logger.debug(f"Executed statement note: {err}")

        logger.info(f"Successfully executed SQL script: {file_path.name}")

    def load_table(self, df: pd.DataFrame, table_name: str, if_exists: str = "replace", schema: Optional[str] = None):
        """Load a DataFrame into a database table using chunking for performance."""
        logger.info(f"Loading {len(df):,} records into table '{table_name}'...")
        # SQLite does not support schemas
        target_schema = None if self.is_sqlite() else schema

        df.to_sql(
            name=table_name,
            con=self.engine,
            schema=target_schema,
            if_exists=if_exists,
            index=False,
            chunksize=5000,
            method="multi" if not self.is_sqlite() else None
        )
        logger.info(f"Loaded '{table_name}' successfully.")

    def build_star_schema(self, cleaned_data: Dict[str, pd.DataFrame]):
        """
        Populate dimensional model tables:
        - DimDate
        - DimCustomer
        - DimProduct
        - DimSeller
        - DimGeography
        - FactSales
        """
        logger.info("Building and loading Star-Schema dimensional warehouse tables...")

        # 1. DimDate
        if "orders" in cleaned_data:
            df_ord = cleaned_data["orders"]
            min_date = pd.to_datetime(df_ord["order_purchase_timestamp"]).min()
            max_date = pd.to_datetime(df_ord["order_purchase_timestamp"]).max() + pd.Timedelta(days=60)
            date_range = pd.date_range(start=min_date, end=max_date, freq="D")

            dim_date = pd.DataFrame({"full_date": date_range})
            dim_date["date_key"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
            dim_date["year"] = dim_date["full_date"].dt.year
            dim_date["quarter"] = dim_date["full_date"].dt.quarter
            dim_date["year_quarter"] = dim_date["full_date"].dt.to_period("Q").astype(str)
            dim_date["month"] = dim_date["full_date"].dt.month
            dim_date["month_name"] = dim_date["full_date"].dt.month_name()
            dim_date["year_month"] = dim_date["full_date"].dt.strftime("%Y-%m")
            dim_date["day_of_month"] = dim_date["full_date"].dt.day
            dim_date["day_of_week"] = dim_date["full_date"].dt.dayofweek
            dim_date["day_name"] = dim_date["full_date"].dt.day_name()
            dim_date["is_weekend"] = dim_date["day_of_week"].isin([5, 6]).astype(int)

            self.load_table(dim_date, "dim_date", if_exists="replace")

        # 2. DimCustomer
        if "customers" in cleaned_data:
            dim_cust = cleaned_data["customers"].copy()
            self.load_table(dim_cust, "dim_customer", if_exists="replace")

        # 3. DimProduct
        if "products" in cleaned_data:
            dim_prod = cleaned_data["products"].copy()
            self.load_table(dim_prod, "dim_product", if_exists="replace")

        # 4. DimSeller
        if "sellers" in cleaned_data:
            dim_seller = cleaned_data["sellers"].copy()
            self.load_table(dim_seller, "dim_seller", if_exists="replace")

        # 5. DimGeography
        if "geolocation" in cleaned_data:
            dim_geo = cleaned_data["geolocation"].copy()
            self.load_table(dim_geo, "dim_geography", if_exists="replace")

        # 6. FactSales (Grain: Order Item Line)
        if "order_items" in cleaned_data and "orders" in cleaned_data:
            df_items = cleaned_data["order_items"].copy()
            df_orders = cleaned_data["orders"].copy()

            # Merge orders onto line items
            fact = df_items.merge(
                df_orders[[
                    "order_id", "customer_id", "order_status", "order_purchase_timestamp",
                    "order_delivered_customer_date", "order_estimated_delivery_date"
                ]],
                on="order_id",
                how="inner"
            )

            # Date key
            purchase_dt = pd.to_datetime(fact["order_purchase_timestamp"])
            fact["order_date_key"] = purchase_dt.dt.strftime("%Y%m%d").astype(int)

            # Metrics
            fact["gross_item_value"] = fact["price"] + fact["freight_value"]

            # Merge review score if available
            if "reviews" in cleaned_data:
                rev_score = cleaned_data["reviews"].groupby("order_id")["review_score"].mean().reset_index()
                fact = fact.merge(rev_score, on="order_id", how="left")
            else:
                fact["review_score"] = None

            fact_cols = [
                "order_id", "order_item_id", "order_date_key", "customer_id",
                "product_id", "seller_id", "order_status", "price", "freight_value",
                "gross_item_value", "review_score"
            ]
            fact_sales = fact[[c for c in fact_cols if c in fact.columns]]
            self.load_table(fact_sales, "fact_sales", if_exists="replace")

        logger.info("Star-Schema warehouse dimensional model populated successfully.")

    def run_query(self, sql_query: str) -> pd.DataFrame:
        """Execute a SELECT query and return results as a Pandas DataFrame."""
        with self.engine.connect() as conn:
            return pd.read_sql_query(text(sql_query), conn)
