# Power BI Dashboard Architecture & UI/UX Specification

## 1. Executive Summary & Design System

This document outlines the end-to-end design specification for the **Olist E-Commerce Executive Business Intelligence Platform** in Power BI Desktop. The design provides senior leaders, operations directors, and commercial heads with an intuitive, executive-grade decision cockpit.

### Visual Design System
- **Theme:** Executive Dark Navy & Precision Blue
- **Canvas Resolution:** 1920 x 1080 (16:9 1080p Widescreen)
- **Grid Layout:** 12-column responsive grid with 16px margins and 12px gutter spacing.
- **Typography:**
  - Header & KPI Numbers: *Segoe UI Semibold / Bold*
  - Body & Axis Labels: *Segoe UI Regular*
  - Card Data Labels: 24pt Bold
  - Visual Titles: 12pt Bold (Upper Camel Case)

### Color Palette (Hex Codes)
| Element | Hex Code | Semantic Purpose |
| :--- | :--- | :--- |
| **Canvas Background** | `#0B132B` | Deep dark slate navy providing high contrast and executive polish |
| **Card / Visual Container** | `#1C2541` | Elevated dark container with 8px border-radius and subtle drop shadow |
| **Primary Blue** | `#3A86FF` | Primary metric bars, line trends, active slicer selections |
| **Secondary Cyan** | `#4CC9F0` | Prior period comparisons, secondary series, and highlights |
| **Accent Gold** | `#FFB703` | Target lines, warning indicators, and VIP/Champion customer badges |
| **Success Emerald** | `#06D6A0` | Positive YoY growth, on-time deliveries, 5-star review ratings |
| **Danger Coral** | `#EF476F` | Late deliveries, order cancellations, 1-star reviews, and churn risk |
| **Text Primary** | `#FFFFFF` | Primary headers, KPI values, and visual titles |
| **Text Muted** | `#8D99AE` | Axis descriptions, sub-labels, and metadata timestamps |

---

## 2. Dimensional Data Model & Relationships (Star Schema)

The Power BI tabular data model implements a strict Star Schema to ensure high VertiPaq engine compression and sub-second query performance:

```
           +--------------------+
           |      DimDate       |
           | (DateKey, Year...) |
           +---------+----------+
                     | 1
                     |
                     | * (order_date_key)
           +---------v----------+
           |     FactSales      |
           | (order_id, price,  |
           |  freight, status)  |
           +----+----+----+-----+
              * |    | *  | *
      +---------+    |    +---------+
    1 |            1 |            1 |
+-----v-------+  +---v-------+  +---v------+
| DimCustomer |  | DimProduct|  | DimSeller|
+-------------+  +-----------+  +----------+
```

### Relationship Matrix:
1. `DimDate[date_key]` (1) ───> `FactSales[order_date_key]` (*) [Single Direction]
2. `DimCustomer[customer_id]` (1) ───> `FactSales[customer_id]` (*) [Single Direction]
3. `DimProduct[product_id]` (1) ───> `FactSales[product_id]` (*) [Single Direction]
4. `DimSeller[seller_id]` (1) ───> `FactSales[seller_id]` (*) [Single Direction]
5. `DimGeography[geolocation_zip_code_prefix]` (1) ───> `DimCustomer[customer_zip_code_prefix]` (*) [Single Direction]

---

## 3. Global Filter & Navigation Header

Every report page shares a standardized top navigation banner:
- **Left:** Company Logo ("OLIST BI EXECUTIVE SUITE") + Page Title
- **Center:** Dynamic Date Range Slicer (Relative Date Filtering + Year / Quarter dropdown)
- **Right:** Universal State Slicer (`customer_state`), Category Slicer (`product_category_name_english`), and Reset Filters button.

---

## 4. Five-Page Detailed Visual Blueprint

### PAGE 1: EXECUTIVE OVERVIEW
*Goal: 10-second pulse check on platform revenue, volume, customer count, and operational health.*

1. **Top KPI Ribbon (5 High-Impact Cards across the top):**
   - **Card 1: Total Revenue:** `[Total Revenue]` (Formatted: R$ 13.5M, sub-label: MoM % Growth)
   - **Card 2: Total Orders:** `[Total Orders]` (Formatted: 96.5K Delivered Orders)
   - **Card 3: Unique Customers:** `[Total Customers]` (Formatted: 93.4K Unique Buyers)
   - **Card 4: Average Order Value:** `[Average Order Value]` (Formatted: R$ 140.20)
   - **Card 5: Average Review Score:** `[Average Review Score]` (Formatted: 4.15 ★)

2. **Visual 1 (Area / Line Chart - Left 60% Width):**
   - *Title:* Monthly Gross Revenue Trajectory & 3-Month Moving Average
   - *X-Axis:* `DimDate[Year-Month]`
   - *Y-Axis:* `[Total Revenue]`, `[3M Moving Avg Revenue]`
   - *Data Colors:* Primary Blue `#3A86FF` with semi-transparent fill; Gold accent for moving average line.

3. **Visual 2 (Horizontal Stacked Bar Chart - Right 40% Width):**
   - *Title:* Top 7 Merchandise Categories by Revenue Share
   - *Y-Axis:* `DimProduct[product_category_name_english]`
   - *X-Axis:* `[Total Revenue]`
   - *Data Labels:* Revenue in Millions + % of Total.

4. **Visual 3 (Filled Map / Shape Map - Bottom Left 40% Width):**
   - *Title:* Order Revenue Density by Brazilian State (UF)
   - *Location:* `DimCustomer[customer_state]`
   - *Color Saturation:* `[Total Revenue]` (Diverging palette: light blue to deep navy `#0B132B`).

