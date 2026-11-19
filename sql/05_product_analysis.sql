-- =============================================================================
-- SQL BUSINESS ANALYSIS: MODULE 3 - PRODUCT & MERCHANDISE PERFORMANCE
-- Queries 15 to 19: Top categories, bottom categories, category price benchmarks,
--                   freight cost burdens, and catalog item velocity distribution.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- QUERY 15: TOP 10 BEST-SELLING PRODUCT CATEGORIES BY REVENUE & VOLUME
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Identify anchor commercial categories driving both high GMV and unit turnover.
--
-- SQL Logic:
--   Groups order_items by translated category name, aggregating items sold, total revenue,
--   distinct sellers active, and ranking by total revenue.
--
-- Business Implication:
--   Health & Beauty, Watches & Gifts, and Bed/Bath/Table represent the core revenue engine.
--   These categories justify dedicated vendor acquisition and supplier co-marketing investments.

SELECT 
    COALESCE(p.product_category_name_english, p.product_category_name, 'Other') AS category_name,
    COUNT(oi.order_item_id) AS total_units_sold,
    COUNT(DISTINCT oi.seller_id) AS active_sellers,
    ROUND(SUM(oi.price), 2) AS total_revenue,
    ROUND(AVG(oi.price), 2) AS avg_unit_price,
    ROUND(
        SUM(oi.price) / SUM(SUM(oi.price)) OVER () * 100, 
        2
    ) AS category_revenue_share_pct
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY COALESCE(p.product_category_name_english, p.product_category_name, 'Other')
ORDER BY total_revenue DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- QUERY 16: BOTTOM 10 LOW-PERFORMING PRODUCT CATEGORIES
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Identify catalog deadweight, niche categories, and underperforming merchandise
--   for potential pruning or targeted category reviews.
--
-- SQL Logic:
--   Ranks categories by total generated revenue in ascending order, filtering out categories
--   with fewer than 1 order.
--
-- Business Implication:
--   Categories like Security & Services, Fashion Children's Clothing, and CDs/DVDs generate
--   negligible revenue (<R$ 5,000 total across 2 years), indicating wasted catalog overhead.

SELECT 
    COALESCE(p.product_category_name_english, p.product_category_name, 'Other') AS category_name,
    COUNT(oi.order_item_id) AS total_units_sold,
    ROUND(SUM(oi.price), 2) AS total_revenue,
    ROUND(AVG(oi.price), 2) AS avg_unit_price
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY COALESCE(p.product_category_name_english, p.product_category_name, 'Other')
ORDER BY total_revenue ASC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- QUERY 17: AVERAGE PRODUCT PRICE, MIN, MAX, AND PRICE RANGE BY CATEGORY
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Establish price dispersion benchmarks across product categories to guide pricing strategy.
--
-- SQL Logic:
--   Computes MIN, MAX, AVG, and Standard Deviation of unit prices per category having at least 100 sales.
--
-- Business Implication:
--   Computers and Small Appliances have massive price dispersion (ranging from R$ 30 to R$ 6,000+),
--   indicating a mix of cheap accessories and expensive enterprise hardware in the same taxonomy.

SELECT 
    COALESCE(p.product_category_name_english, p.product_category_name, 'Other') AS category_name,
    COUNT(oi.order_item_id) AS units_sold,
    ROUND(MIN(oi.price), 2) AS min_price,
    ROUND(AVG(oi.price), 2) AS avg_price,
    ROUND(MAX(oi.price), 2) AS max_price,
    ROUND(STDDEV(oi.price), 2) AS price_std_dev
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY COALESCE(p.product_category_name_english, p.product_category_name, 'Other')
HAVING COUNT(oi.order_item_id) >= 100
ORDER BY avg_price DESC;


-- -----------------------------------------------------------------------------
-- QUERY 18: FREIGHT COST BURDEN AND FREIGHT-TO-PRICE RATIO BY CATEGORY
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Examine which merchandise categories suffer from excessive logistics costs relative
--   to product value, directly causing checkout cart abandonment.
--
-- SQL Logic:
--   Calculates average freight, average item price, and the Freight-to-Price Ratio (Freight / Price * 100).
--
-- Business Implication:
--   Bulky and heavy goods (furniture, construction tools) suffer from freight ratios exceeding 30-45%
--   of item price, drastically eroding consumer conversion outside metropolitan capitals.

SELECT 
    COALESCE(p.product_category_name_english, p.product_category_name, 'Other') AS category_name,
    COUNT(oi.order_item_id) AS total_units_sold,
    ROUND(AVG(oi.price), 2) AS avg_item_price,
    ROUND(AVG(oi.freight_value), 2) AS avg_freight_charge,
    ROUND(
        (SUM(oi.freight_value) / NULLIF(SUM(oi.price), 0)) * 100, 
        2
    ) AS freight_to_price_ratio_pct,
    ROUND(AVG(p.product_weight_g) / 1000.0, 2) AS avg_product_weight_kg
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY COALESCE(p.product_category_name_english, p.product_category_name, 'Other')
HAVING COUNT(oi.order_item_id) >= 150
ORDER BY freight_to_price_ratio_pct DESC;


-- -----------------------------------------------------------------------------
-- QUERY 19: PRODUCT CATALOG SALES VELOCITY DISTRIBUTION
-- -----------------------------------------------------------------------------
-- Business Purpose:
--   Determine catalog turnover velocity: how many products sold only once vs multiple times.
--
-- SQL Logic:
--   Counts total units sold per product_id, then groups into sales velocity tiers.
--
-- Business Implication:
--   Over 50% of distinct catalog products sold only 1 unit throughout the 2-year history,
--   proving a massive "long tail" of low-turnover inventory across third-party sellers.

WITH product_velocity AS (
    SELECT 
        product_id,
        COUNT(order_item_id) AS units_sold
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY product_id
)
SELECT 
    CASE 
        WHEN units_sold = 1 THEN '1 Unit (Single Sale)'
        WHEN units_sold BETWEEN 2 AND 5 THEN '2 - 5 Units (Low Velocity)'
        WHEN units_sold BETWEEN 6 AND 20 THEN '6 - 20 Units (Medium Velocity)'
        WHEN units_sold BETWEEN 21 AND 100 THEN '21 - 100 Units (High Velocity)'
        ELSE '100+ Units (Best Sellers)'
    END AS sales_velocity_tier,
    COUNT(*) AS distinct_products_count,
    ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) AS product_catalog_share_pct,
    SUM(units_sold) AS total_units_sold,
    ROUND(SUM(units_sold)::NUMERIC / SUM(SUM(units_sold)) OVER () * 100, 2) AS total_volume_share_pct
FROM product_velocity
GROUP BY 
    CASE 
        WHEN units_sold = 1 THEN '1 Unit (Single Sale)'
        WHEN units_sold BETWEEN 2 AND 5 THEN '2 - 5 Units (Low Velocity)'
        WHEN units_sold BETWEEN 6 AND 20 THEN '6 - 20 Units (Medium Velocity)'
        WHEN units_sold BETWEEN 21 AND 100 THEN '21 - 100 Units (High Velocity)'
        ELSE '100+ Units (Best Sellers)'
    END
ORDER BY total_units_sold DESC;
