"""
Tests for feature engineering, financial metrics, customer repeat calculations,
and RFM segmentation formulas.
"""

import pytest
import pandas as pd
import numpy as np

from src.feature_engineering import FeatureEngineer
from src.analysis import BusinessAnalytics


@pytest.fixture
def feature_engineer():
    return FeatureEngineer()


def test_order_temporal_and_delivery_features(feature_engineer):
    orders_df = pd.DataFrame({
        "order_id": ["o1", "o2"],
        "order_purchase_timestamp": ["2018-03-01 10:30:00", "2018-05-15 19:45:00"],
        "order_delivered_customer_date": ["2018-03-10 14:30:00", "2018-05-25 10:00:00"],
        "order_estimated_delivery_date": ["2018-03-15 00:00:00", "2018-05-20 00:00:00"],
    })

    enriched = feature_engineer.build_order_features(orders_df)

    # 1. Temporal feature checks
    assert enriched.loc[0, "order_year"] == 2018
    assert enriched.loc[0, "order_month"] == "2018-03"
    assert enriched.loc[0, "order_quarter"] == "2018Q1"
    assert enriched.loc[0, "order_hour"] == 10

    # 2. Logistics feature checks
    # o1: Purchased March 1 10:30, Delivered March 10 14:30 -> ~9.16 days
    assert round(enriched.loc[0, "delivery_duration_days"], 1) == 9.2
    # o1 estimated March 15; delivered March 10 -> delay is negative (-4.4 days, on time)
    assert enriched.loc[0, "delivery_delay_days"] < 0
    assert enriched.loc[0, "is_late_delivery"] == 0

    # o2 estimated May 20; delivered May 25 -> delay is positive (+5.4 days, late!)
    assert enriched.loc[1, "delivery_delay_days"] > 0
    assert enriched.loc[1, "is_late_delivery"] == 1


def test_customer_repeat_features(feature_engineer):
    orders_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "customer_id": ["c1", "c2", "c3"],
    })
    customers_df = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3"],
        # u1 places 2 orders (via c1 and c3), u2 places 1 order (via c2)
        "customer_unique_id": ["u1", "u2", "u1"],
        "customer_state": ["SP", "RJ", "SP"],
        "customer_city": ["sao paulo", "rio de janeiro", "sao paulo"],
    })

    df_ord_enr, df_cust_enr = feature_engineer.build_customer_features(orders_df, customers_df)

    # u1 placed 2 orders
    u1_order_count = df_cust_enr.loc[df_cust_enr["customer_unique_id"] == "u1", "customer_order_count"].iloc[0]
    u1_is_repeat = df_cust_enr.loc[df_cust_enr["customer_unique_id"] == "u1", "is_repeat_customer"].iloc[0]
    assert u1_order_count == 2
    assert u1_is_repeat == 1

    # u2 placed 1 order
    u2_order_count = df_cust_enr.loc[df_cust_enr["customer_unique_id"] == "u2", "customer_order_count"].iloc[0]
    u2_is_repeat = df_cust_enr.loc[df_cust_enr["customer_unique_id"] == "u2", "is_repeat_customer"].iloc[0]
    assert u2_order_count == 1
    assert u2_is_repeat == 0


def test_financial_metrics_distinction(feature_engineer):
    items_df = pd.DataFrame({
        "order_id": ["o1", "o1", "o2"],
        "order_item_id": [1, 2, 1],
        "price": [50.0, 75.0, 120.0],
        "freight_value": [10.0, 15.0, 20.0],
    })
    payments_df = pd.DataFrame({
        "order_id": ["o1", "o1", "o2"],
        "payment_sequential": [1, 2, 1],
        "payment_type": ["voucher", "credit_card", "boleto"],
        "payment_installments": [1, 3, 1],
        "payment_value": [50.0, 100.0, 140.0],  # Total o1 payment = 150.0 (item 125 + freight 25)
    })

    df_items_enr, order_fin = feature_engineer.build_financial_features(items_df, payments_df)

    o1_fin = order_fin.loc[order_fin["order_id"] == "o1"].iloc[0]
    # Revenue = sum of price (50 + 75 = 125.0)
    assert o1_fin["product_revenue"] == 125.0
    # Freight = 10 + 15 = 25.0
    assert o1_fin["freight_charges"] == 25.0
    # Gross value = 150.0
    assert o1_fin["total_order_gross_value"] == 150.0
    # Payment value matches gross
    assert o1_fin["total_payment_value"] == 150.0


def test_rfm_calculation_and_segments(tmp_path):
    analytics = BusinessAnalytics(exports_dir=tmp_path)

    orders_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4", "o5"],
        "customer_id": ["c1", "c2", "c3", "c4", "c5"],
        "order_status": ["delivered"] * 5,
        "order_purchase_timestamp": [
            "2018-08-01 10:00:00",
            "2018-07-01 10:00:00",
            "2018-05-01 10:00:00",
            "2017-01-01 10:00:00",
            "2018-08-15 10:00:00",
        ],
    })
    customers_df = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3", "c4", "c5"],
        "customer_unique_id": ["u1", "u2", "u3", "u4", "u5"],
    })
    items_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4", "o5"],
        "price": [100.0, 250.0, 50.0, 500.0, 120.0],
        "freight_value": [15.0] * 5,
    })

    rfm_df = analytics.calculate_rfm_segmentation(orders_df, customers_df, items_df)

    assert len(rfm_df) == 5
    assert "customer_segment" in rfm_df.columns
    assert "R_Score" in rfm_df.columns
    assert "F_Score" in rfm_df.columns
    assert "M_Score" in rfm_df.columns
    # Check that export file was generated
    assert (tmp_path / "rfm_segment_summary.csv").is_file()


