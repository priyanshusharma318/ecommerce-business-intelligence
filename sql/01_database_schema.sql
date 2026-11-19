-- =============================================================================
-- E-COMMERCE BUSINESS INTELLIGENCE PLATFORM: DATABASE DDL SCHEMA
-- Target Database: PostgreSQL 14+ / ANSI SQL Compatible
-- Description: Creates normalized relational transactional schema and 
--              star-schema analytical dimensional tables with constraints and indexes.
-- =============================================================================

-- =============================================================================
-- PART 1: NORMALIZED TRANSACTIONAL SCHEMA (OLTP / 3NF)
-- =============================================================================

-- 1. Product Category Translation Table
CREATE TABLE IF NOT EXISTS product_category_translation (
    product_category_name VARCHAR(100) PRIMARY KEY,
    product_category_name_english VARCHAR(100) NOT NULL
);

-- 2. Geolocation Table (Unique Zip Code Centroids)
CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix VARCHAR(10) PRIMARY KEY,
    geolocation_lat NUMERIC(10, 6) NOT NULL,
    geolocation_lng NUMERIC(10, 6) NOT NULL,
    geolocation_city VARCHAR(100) NOT NULL,
    geolocation_state VARCHAR(5) NOT NULL
);

-- 3. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL,
    customer_zip_code_prefix VARCHAR(10) NOT NULL,
    customer_city VARCHAR(100) NOT NULL,
    customer_state VARCHAR(5) NOT NULL
);

-- 4. Products Table
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_lenght NUMERIC(6, 1),
    product_description_lenght NUMERIC(8, 1),
    product_photos_qty NUMERIC(4, 1),
    product_weight_g NUMERIC(10, 1),
    product_length_cm NUMERIC(6, 1),
    product_height_cm NUMERIC(6, 1),
    product_width_cm NUMERIC(6, 1),
    product_category_name_english VARCHAR(100)
);

-- 5. Sellers Table
CREATE TABLE IF NOT EXISTS sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(10) NOT NULL,
    seller_city VARCHAR(100) NOT NULL,
    seller_state VARCHAR(5) NOT NULL
);

-- 6. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id),
    order_status VARCHAR(30) NOT NULL,
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP NOT NULL
);

-- 7. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    order_id VARCHAR(50) NOT NULL REFERENCES orders(order_id),
    order_item_id INTEGER NOT NULL,
    product_id VARCHAR(50) NOT NULL REFERENCES products(product_id),
    seller_id VARCHAR(50) NOT NULL REFERENCES sellers(seller_id),
    shipping_limit_date TIMESTAMP NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price > 0),
    freight_value NUMERIC(10, 2) NOT NULL CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);

-- 8. Order Payments Table
CREATE TABLE IF NOT EXISTS order_payments (
    order_id VARCHAR(50) NOT NULL REFERENCES orders(order_id),
    payment_sequential INTEGER NOT NULL,
    payment_type VARCHAR(30) NOT NULL,
    payment_installments INTEGER NOT NULL CHECK (payment_installments >= 1),
    payment_value NUMERIC(10, 2) NOT NULL CHECK (payment_value > 0),
    PRIMARY KEY (order_id, payment_sequential)
);

-- 9. Order Reviews Table
CREATE TABLE IF NOT EXISTS order_reviews (
    review_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL REFERENCES orders(order_id),
    review_score INTEGER NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP NOT NULL,
    review_answer_timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (order_id, review_id)
);

-- Performance Indexes on Foreign Keys & Temporal Search Columns
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_purchase_dt ON orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_seller ON order_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_customers_unique_id ON customers(customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_customers_state ON customers(customer_state);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(product_category_name_english);

-- =============================================================================
-- PART 2: DIMENSIONAL STAR SCHEMA (ANALYTICS / OLAP)
-- =============================================================================

-- 1. DimDate (Calendar Dimension)
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,           -- Format: YYYYMMDD
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    year_quarter VARCHAR(10) NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    year_month VARCHAR(10) NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend INTEGER NOT NULL
);

-- 2. DimCustomer (Customer Dimension)
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL,
    customer_zip_code_prefix VARCHAR(10) NOT NULL,
    customer_city VARCHAR(100) NOT NULL,
    customer_state VARCHAR(5) NOT NULL,
    customer_order_count INTEGER DEFAULT 1,
    is_repeat_customer INTEGER DEFAULT 0
);

-- 3. DimProduct (Product Catalog Dimension)
CREATE TABLE IF NOT EXISTS dim_product (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100),
    product_weight_g NUMERIC(10, 1),
    product_length_cm NUMERIC(6, 1),
    product_height_cm NUMERIC(6, 1),
    product_width_cm NUMERIC(6, 1)
);

-- 4. DimSeller (Seller Dimension)
CREATE TABLE IF NOT EXISTS dim_seller (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(10) NOT NULL,
    seller_city VARCHAR(100) NOT NULL,
    seller_state VARCHAR(5) NOT NULL
);

-- 5. DimGeography (Geographic Centroids)
CREATE TABLE IF NOT EXISTS dim_geography (
    geolocation_zip_code_prefix VARCHAR(10) PRIMARY KEY,
    geolocation_lat NUMERIC(10, 6) NOT NULL,
    geolocation_lng NUMERIC(10, 6) NOT NULL,
    geolocation_city VARCHAR(100) NOT NULL,
    geolocation_state VARCHAR(5) NOT NULL
);

-- 6. FactSales (Central Sales Fact Table at Order Line Item Grain)
CREATE TABLE IF NOT EXISTS fact_sales (
    order_id VARCHAR(50) NOT NULL,
    order_item_id INTEGER NOT NULL,
    order_date_key INTEGER NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    seller_id VARCHAR(50) NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    freight_value NUMERIC(10, 2) NOT NULL,
    gross_item_value NUMERIC(10, 2) NOT NULL,
    review_score NUMERIC(3, 2),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales(order_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_seller ON fact_sales(seller_id);
