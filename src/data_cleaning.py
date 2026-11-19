"""
Data cleaning and validation module for the E-Commerce BI Platform.
Implements robust, reproducible data cleaning pipelines, text normalization,
category translation, key validation, duplicate handling, and data quality logging.
"""

import logging
from pathlib import Path
from typing import Dict, Tuple, Optional
import pandas as pd
import numpy as np

from src.config import PROCESSED_DATA_DIR, REPORTS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Translation overrides for categories missing in the original Olist translation file
CATEGORY_TRANSLATION_OVERRIDES = {
    "portateis_cozinha_e_preparadores_de_alimentos": "small_appliances_and_food_preparers",
    "pc_gamer": "pc_gamer",
    "moveis_colchao_e_estofado": "furniture_mattress_and_upholstery",
}


class DataCleaner:
    """Executes systematic cleaning, type casting, key integrity validation, and normalization."""

    def __init__(self, processed_data_dir: Path = PROCESSED_DATA_DIR):
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.quality_log = []

    def log_operation(self, table: str, operation: str, details: str, count_affected: int = 0):
        """Append a record to the data quality audit log."""
        entry = {
            "table": table,
            "operation": operation,
            "details": details,
            "count_affected": int(count_affected),
        }
        self.quality_log.append(entry)
        logger.info(f"[{table}] {operation}: {details} (Affected: {count_affected})")

    # -------------------------------------------------------------------------
    # 1. Orders Cleaning
    # -------------------------------------------------------------------------
    def clean_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean orders table: type cast timestamps, validate status, check duplicates."""
        initial_count = len(df)
        df_clean = df.copy()

        # Remove duplicate order_ids if any
        dup_count = df_clean.duplicated(subset=["order_id"]).sum()
        if dup_count > 0:
            df_clean = df_clean.drop_duplicates(subset=["order_id"], keep="first")
            self.log_operation("orders", "Deduplication", "Removed duplicate order_id records", dup_count)

        # Standardize text
        df_clean["order_status"] = df_clean["order_status"].astype(str).str.strip().str.lower()

        # Convert timestamps
        date_cols = [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
        for col in date_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_datetime(df_clean[col], errors="coerce")

        # Document missing delivered dates
        null_delivered = df_clean["order_delivered_customer_date"].isnull().sum()
        self.log_operation(
            "orders",
            "Missing Value Audit",
            "Identified orders without customer delivery timestamp (cancelled, in-transit, or processing)",
            null_delivered
        )

        # Retain valid order records
        self.log_operation("orders", "Cleaning Completed", f"Cleaned {len(df_clean)} of {initial_count} records", 0)
        return df_clean

    # -------------------------------------------------------------------------
    # 2. Customers Cleaning
    # -------------------------------------------------------------------------
    def clean_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean customers table: normalize text, deduplicate, validate zip codes."""
        initial_count = len(df)
        df_clean = df.copy()

        # Remove exact duplicate customer_ids
        dup_count = df_clean.duplicated(subset=["customer_id"]).sum()
        if dup_count > 0:
            df_clean = df_clean.drop_duplicates(subset=["customer_id"], keep="first")
            self.log_operation("customers", "Deduplication", "Removed duplicate customer_id rows", dup_count)

        # Normalize text
        df_clean["customer_city"] = df_clean["customer_city"].astype(str).str.strip().str.lower()
        df_clean["customer_state"] = df_clean["customer_state"].astype(str).str.strip().str.upper()

        # Format zip code prefix as 5-character zero-padded string
        df_clean["customer_zip_code_prefix"] = (
            df_clean["customer_zip_code_prefix"].astype(str).str.split(".").str[0].str.zfill(5)
        )

        self.log_operation("customers", "Cleaning Completed", f"Processed {len(df_clean)} records", 0)
        return df_clean

    # -------------------------------------------------------------------------
    # 3. Products Cleaning & Translation
    # -------------------------------------------------------------------------
    def clean_products(
        self, df_prod: pd.DataFrame, df_trans: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Clean products, normalize categories, handle null specs, and merge English translations."""
        df_clean = df_prod.copy()

        # Deduplicate product_id
        dup_count = df_clean.duplicated(subset=["product_id"]).sum()
        if dup_count > 0:
            df_clean = df_clean.drop_duplicates(subset=["product_id"], keep="first")
            self.log_operation("products", "Deduplication", "Removed duplicate product_ids", dup_count)

        # Handle null category names
        null_cat = df_clean["product_category_name"].isnull().sum()
        df_clean["product_category_name"] = df_clean["product_category_name"].fillna("outros")
        self.log_operation("products", "Null Imputation", "Imputed missing category names as 'outros'", null_cat)

        # Build translation dictionary
        trans_dict = {}
        if df_trans is not None and not df_trans.empty:
            trans_dict = dict(zip(
                df_trans["product_category_name"].astype(str).str.strip().str.lower(),
                df_trans["product_category_name_english"].astype(str).str.strip().str.lower()
            ))

        # Add manual overrides
        trans_dict.update(CATEGORY_TRANSLATION_OVERRIDES)
        trans_dict["outros"] = "other_unspecified"

        # Apply translation with fallback to clean Portuguese name
        def map_category(cat):
            cat_norm = str(cat).strip().lower()
            return trans_dict.get(cat_norm, cat_norm)

        df_clean["product_category_name_english"] = df_clean["product_category_name"].apply(map_category)

        # Numeric dimensions imputation with median values where missing
        numeric_cols = [
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]
        for col in numeric_cols:
            if col in df_clean.columns:
                col_nulls = df_clean[col].isnull().sum()
                if col_nulls > 0:
                    median_val = df_clean[col].median()
                    df_clean[col] = df_clean[col].fillna(median_val)
                    self.log_operation("products", "Median Imputation", f"Imputed nulls in {col} with median {median_val}", col_nulls)

        self.log_operation("products", "Cleaning Completed", f"Cleaned {len(df_clean)} products", 0)
        return df_clean

    # -------------------------------------------------------------------------
    # 4. Sellers Cleaning
    # -------------------------------------------------------------------------
    def clean_sellers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean sellers: standardize city/state and zip codes."""
        df_clean = df.copy()
        dup_count = df_clean.duplicated(subset=["seller_id"]).sum()
        if dup_count > 0:
            df_clean = df_clean.drop_duplicates(subset=["seller_id"], keep="first")
            self.log_operation("sellers", "Deduplication", "Removed duplicate seller_ids", dup_count)

        df_clean["seller_city"] = df_clean["seller_city"].astype(str).str.strip().str.lower()
        df_clean["seller_state"] = df_clean["seller_state"].astype(str).str.strip().str.upper()
        df_clean["seller_zip_code_prefix"] = (
            df_clean["seller_zip_code_prefix"].astype(str).str.split(".").str[0].str.zfill(5)
        )

        self.log_operation("sellers", "Cleaning Completed", f"Cleaned {len(df_clean)} sellers", 0)
        return df_clean

    # -------------------------------------------------------------------------
    # 5. Order Items Cleaning
    # -------------------------------------------------------------------------
    def clean_order_items(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean line items: ensure positive price, freight, valid shipping limits."""
        df_clean = df.copy()

        # Remove duplicate line items (order_id + order_item_id)
        dup_count = df_clean.duplicated(subset=["order_id", "order_item_id"]).sum()
        if dup_count > 0:
            df_clean = df_clean.drop_duplicates(subset=["order_id", "order_item_id"], keep="first")
            self.log_operation("order_items", "Deduplication", "Removed duplicate order items", dup_count)

        # Datetime conversion
        if "shipping_limit_date" in df_clean.columns:
            df_clean["shipping_limit_date"] = pd.to_datetime(df_clean["shipping_limit_date"], errors="coerce")

        # Validate price and freight
        invalid_price = (df_clean["price"] <= 0).sum()
        if invalid_price > 0:
            # We filter out non-positive prices as genuine invalid catalog corruptions
            df_clean = df_clean[df_clean["price"] > 0]
            self.log_operation("order_items", "Invalid Value Removal", "Filtered line items with price <= 0", invalid_price)

        # Non-negative freight validation
        df_clean["freight_value"] = df_clean["freight_value"].clip(lower=0.0)

        self.log_operation("order_items", "Cleaning Completed", f"Cleaned {len(df_clean)} line items", 0)
        return df_clean

    # -------------------------------------------------------------------------
    # 6. Payments Cleaning
    # -------------------------------------------------------------------------
    def clean_payments(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean payments: handle payment methods, non-negative values, installments."""
        df_clean = df.copy()

        # Normalize payment type
        df_clean["payment_type"] = df_clean["payment_type"].astype(str).str.strip().str.lower()
        # Filter out rare 'not_defined' test records with 0 payment value
        invalid_mask = (df_clean["payment_type"] == "not_defined") | (df_clean["payment_value"] <= 0)
        invalid_count = invalid_mask.sum()
        if invalid_count > 0:
            df_clean = df_clean[~invalid_mask]
            self.log_operation("payments", "Invalid Value Removal", "Filtered payment_type 'not_defined' or payment_value <= 0", invalid_count)

        # Installments minimum clamp to 1
        df_clean["payment_installments"] = df_clean["payment_installments"].clip(lower=1)

        self.log_operation("payments", "Cleaning Completed", f"Cleaned {len(df_clean)} payment records", 0)
        return df_clean

    # -------------------------------------------------------------------------
    # 7. Reviews Cleaning
    # -------------------------------------------------------------------------
    def clean_reviews(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean reviews: deduplicate, bound score 1-5, fill text nulls, format dates."""
        df_clean = df.copy()

        # Handle review timestamps
        df_clean["review_creation_date"] = pd.to_datetime(df_clean["review_creation_date"], errors="coerce")
        df_clean["review_answer_timestamp"] = pd.to_datetime(df_clean["review_answer_timestamp"], errors="coerce")

        # Deduplicate review_id per order_id, preserving the most recent response
        dup_count = df_clean.duplicated(subset=["order_id", "review_id"]).sum()
        if dup_count > 0:
            df_clean = df_clean.sort_values("review_answer_timestamp").drop_duplicates(
                subset=["order_id", "review_id"], keep="last"
            )
            self.log_operation("reviews", "Deduplication", "Resolved duplicate reviews per order", dup_count)

        # Enforce valid review_score range [1, 5]
        df_clean["review_score"] = pd.to_numeric(df_clean["review_score"], errors="coerce").clip(lower=1, upper=5)

        # Impute textual nulls with empty strings
        df_clean["review_comment_title"] = df_clean["review_comment_title"].fillna("").astype(str).str.strip()
        df_clean["review_comment_message"] = df_clean["review_comment_message"].fillna("").astype(str).str.strip()

        self.log_operation("reviews", "Cleaning Completed", f"Cleaned {len(df_clean)} review records", 0)
        return df_clean

    # -------------------------------------------------------------------------
    # 8. Geolocation Cleaning & Aggregation
    # -------------------------------------------------------------------------
    def clean_geolocation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean geolocation data.
        Because raw geolocation contains over 1 million redundant coordinates per zip prefix,
        we aggregate to a clean 1-to-1 geographic lookup table by zip_code_prefix.
        """
        df_clean = df.copy()

        # Standardize prefix and strings
        df_clean["geolocation_zip_code_prefix"] = (
            df_clean["geolocation_zip_code_prefix"].astype(str).str.split(".").str[0].str.zfill(5)
        )
        df_clean["geolocation_city"] = df_clean["geolocation_city"].astype(str).str.strip().str.lower()
        df_clean["geolocation_state"] = df_clean["geolocation_state"].astype(str).str.strip().str.upper()

        # Filter latitude and longitude to valid Brazilian bounding box
        # Latitude: +5.3 to -33.8, Longitude: -34.8 to -73.9
        valid_geo = (
            (df_clean["geolocation_lat"].between(-35.0, 6.0)) &
            (df_clean["geolocation_lng"].between(-75.0, -30.0))
        )
        invalid_geo_count = (~valid_geo).sum()
        if invalid_geo_count > 0:
            df_clean = df_clean[valid_geo]
            self.log_operation("geolocation", "Bounding Box Filter", "Removed coordinates outside Brazilian borders", invalid_geo_count)

        # Aggregate by zip_code_prefix: median latitude & longitude, mode city and state
        agg_geo = df_clean.groupby("geolocation_zip_code_prefix").agg(
            geolocation_lat=("geolocation_lat", "median"),
            geolocation_lng=("geolocation_lng", "median"),
            geolocation_city=("geolocation_city", lambda x: x.mode().iloc[0] if not x.empty else "unknown"),
            geolocation_state=("geolocation_state", lambda x: x.mode().iloc[0] if not x.empty else "unknown"),
        ).reset_index()

        self.log_operation(
            "geolocation",
            "Aggregation to Unique Prefix",
            f"Condensed {len(df)} coordinate points into {len(agg_geo)} unique zip code centroids",
            len(df) - len(agg_geo)
        )
        return agg_geo

    # -------------------------------------------------------------------------
    # 9. Referential Integrity Validation
    # -------------------------------------------------------------------------
    def validate_referential_integrity(self, cleaned_data: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        """Verify foreign key coverage across all core relational dimensions."""
        violations = {}

        # 1. Orders -> Customers
        if "orders" in cleaned_data and "customers" in cleaned_data:
            cust_keys = set(cleaned_data["customers"]["customer_id"])
            orphan_orders = (~cleaned_data["orders"]["customer_id"].isin(cust_keys)).sum()
            violations["orders_to_customers_orphans"] = int(orphan_orders)

        # 2. Order Items -> Orders
        if "order_items" in cleaned_data and "orders" in cleaned_data:
            order_keys = set(cleaned_data["orders"]["order_id"])
            orphan_items = (~cleaned_data["order_items"]["order_id"].isin(order_keys)).sum()
            violations["items_to_orders_orphans"] = int(orphan_items)

        # 3. Order Items -> Products
        if "order_items" in cleaned_data and "products" in cleaned_data:
            prod_keys = set(cleaned_data["products"]["product_id"])
            orphan_products = (~cleaned_data["order_items"]["product_id"].isin(prod_keys)).sum()
            violations["items_to_products_orphans"] = int(orphan_products)

        # 4. Order Items -> Sellers
        if "order_items" in cleaned_data and "sellers" in cleaned_data:
            seller_keys = set(cleaned_data["sellers"]["seller_id"])
            orphan_sellers = (~cleaned_data["order_items"]["seller_id"].isin(seller_keys)).sum()
            violations["items_to_sellers_orphans"] = int(orphan_sellers)

        for key, count in violations.items():
            self.log_operation("referential_integrity", "Foreign Key Audit", key, count)

        return violations

    # -------------------------------------------------------------------------
    # 10. Master Clean Pipeline Execution
    # -------------------------------------------------------------------------
    def run_cleaning_pipeline(self, raw_datasets: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Execute the full data cleaning process across all staged raw datasets."""
        cleaned = {}

        if "orders" in raw_datasets:
            cleaned["orders"] = self.clean_orders(raw_datasets["orders"])

        if "customers" in raw_datasets:
            cleaned["customers"] = self.clean_customers(raw_datasets["customers"])

        if "products" in raw_datasets:
            df_trans = raw_datasets.get("category_translation", None)
            cleaned["products"] = self.clean_products(raw_datasets["products"], df_trans)

        if "sellers" in raw_datasets:
            cleaned["sellers"] = self.clean_sellers(raw_datasets["sellers"])

        if "order_items" in raw_datasets:
            cleaned["order_items"] = self.clean_order_items(raw_datasets["order_items"])

        if "payments" in raw_datasets:
            cleaned["payments"] = self.clean_payments(raw_datasets["payments"])

        if "reviews" in raw_datasets:
            cleaned["reviews"] = self.clean_reviews(raw_datasets["reviews"])

        if "geolocation" in raw_datasets:
            cleaned["geolocation"] = self.clean_geolocation(raw_datasets["geolocation"])

        # Check foreign key relationships
        self.validate_referential_integrity(cleaned)

        # Save processed CSV files
        for key, df in cleaned.items():
            out_file = self.processed_data_dir / f"cleaned_{key}.csv"
            df.to_csv(out_file, index=False)
            logger.info(f"Saved processed dataset: {out_file} ({len(df)} rows)")

        return cleaned

    def generate_data_quality_report(self) -> str:
        """Generate markdown Data Quality Audit report."""
        lines = [
            "# Data Quality & Cleansing Audit Report",
            "",
            "## 1. Cleansing Objectives & Standards",
            "- Enforced strict primary key uniqueness across orders, customers, products, sellers, and items.",
            "- Translated Portuguese category names to standardized English identifiers.",
            "- Standardized Brazilian zip code prefixes to 5-digit zero-padded format.",
            "- Cast all temporal timestamps to standard ISO datetime formats.",
            "- Clamped review scores to [1, 5] and imputed text nulls gracefully.",
            "- Aggregated redundant geolocation coordinate entries to zip code centroid medians.",
            "",
            "## 2. Operation Audit Log",
            "",
            "| Target Table | Cleansing Operation | Action Details | Records Affected |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for item in self.quality_log:
            lines.append(
                f"| `{item['table']}` | {item['operation']} | {item['details']} | {item['count_affected']:,} |"
            )

        return "\n".join(lines)
