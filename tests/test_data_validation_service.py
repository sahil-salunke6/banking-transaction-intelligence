
import pandas as pd
import pytest

from app.services.data_validation_service import (
    validate_transaction_dataframe,
)


def make_transaction(**overrides):
    transaction = {
        "transaction_id": "TXN001",
        "customer_id": "CUST101",
        "amount": 5000,
        "merchant": "Amazon",
        "merchant_category": "ECOMMERCE",
        "status": "SUCCESS",
        "channel": "UPI",
        "country": "India",
        "transaction_time": "2026-09-20 10:15:00",
    }
    transaction.update(overrides)
    return transaction


def test_valid_transaction_is_accepted():
    df = pd.DataFrame([make_transaction()])

    valid_df, rejected_df = validate_transaction_dataframe(df)

    assert len(valid_df) == 1
    assert len(rejected_df) == 0
    assert valid_df.iloc[0]["amount"] == 5000
    assert pd.notna(valid_df.iloc[0]["transaction_time"])


def test_non_numeric_amount_is_rejected():
    df = pd.DataFrame([
        make_transaction(amount="abc")
    ])

    valid_df, rejected_df = validate_transaction_dataframe(df)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1
    assert any(
        "amount must be" in error
        for error in rejected_df.iloc[0]["_validation_errors"]
    )


def test_invalid_timestamp_is_rejected():
    df = pd.DataFrame([
        make_transaction(transaction_time="not-a-date")
    ])

    valid_df, rejected_df = validate_transaction_dataframe(df)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1
    assert any(
        "transaction_time" in error
        for error in rejected_df.iloc[0]["_validation_errors"]
    )


def test_blank_transaction_id_is_rejected():
    df = pd.DataFrame([
        make_transaction(transaction_id="   ")
    ])

    valid_df, rejected_df = validate_transaction_dataframe(df)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1


def test_missing_required_column_raises_error():
    df = pd.DataFrame([
        {
            "transaction_id": "TXN001",
            "amount": 5000,
        }
    ])

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_transaction_dataframe(df)


def test_original_dataframe_is_not_modified():
    df = pd.DataFrame([
        make_transaction(country="  India  ")
    ])
    original_country = df.loc[0, "country"]

    validate_transaction_dataframe(df)

    assert df.loc[0, "country"] == original_country
