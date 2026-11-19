"""
Unit tests for data cleaning, type conversions, duplicate resolution,
and null value handling across all relational entities.
"""

import pytest
import pandas as pd
import numpy as np
from src.data_cleaning import DataCleaner


@pytest.fixture
def cleaner(tmp_path):
    return DataCleaner(processed_data_dir=tmp_path)


def test_clean_orders_deduplication_and_dates(cleaner):
    # Setup raw mock dataframe with duplicate order_id and string timestamps
    raw_orders = pd.DataFrame({
        "order_id": ["ord_001", "ord_001", "ord_002"],
        "customer_id": ["cust_1", "cust_1", "cust_2"],
        "order_status": [" DELIVERED ", "delivered", "shipped"],
        "order_purchase_timestamp": ["2017-05-10 10:00:00", "2017-05-10 10:00:00", "2018-01-15 14:30:00"],
        "order_delivered_customer_date": ["2017-05-18 16:00:00", "2017-05-18 16:00:00", None],
        "order_estimated_delivery_date": ["2017-05-25 00:00:00", "2017-05-25 00:00:00", "2018-01-30 00:00:00"],
    })

    df_clean = cleaner.clean_orders(raw_orders)

    # 1. Deduplication assertion
    assert len(df_clean) == 2, "Orders should be deduplicated by order_id"
    # 2. String trimming & lowercase assertion
    assert df_clean.iloc[0]["order_status"] == "delivered"
    # 3. Datetime conversion assertion
    assert pd.api.types.is_datetime64_any_dtype(df_clean["order_purchase_timestamp"])
    assert pd.api.types.is_datetime64_any_dtype(df_clean["order_delivered_customer_date"])
    # 4. Null preservation for non-delivered
    assert pd.isna(df_clean[df_clean["order_id"] == "ord_002"]["order_delivered_customer_date"].iloc[0])


def test_clean_customers_normalization(cleaner):
    raw_customers = pd.DataFrame({
        "customer_id": ["c1", "c2", "c2"],
        "customer_unique_id": ["u1", "u2", "u2"],
        "customer_zip_code_prefix": [1008, "01008.0", 35400],
        "customer_city": ["  sao paulo ", "RIO DE JANEIRO", "Belo Horizonte"],
        "customer_state": ["sp", "rj", "mg"],
    })

    df_clean = cleaner.clean_customers(raw_customers)

    # 1. Deduplication
    assert len(df_clean) == 2
    # 2. Zip code zero-padding to 5 digits
    assert df_clean.loc[df_clean["customer_id"] == "c1", "customer_zip_code_prefix"].iloc[0] == "01008"
    # 3. Text standardization
    assert df_clean.loc[df_clean["customer_id"] == "c1", "customer_city"].iloc[0] == "sao paulo"
    assert df_clean.loc[df_clean["customer_id"] == "c1", "customer_state"].iloc[0] == "SP"


def test_clean_products_translation_and_imputation(cleaner):
    raw_products = pd.DataFrame({
        "product_id": ["p1", "p2", "p3"],
        "product_category_name": ["beleza_saude", "portateis_cozinha_e_preparadores_de_alimentos", None],
        "product_weight_g": [500.0, None, 1000.0],
        "product_length_cm": [20.0, 30.0, None],
        "product_height_cm": [10.0, None, 20.0],
        "product_width_cm": [15.0, 25.0, None],
    })

    translation_df = pd.DataFrame({
        "product_category_name": ["beleza_saude"],
        "product_category_name_english": ["health_beauty"],
    })

    df_clean = cleaner.clean_products(raw_products, translation_df)

    # 1. Translation mapping
    assert df_clean.loc[df_clean["product_id"] == "p1", "product_category_name_english"].iloc[0] == "health_beauty"
    # 2. Override mapping for missing dictionary entry
    assert df_clean.loc[df_clean["product_id"] == "p2", "product_category_name_english"].iloc[0] == "small_appliances_and_food_preparers"
    # 3. Missing category fallback
    assert df_clean.loc[df_clean["product_id"] == "p3", "product_category_name_english"].iloc[0] == "other_unspecified"
    # 4. Median imputation of missing weight
    assert df_clean["product_weight_g"].isnull().sum() == 0


def test_clean_order_items_validation(cleaner):
    raw_items = pd.DataFrame({
        "order_id": ["o1", "o1", "o2", "o3"],
        "order_item_id": [1, 1, 1, 1],  # Duplicate on (o1, 1)
        "product_id": ["p1", "p1", "p2", "p3"],
        "seller_id": ["s1", "s1", "s2", "s3"],
        "shipping_limit_date": ["2018-05-01 00:00:00"] * 4,
        "price": [100.0, 100.0, 0.0, -50.0],  # 0.0 and -50.0 are invalid
        "freight_value": [15.0, 15.0, 10.0, -5.0],
    })

    df_clean = cleaner.clean_order_items(raw_items)

    # Deduplicated (o1, 1) + filtered non-positive prices
    assert len(df_clean) == 1
    assert df_clean.iloc[0]["order_id"] == "o1"
    assert df_clean.iloc[0]["price"] == 100.0
    assert df_clean.iloc[0]["freight_value"] == 15.0


def test_clean_payments_validation(cleaner):
    raw_payments = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "payment_sequential": [1, 1, 1],
        "payment_type": ["credit_card", "not_defined", "voucher"],
        "payment_installments": [0, 1, 2],  # 0 installments should clamp to 1
        "payment_value": [150.0, 0.0, 50.0],  # 0.0 is invalid
    })

    df_clean = cleaner.clean_payments(raw_payments)

    assert len(df_clean) == 2
    assert "not_defined" not in df_clean["payment_type"].values
    assert (df_clean["payment_installments"] >= 1).all()


def test_clean_reviews_score_and_nulls(cleaner):
    raw_reviews = pd.DataFrame({
        "review_id": ["r1", "r1", "r2"],
        "order_id": ["o1", "o1", "o2"],
        "review_score": [5, 5, 0],  # Score 0 should clamp to 1
        "review_comment_title": [None, None, "Bom"],
        "review_comment_message": [None, None, "Gostei"],
        "review_creation_date": ["2018-01-01"] * 3,
        "review_answer_timestamp": ["2018-01-02", "2018-01-03", "2018-01-02"],
    })

    df_clean = cleaner.clean_reviews(raw_reviews)

    assert len(df_clean) == 2
    assert df_clean.loc[df_clean["review_id"] == "r2", "review_score"].iloc[0] == 1.0
    assert df_clean.loc[df_clean["review_id"] == "r1", "review_comment_title"].iloc[0] == ""
