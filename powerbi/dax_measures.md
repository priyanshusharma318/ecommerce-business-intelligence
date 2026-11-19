# Comprehensive DAX Measures Library for Power BI

This library contains production-grade, optimized Data Analysis Expressions (DAX) measures developed for the **Olist E-Commerce Business Intelligence Platform**.

All measures are organized into dedicated display folders within a disconnected measure table named `_Measures` or directly inside the `FactSales` model table.

---

## 1. Core Financial & Volume Measures

### 1.1 Total Revenue
```dax
Total Revenue = 
CALCULATE(
    SUM(FactSales[price]),
    FactSales[order_status] = "delivered"
)
```
- **Calculation Explanation:** Computes the total product merchandise sales value across all delivered order items. Strictly uses `FactSales[price]` rather than total payment value to reflect real product sales without double-counting freight charges.
- **Required Data Model:** Star schema with `FactSales` containing `price` and `order_status`. Single-direction filter from `DimDate`.
- **Formatting:** Currency: `R$ #,##0` or `R$ #,##0.00`.
- **Possible Pitfalls:** Do not include cancelled or unavailable orders unless specifically computing gross order funnel attempts.

---

### 1.2 Total Freight
```dax
Total Freight = 
CALCULATE(
    SUM(FactSales[freight_value]),
    FactSales[order_status] = "delivered"
)
```
- **Calculation Explanation:** Aggregates carrier shipping charges collected from customers.
- **Required Data Model:** `FactSales[freight_value]`.
- **Formatting:** Currency: `R$ #,##0.00`.
- **Possible Pitfalls:** Freight belongs to shipping partners; never combine freight directly into net product revenue without clearly labeling it as Gross Merchandise Value (GMV).

---

### 1.3 Gross Merchandise Value (GMV)
```dax
Gross Merchandise Value = 
[Total Revenue] + [Total Freight]
```
- **Calculation Explanation:** Combines net product revenue and logistics fees into total marketplace throughput.
- **Required Data Model:** Built on `[Total Revenue]` and `[Total Freight]`.
- **Formatting:** Currency: `R$ #,##0`.

---

### 1.4 Total Orders
```dax
Total Orders = 
CALCULATE(
    DISTINCTCOUNT(FactSales[order_id]),
    FactSales[order_status] = "delivered"
)
```
- **Calculation Explanation:** Counts distinct order identifiers to avoid multiplying multi-item orders.
- **Required Data Model:** `FactSales[order_id]`.
- **Formatting:** Whole Number: `#,##0`.
- **Possible Pitfalls:** Using `COUNT(FactSales[order_id])` instead of `DISTINCTCOUNT` will overcount orders containing multiple items.

---

### 1.5 Total Customers
```dax
Total Customers = 
DISTINCTCOUNT(DimCustomer[customer_unique_id])
```
- **Calculation Explanation:** Counts distinct physical buyers by `customer_unique_id`.
- **Required Data Model:** `DimCustomer[customer_unique_id]`.
- **Formatting:** Whole Number: `#,##0`.
- **Possible Pitfalls:** Counting `customer_id` will count checkouts rather than distinct human customers.

---

### 1.6 Average Order Value (AOV)
```dax
Average Order Value = 
DIVIDE([Total Revenue], [Total Orders], BLANK())
```
- **Calculation Explanation:** Divides total delivered product revenue by the count of distinct delivered orders using safe division `DIVIDE()`.
- **Required Data Model:** Measures `[Total Revenue]` and `[Total Orders]`.
- **Formatting:** Currency: `R$ #,##0.00`.
- **Possible Pitfalls:** Using the `/` operator can cause divide-by-zero crashes when filters return zero orders.

---

## 2. Customer Retention & Behavioral Measures

### 2.1 Repeat Customer Count
```dax
Repeat Customer Count = 
CALCULATE(
    DISTINCTCOUNT(DimCustomer[customer_unique_id]),
    FILTER(
        DimCustomer,
        DimCustomer[customer_order_count] > 1
    )
)
```
- **Calculation Explanation:** Counts unique consumers whose lifetime order frequency exceeds 1.
- **Required Data Model:** `DimCustomer` enriched with pre-calculated `customer_order_count`.
- **Formatting:** Whole Number: `#,##0`.

---

### 2.2 Repeat Customer Percentage
```dax
Repeat Customer Percentage = 
DIVIDE(
    [Repeat Customer Count],
    [Total Customers],
    0
)
```
- **Calculation Explanation:** Expresses repeat buyers as a proportion of all unique customers.
- **Required Data Model:** Measures `[Repeat Customer Count]` and `[Total Customers]`.
- **Formatting:** Percentage: `0.0%` or `0.00%`.
- **Benchmark in Dataset:** Approximately 3.0%.

---

### 2.3 Customer Count by Segment
```dax
Customer Count by Segment = 
CALCULATE(
    DISTINCTCOUNT(DimCustomer[customer_unique_id]),
    USERELATIONSHIP(DimCustomer[customer_unique_id], FactSales[customer_id]) -- Or via RFM bridge table
)
```
- **Calculation Explanation:** Filters distinct customer counts according to selected RFM behavioral segments.
- **Formatting:** Whole Number: `#,##0`.

