
from app.services import intelligence_service


def test_intelligence_combines_both_assessments(monkeypatch):
    risk_result = {
        "transaction_id": "TXN_TEST_31",
        "risk_score": 70,
        "risk_level": "HIGH",
        "risk_factors": ["High transaction amount"],
    }

    anomaly_result = {
        "transaction_id": "TXN_TEST_31",
        "anomaly_status": "ANOMALY",
        "anomaly_score": 0.12,
        "model": "IsolationForest",
    }

    monkeypatch.setattr(
        intelligence_service,
        "assess_transaction_risk",
        lambda transaction_id: risk_result,
    )

    monkeypatch.setattr(
        intelligence_service,
        "detect_transaction_anomaly",
        lambda transaction_id: anomaly_result,
    )

    result = intelligence_service.get_transaction_intelligence(
        "TXN_TEST_31"
    )

    assert result["transaction_id"] == "TXN_TEST_31"
    assert result["risk_assessment"] == risk_result
    assert result["anomaly_assessment"] == anomaly_result


def test_intelligence_returns_none_for_unknown_transaction(
    monkeypatch,
):
    monkeypatch.setattr(
        intelligence_service,
        "assess_transaction_risk",
        lambda transaction_id: None,
    )

    result = intelligence_service.get_transaction_intelligence(
        "TXN_UNKNOWN"
    )

    assert result is None


def test_intelligence_preserves_insufficient_data_result(
    monkeypatch,
):
    risk_result = {
        "transaction_id": "TXN_TEST_31",
        "risk_score": 0,
        "risk_level": "LOW",
        "risk_factors": [],
    }

    anomaly_result = {
        "transaction_id": "TXN_TEST_31",
        "status": "INSUFFICIENT_DATA",
        "available_transactions": 3,
    }

    monkeypatch.setattr(
        intelligence_service,
        "assess_transaction_risk",
        lambda transaction_id: risk_result,
    )

    monkeypatch.setattr(
        intelligence_service,
        "detect_transaction_anomaly",
        lambda transaction_id: anomaly_result,
    )

    result = intelligence_service.get_transaction_intelligence(
        "TXN_TEST_31"
    )

    assert result["risk_assessment"]["risk_level"] == "LOW"
    assert (
        result["anomaly_assessment"]["status"]
        == "INSUFFICIENT_DATA"
    )
