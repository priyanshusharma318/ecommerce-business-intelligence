# Data Quality & Cleansing Audit Report

## 1. Cleansing Objectives & Standards
- Enforced strict primary key uniqueness across orders, customers, products, sellers, and items.
- Translated Portuguese category names to standardized English identifiers.
- Standardized Brazilian zip code prefixes to 5-digit zero-padded format.
- Cast all temporal timestamps to standard ISO datetime formats.
- Clamped review scores to [1, 5] and imputed text nulls gracefully.
- Aggregated redundant geolocation coordinate entries to zip code centroid medians.

## 2. Operation Audit Log

| Target Table | Cleansing Operation | Action Details | Records Affected |
| :--- | :--- | :--- | :--- |
| `orders` | Missing Value Audit | Identified orders without customer delivery timestamp (cancelled, in-transit, or processing) | 2,965 |
| `orders` | Cleaning Completed | Cleaned 99441 of 99441 records | 0 |
| `customers` | Cleaning Completed | Processed 99441 records | 0 |
| `products` | Null Imputation | Imputed missing category names as 'outros' | 610 |
| `products` | Median Imputation | Imputed nulls in product_name_lenght with median 51.0 | 610 |
| `products` | Median Imputation | Imputed nulls in product_description_lenght with median 595.0 | 610 |
| `products` | Median Imputation | Imputed nulls in product_photos_qty with median 1.0 | 610 |
| `products` | Median Imputation | Imputed nulls in product_weight_g with median 700.0 | 2 |
| `products` | Median Imputation | Imputed nulls in product_length_cm with median 25.0 | 2 |
| `products` | Median Imputation | Imputed nulls in product_height_cm with median 13.0 | 2 |
| `products` | Median Imputation | Imputed nulls in product_width_cm with median 20.0 | 2 |
| `products` | Cleaning Completed | Cleaned 32951 products | 0 |
| `sellers` | Cleaning Completed | Cleaned 3095 sellers | 0 |
| `order_items` | Cleaning Completed | Cleaned 112650 line items | 0 |
| `payments` | Invalid Value Removal | Filtered payment_type 'not_defined' or payment_value <= 0 | 9 |
| `payments` | Cleaning Completed | Cleaned 103877 payment records | 0 |
| `reviews` | Cleaning Completed | Cleaned 99224 review records | 0 |
| `geolocation` | Bounding Box Filter | Removed coordinates outside Brazilian borders | 29 |
| `geolocation` | Aggregation to Unique Prefix | Condensed 1000163 coordinate points into 19011 unique zip code centroids | 981,152 |
| `referential_integrity` | Foreign Key Audit | orders_to_customers_orphans | 0 |
| `referential_integrity` | Foreign Key Audit | items_to_orders_orphans | 0 |
| `referential_integrity` | Foreign Key Audit | items_to_products_orphans | 0 |
| `referential_integrity` | Foreign Key Audit | items_to_sellers_orphans | 0 |