---

## 3. Time Intelligence & Growth Measures

### 3.1 Monthly Revenue
```dax
Monthly Revenue = 
CALCULATE(
    [Total Revenue],
    DATESMTD(DimDate[full_date])
)
```
- **Calculation Explanation:** Computes month-to-date revenue accumulation within the current active calendar filter context.
- **Required Data Model:** Marked Date Table on `DimDate[full_date]` with continuous calendar dates.
- **Formatting:** Currency: `R$ #,##0.00`.

---

### 3.2 Previous Month Revenue
```dax
Previous Month Revenue = 
CALCULATE(
    [Total Revenue],
    DATEADD(DimDate[full_date], -1, MONTH)
)
```
- **Calculation Explanation:** Shifts the active filter context back by exactly one calendar month using `DATEADD()`.
- **Required Data Model:** Marked continuous Date dimension.
- **Formatting:** Currency: `R$ #,##0.00`.
- **Possible Pitfalls:** Fails if `DimDate` contains gaps or duplicate date entries.

---

### 3.3 Month-over-Month (MoM) Growth %
```dax
Month-over-Month Growth % = 
VAR CurrentRev = [Total Revenue]
VAR PriorRev = [Previous Month Revenue]
RETURN
    DIVIDE(CurrentRev - PriorRev, PriorRev, BLANK())
```
- **Calculation Explanation:** Calculates percentage change in revenue compared to the immediate prior month.
- **Formatting:** Percentage: `+0.0%;-0.0%;0.0%`.

---

### 3.4 Year-over-Year (YoY) Revenue Growth %
```dax
Year-over-Year Growth % = 
VAR CurrentRev = [Total Revenue]
VAR PriorYearRev = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(DimDate[full_date]))
RETURN
    DIVIDE(CurrentRev - PriorYearRev, PriorYearRev, BLANK())
```
- **Calculation Explanation:** Measures annual performance comparison for corresponding calendar months in 2017 vs 2018.
- **Required Data Model:** Marked Date Table with multi-year continuity.
- **Formatting:** Percentage: `+0.0%;-0.0%;0.0%`.

---

### 3.5 3-Month Moving Average Revenue
```dax
3M Moving Avg Revenue = 
AVERAGEX(
    DATESINPERIOD(
        DimDate[full_date],
        LASTDATE(DimDate[full_date]),
        -3,
        MONTH
    ),
    [Total Revenue]
)
```
- **Calculation Explanation:** Smooths out short-term fluctuations and seasonal spikes by calculating the rolling 90-day mean revenue.
- **Formatting:** Currency: `R$ #,##0`.

---

## 4. Operational & Delivery Logistics Measures

### 4.1 Average Delivery Days
```dax
Average Delivery Days = 
CALCULATE(
    AVERAGEX(
        orders,
        DATEDIFF(orders[order_purchase_timestamp], orders[order_delivered_customer_date], DAY)
    ),
    orders[order_status] = "delivered",
    NOT(ISBLANK(orders[order_delivered_customer_date]))
)
```
- **Calculation Explanation:** Computes the average duration from customer order purchase to physical delivery.
- **Required Data Model:** `orders` table with valid datetime timestamps.
- **Formatting:** Decimal Number: `0.0` Days.

---

### 4.2 Late Delivery Percentage
```dax
Late Delivery Percentage = 
VAR TotalDelivered = 
    CALCULATE(
        COUNTROWS(orders),
        orders[order_status] = "delivered",
        NOT(ISBLANK(orders[order_delivered_customer_date]))
    )
VAR LateOrders = 
    CALCULATE(
        COUNTROWS(orders),
        orders[order_status] = "delivered",
        orders[order_delivered_customer_date] > orders[order_estimated_delivery_date]
    )
RETURN
    DIVIDE(LateOrders, TotalDelivered, 0)
```
- **Calculation Explanation:** Measures the proportion of delivered orders whose actual customer delivery timestamp exceeded the promised estimated delivery date.
- **Formatting:** Percentage: `0.0%`.
- **Benchmark:** ~7.8% across Olist marketplace.

---

### 4.3 Average Review Score
```dax
Average Review Score = 
AVERAGE(order_reviews[review_score])
```
- **Calculation Explanation:** Computes arithmetic mean of customer feedback scores (bounded between 1.0 and 5.0).
- **Required Data Model:** `order_reviews[review_score]`.
- **Formatting:** Decimal Number: `0.00` Stars.

---

### 4.4 One-Star Review Percentage
```dax
One-Star Review Percentage = 
DIVIDE(
    CALCULATE(COUNTROWS(order_reviews), order_reviews[review_score] = 1),
    COUNTROWS(order_reviews),
    0
)
```
- **Calculation Explanation:** Quantifies severe customer dissatisfaction rate.
- **Formatting:** Percentage: `0.0%`.
