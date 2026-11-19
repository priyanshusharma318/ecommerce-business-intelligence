"""
Data loading and exploratory inspection module for the E-Commerce BI platform.
Loads raw Olist CSV datasets, inspects schemas, validates file presence,
and provides initial summary statistics.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np

from src.config import RAW_DATA_DIR, DATASET_FILES, EXPORTS_DIR


class DataLoader:
    """Handles raw data verification, loading, schema inspection, and metadata generation."""

    def __init__(self, raw_data_dir: Path = RAW_DATA_DIR):
        self.raw_data_dir = Path(raw_data_dir)
        self.files = DATASET_FILES

    def check_files_exist(self) -> Dict[str, bool]:
        """Check the existence of each expected raw CSV file."""
        return {
            key: (self.raw_data_dir / filename).is_file()
            for key, filename in self.files.items()
        }

    def is_dataset_ready(self) -> bool:
        """Return True if all 9 raw dataset files are present."""
        statuses = self.check_files_exist()
        return all(statuses.values())

    def get_missing_files(self) -> list:
        """Return a list of missing filenames."""
        return [
            filename
            for key, filename in self.files.items()
            if not (self.raw_data_dir / filename).is_file()
        ]

    def load_dataset(self, key: str, **kwargs) -> pd.DataFrame:
        """Load an individual dataset by key."""
        if key not in self.files:
            raise KeyError(f"Dataset key '{key}' not recognized. Valid keys: {list(self.files.keys())}")
        file_path = self.raw_data_dir / self.files[key]
        if not file_path.is_file():
            raise FileNotFoundError(
                f"Missing dataset file: {file_path}. "
                f"Please refer to DATASET_SETUP.md for instructions to stage real CSV files."
            )
        return pd.read_csv(file_path, **kwargs)

    def load_all_raw(self) -> Dict[str, pd.DataFrame]:
        """Load all available raw CSV files into a dictionary of DataFrames."""
        datasets = {}
        for key in self.files:
            file_path = self.raw_data_dir / self.files[key]
            if file_path.is_file():
                datasets[key] = pd.read_csv(file_path, low_memory=False)
        return datasets

    def inspect_dataset(self, df: pd.DataFrame, name: str) -> Dict:
        """Generate a thorough structural and statistical profile of a DataFrame."""
        total_rows = len(df)
        total_cols = len(df.columns)
        duplicates = df.duplicated().sum()
        memory_usage_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

        col_profiles = []
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0.0
            n_unique = df[col].nunique()
            dtype = str(df[col].dtype)
            sample_val = df[col].dropna().iloc[0] if n_unique > 0 else None
            col_profiles.append({
                "column": col,
                "dtype": dtype,
                "null_count": int(null_count),
                "null_pct": round(null_pct, 2),
                "unique_values": int(n_unique),
                "sample_value": str(sample_val) if sample_val is not None else "NULL",
            })

        return {
            "name": name,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "duplicate_rows": int(duplicates),
            "memory_usage_mb": round(memory_usage_mb, 2),
            "columns": col_profiles,
        }

    def generate_exploration_summary(self, datasets: Dict[str, pd.DataFrame]) -> str:
        """Compile a markdown data exploration report across all loaded tables."""
        lines = [
            "# Raw Data Exploration Report: Olist Brazilian E-Commerce",
            "",
            "## 1. Dataset Overview",
            "",
            "| Dataset Key | Table File | Total Rows | Total Columns | Duplicate Rows | Memory (MB) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for key, df in datasets.items():
            profile = self.inspect_dataset(df, key)
            lines.append(
                f"| `{key}` | `{self.files[key]}` | {profile['total_rows']:,} | {profile['total_columns']} | "
                f"{profile['duplicate_rows']} | {profile['memory_usage_mb']} MB |"
            )

        lines.extend([
            "",
            "## 2. Column-Level Schema & Null Analysis",
            "",
        ])
        for key, df in datasets.items():
            profile = self.inspect_dataset(df, key)
            lines.append(f"### Table: `{self.files[key]}` ({key})")
            lines.append("")
            lines.append("| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for col in profile["columns"]:
                lines.append(
                    f"| `{col['column']}` | `{col['dtype']}` | {col['null_count']:,} | "
                    f"{col['null_pct']}% | {col['unique_values']:,} | `{col['sample_value']}` |"
                )
            lines.append("")

        return "\n".join(lines)


def export_exploratory_plots(datasets: Dict[str, pd.DataFrame], output_dir: Path = EXPORTS_DIR):
    """
    Generate professional exploratory plots for orders, payments, categories, locations,
    and monthly trends using Matplotlib with publication-grade styling.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Style configuration
    plt.style.use("seaborn-v0_8-whitegrid")
    navy_palette = ["#1B365D", "#2B6CB0", "#4299E1", "#63B3ED", "#90CDF4"]

    # 1. Order Status Distribution
    if "orders" in datasets:
        df_ord = datasets["orders"]
        plt.figure(figsize=(9, 5))
        status_counts = df_ord["order_status"].value_counts()
        bars = plt.bar(status_counts.index, status_counts.values, color="#1B365D", edgecolor="#0A192F", width=0.6)
        plt.title("Order Volume by Fulfillment Status", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Order Status", fontsize=11, labelpad=10)
        plt.ylabel("Order Count", fontsize=11, labelpad=10)
        plt.xticks(rotation=30, ha="right")
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height + (height * 0.01), f"{int(height):,}",
                     ha="center", va="bottom", fontsize=9, fontweight="bold")
        plt.tight_layout()
        plt.savefig(output_dir / "01_order_status_distribution.png", dpi=200)
        plt.close()

    # 2. Payment Method Distribution
    if "payments" in datasets:
        df_pay = datasets["payments"]
        plt.figure(figsize=(8, 5))
        pay_counts = df_pay["payment_type"].value_counts()
        bars = plt.bar(pay_counts.index, pay_counts.values, color="#2B6CB0", edgecolor="#1B365D", width=0.55)
        plt.title("Payment Method Utilization by Transaction Count", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Payment Method", fontsize=11, labelpad=10)
        plt.ylabel("Number of Transactions", fontsize=11, labelpad=10)
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height + (height * 0.01), f"{int(height):,}",
                     ha="center", va="bottom", fontsize=9, fontweight="bold")
        plt.tight_layout()
        plt.savefig(output_dir / "02_payment_method_distribution.png", dpi=200)
        plt.close()

    # 3. Customer Geographic Distribution (Top 10 States)
    if "customers" in datasets:
        df_cust = datasets["customers"]
        plt.figure(figsize=(10, 5))
        state_counts = df_cust["customer_state"].value_counts().head(10)
        bars = plt.bar(state_counts.index, state_counts.values, color="#4299E1", edgecolor="#1B365D", width=0.6)
        plt.title("Top 10 Brazilian States by Customer Concentration", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Federal State (UF)", fontsize=11, labelpad=10)
        plt.ylabel("Customer Count", fontsize=11, labelpad=10)
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height + 200, f"{int(height):,}",
                     ha="center", va="bottom", fontsize=9)
        plt.tight_layout()
        plt.savefig(output_dir / "03_top_states_distribution.png", dpi=200)
        plt.close()

    # 4. Monthly Order Volume Trend
    if "orders" in datasets:
        df_ord = datasets["orders"].copy()
        df_ord["purchase_dt"] = pd.to_datetime(df_ord["order_purchase_timestamp"], errors="coerce")
        df_ord = df_ord.dropna(subset=["purchase_dt"])
        df_ord["year_month"] = df_ord["purchase_dt"].dt.to_period("M").astype(str)
        monthly_trend = df_ord.groupby("year_month").size()

        plt.figure(figsize=(12, 5))
        plt.plot(monthly_trend.index, monthly_trend.values, marker="o", color="#1B365D", linewidth=2.5, markersize=5)
        plt.title("Monthly Order Volume Trajectory (2016 - 2018)", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Year-Month", fontsize=11, labelpad=10)
        plt.ylabel("Number of Orders Placed", fontsize=11, labelpad=10)
        plt.xticks(rotation=45, ha="right")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(output_dir / "04_monthly_order_trend.png", dpi=200)
        plt.close()
