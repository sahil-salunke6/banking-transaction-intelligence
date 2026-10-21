
import pytest
from pydantic import ValidationError

from app.schema.transaction_schema import TransactionCreate


def valid_transaction():
    return {
        "transaction_id": "TXN6001",
        "customer_id": "CUST101",
        "amount": 5000,
        "merchant": "Amazon",
        "merchant_category": "ecommerce",
        "status": "success",
        "channel": "upi",
        "country": "india",
        "transaction_time": "2026-10-14T10:15:00",
    }


def test_transaction_fields_are_normalized():
    transaction = TransactionCreate(
        **valid_transaction()
    )

    assert transaction.transaction_id == "TXN6001"
    assert transaction.customer_id == "CUST101"
    assert transaction.merchant_category == "ECOMMERCE"
    assert transaction.status == "SUCCESS"
    assert transaction.channel == "UPI"
    assert transaction.country == "India"


def test_negative_amount_is_rejected():
    data = valid_transaction()
    data["amount"] = -500

    with pytest.raises(ValidationError):
        TransactionCreate(**data)


def test_unknown_status_is_rejected():
    data = valid_transaction()
    data["status"] = "COMPLETED"

    with pytest.raises(ValidationError):
        TransactionCreate(**data)


def test_blank_merchant_is_rejected():
    data = valid_transaction()
    data["merchant"] = "   "

    with pytest.raises(ValidationError):
        TransactionCreate(**data)


def test_missing_transaction_time_is_allowed():
    data = valid_transaction()
    data.pop("transaction_time")

    transaction = TransactionCreate(**data)

    assert transaction.transaction_time is None
