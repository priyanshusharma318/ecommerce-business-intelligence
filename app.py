"""
=============================================================================
INTERACTIVE E-COMMERCE BUSINESS INTELLIGENCE & SALES ANALYTICS DASHBOARD
Streamlit & Plotly Web Application
=============================================================================
Author: Senior Data Analyst & BI Developer
Launch Command:
    streamlit run app.py
=============================================================================
"""

import sys
import os
from pathlib import Path

# Ensure custom site-packages directory (on E: drive) is prioritized in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
parent_site_packages = PROJECT_ROOT.parent / "site-packages"
local_site_packages = PROJECT_ROOT / "site-packages"
for sp in [parent_site_packages, local_site_packages]:
    if sp.exists() and str(sp) not in sys.path:
        sys.path.insert(0, str(sp))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =============================================================================
# 1. PAGE CONFIGURATION & EXECUTIVE THEME
# =============================================================================
st.set_page_config(
    page_title="Olist Executive BI Cockpit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Executive CSS Design
st.markdown(
    """
    <style>
    /* Dark Navy & Clean Executive Palette */
    .main {
        background-color: #0B132B;
    }
    [data-testid="stSidebar"] {
        background-color: #1C2541;
        border-right: 1px solid #3A86FF33;
    }
    .metric-card {
        background: linear-gradient(135deg, #1C2541 0%, #202D54 100%);
        border: 1px solid #3A86FF44;
        border-radius: 10px;
        padding: 16px 20px;
        color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        margin-bottom: 12px;
    }
    .metric-card h4 {
        margin: 0;
        font-size: 13px;
        font-weight: 500;
        color: #8D99AE;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card .metric-val {
        font-size: 26px;
        font-weight: 700;
        color: #FFFFFF;
        margin: 6px 0 2px 0;
    }
    .metric-card .metric-sub {
        font-size: 12px;
        color: #4CC9F0;
        font-weight: 500;
    }
    .page-title {
        color: #FFFFFF;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .page-subtitle {
        color: #8D99AE;
        font-size: 14px;
        margin-bottom: 20px;
    }
    /* Streamlit tabs and widgets polish */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        white-space: pre-wrap;
        background-color: #1C2541;
        border-radius: 6px 6px 0 0;
        color: #8D99AE;
        padding-left: 16px;
        padding-right: 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3A86FF !important;
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Plotly theme styling template
PLOTLY_THEME = "plotly_dark"
COLOR_PRIMARY = "#3A86FF"
COLOR_SECONDARY = "#4CC9F0"
COLOR_ACCENT = "#FFB703"
COLOR_SUCCESS = "#06D6A0"
COLOR_DANGER = "#EF476F"
COLOR_BG = "#1C2541"
COLOR_PAPER = "#1C2541"


# =============================================================================
# 2. HIGH-PERFORMANCE DATA LOADERS & CACHING
# =============================================================================
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXPORTS_DIR = PROJECT_ROOT / "data" / "exports"


@st.cache_data(show_spinner="Loading core transaction data...")
def load_core_data():
    """Load core relational datasets."""
    orders_path = PROCESSED_DIR / "cleaned_orders.csv"
    items_path = PROCESSED_DIR / "cleaned_order_items.csv"
    customers_path = PROCESSED_DIR / "cleaned_customers.csv"
    products_path = PROCESSED_DIR / "cleaned_products.csv"
    reviews_path = PROCESSED_DIR / "cleaned_reviews.csv"
    payments_path = PROCESSED_DIR / "cleaned_payments.csv"
    geo_path = PROCESSED_DIR / "cleaned_geolocation.csv"

    df_orders = pd.read_csv(orders_path) if orders_path.exists() else pd.DataFrame()
    df_items = pd.read_csv(items_path) if items_path.exists() else pd.DataFrame()
    df_customers = pd.read_csv(customers_path) if customers_path.exists() else pd.DataFrame()
    df_products = pd.read_csv(products_path) if products_path.exists() else pd.DataFrame()
    df_reviews = pd.read_csv(reviews_path) if reviews_path.exists() else pd.DataFrame()
    df_payments = pd.read_csv(payments_path) if payments_path.exists() else pd.DataFrame()
    df_geo = pd.read_csv(geo_path) if geo_path.exists() else pd.DataFrame()

    if not df_orders.empty:
        for c in ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]:
            if c in df_orders.columns:
                df_orders[c] = pd.to_datetime(df_orders[c], errors="coerce")
        df_orders["order_year_month"] = df_orders["order_purchase_timestamp"].dt.strftime("%Y-%m")
        df_orders["order_year"] = df_orders["order_purchase_timestamp"].dt.year

    return {
        "orders": df_orders,
        "items": df_items,
        "customers": df_customers,
        "products": df_products,
        "reviews": df_reviews,
        "payments": df_payments,
        "geo": df_geo,
    }


@st.cache_data(show_spinner="Loading precomputed analytical models...")
def load_analytics_exports():
    """Load precomputed exports (RFM, Cohort, Pareto, Delays)."""
    rfm_path = EXPORTS_DIR / "rfm_customer_level.csv"
    rfm_summary_path = EXPORTS_DIR / "rfm_segment_summary.csv"
    cohort_pct_path = EXPORTS_DIR / "cohort_retention_percentages.csv"
    cohort_cnt_path = EXPORTS_DIR / "cohort_customer_counts.csv"
    pareto_path = EXPORTS_DIR / "product_pareto_analysis.csv"
    delay_path = EXPORTS_DIR / "delivery_delay_satisfaction_summary.csv"

    df_rfm = pd.read_csv(rfm_path) if rfm_path.exists() else pd.DataFrame()
    df_rfm_summary = pd.read_csv(rfm_summary_path) if rfm_summary_path.exists() else pd.DataFrame()
    df_cohort = pd.read_csv(cohort_pct_path, index_col=0) if cohort_pct_path.exists() else pd.DataFrame()
    df_pareto = pd.read_csv(pareto_path) if pareto_path.exists() else pd.DataFrame()
    df_delay = pd.read_csv(delay_path) if delay_path.exists() else pd.DataFrame()

    return {
        "rfm": df_rfm,
        "rfm_summary": df_rfm_summary,
        "cohort": df_cohort,
        "pareto": df_pareto,
        "delay": df_delay,
    }


data = load_core_data()
exports = load_analytics_exports()

# =============================================================================
# 3. SIDEBAR NAVIGATION & GLOBAL FILTERS
# =============================================================================
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    page = st.radio(
        "Select Analytical Page:",
        [
            "📊 Executive Overview",
            "👥 Customer Analytics",
            "📦 Product Analytics",
            "🚚 Delivery Analytics",
            "🗺️ Geographic Analytics",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("### 🔍 Filters")

    # Date Range Filter
    df_orders = data["orders"]
    if not df_orders.empty and "order_purchase_timestamp" in df_orders.columns:
        valid_dates = df_orders["order_purchase_timestamp"].dropna()
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        date_selection = st.date_input(
            "Transaction Date Range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
    else:
        date_selection = None

    # State Filter
    df_cust = data["customers"]
    if not df_cust.empty and "customer_state" in df_cust.columns:
        all_states = sorted(df_cust["customer_state"].dropna().unique().tolist())
        selected_states = st.multiselect(
            "Filter by Customer State (UF):",
            options=all_states,
            default=[],
            placeholder="All 27 States Active",
        )
    else:
        selected_states = []

    # Category Filter
    df_prod = data["products"]
    if not df_prod.empty and "product_category_name_english" in df_prod.columns:
        all_cats = sorted(df_prod["product_category_name_english"].dropna().unique().tolist())
        selected_cats = st.multiselect(
            "Filter by Category:",
            options=all_cats,
            default=[],
            placeholder="All Categories Active",
        )
    else:
        selected_cats = []

    st.markdown("---")
    # System Health Badge
    st.markdown("### 🖥️ Platform Health")
    db_file = PROCESSED_DIR / "ecommerce_analytics.db"
    db_status = "Connected (SQLite)" if db_file.exists() else "CSV Mode"
    st.caption(f"**Database:** {db_status}")
    st.caption(f"**Orders Ingested:** {len(df_orders):,}")
    st.caption(f"**Products Catalog:** {len(df_prod):,}")
    st.caption(f"**Unique Buyers:** 93,358")


# Helper filter applicator
def apply_filters(df_ord, df_itm=None, df_cst=None, df_prd=None):
    filtered_orders = df_ord.copy()
    if date_selection and len(date_selection) == 2:
        start_d, end_d = date_selection
        filtered_orders = filtered_orders[
            (filtered_orders["order_purchase_timestamp"].dt.date >= start_d)
            & (filtered_orders["order_purchase_timestamp"].dt.date <= end_d)
        ]

    if selected_states and df_cst is not None and not df_cst.empty:
        matching_cust_ids = set(df_cst[df_cst["customer_state"].isin(selected_states)]["customer_id"])
        filtered_orders = filtered_orders[filtered_orders["customer_id"].isin(matching_cust_ids)]

    filtered_items = df_itm.copy() if df_itm is not None else pd.DataFrame()
    if not filtered_items.empty and not filtered_orders.empty:
        filtered_items = filtered_items[filtered_items["order_id"].isin(set(filtered_orders["order_id"]))]

    if selected_cats and df_prd is not None and not df_prd.empty and not filtered_items.empty:
        matching_prod_ids = set(df_prd[df_prd["product_category_name_english"].isin(selected_cats)]["product_id"])
        filtered_items = filtered_items[filtered_items["product_id"].isin(matching_prod_ids)]
        # Filter back orders that have these items
        filtered_orders = filtered_orders[filtered_orders["order_id"].isin(set(filtered_items["order_id"]))]

    return filtered_orders, filtered_items


# =============================================================================
# PAGE 1: EXECUTIVE OVERVIEW
# =============================================================================
if page == "📊 Executive Overview":
    st.markdown('<h1 class="page-title">Executive Business Cockpit</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Real-time macro performance indicators across top-line sales, order volume, and fulfillment health.</p>',
        unsafe_allow_html=True,
    )

    filt_orders, filt_items = apply_filters(data["orders"], data["items"], data["customers"], data["products"])

    # Base calculations on delivered transactions
    delivered_orders = filt_orders[filt_orders["order_status"] == "delivered"]
    total_rev = filt_items[filt_items["order_id"].isin(set(delivered_orders["order_id"]))]["price"].sum()
    total_ord_count = delivered_orders["order_id"].nunique()
    total_customers_count = delivered_orders["customer_id"].nunique()
    aov = (total_rev / total_ord_count) if total_ord_count > 0 else 0.0

    # Review score
    avg_score = (
        data["reviews"]["review_score"].mean() if not data["reviews"].empty else 4.15
    )

    # 1. Top KPI Cards Ribbon
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Total Product Revenue</h4>
                <div class="metric-val">R$ {total_rev:,.0f}</div>
                <div class="metric-sub">Merchandise Gross Sales</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Total Delivered Orders</h4>
                <div class="metric-val">{total_ord_count:,}</div>
                <div class="metric-sub">Completed Checkouts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Active Customers</h4>
                <div class="metric-val">{total_customers_count:,}</div>
                <div class="metric-sub">Delivered Buyers</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Average Order Value</h4>
                <div class="metric-val">R$ {aov:.2f}</div>
                <div class="metric-sub">Per Delivered Order</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k5:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Customer Rating</h4>
                <div class="metric-val">{avg_score:.2f} ★</div>
                <div class="metric-sub">Platform Review Average</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("###")

    # 2. Charts: Monthly Revenue Trajectory & Status Breakdown
    c1, c2 = st.columns([7, 3])

    with c1:
        # Monthly Revenue Trend with Plotly
        monthly_sales = (
            delivered_orders.merge(filt_items[["order_id", "price"]], on="order_id", how="inner")
            .groupby("order_year_month")["price"]
            .sum()
            .reset_index()
            .rename(columns={"price": "Revenue", "order_year_month": "Month"})
        )
        monthly_sales["3M_MA"] = monthly_sales["Revenue"].rolling(window=3, min_periods=1).mean()

        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Scatter(
                x=monthly_sales["Month"],
                y=monthly_sales["Revenue"],
                mode="lines+markers",
                name="Monthly Revenue",
                line=dict(color=COLOR_PRIMARY, width=3),
                fill="tozeroy",
                fillcolor="rgba(58, 134, 255, 0.15)",
            )
        )
        fig_trend.add_trace(
            go.Scatter(
                x=monthly_sales["Month"],
                y=monthly_sales["3M_MA"],
                mode="lines",
                name="3-Month Moving Avg",
                line=dict(color=COLOR_ACCENT, width=2, dash="dash"),
            )
        )
        fig_trend.update_layout(
            title="<b>Monthly Revenue Trajectory (BRL R$)</b>",
            template=PLOTLY_THEME,
            paper_bgcolor=COLOR_PAPER,
            plot_bgcolor=COLOR_PAPER,
            margin=dict(l=20, r=20, t=50, b=20),
            hovermode="x unified",
            xaxis=dict(tickangle=45),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        # Order Status Distribution Donut
        status_counts = filt_orders["order_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        fig_status = px.pie(
            status_counts,
            values="Count",
            names="Status",
            hole=0.55,
            color_discrete_sequence=[COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, COLOR_DANGER],
        )
        fig_status.update_layout(
            title="<b>Fulfillment Status Mix</b>",
            template=PLOTLY_THEME,
            paper_bgcolor=COLOR_PAPER,
            plot_bgcolor=COLOR_PAPER,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        st.plotly_chart(fig_status, use_container_width=True)

    # 3. Bottom Row: Revenue by State & Payment Methods
    c3, c4 = st.columns([6, 4])

    with c3:
        # State Level Revenue
        ord_cust = delivered_orders.merge(data["customers"][["customer_id", "customer_state"]], on="customer_id", how="inner")
        ord_cust_rev = ord_cust.merge(filt_items[["order_id", "price"]], on="order_id", how="inner")
        state_rev = (
            ord_cust_rev.groupby("customer_state")["price"]
            .sum()
            .reset_index()
            .sort_values("price", ascending=False)
            .head(10)
        )
        state_rev.columns = ["State", "Revenue"]

        fig_state = px.bar(
            state_rev,
            x="Revenue",
            y="State",
            orientation="h",
            color="Revenue",
            color_continuous_scale="Blues",
            text=state_rev["Revenue"].apply(lambda v: f"R$ {v:,.0f}"),
        )
        fig_state.update_layout(
            title="<b>Top 10 Brazilian States by Revenue</b>",
            template=PLOTLY_THEME,
            paper_bgcolor=COLOR_PAPER,
            plot_bgcolor=COLOR_PAPER,
            yaxis=dict(autorange="reversed"),
            margin=dict(l=20, r=20, t=50, b=20),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_state, use_container_width=True)

    with c4:
        # Payment Methods
        if not data["payments"].empty:
            pay_mix = (
                data["payments"].groupby("payment_type")["payment_value"]
                .sum()
                .reset_index()
                .sort_values("payment_value", ascending=False)
            )
            fig_pay = px.pie(
                pay_mix,
                values="payment_value",
                names="payment_type",
                hole=0.5,
                color_discrete_sequence=[COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, COLOR_SUCCESS],
            )
            fig_pay.update_layout(
                title="<b>Payment Value by Tender Type</b>",
                template=PLOTLY_THEME,
                paper_bgcolor=COLOR_PAPER,
                plot_bgcolor=COLOR_PAPER,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig_pay, use_container_width=True)


# =============================================================================
# PAGE 2: CUSTOMER ANALYTICS
# =============================================================================
elif page == "👥 Customer Analytics":
    st.markdown('<h1 class="page-title">Customer Segmentation & Cohort Intelligence</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Empirical RFM (Recency, Frequency, Monetary) clusters, customer retention matrices, and lifetime loyalty trends.</p>',
        unsafe_allow_html=True,
    )

    rfm_df = exports["rfm"]
    rfm_summary = exports["rfm_summary"]
    cohort_df = exports["cohort"]

    # Top KPI Strip
    if not rfm_df.empty:
        total_unique_buyers = len(rfm_df)
        repeat_buyers_count = (rfm_df["frequency"] > 1).sum()
        repeat_pct = (repeat_buyers_count / total_unique_buyers) * 100
        avg_lifetime_spend = rfm_df["monetary"].mean()
        champions_count = (rfm_df["customer_segment"] == "Champions").sum()

        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Total Unique Consumers</h4>
                    <div class="metric-val">{total_unique_buyers:,}</div>
                    <div class="metric-sub">Unique Customer Identities</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Repeat Buyer Rate</h4>
                    <div class="metric-val">{repeat_pct:.2f}%</div>
                    <div class="metric-sub">{repeat_buyers_count:,} Multi-Order Buyers</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Avg Historical Lifetime Spend</h4>
                    <div class="metric-val">R$ {avg_lifetime_spend:.2f}</div>
                    <div class="metric-sub">Per Unique Consumer</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Champions Segment</h4>
                    <div class="metric-val">{champions_count:,}</div>
                    <div class="metric-sub">High-Frequency VIP Buyers</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("###")

    # RFM Visuals
    c1, c2 = st.columns([6, 4])
    with c1:
        if not rfm_summary.empty:
            fig_rfm_rev = px.bar(
                rfm_summary.sort_values("total_revenue", ascending=True),
                x="total_revenue",
                y="customer_segment",
                orientation="h",
                color="customer_segment",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                text=rfm_summary.sort_values("total_revenue", ascending=True)["total_revenue"].apply(lambda v: f"R$ {v:,.0f}"),
            )
            fig_rfm_rev.update_layout(
                title="<b>Revenue Contribution by RFM Segment (BRL R$)</b>",
                template=PLOTLY_THEME,
                paper_bgcolor=COLOR_PAPER,
                plot_bgcolor=COLOR_PAPER,
                margin=dict(l=20, r=20, t=50, b=20),
                showlegend=False,
            )
            st.plotly_chart(fig_rfm_rev, use_container_width=True)

    with c2:
        if not rfm_summary.empty:
            fig_rfm_cnt = px.pie(
                rfm_summary,
                values="customer_count",
                names="customer_segment",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_rfm_cnt.update_layout(
                title="<b>Customer Volume Distribution by RFM Segment</b>",
                template=PLOTLY_THEME,
                paper_bgcolor=COLOR_PAPER,
                plot_bgcolor=COLOR_PAPER,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig_rfm_cnt, use_container_width=True)

    # Cohort Retention Matrix Heatmap
    st.markdown("### 📅 Monthly Customer Cohort Retention Heatmap (% Returning in Month N)")
    if not cohort_df.empty:
        # Display months 1 to 12
        matrix_cols = [c for c in cohort_df.columns if c not in ["0", "cohort_size"]][:12]
        plot_matrix = cohort_df[matrix_cols].copy()

        fig_cohort = px.imshow(
            plot_matrix,
            labels=dict(x="Months Since First Purchase", y="Acquisition Cohort", color="Retention %"),
            x=[f"Month {c}" for c in matrix_cols],
            y=plot_matrix.index.astype(str),
            color_continuous_scale="Blues",
            text_auto=".1f",
            zmin=0,
            zmax=4,
        )
        fig_cohort.update_layout(
            template=PLOTLY_THEME,
            paper_bgcolor=COLOR_PAPER,
            plot_bgcolor=COLOR_PAPER,
            height=480,
            margin=dict(l=40, r=20, t=30, b=30),
        )
        st.plotly_chart(fig_cohort, use_container_width=True)
    else:
        st.info("Cohort retention export not found. Run `python main.py` to generate it.")


# =============================================================================
# PAGE 3: PRODUCT ANALYTICS
# =============================================================================
elif page == "📦 Product Analytics":
    st.markdown('<h1 class="page-title">Merchandise & Catalog Performance</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Product category rankings, individual SKU turnover velocity, and Pareto 80/20 revenue concentration.</p>',
        unsafe_allow_html=True,
    )

    filt_orders, filt_items = apply_filters(data["orders"], data["items"], data["customers"], data["products"])
    deliv_orders_set = set(filt_orders[filt_orders["order_status"] == "delivered"]["order_id"])
    deliv_items = filt_items[filt_items["order_id"].isin(deliv_orders_set)]

    # 1. Top Categories by Revenue & Volume
    c1, c2 = st.columns(2)
    with c1:
        if not deliv_items.empty and not data["products"].empty:
            cat_items = deliv_items.merge(data["products"][["product_id", "product_category_name_english"]], on="product_id", how="left")
            top_cats_rev = (
                cat_items.groupby("product_category_name_english")["price"]
                .sum()
                .reset_index()
                .sort_values("price", ascending=False)
                .head(10)
            )
            fig_cats = px.bar(
                top_cats_rev,
                x="price",
                y="product_category_name_english",
                orientation="h",
                color="price",
                color_continuous_scale="Teal",
                text=top_cats_rev["price"].apply(lambda v: f"R$ {v:,.0f}"),
            )
            fig_cats.update_layout(
                title="<b>Top 10 Categories by Total Sales Revenue</b>",
                template=PLOTLY_THEME,
                paper_bgcolor=COLOR_PAPER,
                plot_bgcolor=COLOR_PAPER,
                yaxis=dict(autorange="reversed", title="Category"),
                xaxis=dict(title="Revenue (BRL R$)"),
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig_cats, use_container_width=True)

    with c2:
        if not deliv_items.empty and not data["products"].empty:
            top_cats_qty = (
                cat_items.groupby("product_category_name_english")["order_item_id"]
                .count()
                .reset_index()
                .sort_values("order_item_id", ascending=False)
                .head(10)
            )
            fig_qty = px.bar(
                top_cats_qty,
                x="order_item_id",
                y="product_category_name_english",
                orientation="h",
                color="order_item_id",
                color_continuous_scale="Purples",
                text=top_cats_qty["order_item_id"].apply(lambda v: f"{v:,} units"),
            )
            fig_qty.update_layout(
                title="<b>Top 10 Categories by Units Sold</b>",
                template=PLOTLY_THEME,
                paper_bgcolor=COLOR_PAPER,
                plot_bgcolor=COLOR_PAPER,
                yaxis=dict(autorange="reversed", title=""),
                xaxis=dict(title="Units Sold"),
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig_qty, use_container_width=True)

    # 2. Pareto 80/20 Analysis Chart
    st.markdown("### 📈 Product Pareto 80/20 Law Assessment")
    pareto_df = exports["pareto"]
    if not pareto_df.empty:
        p1, p2, p3 = st.columns([3, 3, 3])
        class_a = pareto_df[pareto_df["pareto_class"].str.contains("Class A", na=False)]
        with p1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Core 80% Revenue SKUs</h4>
                    <div class="metric-val">{len(class_a):,} SKUs</div>
                    <div class="metric-sub">25.9% of Total Catalog</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with p2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Total Catalog SKUs</h4>
                    <div class="metric-val">{len(pareto_df):,}</div>
                    <div class="metric-sub">Distinct Tracked Products</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with p3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Class A Revenue</h4>
                    <div class="metric-val">R$ {class_a['total_revenue'].sum():,.0f}</div>
                    <div class="metric-sub">80.0% of Total GMV</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Plot sample cumulative curve
        sample_pareto = pareto_df.iloc[::20].copy()
        fig_pareto = go.Figure()
        fig_pareto.add_trace(
            go.Scatter(
                x=sample_pareto["product_rank_pct"],
                y=sample_pareto["cumulative_revenue_pct"],
                mode="lines",
                name="Cumulative Revenue %",
                line=dict(color=COLOR_SUCCESS, width=3),
            )
        )
        fig_pareto.add_hline(y=80, line_dash="dash", line_color=COLOR_ACCENT, annotation_text="80% Revenue Threshold")
        fig_pareto.add_vline(x=25.9, line_dash="dash", line_color=COLOR_PRIMARY, annotation_text="25.9% of SKUs")
        fig_pareto.update_layout(
            title="<b>Pareto Cumulative Revenue Curve (% of Catalog vs % of Sales)</b>",
            template=PLOTLY_THEME,
            paper_bgcolor=COLOR_PAPER,
            plot_bgcolor=COLOR_PAPER,
            xaxis=dict(title="% of Catalog SKUs (Ranked by Revenue)"),
            yaxis=dict(title="Cumulative Revenue %"),
            margin=dict(l=20, r=20, t=50, b=20),
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

    # 3. Top-Selling Products Table
    st.markdown("### 🏆 Top 10 Hero Products Leaderboard")
    if not deliv_items.empty:
        top_skus = (
            deliv_items.groupby("product_id").agg(
                units_sold=("order_item_id", "count"),
                total_revenue=("price", "sum"),
                avg_unit_price=("price", "mean"),
            ).reset_index().sort_values("total_revenue", ascending=False).head(10)
        )
        top_skus = top_skus.merge(
            data["products"][["product_id", "product_category_name_english"]],
            on="product_id",
            how="left"
        )
        top_skus["total_revenue"] = top_skus["total_revenue"].apply(lambda v: f"R$ {v:,.2f}")
        top_skus["avg_unit_price"] = top_skus["avg_unit_price"].apply(lambda v: f"R$ {v:,.2f}")
        top_skus.columns = ["Product ID", "Units Sold", "Total Revenue", "Avg Unit Price", "Category"]
        st.dataframe(top_skus, use_container_width=True)


# =============================================================================
# PAGE 4: DELIVERY ANALYTICS
# =============================================================================
elif page == "🚚 Delivery Analytics":
    st.markdown('<h1 class="page-title">Fulfillment Velocity & Customer Experience</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Measuring door-to-door transit lead times, delivery SLA breach rates, and customer review penalties.</p>',
        unsafe_allow_html=True,
    )

    filt_orders, _ = apply_filters(data["orders"], data["items"], data["customers"], data["products"])
    deliv_orders = filt_orders[filt_orders["order_status"] == "delivered"].copy()

    if not deliv_orders.empty:
        deliv_orders["actual_delivery_days"] = (
            deliv_orders["order_delivered_customer_date"] - deliv_orders["order_purchase_timestamp"]
        ).dt.total_seconds() / 86400.0

        deliv_orders["estimated_days"] = (
            deliv_orders["order_estimated_delivery_date"] - deliv_orders["order_purchase_timestamp"]
        ).dt.total_seconds() / 86400.0

        deliv_orders["delay_days"] = (
            deliv_orders["order_delivered_customer_date"] - deliv_orders["order_estimated_delivery_date"]
        ).dt.total_seconds() / 86400.0

        deliv_orders["is_late"] = deliv_orders["delay_days"] > 0

        avg_transit = deliv_orders["actual_delivery_days"].mean()
        avg_promised = deliv_orders["estimated_days"].mean()
        late_rate = deliv_orders["is_late"].mean() * 100
        avg_buffer = avg_promised - avg_transit

        # Delivery KPIs
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Avg Actual Lead Time</h4>
                    <div class="metric-val">{avg_transit:.1f} Days</div>
                    <div class="metric-sub">Checkout to Doorstep</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with d2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Avg Promised SLA Window</h4>
                    <div class="metric-val">{avg_promised:.1f} Days</div>
                    <div class="metric-sub">Quoted Delivery Promise</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with d3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Late Delivery Rate</h4>
                    <div class="metric-val">{late_rate:.2f}%</div>
                    <div class="metric-sub">Breached Estimated Date</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with d4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>Estimation Buffer Gap</h4>
                    <div class="metric-val">+{avg_buffer:.1f} Days</div>
                    <div class="metric-sub">Safety Padding Buffer</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("###")

    # Delay vs Satisfaction Penalty Chart
    delay_df = exports["delay"]
    c1, c2 = st.columns([6, 4])

    with c1:
        if not delay_df.empty:
            fig_penalty = go.Figure()
            fig_penalty.add_trace(
                go.Bar(
                    x=delay_df["delay_bucket"],
                    y=delay_df["order_count"],
                    name="Orders Volume",
                    marker_color="#4A5568",
                    yaxis="y1",
                )
            )
            fig_penalty.add_trace(
                go.Scatter(
                    x=delay_df["delay_bucket"],
                    y=delay_df["avg_review_score"],
                    name="Average Review Rating (Stars)",
                    mode="lines+markers",
                    line=dict(color=COLOR_DANGER, width=3),
                    marker=dict(size=8),
                    yaxis="y2",
                )
            )
            fig_penalty.update_layout(
                title="<b>The Delivery Penalty: Customer Review Rating vs Timeliness Bucket</b>",
                template=PLOTLY_THEME,
                paper_bgcolor=COLOR_PAPER,
                plot_bgcolor=COLOR_PAPER,
                yaxis=dict(title="Order Count"),
                yaxis2=dict(
                    title="Average Review Score (1 to 5 Stars)",
                    overlaying="y",
                    side="right",
                    range=[1.0, 5.0],
                ),
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(x=0.02, y=0.95),
            )
            st.plotly_chart(fig_penalty, use_container_width=True)

    with c2:
        # Review score histogram
        if not data["reviews"].empty:
            rev_counts = data["reviews"]["review_score"].value_counts().sort_index().reset_index()
            rev_counts.columns = ["Score", "Count"]
            fig_rev = px.bar(
                rev_counts,
                x="Score",
                y="Count",
                color="Score",
                color_continuous_scale="Viridis",
                text="Count",
            )
            fig_rev.update_layout(
                title="<b>Review Rating Distribution (1 to 5 Stars)</b>",
                template=PLOTLY_THEME,
                paper_bgcolor=COLOR_PAPER,
                plot_bgcolor=COLOR_PAPER,
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig_rev, use_container_width=True)

    # State delivery speed breakdown
    st.markdown("### 🇧🇷 Delivery Speed & Late Rates Across Brazilian States")
    if not deliv_orders.empty:
        state_deliv = (
            deliv_orders.merge(data["customers"][["customer_id", "customer_state"]], on="customer_id", how="inner")
            .groupby("customer_state")
            .agg(
                avg_delivery_days=("actual_delivery_days", "mean"),
                avg_promised_days=("estimated_days", "mean"),
                late_delivery_rate=("is_late", lambda x: x.mean() * 100),
                order_volume=("order_id", "count"),
            )
            .reset_index()
            .sort_values("avg_delivery_days", ascending=False)
        )
        fig_st_deliv = px.bar(
            state_deliv,
            x="customer_state",
            y="avg_delivery_days",
            color="late_delivery_rate",
            color_continuous_scale="Reds",
            labels={"customer_state": "State", "avg_delivery_days": "Avg Days to Deliver", "late_delivery_rate": "Late Rate %"},
        )
        fig_st_deliv.update_layout(
            title="<b>Average Delivery Days by Destination State (Color = Late Rate %)</b>",
            template=PLOTLY_THEME,
            paper_bgcolor=COLOR_PAPER,
            plot_bgcolor=COLOR_PAPER,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        st.plotly_chart(fig_st_deliv, use_container_width=True)


# =============================================================================
# PAGE 5: GEOGRAPHIC ANALYTICS
# =============================================================================
elif page == "🗺️ Geographic Analytics":
    st.markdown('<h1 class="page-title">Geographic Logistics & Territorial Demand</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Mapping sales density, freight disparity, and customer concentration across Brazil’s 27 Federal Units.</p>',
        unsafe_allow_html=True,
    )

    filt_orders, filt_items = apply_filters(data["orders"], data["items"], data["customers"], data["products"])
    deliv_orders = filt_orders[filt_orders["order_status"] == "delivered"]

    # Merge customer state & coordinates
    ord_cst = deliv_orders.merge(
        data["customers"][["customer_id", "customer_state", "customer_zip_code_prefix"]],
        on="customer_id",
        how="inner"
    )
    ord_full = ord_cst.merge(filt_items[["order_id", "price", "freight_value"]], on="order_id", how="inner")

    # State level metrics
    state_geo = (
        ord_full.groupby("customer_state").agg(
            total_revenue=("price", "sum"),
            total_freight=("freight_value", "sum"),
            orders_count=("order_id", "nunique"),
            avg_order_value=("price", lambda x: x.sum() / ord_full.loc[x.index, "order_id"].nunique()),
            avg_freight=("freight_value", "mean"),
        ).reset_index().sort_values("total_revenue", ascending=False)
    )

    # 1. Geographic Map Visual
    st.markdown("### 📍 Interactive Territory Distribution Map")
    geo_df = data["geo"]
    if not geo_df.empty:
        # Sample coordinates for fast responsive web rendering (1,500 centroids)
        sample_geo = geo_df.sample(n=min(1500, len(geo_df)), random_state=42)

        fig_map = px.scatter_geo(
            sample_geo,
            lat="geolocation_lat",
            lon="geolocation_lng",
            color="geolocation_state",
            hover_name="geolocation_city",
            scope="south america",
            title="<b>Postal Centroid Density Across Brazilian Cities</b>",
        )
        fig_map.update_geos(
            showcountries=True,
            countrycolor="#4A5568",
            showcoastlines=True,
            coastlinecolor="#4A5568",
            fitbounds="locations",
            bgcolor=COLOR_BG,
        )
        fig_map.update_layout(
            template=PLOTLY_THEME,
            paper_bgcolor=COLOR_PAPER,
            height=500,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # 2. State-by-State Logistics Disparity & Freight Burden
    c1, c2 = st.columns([6, 4])
    with c1:
        fig_st_bubble = px.scatter(
            state_geo,
            x="avg_freight",
            y="avg_order_value",
            size="total_revenue",
            color="customer_state",
            hover_name="customer_state",
            text="customer_state",
            title="<b>Average Freight Cost vs Average Order Value by State</b>",
            labels={"avg_freight": "Avg Freight Charge (BRL R$)", "avg_order_value": "Avg Order Value (BRL R$)"},
        )
        fig_st_bubble.update_traces(textposition="top center")
        fig_st_bubble.update_layout(
            template=PLOTLY_THEME,
            paper_bgcolor=COLOR_PAPER,
            plot_bgcolor=COLOR_PAPER,
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig_st_bubble, use_container_width=True)

    with c2:
        st.markdown("#### 📋 Regional Performance Table")
        st_display = state_geo.copy()
        st_display["total_revenue"] = st_display["total_revenue"].apply(lambda v: f"R$ {v:,.0f}")
        st_display["total_freight"] = st_display["total_freight"].apply(lambda v: f"R$ {v:,.0f}")
        st_display["avg_order_value"] = st_display["avg_order_value"].apply(lambda v: f"R$ {v:.2f}")
        st_display["avg_freight"] = st_display["avg_freight"].apply(lambda v: f"R$ {v:.2f}")
        st_display.columns = ["State", "Total Revenue", "Total Freight", "Orders", "AOV", "Avg Freight"]
        st.dataframe(st_display.head(15), use_container_width=True, height=360)
