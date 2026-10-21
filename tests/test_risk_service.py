
from app.services.risk_service import calculate_risk


def make_transaction(**overrides):
    transaction = {
        "transaction_id": "TXN_TEST_01",
        "customer_id": "CUST101",
        "amount": 1000,
        "merchant": "Amazon",
        "merchant_category": "ECOMMERCE",
        "status": "SUCCESS",
        "channel": "UPI",
        "country": "India",
        "transaction_time": "2026-10-14T14:30:00",
    }

    transaction.update(overrides)
    return transaction


def test_low_risk_transaction():
    result = calculate_risk(make_transaction())

    assert result["risk_score"] == 0
    assert result["risk_level"] == "LOW"
    assert result["risk_factors"] == []


def test_high_amount_adds_30_points():
    result = calculate_risk(
        make_transaction(amount=50001)
    )

    assert result["risk_score"] == 30
    assert result["risk_level"] == "MEDIUM"
    assert "High transaction amount" in result["risk_factors"]


def test_amount_of_50000_does_not_add_points():
    result = calculate_risk(
        make_transaction(amount=50000)
    )

    assert result["risk_score"] == 0


def test_foreign_transaction_adds_25_points():
    result = calculate_risk(
        make_transaction(country="United States")
    )

    assert result["risk_score"] == 25
    assert result["risk_level"] == "LOW"
    assert "Foreign transaction" in result["risk_factors"]


def test_unusual_hour_adds_15_points():
    result = calculate_risk(
        make_transaction(
            transaction_time="2026-10-14T02:30:00"
        )
    )

    assert result["risk_score"] == 15
    assert "Unusual transaction hour" in result["risk_factors"]


def test_failed_transaction_adds_20_points():
    result = calculate_risk(
        make_transaction(status="FAILED")
    )

    assert result["risk_score"] == 20
    assert "Failed transaction" in result["risk_factors"]


def test_combined_risk_rules():
    result = calculate_risk(
        make_transaction(
            amount=85000,
            country="United States",
            transaction_time="2026-10-14T02:30:00",
        )
    )

    assert result["risk_score"] == 70
    assert result["risk_level"] == "HIGH"
    assert len(result["risk_factors"]) == 3


def test_all_four_rules_add_up_correctly():
    result = calculate_risk(
        make_transaction(
            amount=85000,
            country="United States",
            transaction_time="2026-10-14T02:30:00",
            status="FAILED",
        )
    )

    assert result["risk_score"] == 90
    assert result["risk_level"] == "HIGH"
    assert len(result["risk_factors"]) == 4


def test_missing_transaction_time_is_allowed():
    result = calculate_risk(
        make_transaction(transaction_time=None)
    )

    assert result["risk_score"] == 0
    assert result["risk_level"] == "LOW"
