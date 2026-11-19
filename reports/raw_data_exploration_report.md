# Raw Data Exploration Report: Olist Brazilian E-Commerce

## 1. Dataset Overview

| Dataset Key | Table File | Total Rows | Total Columns | Duplicate Rows | Memory (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `orders` | `olist_orders_dataset.csv` | 99,441 | 8 | 0 | 21.95 MB |
| `order_items` | `olist_order_items_dataset.csv` | 112,650 | 7 | 0 | 18.37 MB |
| `customers` | `olist_customers_dataset.csv` | 99,441 | 5 | 0 | 11.03 MB |
| `products` | `olist_products_dataset.csv` | 32,951 | 9 | 0 | 3.73 MB |
| `sellers` | `olist_sellers_dataset.csv` | 3,095 | 4 | 0 | 0.22 MB |
| `payments` | `olist_order_payments_dataset.csv` | 103,886 | 5 | 0 | 8.11 MB |
| `reviews` | `olist_order_reviews_dataset.csv` | 99,224 | 7 | 0 | 17.84 MB |
| `geolocation` | `olist_geolocation_dataset.csv` | 1,000,163 | 5 | 261831 | 50.12 MB |
| `category_translation` | `product_category_name_translation.csv` | 71 | 2 | 0 | 0.0 MB |

## 2. Column-Level Schema & Null Analysis

### Table: `olist_orders_dataset.csv` (orders)

| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `str` | 0 | 0.0% | 99,441 | `e481f51cbdc54678b7cc49136f2d6af7` |
| `customer_id` | `str` | 0 | 0.0% | 99,441 | `9ef432eb6251297304e76186b10a928d` |
| `order_status` | `str` | 0 | 0.0% | 8 | `delivered` |
| `order_purchase_timestamp` | `str` | 0 | 0.0% | 98,875 | `2017-10-02 10:56:33` |
| `order_approved_at` | `str` | 160 | 0.16% | 90,733 | `2017-10-02 11:07:15` |
| `order_delivered_carrier_date` | `str` | 1,783 | 1.79% | 81,018 | `2017-10-04 19:55:00` |
| `order_delivered_customer_date` | `str` | 2,965 | 2.98% | 95,664 | `2017-10-10 21:25:13` |
| `order_estimated_delivery_date` | `str` | 0 | 0.0% | 459 | `2017-10-18 00:00:00` |

### Table: `olist_order_items_dataset.csv` (order_items)

| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `str` | 0 | 0.0% | 98,666 | `00010242fe8c5a6d1ba2dd792cb16214` |
| `order_item_id` | `int64` | 0 | 0.0% | 21 | `1` |
| `product_id` | `str` | 0 | 0.0% | 32,951 | `4244733e06e7ecb4970a6e2683c13e61` |
| `seller_id` | `str` | 0 | 0.0% | 3,095 | `48436dade18ac8b2bce089ec2a041202` |
| `shipping_limit_date` | `str` | 0 | 0.0% | 93,318 | `2017-09-19 09:45:35` |
| `price` | `float64` | 0 | 0.0% | 5,968 | `58.9` |
| `freight_value` | `float64` | 0 | 0.0% | 6,999 | `13.29` |

### Table: `olist_customers_dataset.csv` (customers)

| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `str` | 0 | 0.0% | 99,441 | `06b8999e2fba1a1fbc88172c00ba8bc7` |
| `customer_unique_id` | `str` | 0 | 0.0% | 96,096 | `861eff4711a542e4b93843c6dd7febb0` |
| `customer_zip_code_prefix` | `int64` | 0 | 0.0% | 14,994 | `14409` |
| `customer_city` | `str` | 0 | 0.0% | 4,119 | `franca` |
| `customer_state` | `str` | 0 | 0.0% | 27 | `SP` |

### Table: `olist_products_dataset.csv` (products)

| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | `str` | 0 | 0.0% | 32,951 | `1e9e8ef04dbcff4541ed26657ea517e5` |
| `product_category_name` | `str` | 610 | 1.85% | 73 | `perfumaria` |
| `product_name_lenght` | `float64` | 610 | 1.85% | 66 | `40.0` |
| `product_description_lenght` | `float64` | 610 | 1.85% | 2,960 | `287.0` |
| `product_photos_qty` | `float64` | 610 | 1.85% | 19 | `1.0` |
| `product_weight_g` | `float64` | 2 | 0.01% | 2,204 | `225.0` |
| `product_length_cm` | `float64` | 2 | 0.01% | 99 | `16.0` |
| `product_height_cm` | `float64` | 2 | 0.01% | 102 | `10.0` |
| `product_width_cm` | `float64` | 2 | 0.01% | 95 | `14.0` |

### Table: `olist_sellers_dataset.csv` (sellers)

| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `seller_id` | `str` | 0 | 0.0% | 3,095 | `3442f8959a84dea7ee197c632cb2df15` |
| `seller_zip_code_prefix` | `int64` | 0 | 0.0% | 2,246 | `13023` |
| `seller_city` | `str` | 0 | 0.0% | 611 | `campinas` |
| `seller_state` | `str` | 0 | 0.0% | 23 | `SP` |

### Table: `olist_order_payments_dataset.csv` (payments)

| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `str` | 0 | 0.0% | 99,440 | `b81ef226f3fe1789b1e8b2acac839d17` |
| `payment_sequential` | `int64` | 0 | 0.0% | 29 | `1` |
| `payment_type` | `str` | 0 | 0.0% | 5 | `credit_card` |
| `payment_installments` | `int64` | 0 | 0.0% | 24 | `8` |
| `payment_value` | `float64` | 0 | 0.0% | 29,077 | `99.33` |

### Table: `olist_order_reviews_dataset.csv` (reviews)

| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `review_id` | `str` | 0 | 0.0% | 98,410 | `7bc2406110b926393aa56f80a40eba40` |
| `order_id` | `str` | 0 | 0.0% | 98,673 | `73fc7af87114b39712e6da79b0a377eb` |
| `review_score` | `int64` | 0 | 0.0% | 5 | `4` |
| `review_comment_title` | `str` | 87,656 | 88.34% | 4,527 | `recomendo` |
| `review_comment_message` | `str` | 58,247 | 58.7% | 36,159 | `Recebi bem antes do prazo estipulado.` |
| `review_creation_date` | `str` | 0 | 0.0% | 636 | `2018-01-18 00:00:00` |
| `review_answer_timestamp` | `str` | 0 | 0.0% | 98,248 | `2018-01-18 21:46:59` |

### Table: `olist_geolocation_dataset.csv` (geolocation)

| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `geolocation_zip_code_prefix` | `int64` | 0 | 0.0% | 19,015 | `1037` |
| `geolocation_lat` | `float64` | 0 | 0.0% | 717,360 | `-23.54562128115268` |
| `geolocation_lng` | `float64` | 0 | 0.0% | 717,613 | `-46.63929204800168` |
| `geolocation_city` | `str` | 0 | 0.0% | 8,011 | `sao paulo` |
| `geolocation_state` | `str` | 0 | 0.0% | 27 | `SP` |

### Table: `product_category_name_translation.csv` (category_translation)

| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `product_category_name` | `str` | 0 | 0.0% | 71 | `beleza_saude` |
| `product_category_name_english` | `str` | 0 | 0.0% | 71 | `health_beauty` |
