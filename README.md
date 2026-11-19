# E-Commerce Business Intelligence & Sales Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite%20Fallback-336791.svg)](https://www.sqlite.org/)
[![Dashboard](https://img.shields.io/badge/Streamlit-Interactive%20Web%20App-FF4B4B.svg)](https://streamlit.io/)
[![Power BI](https://img.shields.io/badge/Power%20BI-DAX%20Design%20Guide-F2C811.svg)](https://powerbi.microsoft.com/)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, end-to-end Business Intelligence, Data Engineering, and Sales Analytics platform built on the **Brazilian E-Commerce Public Dataset by Olist**. The platform analyzes **99,441 historical commercial orders** (96,478 delivered orders) placed across Brazil between **October 2016 and September 2018**.

This repository demonstrates a complete, production-ready analytics engineering lifecycle: automated ingestion of 9 relational tables, data quality auditing and cleaning, multi-dimensional feature engineering, relational schema design, Star Schema data warehousing, 30 production SQL analytical queries, statistical RFM customer segmentation, monthly cohort retention modeling, catalog Pareto 80/20 distribution analysis, an interactive 5-page Streamlit web dashboard, and an executive Power BI dashboard design specification with complete DAX measures.

---

## Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Ingestion["1. Ingestion & Validation"]
        A["Raw Olist CSVs (9 Files)"] --> B["DataLoader (src/data_loader.py)"]
        B --> C["Schema Profiler & Null Audit"]
    end

    subgraph Cleaning["2. Cleaning & Normalization"]
        C --> D["DataCleaner (src/data_cleaning.py)"]
        D --> E["Deduplication & Type Casting"]
        D --> F["Category Translation & Mapping"]
        D --> G["Centroid Aggregation (Geo)"]
        E & F & G --> H["Cleaned Staging (data/processed/)"]
    end

    subgraph FeatureEngineering["3. Feature Engineering"]
        H --> I["FeatureEngineer (src/feature_engineering.py)"]
        I --> J["Temporal Decompositions"]
        I --> K["Delivery Lead Time & SLA Delays"]
        I --> L["Repeat Customer & Spend Features"]
    end

    subgraph Warehouse["4. Data Warehousing & Star Schema"]
        J & K & L --> M["DatabaseManager (src/database.py)"]
        M --> N[("Database Engine\nPostgreSQL supported\nSQLite fallback utilized")]
        N --> O["FactSales (Line Grain)"]
        N --> P["DimDate, DimCustomer, DimProduct, DimSeller, DimGeography"]
    end

    subgraph Analytics["5. Analytics & Statistical Modeling"]
        N --> Q["30 Production SQL Queries (sql/)"]
        Q --> R["RFM Segmentation (Recency, Frequency, Monetary)"]
        Q --> S["Monthly Cohort Retention Matrix"]
        Q --> T["Pareto 80/20 SKU Revenue Concentration"]
        Q --> U["Delivery Delay vs Review Correlation"]
    end

    subgraph BI["6. Presentation & Interactive BI"]
        R & S & T & U --> V["Streamlit Interactive App (app.py)"]
        R & S & T & U --> W["Power BI Design Guide & DAX (powerbi/)"]
        R & S & T & U --> X["Executive Reports & Recommendations (reports/)"]
    end
```

---

## 1. Project Overview & Business Problem

Olist connects independent small merchants across Brazil to Brazil's leading e-commerce marketplaces (Mercado Livre, B2W, Amazon Brazil). While processing over **R$ 15.4M in Gross Merchandise Value (GMV)** across 2016–2018, leadership required data-driven insights into five existential commercial bottlenecks:

1. **Severe Customer Retention Bottleneck:** Does the marketplace drive sustainable recurring customer loyalty, or does it function merely as an expensive one-time acquisition funnel?
2. **Logistics & Customer Review Penalty:** What is the quantified customer review penalty for late deliveries, and which states experience the most severe logistics delays?
3. **Supplier & Product Concentration Risk:** How dependent is marketplace revenue on a handful of top merchants and bestselling SKUs?
4. **Unit Economics & Monetization Ceilings:** What is the realistic Customer Lifetime Value (CLV) and marketplace commission monetization ceiling given that the platform captures marketplace take-rate commission rather than merchant retail margins?
5. **Geographic Demand Disparities:** How concentrated is consumer spending in the Southeast compared to underserved Northern and Northeastern territories?

---

## 2. Dataset Structure

The analysis is conducted on the historical **Brazilian E-Commerce Public Dataset by Olist** covering commercial orders from **2016 to 2018**:

| Dataset File | Records Analyzed | Grain / Description | Key Identifiers |
| :--- | :--- | :--- | :--- |
| `olist_orders_dataset.csv` | 99,441 rows | Order level; lifecycle statuses and 5 timestamps | `order_id`, `customer_id` |
| `olist_order_items_dataset.csv` | 112,650 rows | Item line level; item sequence, price, freight | `order_id`, `order_item_id`, `product_id`, `seller_id` |
| `olist_customers_dataset.csv` | 99,441 rows | Customer mapping token to unique physical buyer | `customer_id`, `customer_unique_id`, `customer_zip_code_prefix` |
| `olist_products_dataset.csv` | 32,951 rows | Product catalog specifications, dimensions, weight | `product_id`, `product_category_name` |
| `olist_sellers_dataset.csv` | 3,095 rows | Merchant location and zip code prefixes | `seller_id`, `seller_zip_code_prefix` |
| `olist_order_payments_dataset.csv` | 103,877 rows | Payment sequence, type, installments, value | `order_id`, `payment_sequential`, `payment_type` |
| `olist_order_reviews_dataset.csv` | 99,224 rows | Customer satisfaction rating (1–5) and review text | `review_id`, `order_id`, `review_score` |
| `olist_geolocation_dataset.csv` | 1,000,163 rows | Raw GPS coordinates aggregated into 19,011 zip centroids | `geolocation_zip_code_prefix`, `geolocation_lat`, `geolocation_lng` |
| `product_category_name_translation.csv` | 71 rows | Portuguese-to-English category translation mapping | `product_category_name`, `product_category_name_english` |

> **Setup Note:** Refer to [DATASET_SETUP.md](DATASET_SETUP.md) for Kaggle download instructions. The pipeline automatically validates and cleans the raw data.

---

## 3. Technology Stack

- **Data Engineering & Pipeline:** Python 3.12, Pandas, NumPy
- **Database & Dimensional Modeling:**
  - **PostgreSQL 14+:** Full ANSI SQL DDL, referential constraints, performance indexes, and analytical queries supported.
  - **SQLite 3 (Verified Local Engine):** Fully functional fallback engine utilized during local execution (`data/processed/ecommerce_analytics.db`, 111.5 MB), guaranteeing zero-external-dependency reproducibility.
- **SQL Analytics:** 30 production queries utilizing advanced window functions (`LAG`, `ROW_NUMBER`, `PERCENT_RANK`, cumulative `SUM`), CTEs, and cohort aggregations.
- **Interactive Business Intelligence:** Streamlit 1.51+, Plotly 7.1+ (interactive multi-page web application in `app.py`).
- **Power BI Asset Suite:** 5-page dashboard architectural specification (`powerbi/dashboard_design.md`) and production DAX measure formulas (`powerbi/dax_measures.md`).
- **Automated Testing:** Pytest 9.1+ (**17 automated unit tests**, 100% pass rate).
- **Environment Management:** Python-dotenv, Psycopg2-binary, SQLAlchemy 2.0.

---

## 4. Directory & Project Structure

The project repository is structured as follows:

```text
ecommerce-business-intelligence/
├── data/
│   ├── raw/                                  # Raw Olist CSV datasets (9 source files)
│   ├── processed/                            # Cleaned CSVs & local analytical SQLite DB
│   │   ├── cleaned_customers.csv
│   │   ├── cleaned_geolocation.csv
│   │   ├── cleaned_order_items.csv
│   │   ├── cleaned_orders.csv
│   │   ├── cleaned_payments.csv
│   │   ├── cleaned_products.csv
│   │   ├── cleaned_reviews.csv
│   │   ├── cleaned_sellers.csv
│   │   └── ecommerce_analytics.db            # 111.5 MB local analytical data warehouse
│   └── exports/                              # Analytical CSV summaries & static charts
│       ├── 01_order_status_distribution.png
│       ├── 02_payment_method_distribution.png
│       ├── 03_top_states_distribution.png
│       ├── 04_monthly_order_trend.png
│       ├── 05_rfm_revenue_by_segment.png
│       ├── 06_cohort_retention_heatmap.png
│       ├── 07_delivery_delay_vs_satisfaction.png
│       ├── cohort_customer_counts.csv
│       ├── cohort_retention_percentages.csv
│       ├── delivery_delay_satisfaction_summary.csv
│       ├── product_pareto_analysis.csv
│       ├── rfm_customer_level.csv
│       └── rfm_segment_summary.csv
├── notebooks/
│   ├── 01_data_exploration.ipynb             # Initial dataset profiling and null audit
│   ├── 02_data_cleaning.ipynb                # Step-by-step cleaning transformations
│   ├── 03_exploratory_data_analysis.ipynb    # Feature distributions and correlations
│   └── 04_business_insights.ipynb            # RFM clustering and cohort retention curves
├── src/
│   ├── config.py                             # Configuration, directory paths, database URIs
│   ├── data_loader.py                        # Ingestion, validation, and profiling engine
│   ├── data_cleaning.py                      # Cleansing, type coercion, and centroid aggregation
│   ├── feature_engineering.py                # Lead times, delay flags, and customer metrics
│   ├── database.py                           # SQLAlchemy manager, DDL execution, Star Schema loader
│   └── analysis.py                           # RFM, cohort retention, and Pareto analytical engines
├── sql/
│   ├── 01_database_schema.sql                # Relational DDL + Star Schema DDL + Indexes
│   ├── 02_data_validation.sql                # Uniqueness audits and referential foreign key checks
│   ├── 03_sales_analysis.sql                 # Queries 1–8: Revenue, AOV, YoY velocity, category share
│   ├── 04_customer_analysis.sql              # Queries 9–14: Repeat buyers, spenders, RFM scoring
│   ├── 05_product_analysis.sql               # Queries 15–19: Top/bottom categories, freight burdens
│   ├── 06_delivery_analysis.sql              # Queries 20–24: Lead time, SLA breach rates, review impact
│   └── 07_advanced_analysis.sql              # Queries 25–30: Cohort matrix, CLV, Pareto 80/20, seasonality
├── powerbi/
│   ├── dashboard_design.md                   # 5-page executive dashboard wireframes & UI specs
│   ├── dax_measures.md                       # Complete production library of DAX measures
│   └── dashboard_screenshots/                # Visual design reference directory
├── reports/
│   ├── executive_summary.md                  # Comprehensive answers to 10 executive business questions
│   ├── business_recommendations.md           # 5 prioritized strategic initiatives with ROI models
│   ├── data_quality_report.md                # Before/after cleaning data quality audit
│   └── raw_data_exploration_report.md        # Comprehensive exploratory data profiling summary
├── tests/
│   ├── test_data_cleaning.py                 # Tests for cleaning rules and normalization
│   ├── test_data_validation.py               # Tests for schema integrity and missing file detection
│   └── test_metrics.py                       # Tests for feature engineering, RFM, and retention
├── app.py                                    # Interactive 5-page Streamlit web dashboard
├── run_app.bat                               # Windows one-click batch launcher for dashboard
├── requirements.txt                          # Python package dependencies
├── .env.example                              # Environment variable template
├── .gitignore                                # Git ignore rules
├── DATASET_SETUP.md                          # Raw dataset download documentation
├── README.md                                 # Master project documentation
└── main.py                                   # Master pipeline orchestration entrypoint
```

---

## 5. Verified Key Findings & Business Insights

Every numerical finding reported below has been strictly audited and verified against the actual generated data warehouse and exported analytical tables:

### 1. High-Level Platform Scale & Sales Performance
- **Delivered Orders:** **96,478 orders** (out of 99,441 total orders across all statuses).
- **Net Product Merchandise Revenue:** **R$ 13,221,498.11** (delivered orders).
- **Total Shipping Freight Collected:** **R$ 2,198,275.64** (~14.2% of total delivered transaction value).
- **Average Order Value (AOV):** **R$ 137.04** per delivered order.
- **Top Product Categories (by delivered revenue):**
  1. *Health & Beauty (`health_beauty`):* **R$ 1,233,131.72** (9.33% share, 9,465 items)
  2. *Watches & Gifts (`watches_gifts`):* **R$ 1,166,176.98** (8.82% share, 5,859 items)
  3. *Bed, Bath & Table (`bed_bath_table`):* **R$ 1,023,434.76** (7.74% share, 10,953 items)
  4. *Sports & Leisure (`sports_leisure`):* **R$ 954,852.55** (7.22% share, 8,431 items)
  5. *Computers & Accessories (`computers_accessories`):* **R$ 888,724.61** (6.72% share, 7,644 items)
  - Together, the top 5 categories drive **R$ 5,266,320.62 (39.83%)** of all delivered merchandise revenue.

### 2. Product Catalog Pareto 80/20 Distribution (Verified: 25.90%)
- **Empirical Pareto Result:** Analysis of all 32,951 catalog products (`product_pareto_analysis.csv`) reveals that **8,535 products (25.90% of the catalog)** generate **80.0% of total revenue**.
- *(Clarification on Earlier Literature / Drafts):* Preliminary hypotheses often quote a textbook theoretical 80/20 ratio or 18.2%. The verified empirical calculation from this dataset confirms that **25.90% of catalog SKUs** generate 80% of revenue (and **25.93%** of SKUs sold in delivered orders).
- **Long-Tail Inefficiency:** Over **39.7% of catalog SKUs (13,115 products)** belong to Class C, generating only the bottom 5% of marketplace revenue. Over 50% of distinct catalog products sold only 1 unit across the entire two-year historical window.

### 3. Customer Retention & Repeat Purchasing Bottleneck
- **Unique Customers Analyzed:** **93,358 distinct buyers** with delivered orders (96,096 across all order statuses).
- **The One-Time Purchase Dilemma:** **90,557 buyers (97.00%)** made only a single purchase.
- **Repeat Customers:** Only **2,801 buyers (3.00%)** completed two or more delivered purchases.
- **Spend Multiplier:** While repeat customers comprise only 3.00% of the customer base, they generated **R$ 728,408.75 in product revenue (5.51%)**. Repeat buyers spend an average of **R$ 260.05** over their lifetime compared to **R$ 137.96** for one-time buyers—an **+88.5% spend premium**.
- **Cohort Retention Collapse:** Tracking monthly acquisition cohorts across 2017–2018 shows that **Month 1 retention drops below 0.8%** across nearly all cohorts, confirming that Olist operates primarily as a top-of-funnel customer acquisition gateway rather than a sticky repeat destination.

### 4. Logistics Lead Times & The Review Score Penalty
- **Overall Delivery Timeliness:** Orders arriving early or on time average a **4.29★ customer rating** (62.3% 5-star, 6.5% 1-star).
- **Empirical Review Collapse from Delay Buckets (`delivery_delay_satisfaction_summary.csv`):**
  - *Slight Delay (1–5 days late):* Average review score falls to **3.46★** (22.0% 1-star ratings).
  - *Moderate Delay (6–10 days late):* Average review score collapses to **1.89★** (64.3% 1-star ratings).
  - *Severe Delay (11–20 days late):* Average review score falls to **1.66★** (70.0% 1-star ratings).
  - *Extreme Delay (>20 days late):* Average review score drops to **1.76★** (68.9% 1-star ratings).
- **SLA Breach Rate:** **7,652 delivered orders (7.9%)** arrived after the promised delivery date. A delivery delay greater than 5 days increases the likelihood of a 1-star review by **more than 980%**.

### 5. Geographic Concentration & Regional Logistics Disparity
- **Southeast Dominance:**
  - **São Paulo (SP):** Generates **41.98% of delivered orders** (40,501 orders) and **38.33% of revenue** (R$ 5.07M).
  - **Rio de Janeiro (RJ):** Generates **12.80% of orders** (12,350 orders) and **13.31% of revenue** (R$ 1.76M).
  - **Minas Gerais (MG):** Generates **11.77% of orders** (11,354 orders) and **11.74% of revenue** (R$ 1.55M).
  - The Southeast region (SP, RJ, MG) commands **66.55% of national delivered orders** and **63.38% of platform merchandise revenue**.
- **Transit Time Disparity:**
  - *Fastest Delivery:* São Paulo consumers receive orders in **8.8 days** on average.
  - *Slowest Delivery:* Deliveries to Northern/Northeastern states take nearly a month: **Roraima (29.4 days)**, Amapá (27.2 days), Amazonas (26.4 days), Alagoas (24.5 days), and Pará (23.8 days).

### 6. Seller Concentration & Marketplace Supplier Risk
- **Total Active Sellers:** 3,095 registered merchants.
- **Supply Dependency:**
  - **Top 1% of sellers (30 merchants):** Generate **25.67% of total revenue** (R$ 3.49M).
  - **Top 5% of sellers (154 merchants):** Generate **53.18% of total revenue** (R$ 7.23M).
  - **Top 10% of sellers (309 merchants):** Generate **67.49% of total revenue** (R$ 9.17M).
  - **543 sellers (17.5% of seller base)** generate 80% of total marketplace revenue.

---

## 6. Analytical Visualizations & Dashboard

### 1. Generated Analytical Charts
The automated analytics engine exports publication-ready visualizations directly to `data/exports/`:

| Visual Focus | Chart Output File | Key Finding Highlight |
| :--- | :--- | :--- |
| **Order Status Distribution** | `data/exports/01_order_status_distribution.png` | 97.0% delivered orders; 0.6% cancelled; 0.6% unavailable. |
| **Payment Method Distribution** | `data/exports/02_payment_method_distribution.png` | Credit cards account for 75.4% of checkout value (avg 3.5 installments). |
| **Geographic State Volume** | `data/exports/03_top_states_distribution.png` | SP represents 42.0% of orders; SE region represents 66.6% of volume. |
| **Monthly Order Trends** | `data/exports/04_monthly_order_trend.png` | Rapid growth from 2017 to peak in late 2017 (Black Friday surge). |
| **RFM Segment Revenue** | `data/exports/05_rfm_revenue_by_segment.png` | Champions & Loyal buyers deliver outsized lifetime value. |
| **Cohort Retention Heatmap** | `data/exports/06_cohort_retention_heatmap.png` | Month 1 repeat retention drops below 0.8% across monthly cohorts. |
| **Delivery Delay vs Rating** | `data/exports/07_delivery_delay_vs_satisfaction.png` | Reviews collapse from 4.29★ on-time to <1.9★ when delayed >5 days. |

### 2. Interactive Web Dashboard (`app.py`)
In addition to static chart exports, the repository provides an interactive multi-page web application built with **Streamlit** and **Plotly**:
- **Page 1: Executive Overview:** High-level KPIs, monthly revenue trajectory, order status breakdown, and state volume charts.
- **Page 2: Customer Analytics & RFM:** Interactive RFM customer segment scatter plots, segment distribution bar charts, and monthly cohort retention heatmaps.
- **Page 3: Product & Pareto Analytics:** Top revenue categories, top individual products, and interactive Pareto 80/20 cumulative revenue curves.
- **Page 4: Delivery & Lead Time Analytics:** Lead time distribution histograms, late delivery buckets, and review score correlation charts.
- **Page 5: Geographic Analytics:** Interactive state-level revenue and order choropleth maps with regional fulfillment filters.

---

## 7. Power BI Dashboard Architecture & DAX Modeling

Rather than committing a static proprietary binary file, the repository provides a comprehensive **Enterprise Power BI Implementation Specification**:

- **[powerbi/dashboard_design.md](powerbi/dashboard_design.md):** Detailed wireframe blueprints for a 5-page executive dashboard formatted in an executive dark navy theme (`#0A192F`), complete with layout grids, card visual KPIs, slicers, and filter interactions.
- **[powerbi/dax_measures.md](powerbi/dax_measures.md):** Complete, production-ready DAX measure formulas, including:
  - `[Total Revenue]` = `SUM(fact_sales[price])`
  - `[AOV]` = `DIVIDE([Total Revenue], DISTINCTCOUNT(fact_sales[order_id]), 0)`
  - `[On-Time Delivery Rate %]` = `DIVIDE(CALCULATE(COUNTROWS(fact_sales), fact_sales[is_late] = 0), COUNTROWS(fact_sales), 0)`
  - `[Revenue YoY Growth %]` using `SAMEPERIODLASTYEAR()`
  - `[Repeat Customer Rate %]` and dynamic RFM segmentation measures.

---

## 8. Strategic Business Recommendations

Based on empirical data findings, 5 prioritized strategic initiatives are detailed in [reports/business_recommendations.md](reports/business_recommendations.md):

1. **Automated Replenishment Engine (Priority 1):** Deploy automated email/SMS reorder reminders at 45/60/90 days for consumable categories (*Health & Beauty*, *Pet Supplies*) to lift repeat buyer rates from 3.0% to 6.0%, capturing an estimated R$ 900,000+ in zero-CAC revenue.
2. **Dynamic Machine Learning Delivery Promise (Priority 1):** Replace conservative static state-level delivery estimates (which quote 11.2 days later than actual arrival) with dynamic postal-code ML models to eliminate top-of-funnel checkout cart abandonment in São Paulo and the Southeast.
3. **Merchant Dispatch SLAs & Incentive Rebates (Priority 2):** Institute a 1.0% marketplace commission rebate for sellers scanning packages within 24 hours of approval. High-velocity sellers average 4.35★ versus 3.65★ for sellers taking >4 days to dispatch.
4. **Northeastern Regional Fulfillment Cross-Docking (Priority 2):** Establish a regional 3PL cross-docking hub in Recife or Salvador to cut delivery times to Northern/Northeastern states from 25–29 days down to 8–10 days, unlocking 50M+ consumers.
5. **Catalog Rationalization & Class A SKU Stock Protection (Priority 3):** Focus supply chain inventory buffers on the **8,535 Class A SKUs** driving 80% of sales, while consolidating near-zero-turnover categories.

---

## 9. Setup & Execution Instructions

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git
- Modern Web Browser (for interactive dashboard)

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/priyanshusharma318/ecommerce-business-intelligence.git
cd ecommerce-business-intelligence

python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 2: Download Dataset Files
1. Download the Brazilian E-Commerce dataset from Kaggle: [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
2. Extract all 9 CSV files into the `data/raw/` directory (see [DATASET_SETUP.md](DATASET_SETUP.md) for detailed file naming checklist).

### Step 3: Run the Automated Unit Test Suite
Execute the test suite to verify data cleaning logic, schema integrity, and RFM calculations:
```bash
pytest tests -v
```
*(Executes all **17 automated unit tests**; all 17 tests should pass).*

### Step 4: Execute Master Data Pipeline
Run the end-to-end data pipeline to clean the raw data, generate engineered features, build the Star Schema database, execute SQL queries, and generate analytical exports:
```bash
python main.py
```
*(By default, the platform checks for PostgreSQL and automatically falls back to the embedded high-performance SQLite engine `data/processed/ecommerce_analytics.db`).*

### Step 5: Launch Interactive Web Dashboard
To explore the interactive Business Intelligence dashboard:
```bash
streamlit run app.py
```
*Or on Windows, simply double-click [run_app.bat](run_app.bat).*  
The application will open automatically at `http://localhost:8501`.

---

## 10. Project Limitations & Analytical Boundaries

To maintain rigorous data integrity, the following boundaries and constraints are explicitly acknowledged:

1. **Historical Dataset Window (2016–2018):** All metrics reflect Brazilian e-commerce operations between late 2016 and late 2018. Economic conditions, postal carrier dynamics, and marketplace market share have evolved since this period.
2. **Absence of Merchant COGS & Ad Spend Data:** The Olist public dataset includes merchandise sale prices and freight charges, but does not provide supplier Cost of Goods Sold (COGS) or Google/Meta marketing customer acquisition costs (CAC). Therefore, financial metrics represent **Gross Merchandise Value (GMV)**, **Merchandise Revenue**, and **Estimated Platform Take-Rate Commission**, rather than merchant net operating margins.
3. **Database Engine Implementation:** The pipeline provides complete DDL for enterprise PostgreSQL. In local standalone environments without active PostgreSQL instances, the pipeline utilizes SQLite as an automated fallback. All 30 analytical queries and Star Schema tables are fully compatible and populated in SQLite.
4. **Postal Logistics Dependency:** Over 90% of seller dispatches in this period relied on the Brazilian public postal service (*Correios*), meaning transit times and delivery volatility reflect postal carrier infrastructure.

---

## 11. Verification Audit Summary

Every claim in this documentation has been verified against the actual generated project assets:

| Claim / Metric | Documented Value | Empirical Verification Source | Verification Status |
| :--- | :--- | :--- | :--- |
| **Catalog Pareto Revenue** | 25.90% of SKUs generate 80% revenue | `product_pareto_analysis.csv` (8,535 / 32,951 SKUs) | **VERIFIED** |
| **Total Delivered Orders** | 96,478 orders | `cleaned_orders.csv` & SQLite `orders` table | **VERIFIED** |
| **Net Product Revenue** | R$ 13,221,498.11 | `fact_sales` price aggregation | **VERIFIED** |
| **One-Time Customer Rate** | 97.00% (90,557 customers) | `customers` joined to delivered `orders` | **VERIFIED** |
| **Repeat Customer Rate** | 3.00% (2,801 customers) | `customers` joined to delivered `orders` | **VERIFIED** |
| **Repeat Customer Spend** | R$ 260.05 avg (+88.5% over 1-time) | Customer lifetime aggregation on delivered orders | **VERIFIED** |
| **Top 5% Seller Concentration**| 53.18% of revenue (R$ 7.23M) | `fact_sales` seller revenue cumulative distribution | **VERIFIED** |
| **Top 1% Seller Concentration**| 25.67% of revenue (R$ 3.49M) | `fact_sales` seller revenue cumulative distribution | **VERIFIED** |
| **SP State Order Share** | 41.98% of orders (40,501 orders) | `cleaned_orders.csv` joined to `cleaned_customers.csv` | **VERIFIED** |
| **Southeast (SP/RJ/MG) Share** | 66.55% orders, 63.38% revenue | Customer state aggregation on delivered orders | **VERIFIED** |
| **Delivery Delay vs Rating** | 4.29★ on-time, 3.46★ (1–5d late), 1.89★ (6–10d late), 1.66★ (11–20d late) | `delivery_delay_satisfaction_summary.csv` | **VERIFIED** |
| **Automated Unit Tests** | 17 passed in 12.30s | Pytest suite (`tests/`) execution | **VERIFIED** |
| **Database Execution** | SQLite fallback used (`111.5 MB`) | `data/processed/ecommerce_analytics.db` | **VERIFIED** |
| **Interactive Dashboard** | 5 pages active on `app.py` | Streamlit server verified live on `http://localhost:8501` | **VERIFIED** |
