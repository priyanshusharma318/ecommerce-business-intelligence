"""
Feature engineering module for the E-Commerce BI Platform.
Constructs temporal, behavioral, logistic, and financial metrics
while strictly distinguishing actual revenue, freight charges, payment values,
and explicit modeling assumptions.
"""

import logging
from typing import Dict, Tuple
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Constructs business features and analytical dimensions from cleaned relational tables.
    """

    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    # 1. Temporal & Delivery Logistics Features (Orders Level)
    # -------------------------------------------------------------------------
    def build_order_features(self, df_orders: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich orders with temporal breakdown and delivery logistics performance metrics.
        """
        df = df_orders.copy()

        # Ensure datetime
        df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
        df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"])
        df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"])

        # Temporal breakdown
        df["order_year"] = df["order_purchase_timestamp"].dt.year
        df["order_month"] = df["order_purchase_timestamp"].dt.strftime("%Y-%m")
        df["order_quarter"] = df["order_purchase_timestamp"].dt.to_period("Q").astype(str)
        df["order_day_name"] = df["order_purchase_timestamp"].dt.day_name()
        df["order_day_of_week"] = df["order_purchase_timestamp"].dt.dayofweek  # 0=Monday, 6=Sunday
        df["order_hour"] = df["order_purchase_timestamp"].dt.hour

        # Time of day segment
        bins = [-1, 6, 12, 18, 24]
        labels = ["Night", "Morning", "Afternoon", "Evening"]
        df["time_of_day_segment"] = pd.cut(df["order_hour"], bins=bins, labels=labels)

        # Logistics: Delivery duration in days (delivered date - purchase date)
        duration_delta = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"])
        df["delivery_duration_days"] = duration_delta.dt.total_seconds() / 86400.0

        # Estimated delivery duration in days (estimated date - purchase date)
        est_duration_delta = (df["order_estimated_delivery_date"] - df["order_purchase_timestamp"])
        df["estimated_delivery_duration_days"] = est_duration_delta.dt.total_seconds() / 86400.0

        # Delivery delay in days: actual delivered date minus estimated delivery date
        # Positive value = late delivery; Negative value = delivered ahead of schedule
        delay_delta = (df["order_delivered_customer_date"] - df["order_estimated_delivery_date"])
        df["delivery_delay_days"] = delay_delta.dt.total_seconds() / 86400.0

        # Binary indicator: Is Late Delivery (only applicable when delivered)
        df["is_late_delivery"] = np.where(
            df["order_delivered_customer_date"].notnull(),
            (df["delivery_delay_days"] > 0).astype(int),
            np.nan
        )

        return df

    # -------------------------------------------------------------------------
    # 2. Customer Behavioral & Frequency Features
    # -------------------------------------------------------------------------
    def build_customer_features(
        self, df_orders: pd.DataFrame, df_customers: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Compute customer order counts, repeat purchase indicators,
        and link customer_unique_id metrics back to orders.
        """
        # Ensure df_orders doesn't retain old duplicate customer columns if re-run
        cols_to_drop = [c for c in ["customer_unique_id", "customer_state", "customer_city", "customer_order_count", "is_repeat_customer"] if c in df_orders.columns]
        df_ord_base = df_orders.drop(columns=cols_to_drop) if cols_to_drop else df_orders.copy()

        # Join customer_unique_id onto orders
        df_ord_cust = df_ord_base.merge(
            df_customers[["customer_id", "customer_unique_id", "customer_state", "customer_city"]].drop_duplicates(subset=["customer_id"]),
            on="customer_id",
            how="left"
        )

        # Count lifetime orders per customer_unique_id
        # Considering all placed orders (or delivered orders)
        order_counts = df_ord_cust.groupby("customer_unique_id")["order_id"].nunique().rename("customer_order_count")

        # Merge order count back to customer level
        df_customers_enriched = df_customers.merge(order_counts, on="customer_unique_id", how="left")
        df_customers_enriched["customer_order_count"] = df_customers_enriched["customer_order_count"].fillna(1).astype(int)
        df_customers_enriched["is_repeat_customer"] = (df_customers_enriched["customer_order_count"] > 1).astype(int)

        # Merge back to orders
        df_orders_enriched = df_ord_cust.merge(
            df_customers_enriched[["customer_id", "customer_order_count", "is_repeat_customer"]].drop_duplicates(subset=["customer_id"]),
            on="customer_id",
            how="left"
        )

        return df_orders_enriched, df_customers_enriched

    # -------------------------------------------------------------------------
    # 3. Revenue, Freight, and Order Financial Aggregations
    # -------------------------------------------------------------------------
    def build_financial_features(
        self, df_order_items: pd.DataFrame, df_payments: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Enrich order items and aggregate financial metrics to order level:
        - Product Revenue = SUM(item price)
        - Freight Value = SUM(freight value)
        - Order Value (GMV) = Product Revenue + Freight Value
        - Payment Value = Total collected payments
        """
        df_items = df_order_items.copy()

        # Item-level financial features
        df_items["item_total_cost"] = df_items["price"] + df_items["freight_value"]

        # Aggregate items by order_id
        order_financials = df_items.groupby("order_id").agg(
            item_count=("order_item_id", "count"),
            product_revenue=("price", "sum"),
            freight_charges=("freight_value", "sum"),
            total_order_gross_value=("item_total_cost", "sum")
        ).reset_index()

        # Aggregate payments by order_id
        order_payments = df_payments.groupby("order_id").agg(
            total_payment_value=("payment_value", "sum"),
            max_payment_installments=("payment_installments", "max"),
            primary_payment_type=("payment_type", lambda x: x.mode().iloc[0] if not x.empty else "unknown"),
            payment_methods_count=("payment_type", "nunique")
        ).reset_index()

        # Merge financial summaries
        order_finance_summary = order_financials.merge(order_payments, on="order_id", how="left")

        return df_items, order_finance_summary

    # -------------------------------------------------------------------------
    # 4. Review Sentiment Category Features
    # -------------------------------------------------------------------------
    def build_review_features(self, df_reviews: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich review table with sentiment tiers:
        - Negative: Score 1 or 2
        - Neutral: Score 3
        - Positive: Score 4 or 5
        """
        df = df_reviews.copy()

        conditions = [
            df["review_score"].isin([1, 2]),
            df["review_score"] == 3,
            df["review_score"].isin([4, 5]),
        ]
        choices = ["Negative", "Neutral", "Positive"]
        df["review_score_category"] = np.select(conditions, choices, default="Unrated")

        # Response time in hours (from review creation to answer)
        if "review_creation_date" in df.columns and "review_answer_timestamp" in df.columns:
            resp_hours = (
                pd.to_datetime(df["review_answer_timestamp"]) - pd.to_datetime(df["review_creation_date"])
            ).dt.total_seconds() / 3600.0
            df["review_response_time_hours"] = resp_hours.clip(lower=0.0)

        return df

    # -------------------------------------------------------------------------
    # 5. Master Feature Generation Pipeline
    # -------------------------------------------------------------------------
    def run_feature_engineering_pipeline(
        self, cleaned_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """
        Execute feature engineering across all cleaned tables and produce
        the unified analytical dataset.
        """
        logger.info("Executing analytical feature engineering pipeline...")
        enriched = dict(cleaned_data)

        # 1. Orders temporal and logistics
        if "orders" in cleaned_data:
            enriched["orders"] = self.build_order_features(cleaned_data["orders"])

        # 2. Customers and customer-order linking
        if "orders" in enriched and "customers" in cleaned_data:
            enriched["orders"], enriched["customers"] = self.build_customer_features(
                enriched["orders"], cleaned_data["customers"]
            )

        # 3. Line items and financial aggregations
        if "order_items" in cleaned_data and "payments" in cleaned_data:
            enriched["order_items"], order_fin = self.build_financial_features(
                cleaned_data["order_items"], cleaned_data["payments"]
            )
            enriched["order_financials"] = order_fin
            # Merge financial totals into enriched orders (dropping old cols to prevent duplicate suffixes)
            fin_cols = [c for c in order_fin.columns if c != "order_id" and c in enriched["orders"].columns]
            if fin_cols:
                enriched["orders"] = enriched["orders"].drop(columns=fin_cols)
            enriched["orders"] = enriched["orders"].merge(order_fin, on="order_id", how="left")

        # 4. Review sentiment features
        if "reviews" in cleaned_data:
            enriched["reviews"] = self.build_review_features(cleaned_data["reviews"])

        logger.info("Feature engineering completed successfully.")
        return enriched
