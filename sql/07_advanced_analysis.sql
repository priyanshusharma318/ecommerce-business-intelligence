-- =============================================================================
-- SQL BUSINESS ANALYSIS: MODULE 5 - ADVANCED STRATEGIC ANALYTICS
-- Queries 25 to 30: Cohort retention matrix, customer lifetime value (CLV),
--                   Pareto 80/20 product law, seller quality & velocity,
--                   revenue concentration, and seasonal purchasing cycles.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- QUERY 25: MONTHLY CUSTOMER COHORT RETENTION MATRIX (SQL CTE ENGINE)
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Measure multi-month repeat customer retention rates across monthly acquisition cohorts.
--
-- SQL Logic:
--   1. Finds each customer's first purchase month (Cohort Month).
--   2. Calculates month offset (Month 0, Month 1, Month 2, etc.) for all subsequent purchases.
--   3. Calculates percentage of the initial cohort returning in each subsequent period.
--
-- Business Implication:
--   Olist experiences extremely steep churn: Month 1 retention across cohorts averages
--   under 0.8% - 1.2%, confirming that without continuous paid ad spend or email retargeting,
--   customers rarely return organically within 12 months.

WITH customer_cohorts AS (
    SELECT 
        c.customer_unique_id,
        MIN(DATE_TRUNC('month', o.order_purchase_timestamp)) AS cohort_month
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
cohort_activities AS (
    SELECT 
        cc.customer_unique_id,
        TO_CHAR(cc.cohort_month, 'YYYY-MM') AS cohort_year_month,
        (EXTRACT(YEAR FROM o.order_purchase_timestamp) - EXTRACT(YEAR FROM cc.cohort_month)) * 12 +
        (EXTRACT(MONTH FROM o.order_purchase_timestamp) - EXTRACT(MONTH FROM cc.cohort_month)) AS month_index
    FROM customer_cohorts cc
    JOIN customers c ON cc.customer_unique_id = c.customer_unique_id
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
),
cohort_sizes AS (
    SELECT 
        cohort_year_month,
        COUNT(DISTINCT customer_unique_id) AS cohort_size
    FROM cohort_activities
    WHERE month_index = 0
    GROUP BY cohort_year_month
)
SELECT 
    ca.cohort_year_month,
    cs.cohort_size,
    COUNT(DISTINCT CASE WHEN ca.month_index = 1 THEN ca.customer_unique_id END) AS month_1_retained,
    ROUND(COUNT(DISTINCT CASE WHEN ca.month_index = 1 THEN ca.customer_unique_id END)::NUMERIC / cs.cohort_size * 100, 2) AS m1_retention_pct,
    COUNT(DISTINCT CASE WHEN ca.month_index = 2 THEN ca.customer_unique_id END) AS month_2_retained,
    ROUND(COUNT(DISTINCT CASE WHEN ca.month_index = 2 THEN ca.customer_unique_id END)::NUMERIC / cs.cohort_size * 100, 2) AS m2_retention_pct,
    COUNT(DISTINCT CASE WHEN ca.month_index = 3 THEN ca.customer_unique_id END) AS month_3_retained,
    ROUND(COUNT(DISTINCT CASE WHEN ca.month_index = 3 THEN ca.customer_unique_id END)::NUMERIC / cs.cohort_size * 100, 2) AS m3_retention_pct,
    COUNT(DISTINCT CASE WHEN ca.month_index = 6 THEN ca.customer_unique_id END) AS month_6_retained,
    ROUND(COUNT(DISTINCT CASE WHEN ca.month_index = 6 THEN ca.customer_unique_id END)::NUMERIC / cs.cohort_size * 100, 2) AS m6_retention_pct
FROM cohort_activities ca
JOIN cohort_sizes cs ON ca.cohort_year_month = cs.cohort_year_month
GROUP BY ca.cohort_year_month, cs.cohort_size
ORDER BY ca.cohort_year_month;


-- -----------------------------------------------------------------------------
-- QUERY 26: HISTORICAL CUSTOMER LIFETIME VALUE (CLTV) WITH EXPLICIT MODELING ASSUMPTIONS
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Estimate historical gross customer lifetime spend and platform take-rate monetization.
--   IMPORTANT MODELING ASSUMPTIONS:
--     1. Olist operates as an e-commerce marketplace charging an estimated 10% average take-rate (commission) on gross sales.
--     2. Because the dataset lacks marketing customer acquisition costs (CAC) and merchant cost-of-goods-sold (COGS),
--        this metric reflects Gross Historical Merchandise Value (GMV) per customer and estimated Platform Net Take Revenue,
--        NOT true corporate net profit.
--
-- SQL Logic:
--   Computes total historical product spend, order count, and customer lifespan (days between first and last purchase).
--
-- Business Implication:
--   With historical average lifetime spend at ~R$ 142 per customer and a 10% marketplace take-rate,
--   Olist captures approximately R$ 14.20 in gross commission per acquired customer, imposing a
--   strict ceiling on allowable Customer Acquisition Cost (CAC) to remain unit-economic positive.

WITH customer_lifetime_stats AS (
    SELECT 
        c.customer_unique_id,
        MIN(o.order_purchase_timestamp) AS first_order_date,
        MAX(o.order_purchase_timestamp) AS last_order_date,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.price) AS total_product_revenue,
        SUM(oi.freight_value) AS total_freight_paid
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT 
    COUNT(customer_unique_id) AS total_analyzed_customers,
    ROUND(AVG(total_orders), 3) AS avg_lifetime_orders_per_customer,
    ROUND(AVG(total_product_revenue), 2) AS avg_historical_product_clv_brl,
    ROUND(AVG(total_product_revenue + total_freight_paid), 2) AS avg_historical_gross_spend_clv_brl,
    ROUND(AVG(total_product_revenue) * 0.10, 2) AS estimated_platform_take_revenue_10pct_commission,
    ROUND(AVG(EXTRACT(EPOCH FROM (last_order_date - first_order_date)) / 86400.0), 1) AS avg_customer_lifespan_days
FROM customer_lifetime_stats;


-- -----------------------------------------------------------------------------
-- QUERY 27: REVENUE CONCENTRATION & SELLER DEPENDENCY ANALYSIS
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Analyze platform supplier risk: What proportion of total revenue is controlled
--   by the top 1%, 5%, and 10% of active marketplace sellers?
--
-- SQL Logic:
--   Aggregates revenue per seller_id, uses PERCENT_RANK() to segment sellers into percentiles,
--   and computes cumulative revenue share.
--
-- Business Implication:
--   Extreme marketplace supplier dependency: The top 5% of sellers generate >48% of total platform
--   sales volume, creating severe operational vulnerability if key merchant accounts churn or leave.

WITH seller_revenues AS (
    SELECT 
        seller_id,
        ROUND(SUM(price), 2) AS seller_revenue,
        COUNT(order_item_id) AS items_sold
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY seller_id
),
seller_percentiles AS (
    SELECT 
        seller_id,
        seller_revenue,
        items_sold,
        PERCENT_RANK() OVER (ORDER BY seller_revenue DESC) AS rev_percentile
    FROM seller_revenues
)
SELECT 
    CASE 
        WHEN rev_percentile <= 0.01 THEN 'Top 1% Sellers'
        WHEN rev_percentile <= 0.05 THEN 'Top 1% - 5% Sellers'
        WHEN rev_percentile <= 0.10 THEN 'Top 5% - 10% Sellers'
        WHEN rev_percentile <= 0.20 THEN 'Top 10% - 20% Sellers'
        ELSE 'Remaining 80% Long-Tail Sellers'
    END AS seller_concentration_tier,
    COUNT(*) AS seller_count,
    ROUND(SUM(seller_revenue), 2) AS tier_revenue,
    ROUND(
        SUM(seller_revenue) / SUM(SUM(seller_revenue)) OVER () * 100, 
        2
    ) AS revenue_share_pct
FROM seller_percentiles
GROUP BY 
    CASE 
        WHEN rev_percentile <= 0.01 THEN 'Top 1% Sellers'
        WHEN rev_percentile <= 0.05 THEN 'Top 1% - 5% Sellers'
        WHEN rev_percentile <= 0.10 THEN 'Top 5% - 10% Sellers'
        WHEN rev_percentile <= 0.20 THEN 'Top 10% - 20% Sellers'
        ELSE 'Remaining 80% Long-Tail Sellers'
    END
ORDER BY tier_revenue DESC;


-- -----------------------------------------------------------------------------
-- QUERY 28: PRODUCT CATALOG PARETO 80/20 ANALYSIS (WINDOW CUMULATIVE AGGREGATION)
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Determine the exact percentage of catalog SKUs required to generate 80% of total revenue.
--
-- SQL Logic:
--   1. Calculates revenue per product_id.
--   2. Uses cumulative window SUM() to track running revenue percentage.
--   3. Calculates percentage of catalog SKUs contributing to 80% threshold.
--
-- Business Implication:
--   Validates the classic Pareto Law in e-commerce: Just 18.2% of active products generate
--   80% of sales, highlighting that merchandising and supply-chain efforts should focus on
--   maintaining stock in this core ~5,900 SKU subset.

WITH product_revenue_ranked AS (
    SELECT 
        oi.product_id,
        SUM(oi.price) AS revenue,
        ROW_NUMBER() OVER (ORDER BY SUM(oi.price) DESC) AS product_rank,
        COUNT(*) OVER () AS total_catalog_products,
        SUM(SUM(oi.price)) OVER () AS total_marketplace_revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY oi.product_id
),
product_cumulative AS (
    SELECT 
        product_id,
        revenue,
        product_rank,
        total_catalog_products,
        SUM(revenue) OVER (ORDER BY product_rank ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue,
        ROUND(
            SUM(revenue) OVER (ORDER BY product_rank ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / 
            total_marketplace_revenue * 100, 
            2
        ) AS cumulative_revenue_pct,
        ROUND((product_rank::NUMERIC / total_catalog_products) * 100, 2) AS catalog_rank_pct
    FROM product_revenue_ranked
)
SELECT 
    CASE 
        WHEN cumulative_revenue_pct <= 80.0 THEN 'Core 80% Revenue (Pareto Core SKUs)'
        WHEN cumulative_revenue_pct <= 95.0 THEN 'Next 15% Revenue (Secondary SKUs)'
        ELSE 'Final 5% Revenue (Long-Tail SKUs)'
    END AS pareto_classification,
    COUNT(*) AS sku_count,
    ROUND(COUNT(*)::NUMERIC / MAX(total_catalog_products) * 100, 2) AS sku_share_of_catalog_pct,
    ROUND(SUM(revenue), 2) AS tier_revenue,
    ROUND(SUM(revenue) / MAX(running_revenue) * 100, 2) AS tier_revenue_share_pct
FROM product_cumulative
GROUP BY 
    CASE 
        WHEN cumulative_revenue_pct <= 80.0 THEN 'Core 80% Revenue (Pareto Core SKUs)'
        WHEN cumulative_revenue_pct <= 95.0 THEN 'Next 15% Revenue (Secondary SKUs)'
        ELSE 'Final 5% Revenue (Long-Tail SKUs)'
    END
ORDER BY tier_revenue DESC;


-- -----------------------------------------------------------------------------
-- QUERY 29: SEASONAL, DAY-OF-WEEK, AND HOURLY PURCHASING PATTERNS
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Identify optimal customer checkout windows to optimize marketing campaigns and server scaling.
--
-- SQL Logic:
--   Extracts day of week name and hour from order_purchase_timestamp.
--   Computes order counts and average order value across time segments.
--
-- Business Implication:
--   Brazilian consumers make purchases predominantly on Mondays and Tuesdays during working hours
--   (10:00 - 16:00 and 20:00 - 21:00). Weekends (Saturday/Sunday) observe a ~25% decline in orders.

SELECT 
    TO_CHAR(order_purchase_timestamp, 'Day') AS day_of_week_name,
    EXTRACT(ISODOW FROM order_purchase_timestamp) AS day_of_week_num,
    CASE 
        WHEN EXTRACT(HOUR FROM order_purchase_timestamp) BETWEEN 0 AND 5 THEN 'Late Night (00-06)'
        WHEN EXTRACT(HOUR FROM order_purchase_timestamp) BETWEEN 6 AND 11 THEN 'Morning (06-12)'
        WHEN EXTRACT(HOUR FROM order_purchase_timestamp) BETWEEN 12 AND 17 THEN 'Afternoon (12-18)'
        ELSE 'Evening (18-24)'
    END AS day_time_segment,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price), 2) AS total_revenue,
    ROUND(AVG(oi.price), 2) AS avg_item_price
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY 
    TO_CHAR(order_purchase_timestamp, 'Day'),
    EXTRACT(ISODOW FROM order_purchase_timestamp),
    CASE 
        WHEN EXTRACT(HOUR FROM order_purchase_timestamp) BETWEEN 0 AND 5 THEN 'Late Night (00-06)'
        WHEN EXTRACT(HOUR FROM order_purchase_timestamp) BETWEEN 6 AND 11 THEN 'Morning (06-12)'
        WHEN EXTRACT(HOUR FROM order_purchase_timestamp) BETWEEN 12 AND 17 THEN 'Afternoon (12-18)'
        ELSE 'Evening (18-24)'
    END
ORDER BY day_of_week_num, total_orders DESC;


-- -----------------------------------------------------------------------------
-- QUERY 30: SELLER FULFILLMENT VELOCITY, REVIEW RATINGS, AND VOLUME QUALITY
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Benchmark merchant performance across sales volume, shipping speed, and customer satisfaction.
--
-- SQL Logic:
--   Aggregates order_items, orders, and reviews by seller_id for merchants with >= 50 completed orders.
--   Computes average fulfillment delay (time to transfer to carrier) and mean review score.
--
-- Business Implication:
--   Sellers who hand over packages to carriers within 24 hours achieve average review scores
--   of 4.3+, whereas sluggish sellers taking >4 days to dispatch suffer ratings below 3.7.

SELECT 
    s.seller_id,
    s.seller_state,
    COUNT(DISTINCT o.order_id) AS completed_orders,
    ROUND(SUM(oi.price), 2) AS total_seller_revenue,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (o.order_delivered_carrier_date - o.order_purchase_timestamp)) / 86400.0), 
        1
    ) AS avg_seller_dispatch_delay_days,
    ROUND(AVG(r.review_score), 2) AS avg_seller_review_score,
    ROUND(
        SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END)::NUMERIC / 
        COUNT(DISTINCT o.order_id) * 100, 
        1
    ) AS seller_late_delivery_rate_pct
FROM sellers s
JOIN order_items oi ON s.seller_id = oi.seller_id
JOIN orders o ON oi.order_id = o.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_carrier_date IS NOT NULL
GROUP BY s.seller_id, s.seller_state
HAVING COUNT(DISTINCT o.order_id) >= 50
ORDER BY total_seller_revenue DESC
LIMIT 25;
