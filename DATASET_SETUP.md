# Dataset Setup Guide: Brazilian E-Commerce Public Dataset by Olist

This document outlines the source, structure, and instructions for obtaining and staging the real Brazilian E-Commerce public dataset provided by Olist.

---

## 1. Dataset Origin & Background

The dataset is an official public collection of 100,000 anonymized orders placed between **September 2016 and September 2018** on the Brazilian marketplace **Olist**. Olist connects small businesses across Brazil to leading e-commerce marketplaces and manages end-to-end fulfillment, catalog publishing, and customer logistics.

- **Primary Source:** [Kaggle Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **Publisher:** Olist & Kaggle
- **License:** CC BY-NC-SA 4.0 (Non-Commercial, Attribution, Share-Alike)
- **Currency:** Brazilian Real (BRL / R$)
- **Geographic Scope:** Brazil (27 Federal Units / States)

---

## 2. Required CSV Files & Target Location

All raw CSV files must be downloaded and placed directly inside the `data/raw/` folder at the root of this project:

```text
ecommerce-business-intelligence/
└── data/
    └── raw/
        ├── olist_orders_dataset.csv
        ├── olist_order_items_dataset.csv
        ├── olist_customers_dataset.csv
        ├── olist_products_dataset.csv
        ├── olist_sellers_dataset.csv
        ├── olist_order_payments_dataset.csv
        ├── olist_order_reviews_dataset.csv
        ├── olist_geolocation_dataset.csv
        └── product_category_name_translation.csv
```

---

## 3. Step-by-Step Download Instructions

### Method A: Manual Download via Kaggle Web Interface (Recommended)
1. Open your web browser and navigate to:
   [https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
2. Sign in to your Kaggle account (free registration).
3. Click the **"Download"** button (top right of the dataset overview, approx. 45 MB compressed archive `brazilian-ecommerce.zip`).
4. Extract the ZIP archive onto your computer.
5. Copy or move all 9 extracted `.csv` files into the project's `data/raw/` directory:
   - `olist_orders_dataset.csv` (~99,441 rows)
   - `olist_order_items_dataset.csv` (~112,650 rows)
   - `olist_customers_dataset.csv` (~99,441 rows)
   - `olist_products_dataset.csv` (~32,951 rows)
   - `olist_sellers_dataset.csv` (~3,095 rows)
   - `olist_order_payments_dataset.csv` (~103,886 rows)
   - `olist_order_reviews_dataset.csv` (~99,224 rows)
   - `olist_geolocation_dataset.csv` (~1,000,163 rows)
   - `product_category_name_translation.csv` (~71 rows)

### Method B: Automated Download via Kaggle CLI (Terminal / Command Line)
If you have configured Kaggle API credentials (`kaggle.json` in `~/.kaggle/` or `%USERPROFILE%\.kaggle\`), run:

```bash
# Ensure Kaggle CLI is installed
pip install kaggle

# Download the archive directly to data/raw/
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
```

---

## 4. Dataset Schemas & Relational Mapping

| Filename | Primary Key | Description & Key Foreign Keys |
| :--- | :--- | :--- |
| `olist_orders_dataset.csv` | `order_id` | Core transaction fact. Links to `customer_id`. Contains order status and full delivery timestamps (purchase, approved, carrier, delivered, estimated). |
| `olist_order_items_dataset.csv` | (`order_id`, `order_item_id`) | Line items per order. Links to `product_id` and `seller_id`. Contains `price` and `freight_value`. |
| `olist_customers_dataset.csv` | `customer_id` | Unique per order key. Links to `customer_unique_id` (real persistent customer identity across multiple purchases) and customer zip code prefix. |
| `olist_products_dataset.csv` | `product_id` | Product catalog details: category name in Portuguese, description length, photos quantity, weight, and dimensional measurements. |
| `olist_sellers_dataset.csv` | `seller_id` | Merchant profile: seller zip code prefix, city, and state. |
| `olist_order_payments_dataset.csv` | (`order_id`, `payment_sequential`) | Payment transactions: payment type (credit card, boleto, voucher, debit), installments, and payment value. |
| `olist_order_reviews_dataset.csv` | `review_id` (note: some reviews cover multi-item orders) | Customer feedback: score (1 to 5), review title, comments, creation date, and answer timestamp. |
| `olist_geolocation_dataset.csv` | Non-unique (`geolocation_zip_code_prefix`) | Geographic mapping of Brazilian zip codes to latitude, longitude, city, and state. |
| `product_category_name_translation.csv` | `product_category_name` | Dictionary mapping Portuguese category names to English equivalents. |

---

## 5. Important Data Quality & Modeling Notes

1. **Two Customer IDs:**
   - `customer_id`: Unique identifier created per order. Used as a transaction key.
   - `customer_unique_id`: Identifies the physical person. **Must be used for customer retention, cohort analysis, and RFM segmentation.**
2. **Delivery Statuses:**
   - Statuses include: `delivered`, `shipped`, `canceled`, `invoiced`, `processing`, `unavailable`, `created`, `approved`.
   - Core sales and delivery metrics focus strictly on `delivered` orders (~97% of total volume) unless explicitly analyzing cancellation rates or order funnel drop-off.
3. **Multi-Payment Orders:**
   - An order may be paid using multiple payment methods (e.g., partial voucher + credit card) or multiple vouchers.
4. **Untranslated Categories:**
   - Certain categories in `olist_products_dataset.csv` (e.g., `portateis_cozinha_e_preparadores_de_alimentos`, `pc_gamer`) may not appear in the translation file. The data cleaning pipeline handles these gracefully via standardized normalization fallbacks.