5. **Visual 4 (Donut Chart - Bottom Right 30% Width):**
   - *Title:* Payment Method Breakdown
   - *Legend:* `order_payments[payment_type]` (Credit Card, Boleto, Voucher, Debit)
   - *Values:* `[Total Payment Value]`

---

### PAGE 2: SALES PERFORMANCE & COMMERCIAL MOMENTUM
*Goal: Deep commercial inspection of revenue growth, seasonality, pricing, and basket size.*

1. **Visual 1 (Clustered Column & Line Combo Chart):**
   - *Title:* Monthly Delivered Revenue vs. Month-over-Month Growth %
   - *Columns:* `[Total Revenue]`
   - *Line:* `[Month-over-Month Growth %]`
   - *Conditional Formatting:* Columns turn Danger Coral `#EF476F` when MoM growth < 0.

2. **Visual 2 (Matrix Table with Heatmap Bars):**
   - *Title:* Year-over-Year Monthly Revenue Performance Matrix (2017 vs 2018)
   - *Rows:* `DimDate[Month Name]`
   - *Columns:* `DimDate[Year]`
   - *Values:* `[Total Revenue]`, `[YoY Revenue Growth %]`

3. **Visual 3 (Decomposition Tree / Drill-Through):**
   - *Title:* Revenue Breakdown by Category -> Sub-Product -> Seller State
   - *Root Metric:* `[Total Revenue]`
   - *Explain By:* `DimProduct[Category]`, `DimSeller[seller_state]`, `DimDate[Year]`

4. **Visual 4 (Scatter Plot):**
   - *Title:* Average Product Price vs. Order Volume by Category
   - *X-Axis:* `[Average Product Price]` (Logarithmic scale option)
   - *Y-Axis:* `[Total Items Sold]`
   - *Bubble Size:* `[Total Revenue]`

---

### PAGE 3: CUSTOMER ANALYTICS & RETENTION
*Goal: Reveal the customer acquisition funnel, repeat purchase frequency, and RFM segments.*

1. **KPI Mini-Ribbon:**
   - *Total Unique Buyers:* 93.4K | *Repeat Customers:* 2.8K | *Repeat Buyer Rate:* 3.0% | *Avg Lifetime Spend:* R$ 142.10

2. **Visual 1 (Treemap):**
   - *Title:* Customer Distribution across RFM Behavioral Segments
   - *Group:* `[Customer RFM Segment]` (Champions, Loyal Customers, Promising, At Risk, Lost)
   - *Values:* `[Customer Count]`
   - *Color Details:* Champions = Gold `#FFB703`, Loyal = Emerald `#06D6A0`, At Risk = Coral `#EF476F`.

3. **Visual 2 (Cohort Retention Heatmap Matrix):**
   - *Title:* Monthly Cohort Customer Retention Matrix (% Returning)
   - *Rows:* `Cohort Month` (First purchase month)
   - *Columns:* `Month Offset` (+1, +2, +3, +4, +5, +6...)
   - *Values:* `[Cohort Retention %]` with background color gradient.

4. **Visual 3 (Stacked Bar Chart - 100% Normalized):**
   - *Title:* Monthly Order Mix: First-Time Buyers vs. Returning Customers
   - *X-Axis:* `DimDate[Year-Month]`
   - *Y-Axis:* `% Share of Orders`
   - *Series:* `New Customer Orders` vs. `Returning Customer Orders`

---

### PAGE 4: PRODUCT & SELLER ECOSYSTEM
*Goal: Monitor marketplace supplier quality, catalog turnover velocity, and freight burdens.*

1. **Visual 1 (Pareto Dual-Axis Chart):**
   - *Title:* Product Pareto Analysis: Cumulative Revenue vs. Catalog SKUs
   - *X-Axis:* Product SKUs ranked by revenue
   - *Bar:* Individual Product Revenue
   - *Line:* Cumulative Revenue Share % (with 80% reference threshold line)

2. **Visual 2 (Top 10 Sellers Leaderboard Table):**
   - *Columns:* Seller ID, Seller State, Completed Orders, Total Generated Revenue, Avg Dispatch Delay, Avg Review Rating ★.

3. **Visual 3 (Bar Chart):**
   - *Title:* Freight-to-Price Burden Ratio by Product Category (%)
   - *Y-Axis:* Category Name
   - *X-Axis:* `[Freight to Price Ratio %]`

---

### PAGE 5: DELIVERY LOGISTICS & CUSTOMER SATISFACTION
*Goal: Diagnose supply-chain delivery bottlenecks, late delivery rates, and review ratings.*

1. **KPI Ribbon:**
   - *Avg Delivery Days:* 12.5 Days | *Late Delivery Rate:* 7.8% | *Avg Review Score:* 4.15 ★ | *1-Star Review Rate:* 11.5%

2. **Visual 1 (Clustered Column Chart):**
   - *Title:* Actual Delivery Days vs. Quoted Estimated Delivery Days by State
   - *X-Axis:* `DimCustomer[customer_state]` (Sorted by actual delivery days descending)
   - *Series 1:* `[Avg Delivery Days]` (Dark Navy Bar)
   - *Series 2:* `[Avg Estimated Delivery Days]` (Light Blue Bar)

3. **Visual 2 (Bar & Line Combo Chart):**
   - *Title:* The Delivery Penalty: Customer Review Rating by Fulfillment Timeliness Bucket
   - *X-Axis:* Punctuality Tier (5+ Days Early, On-Time, 1-5 Days Late, >10 Days Late)
   - *Bars (Left Y):* Order Volume in Tier
   - *Line (Right Y):* Average Customer Review Rating (1 to 5 Stars)

4. **Visual 3 (Scatter Plot / Correlation):**
   - *Title:* Delivery Delay in Days vs. Review Score
   - *X-Axis:* `Delivery Delay Days`
   - *Y-Axis:* `Review Score`
