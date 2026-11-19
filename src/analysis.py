"""
Business intelligence and advanced analytics module for the E-Commerce Platform.
Implements RFM segmentation, monthly cohort retention analysis, Pareto 80/20 product analysis,
delivery logistics vs. review score correlation, and publication-ready visual exports.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import EXPORTS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class BusinessAnalytics:
    """Executes advanced marketing, customer, logistics, and sales analytics."""

    def __init__(self, exports_dir: Path = EXPORTS_DIR):
        self.exports_dir = Path(exports_dir)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        # Apply dark navy/clean styling for plots
        plt.style.use("seaborn-v0_8-whitegrid")
        self.primary_color = "#1B365D"
        self.secondary_color = "#2B6CB0"
        self.accent_color = "#D69E2E"
        self.danger_color = "#E53E3E"
        self.success_color = "#38A169"

    # -------------------------------------------------------------------------
    # 1. RFM Customer Segmentation
    # -------------------------------------------------------------------------
    def calculate_rfm_segmentation(
        self, df_orders: pd.DataFrame, df_customers: pd.DataFrame, df_order_items: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute Recency, Frequency, and Monetary (RFM) metrics per customer_unique_id:
        - Recency: Days since last purchase relative to reference date (dataset snapshot date).
        - Frequency: Total distinct delivered orders placed.
        - Monetary: Total product revenue spent (excluding freight).
        - Assign RFM Scores (1 to 5) and assign customer segments.
        """
        logger.info("Computing RFM customer segmentation...")

        # Focus on delivered orders
        df_ord = df_orders[df_orders["order_status"] == "delivered"].copy()
        df_ord["purchase_dt"] = pd.to_datetime(df_ord["order_purchase_timestamp"])

        # Ensure customer_unique_id is present without suffix collisions
        # df_orders might already have customer_unique_id (if enriched) or not (if raw)
        if "customer_unique_id" in df_ord.columns:
            df_merged = df_ord.copy()
        else:
            cust_subset = df_customers[["customer_id", "customer_unique_id"]].drop_duplicates(subset=["customer_id"])
            df_merged = df_ord.merge(
                cust_subset,
                on="customer_id",
                how="inner"
            )

        # Handle any possible collision if df_ord had customer_unique_id along with merge
        if "customer_unique_id" not in df_merged.columns:
            if "customer_unique_id_x" in df_merged.columns:
                df_merged["customer_unique_id"] = df_merged["customer_unique_id_x"].combine_first(
                    df_merged.get("customer_unique_id_y")
                )
                df_merged.drop(
                    columns=[c for c in ["customer_unique_id_x", "customer_unique_id_y"] if c in df_merged.columns],
                    inplace=True
                )

        # Safely filter out missing, null, empty, or placeholder customer identifiers
        df_merged = df_merged[df_merged["customer_unique_id"].notna()]
        df_merged = df_merged[df_merged["customer_unique_id"].astype(str).str.strip() != ""]
        df_merged = df_merged[~df_merged["customer_unique_id"].astype(str).str.lower().isin(["nan", "null", "none"])]

        # Ensure order-level grain: one row per order_id before joining item revenue
        df_merged = df_merged.drop_duplicates(subset=["order_id"])

        # Aggregate line item revenue by order_id first to prevent order or revenue duplication
        item_rev = df_order_items.groupby("order_id")["price"].sum().reset_index().rename(
            columns={"price": "order_product_revenue"}
        )
        if "order_product_revenue" in df_merged.columns:
            df_merged = df_merged.drop(columns=["order_product_revenue"])
        df_merged = df_merged.merge(item_rev, on="order_id", how="left")
        df_merged["order_product_revenue"] = df_merged["order_product_revenue"].fillna(0.0)

        # Reference date is max purchase date + 1 day
        reference_date = df_merged["purchase_dt"].max() + pd.Timedelta(days=1)

        # Group by customer_unique_id
        rfm = df_merged.groupby("customer_unique_id").agg(
            recency=("purchase_dt", lambda x: (reference_date - x.max()).days),
            frequency=("order_id", "nunique"),
            monetary=("order_product_revenue", "sum")
        ).reset_index()

        # Score quintiles (1-5)
        # Recency: lower days = higher score (5 is best)
        # Frequency and Monetary: higher = higher score (5 is best)
        # Using ranking method to handle identical values
        num_records = len(rfm)
        if num_records >= 5:
            rfm["R_Score"] = pd.qcut(rfm["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
            rfm["F_Score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
            rfm["M_Score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
        else:
            rfm["R_Score"] = 3
            rfm["F_Score"] = 3
            rfm["M_Score"] = 3

        rfm["RFM_Score_Comb"] = rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)

        # Segment Assignment based on R and F scores
        def assign_segment(row):
            r = row["R_Score"]
            f = row["F_Score"]
            m = row["M_Score"]

            if r >= 4 and f >= 4:
                return "Champions"
            elif r >= 3 and f >= 3:
                return "Loyal Customers"
            elif r >= 4 and f <= 2:
                return "Recent Inactive / Promising"
            elif r == 3 and f <= 2:
                return "Needs Attention"
            elif r <= 2 and f >= 3:
                return "At Risk"
            elif r <= 2 and f <= 2 and m >= 4:
                return "High-Value Churned"
            else:
                return "Lost / Dormant"

        rfm["customer_segment"] = rfm.apply(assign_segment, axis=1)

        # Export RFM summary
        rfm_summary = rfm.groupby("customer_segment").agg(
            customer_count=("customer_unique_id", "count"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_revenue=("monetary", "sum")
        ).reset_index()
        rfm_summary["revenue_share_pct"] = (
            rfm_summary["total_revenue"] / rfm_summary["total_revenue"].sum() * 100
        ).round(2)

        rfm.to_csv(self.exports_dir / "rfm_customer_level.csv", index=False)
        rfm_summary.to_csv(self.exports_dir / "rfm_segment_summary.csv", index=False)
        logger.info(f"RFM analysis completed. Total segmented customers: {len(rfm):,}")

        # Plot RFM Segment Distribution
        plt.figure(figsize=(10, 5))
        seg_sorted = rfm_summary.sort_values("total_revenue", ascending=False)
        bars = plt.barh(seg_sorted["customer_segment"], seg_sorted["total_revenue"], color="#2B6CB0", edgecolor="#1B365D")
        plt.title("Total Product Revenue by RFM Customer Segment", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Total Revenue (BRL R$)", fontsize=11, labelpad=10)
        plt.ylabel("Customer Segment", fontsize=11, labelpad=10)
        for bar in bars:
            w = bar.get_width()
            plt.text(w + (w * 0.01), bar.get_y() + bar.get_height() / 2, f"R$ {w:,.0f}",
                     ha="left", va="center", fontsize=9, fontweight="bold")
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(self.exports_dir / "05_rfm_revenue_by_segment.png", dpi=200)
        plt.close()

        return rfm

    # -------------------------------------------------------------------------
    # 2. Monthly Cohort Retention Analysis
    # -------------------------------------------------------------------------
    def calculate_cohort_retention(
        self, df_orders: pd.DataFrame, df_customers: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Construct a monthly cohort retention matrix based on first purchase month.
        """
        logger.info("Computing monthly cohort retention matrix...")

        df_ord = df_orders[df_orders["order_status"] == "delivered"].copy()
        df_ord["purchase_dt"] = pd.to_datetime(df_ord["order_purchase_timestamp"])
        df_ord["order_month"] = df_ord["purchase_dt"].dt.to_period("M")

        # Ensure customer_unique_id is present without suffix collisions
        if "customer_unique_id" in df_ord.columns:
            df_merged = df_ord.copy()
        else:
            cust_subset = df_customers[["customer_id", "customer_unique_id"]].drop_duplicates(subset=["customer_id"])
            df_merged = df_ord.merge(
                cust_subset,
                on="customer_id",
                how="inner"
            )

        if "customer_unique_id" not in df_merged.columns:
            if "customer_unique_id_x" in df_merged.columns:
                df_merged["customer_unique_id"] = df_merged["customer_unique_id_x"].combine_first(
                    df_merged.get("customer_unique_id_y")
                )
                df_merged.drop(
                    columns=[c for c in ["customer_unique_id_x", "customer_unique_id_y"] if c in df_merged.columns],
                    inplace=True
                )

        # Safely filter out missing/invalid customer identifiers
        df_merged = df_merged[df_merged["customer_unique_id"].notna()]
        df_merged = df_merged[df_merged["customer_unique_id"].astype(str).str.strip() != ""]
        df_merged = df_merged[~df_merged["customer_unique_id"].astype(str).str.lower().isin(["nan", "null", "none"])]

        # Ensure order-level uniqueness
        df_merged = df_merged.drop_duplicates(subset=["order_id"])

        # Identify cohort month (first purchase month per unique customer)
        df_merged["cohort_month"] = df_merged.groupby("customer_unique_id")["order_month"].transform("min")

        # Compute period number (month offset)
        def get_month_offset(row):
            return (row["order_month"].year - row["cohort_month"].year) * 12 + (
                row["order_month"].month - row["cohort_month"].month
            )

        df_merged["cohort_index"] = df_merged.apply(get_month_offset, axis=1)

        # Count unique customers per cohort and month offset
        cohort_counts = df_merged.groupby(["cohort_month", "cohort_index"])["customer_unique_id"].nunique().reset_index()

        # Pivot to matrix
        cohort_pivot = cohort_counts.pivot(index="cohort_month", columns="cohort_index", values="customer_unique_id")
        cohort_sizes = cohort_pivot.iloc[:, 0]
        retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0) * 100

        # Export CSVs
        cohort_pivot.to_csv(self.exports_dir / "cohort_customer_counts.csv")
        retention_matrix.to_csv(self.exports_dir / "cohort_retention_percentages.csv")

        # Plot retention heatmap if multi-month columns exist
        if retention_matrix.shape[1] > 1:
            plt.figure(figsize=(14, 8))
            matrix_to_plot = retention_matrix.iloc[:, 1:13]  # Months 1 to 12
            if matrix_to_plot.shape[1] > 0:
                im = plt.imshow(matrix_to_plot, cmap="Blues", aspect="auto", vmin=0, vmax=5)
                plt.title("Monthly Customer Retention Rate Heatmap (% Returning in Month N)", fontsize=14, fontweight="bold", pad=15)
                plt.xlabel("Months Since First Purchase", fontsize=11, labelpad=10)
                plt.ylabel("Cohort (First Purchase Month)", fontsize=11, labelpad=10)
                plt.xticks(range(len(matrix_to_plot.columns)), [f"Month {c}" for c in matrix_to_plot.columns])
                plt.yticks(range(len(matrix_to_plot.index)), [str(idx) for idx in matrix_to_plot.index])
                plt.colorbar(im, label="Retention Rate (%)")

                # Annotate text
                for i in range(len(matrix_to_plot.index)):
                    for j in range(len(matrix_to_plot.columns)):
                        val = matrix_to_plot.iloc[i, j]
                        if not np.isnan(val) and val > 0:
                            plt.text(j, i, f"{val:.1f}%", ha="center", va="center", color="black", fontsize=8)

                plt.tight_layout()
                plt.savefig(self.exports_dir / "06_cohort_retention_heatmap.png", dpi=200)
                plt.close()

        logger.info("Cohort retention analysis completed.")
        return retention_matrix

    # -------------------------------------------------------------------------
    # 3. Product Pareto 80/20 Analysis
    # -------------------------------------------------------------------------
    def calculate_pareto_analysis(
        self, df_order_items: pd.DataFrame, df_products: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Assess product revenue concentration (Pareto 80/20 principle):
        What percentage of catalog products drive 80% of total revenue?
        """
        logger.info("Computing product Pareto revenue concentration...")

        # Aggregate revenue by product_id
        prod_rev = df_order_items.groupby("product_id").agg(
            total_units_sold=("order_item_id", "count"),
            total_revenue=("price", "sum")
        ).reset_index().sort_values("total_revenue", ascending=False)

        # Merge category translation
        if "product_category_name_english" in df_products.columns:
            prod_rev = prod_rev.merge(
                df_products[["product_id", "product_category_name_english"]],
                on="product_id",
                how="left"
            )

        # Cumulative percentages
        total_rev_sum = prod_rev["total_revenue"].sum()
        prod_rev["cumulative_revenue"] = prod_rev["total_revenue"].cumsum()
        prod_rev["cumulative_revenue_pct"] = (prod_rev["cumulative_revenue"] / total_rev_sum) * 100
        prod_rev["product_rank"] = range(1, len(prod_rev) + 1)
        prod_rev["product_rank_pct"] = (prod_rev["product_rank"] / len(prod_rev)) * 100

        # Classify Pareto category
        prod_rev["pareto_class"] = np.where(
            prod_rev["cumulative_revenue_pct"] <= 80, "Top 80% Revenue (Class A)",
            np.where(prod_rev["cumulative_revenue_pct"] <= 95, "Next 15% Revenue (Class B)", "Bottom 5% Revenue (Class C)")
        )

        prod_rev.to_csv(self.exports_dir / "product_pareto_analysis.csv", index=False)

        # Summary KPIs
        class_a_count = (prod_rev["pareto_class"] == "Top 80% Revenue (Class A)").sum()
        class_a_pct = (class_a_count / len(prod_rev)) * 100
        logger.info(f"Pareto Result: {class_a_pct:.2f}% of products generate 80% of total catalog revenue.")

        return prod_rev

    # -------------------------------------------------------------------------
    # 4. Delivery Delay vs. Review Score Correlation
    # -------------------------------------------------------------------------
    def analyze_delivery_vs_satisfaction(
        self, df_orders: pd.DataFrame, df_reviews: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Analyze statistical correlation between delivery delays and customer review scores.
        """
        logger.info("Analyzing delivery performance impact on customer review ratings...")

        # Filter delivered orders with valid delivery delta
        df_ord = df_orders[df_orders["order_status"] == "delivered"].copy()
        df_ord = df_ord.dropna(subset=["order_delivered_customer_date", "order_estimated_delivery_date"])

        # Delay in days: positive = late, negative = early
        df_ord["delivery_delay_days"] = (
            pd.to_datetime(df_ord["order_delivered_customer_date"]) -
            pd.to_datetime(df_ord["order_estimated_delivery_date"])
        ).dt.total_seconds() / 86400.0

        # Join review score
        if "review_score" in df_ord.columns:
            df_ord = df_ord.drop(columns=["review_score"])
        avg_reviews = df_reviews.groupby("order_id")["review_score"].mean().reset_index()
        df_merged = df_ord.merge(avg_reviews, on="order_id", how="inner")

        # Bin delivery timeliness
        delay_bins = [-999, -5, -0.01, 0.01, 5, 10, 20, 999]
        delay_labels = [
            "Very Early (>5d)", "Early (1-5d)", "On Time (0d)",
            "Slight Delay (1-5d)", "Moderate Delay (6-10d)", "Severe Delay (11-20d)", "Extreme Delay (>20d)"
        ]
        df_merged["delay_bucket"] = pd.cut(df_merged["delivery_delay_days"], bins=delay_bins, labels=delay_labels)

        # Aggregate satisfaction by delay bucket
        delay_summary = df_merged.groupby("delay_bucket", observed=False).agg(
            order_count=("order_id", "count"),
            avg_review_score=("review_score", "mean"),
            pct_one_star=("review_score", lambda x: (x == 1).mean() * 100),
            pct_five_star=("review_score", lambda x: (x == 5).mean() * 100)
        ).reset_index()

        delay_summary.to_csv(self.exports_dir / "delivery_delay_satisfaction_summary.csv", index=False)

        # Plot Delay vs Score
        fig, ax1 = plt.subplots(figsize=(11, 5))
        ax2 = ax1.twinx()

        bars = ax1.bar(
            range(len(delay_summary)),
            delay_summary["order_count"],
            color="#CBD5E0",
            edgecolor="#718096",
            width=0.5,
            label="Order Volume"
        )
        line = ax2.plot(
            range(len(delay_summary)),
            delay_summary["avg_review_score"],
            color="#E53E3E",
            marker="o",
            linewidth=2.5,
            markersize=7,
            label="Avg Review Score"
        )

        ax1.set_xlabel("Delivery Timeliness Bucket", fontsize=11, labelpad=10)
        ax1.set_ylabel("Order Count", fontsize=11, color="#4A5568", labelpad=10)
        ax2.set_ylabel("Average Review Rating (1-5 Stars)", fontsize=11, color="#E53E3E", labelpad=10)
        ax2.set_ylim(1.0, 5.0)

        plt.title("Impact of Delivery Delays on Customer Review Ratings", fontsize=14, fontweight="bold", pad=15)
        ax1.set_xticks(range(len(delay_summary)))
        ax1.set_xticklabels(delay_summary["delay_bucket"], rotation=30, ha="right")
        ax1.grid(False)

        plt.tight_layout()
        plt.savefig(self.exports_dir / "07_delivery_delay_vs_satisfaction.png", dpi=200)
        plt.close()

        logger.info("Delivery satisfaction analysis completed.")
        return delay_summary

    # -------------------------------------------------------------------------
    # 5. Master Python Analytics Pipeline Runner
    # -------------------------------------------------------------------------
    def run_full_analytics_pipeline(self, cleaned_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Execute all advanced analytics modules and persist summary artifacts."""
        results = {}

        if all(k in cleaned_data for k in ["orders", "customers", "order_items"]):
            results["rfm"] = self.calculate_rfm_segmentation(
                cleaned_data["orders"], cleaned_data["customers"], cleaned_data["order_items"]
            )

        if "orders" in cleaned_data and "customers" in cleaned_data:
            results["cohort_retention"] = self.calculate_cohort_retention(
                cleaned_data["orders"], cleaned_data["customers"]
            )

        if "order_items" in cleaned_data and "products" in cleaned_data:
            results["pareto"] = self.calculate_pareto_analysis(
                cleaned_data["order_items"], cleaned_data["products"]
            )

        if "orders" in cleaned_data and "reviews" in cleaned_data:
            results["delivery_satisfaction"] = self.analyze_delivery_vs_satisfaction(
                cleaned_data["orders"], cleaned_data["reviews"]
            )

        return results
