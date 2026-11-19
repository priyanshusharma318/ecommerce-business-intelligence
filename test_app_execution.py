import sys
from pathlib import Path

proj = Path(r"E:\DataAnalytics\ecommerce-business-intelligence")
site_packages = proj.parent / "site-packages"
if site_packages.exists():
    sys.path.insert(0, str(site_packages))
sys.path.insert(0, str(proj))

# Test imports
import streamlit
import plotly
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

print("Imports verified successfully.")
print(f"Streamlit version: {streamlit.__version__}")
print(f"Plotly version: {plotly.__version__}")

# Verify data availability
processed = proj / "data" / "processed"
exports = proj / "data" / "exports"

files_to_check = [
    processed / "cleaned_orders.csv",
    processed / "cleaned_order_items.csv",
    processed / "cleaned_customers.csv",
    processed / "cleaned_products.csv",
    processed / "cleaned_reviews.csv",
    processed / "cleaned_payments.csv",
    processed / "cleaned_geolocation.csv",
    exports / "rfm_customer_level.csv",
    exports / "rfm_segment_summary.csv",
    exports / "cohort_retention_percentages.csv",
    exports / "product_pareto_analysis.csv",
    exports / "delivery_delay_satisfaction_summary.csv",
]

all_ok = True
for f in files_to_check:
    if not f.exists() or f.stat().st_size == 0:
        print(f"[MISSING/EMPTY] {f.name}")
        all_ok = False
    else:
        print(f"[OK] {f.name} ({f.stat().st_size:,} bytes)")

if all_ok:
    print("\n[SUCCESS] All data sources for all 5 dashboard pages are verified and ready!")
