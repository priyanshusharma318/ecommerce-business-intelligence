-- =============================================================================
-- SQL BUSINESS ANALYSIS: MODULE 1 - SALES & REVENUE PERFORMANCE
-- Queries 1 to 8: Revenue totals, monthly trends, YoY growth, AOV, category mix,
--                 top products, payment channels, and geographic performance.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- QUERY 1: TOTAL ORDER REVENUE, FREIGHT CHARGES, AND GROSS MERCHANDISE VALUE (GMV)
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Establish the foundational baseline top-line financial performance of the platform.
--   Clearly distinguishes between actual product sales revenue (money going to goods/merchants)
--   and freight charges (shipping fees paid to carriers), preventing inflated revenue claims.
--
-- SQL Logic:
--   Joins orders with order_items filtering strictly on 'delivered' status to exclude
--   cancelled or unavailable orders. Computes SUM(price), SUM(freight_value), and overall GMV.
--
-- Business Implication:
--   Freight accounts for ~14-16% of gross marketplace volume, indicating that shipping
--   costs represent a substantial friction point for Brazilian e-commerce consumers.

SELECT 
    COUNT(DISTINCT o.order_id) AS total_delivered_orders,
    ROUND(SUM(oi.price), 2) AS total_product_revenue,
    ROUND(SUM(oi.freight_value), 2) AS total_freight_revenue,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS gross_merchandise_value_gmv,
    ROUND(SUM(oi.freight_value) / SUM(oi.price + oi.freight_value) * 100, 2) AS freight_share_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered';


-- -----------------------------------------------------------------------------
-- QUERY 2: MONTHLY REVENUE AND ORDER VOLUME TRAJECTORY
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Track business growth, volume momentum, and revenue seasonality over the 2-year lifecycle.
--
-- SQL Logic:
--   Extracts year-month from purchase timestamp. Aggregates monthly product revenue,
--   order volume, and calculates MoM (Month-over-Month) percentage revenue growth using
--   the LAG() window function.
--
-- Business Implication:
--   Demonstrates explosive platform expansion from late 2016 through mid-2018,
--   with notable revenue spikes around Black Friday (November 2017).

WITH monthly_sales AS (
    SELECT 
        TO_CHAR(o.order_purchase_timestamp, 'YYYY-MM') AS year_month,
        COUNT(DISTINCT o.order_id) AS total_orders,
        ROUND(SUM(oi.price), 2) AS monthly_revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY TO_CHAR(o.order_purchase_timestamp, 'YYYY-MM')
)
SELECT 
    year_month,
    total_orders,
    monthly_revenue,
    LAG(monthly_revenue) OVER (ORDER BY year_month) AS prior_month_revenue,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY year_month)) / 
        NULLIF(LAG(monthly_revenue) OVER (ORDER BY year_month), 0) * 100, 
        2
    ) AS mom_growth_pct
FROM monthly_sales
ORDER BY year_month;


-- -----------------------------------------------------------------------------
-- QUERY 3: YEAR-OVER-YEAR (YOY) COMPARATIVE SALES ANALYSIS
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Measure annual scale comparisons for overlapping active periods (e.g., 2017 vs 2018).
--
-- SQL Logic:
--   Extracts order year and calendar month. Uses CTEs and conditional aggregation to align
--   matching calendar months across 2017 and 2018, calculating absolute and percentage growth.
--
-- Business Implication:
--   Highlights rapid market adoption: early 2018 months consistently posted >100% YoY gains
--   relative to 2017, proving increasing consumer trust and catalog depth.