def test_rfm_with_pre_existing_customer_unique_id(tmp_path):
    """
    Test the exact failure scenario: orders_df ALREADY has customer_unique_id
    (e.g., from FeatureEngineer.build_customer_features).
    Must not crash with KeyError: 'customer_unique_id' due to _x/_y merge suffix collisions.
    """
    analytics = BusinessAnalytics(exports_dir=tmp_path)

    orders_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "customer_id": ["c1", "c2", "c3"],
        "customer_unique_id": ["u1", "u2", "u3"],  # Pre-existing!
        "order_status": ["delivered"] * 3,
        "order_purchase_timestamp": ["2018-08-01 10:00:00", "2018-07-01 10:00:00", "2018-05-01 10:00:00"],
    })
    customers_df = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3"],
        "customer_unique_id": ["u1", "u2", "u3"],
    })
    items_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "price": [100.0, 200.0, 300.0],
        "freight_value": [10.0, 10.0, 10.0],
    })

    rfm_df = analytics.calculate_rfm_segmentation(orders_df, customers_df, items_df)
    assert len(rfm_df) == 3
    assert "customer_unique_id" in rfm_df.columns
    assert set(rfm_df["customer_unique_id"]) == {"u1", "u2", "u3"}


def test_rfm_with_missing_and_invalid_customer_unique_ids(tmp_path):
    """
    Test safe handling of missing, empty, NaN, and placeholder customer identifiers.
    """
    analytics = BusinessAnalytics(exports_dir=tmp_path)

    orders_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4", "o5"],
        "customer_id": ["c1", "c2", "c3", "c4", "c5"],
        "order_status": ["delivered"] * 5,
        "order_purchase_timestamp": ["2018-08-01 10:00:00"] * 5,
    })
    customers_df = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3", "c4", "c5"],
        # u1 valid, c2 has None, c3 has empty string, c4 has 'NaN', u5 valid
        "customer_unique_id": ["u1", None, "   ", "NaN", "u5"],
    })
    items_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4", "o5"],
        "price": [100.0] * 5,
        "freight_value": [10.0] * 5,
    })

    rfm_df = analytics.calculate_rfm_segmentation(orders_df, customers_df, items_df)
    # Only u1 and u5 should be in final RFM dataset
    assert len(rfm_df) == 2
    assert set(rfm_df["customer_unique_id"]) == {"u1", "u5"}


def test_rfm_no_revenue_or_order_duplication(tmp_path):
    """
    Test that multi-item orders do not duplicate orders or inflate revenue in RFM.
    Customer u1 places 1 order (o1) containing 3 items of price 50 each (total 150).
    Customer u2 places 2 orders (o2, o3) with 1 item of price 100 each (total 200).
    """
    analytics = BusinessAnalytics(exports_dir=tmp_path)

    orders_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "customer_id": ["c1", "c2", "c3"],
        "order_status": ["delivered"] * 3,
        "order_purchase_timestamp": ["2018-08-01 10:00:00", "2018-07-01 10:00:00", "2018-06-01 10:00:00"],
    })
    customers_df = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3"],
        "customer_unique_id": ["u1", "u2", "u2"],
    })
    # o1 has 3 items
    items_df = pd.DataFrame({
        "order_id": ["o1", "o1", "o1", "o2", "o3"],
        "order_item_id": [1, 2, 3, 1, 1],
        "price": [50.0, 50.0, 50.0, 100.0, 100.0],
        "freight_value": [10.0] * 5,
    })

    rfm_df = analytics.calculate_rfm_segmentation(orders_df, customers_df, items_df)

    # u1: 1 order, monetary = 150.0
    u1_row = rfm_df.loc[rfm_df["customer_unique_id"] == "u1"].iloc[0]
    assert u1_row["frequency"] == 1
    assert u1_row["monetary"] == 150.0

    # u2: 2 orders, monetary = 200.0
    u2_row = rfm_df.loc[rfm_df["customer_unique_id"] == "u2"].iloc[0]
    assert u2_row["frequency"] == 2
    assert u2_row["monetary"] == 200.0


def test_cohort_retention_with_pre_existing_customer_unique_id(tmp_path):
    """
    Test that cohort retention works seamlessly when df_orders already has customer_unique_id.
    """
    analytics = BusinessAnalytics(exports_dir=tmp_path)

    orders_df = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "customer_id": ["c1", "c2", "c3"],
        "customer_unique_id": ["u1", "u1", "u2"],
        "order_status": ["delivered"] * 3,
        "order_purchase_timestamp": [
            "2018-01-10 10:00:00",
            "2018-02-15 10:00:00",
            "2018-01-20 10:00:00",
        ],
    })
    customers_df = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3"],
        "customer_unique_id": ["u1", "u1", "u2"],
    })

    retention_matrix = analytics.calculate_cohort_retention(orders_df, customers_df)
    assert not retention_matrix.empty
