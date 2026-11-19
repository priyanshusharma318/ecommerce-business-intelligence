-- =============================================================================
-- SQL DATA VALIDATION & REFERENTIAL INTEGRITY AUDIT SUITE
-- Description: Asserts row counts, primary key uniqueness, foreign key consistency,
--              business constraint compliance, and logical date chronology.
-- =============================================================================

-- 1. Table Volume Overview
SELECT 'customers' AS table_name, COUNT(*) AS total_records FROM customers
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL
SELECT 'order_payments', COUNT(*) FROM order_payments
UNION ALL
SELECT 'order_reviews', COUNT(*) FROM order_reviews
UNION ALL
SELECT 'geolocation', COUNT(*) FROM geolocation;

-- 2. Primary Key Uniqueness Verification (Should return 0 rows if valid)
SELECT 'orders_duplicate_pks' AS check_name, COUNT(*) AS violations
FROM (
    SELECT order_id FROM orders GROUP BY order_id HAVING COUNT(*) > 1
) sub
UNION ALL
SELECT 'customers_duplicate_pks', COUNT(*)
FROM (
    SELECT customer_id FROM customers GROUP BY customer_id HAVING COUNT(*) > 1
) sub
UNION ALL
SELECT 'products_duplicate_pks', COUNT(*)
FROM (
    SELECT product_id FROM products GROUP BY product_id HAVING COUNT(*) > 1
) sub
UNION ALL
SELECT 'sellers_duplicate_pks', COUNT(*)
FROM (
    SELECT seller_id FROM sellers GROUP BY seller_id HAVING COUNT(*) > 1
) sub
UNION ALL
SELECT 'order_items_composite_dup_pks', COUNT(*)
FROM (
    SELECT order_id, order_item_id FROM order_items GROUP BY order_id, order_item_id HAVING COUNT(*) > 1
) sub;

-- 3. Foreign Key Integrity Checks (Orphan Records Detection)
-- Target: 0 orphan rows across all child tables
SELECT 'orders_missing_customer' AS check_name, COUNT(*) AS orphan_count
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'order_items_missing_order', COUNT(*)
FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT 'order_items_missing_product', COUNT(*)
FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE p.product_id IS NULL
UNION ALL
SELECT 'order_items_missing_seller', COUNT(*)
FROM order_items oi
LEFT JOIN sellers s ON oi.seller_id = s.seller_id
WHERE s.seller_id IS NULL
UNION ALL
SELECT 'payments_missing_order', COUNT(*)
FROM order_payments op
LEFT JOIN orders o ON op.order_id = o.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT 'reviews_missing_order', COUNT(*)
FROM order_reviews orv
LEFT JOIN orders o ON orv.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 4. Business Metric Constraints & Data Range Assertions
SELECT 'negative_or_zero_price' AS anomaly_type, COUNT(*) AS violation_count
FROM order_items
WHERE price <= 0
UNION ALL
SELECT 'negative_freight', COUNT(*)
FROM order_items
WHERE freight_value < 0
UNION ALL
SELECT 'negative_or_zero_payment', COUNT(*)
FROM order_payments
WHERE payment_value <= 0
UNION ALL
SELECT 'invalid_review_score_range', COUNT(*)
FROM order_reviews
WHERE review_score < 1 OR review_score > 5
UNION ALL
SELECT 'chronology_delivered_before_purchase', COUNT(*)
FROM orders
WHERE order_delivered_customer_date < order_purchase_timestamp;