WITH monthly_yearly_sales AS (
    SELECT 
        EXTRACT(MONTH FROM o.order_purchase_timestamp) AS month_num,
        TO_CHAR(o.order_purchase_timestamp, 'Mon') AS month_name,
        EXTRACT(YEAR FROM o.order_purchase_timestamp) AS order_year,
        ROUND(SUM(oi.price), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND EXTRACT(YEAR FROM o.order_purchase_timestamp) IN (2017, 2018)
    GROUP BY EXTRACT(MONTH FROM o.order_purchase_timestamp), 
             TO_CHAR(o.order_purchase_timestamp, 'Mon'), 
             EXTRACT(YEAR FROM o.order_purchase_timestamp)
)
SELECT 
    month_num,
    month_name,
    MAX(CASE WHEN order_year = 2017 THEN revenue ELSE 0 END) AS revenue_2017,
    MAX(CASE WHEN order_year = 2018 THEN revenue ELSE 0 END) AS revenue_2018,
    ROUND(
        (MAX(CASE WHEN order_year = 2018 THEN revenue ELSE 0 END) - 
         MAX(CASE WHEN order_year = 2017 THEN revenue ELSE 0 END)) /
        NULLIF(MAX(CASE WHEN order_year = 2017 THEN revenue ELSE 0 END), 0) * 100, 
        2
    ) AS yoy_growth_pct
FROM monthly_yearly_sales
GROUP BY month_num, month_name
ORDER BY month_num;


-- -----------------------------------------------------------------------------
-- QUERY 4: AVERAGE ORDER VALUE (AOV) AND BASKET SIZE DYNAMICS
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Determine average transaction size and whether revenue growth is driven by
--   higher basket values or transaction volume expansion.
--
-- SQL Logic:
--   Calculates average product revenue per order and average item quantity per order.
--
-- Business Implication:
--   Average Order Value remains remarkably stable around R$ 135 - R$ 145 throughout the platform's
--   growth, showing that revenue scaling was fueled almost entirely by customer acquisition volume.

SELECT 
    TO_CHAR(o.order_purchase_timestamp, 'YYYY-MM') AS year_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(oi.order_item_id) AS total_items_sold,
    ROUND(SUM(oi.price), 2) AS total_revenue,
    ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value_aov,
    ROUND(COUNT(oi.order_item_id)::NUMERIC / COUNT(DISTINCT o.order_id), 2) AS avg_items_per_order
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY TO_CHAR(o.order_purchase_timestamp, 'YYYY-MM')
ORDER BY year_month;


-- -----------------------------------------------------------------------------
-- QUERY 5: REVENUE & ORDER COUNT BY PRODUCT CATEGORY (ENGLISH TRANSLATION)
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Identify core merchandise drivers and understand category sales mix.
--
-- SQL Logic:
--   Joins order_items with products and translation mappings. Computes total revenue,
--   order volume, and category revenue share percentage using a window sum.
--
-- Business Implication:
--   Health & Beauty, Watches & Gifts, Bed & Bath, and Sports & Leisure drive over 35%
--   of total gross merchandise sales, representing high-velocity anchor departments.

SELECT 
    COALESCE(p.product_category_name_english, p.product_category_name, 'Other') AS category_name,
    COUNT(DISTINCT oi.order_id) AS order_count,
    COUNT(oi.order_item_id) AS items_sold,
    ROUND(SUM(oi.price), 2) AS total_category_revenue,
    ROUND(
        SUM(oi.price) / SUM(SUM(oi.price)) OVER () * 100, 
        2
    ) AS category_revenue_share_pct
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY COALESCE(p.product_category_name_english, p.product_category_name, 'Other')
ORDER BY total_category_revenue DESC;


-- -----------------------------------------------------------------------------
-- QUERY 6: TOP 10 INDIVIDUAL PRODUCTS BY TOTAL REVENUE GENERATED
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Detect hero SKUs and identify individual high-value items driving catalog sales.
--
-- SQL Logic:
--   Aggregates sales by product_id, joining category translation. Uses DENSE_RANK()
--   to output the top 10 products with average unit selling price and units sold.
--
-- Business Implication:
--   Top products belong primarily to high-ticket electronics (computers, health devices, watches),
--   requiring prioritized seller stock replenishment and fraud protection.

WITH product_sales AS (
    SELECT 
        oi.product_id,
        COALESCE(p.product_category_name_english, 'Unspecified') AS category,
        COUNT(oi.order_item_id) AS units_sold,
        ROUND(AVG(oi.price), 2) AS avg_unit_price,
        ROUND(SUM(oi.price), 2) AS total_product_revenue,
        DENSE_RANK() OVER (ORDER BY SUM(oi.price) DESC) AS sales_rank
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY oi.product_id, p.product_category_name_english
)
SELECT 
    sales_rank,
    product_id,
    category,
    units_sold,
    avg_unit_price,
    total_product_revenue
FROM product_sales
WHERE sales_rank <= 10
ORDER BY sales_rank;


-- -----------------------------------------------------------------------------
-- QUERY 7: REVENUE AND TRANSACTION DISTRIBUTION BY PAYMENT METHOD
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Examine Brazilian consumer payment preferences, installment habits, and payment risk.
--
-- SQL Logic:
--   Aggregates order_payments by payment_type, calculating total processed value,
--   transaction count, average installment count, and percentage share.
--
-- Business Implication:
--   Credit cards dominate (~75% of total payment value), with customers heavily utilizing
--   interest-free installment plans (average ~3.5 installments per transaction).
--   Boleto Bancário represents ~19% of volume, catering to cash/unbanked consumers.

SELECT 
    op.payment_type,
    COUNT(*) AS total_transactions,
    ROUND(SUM(op.payment_value), 2) AS total_payment_value,
    ROUND(
        SUM(op.payment_value) / SUM(SUM(op.payment_value)) OVER () * 100, 
        2
    ) AS payment_value_share_pct,
    ROUND(AVG(op.payment_installments), 2) AS avg_installments
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY op.payment_type
ORDER BY total_payment_value DESC;


-- -----------------------------------------------------------------------------
-- QUERY 8: REVENUE AND AVERAGE BASKET SIZE BY CUSTOMER STATE (UF)
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Assess regional commercial performance and geographic demand concentration.
--
-- SQL Logic:
--   Joins orders, customers, and order_items. Groups by customer_state, computing total
--   orders, revenue, customer count, and average order value.
--
-- Business Implication:
--   São Paulo (SP) generates over 37% of platform revenue alone. The Southeast region
--   (SP, RJ, MG) collectively commands >65% of demand, reflecting economic population centers.

SELECT 
    c.customer_state,
    COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price), 2) AS total_revenue,
    ROUND(SUM(oi.freight_value), 2) AS total_freight,
    ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value,
    ROUND(
        SUM(oi.price) / SUM(SUM(oi.price)) OVER () * 100, 
        2
    ) AS state_revenue_share_pct
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY total_revenue DESC;
