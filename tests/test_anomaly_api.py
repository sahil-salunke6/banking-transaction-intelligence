
from fastapi.testclient import TestClient

from app.main import app
from app.api import anomaly_router

import pytest


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch):
    monkeypatch.setenv("BANKING_API_KEY", "test-api-key")

client = TestClient(
    app,
    headers={"X-API-Key": "test-api-key"},
)


def test_anomaly_endpoint_returns_assessment(monkeypatch):
    expected_result = {
        "transaction_id": "TXN_ML_10",
        "anomaly_status": "ANOMALY",
        "anomaly_score": 0.1234,
        "features": {
            "amount": 500000.0,
            "transaction_hour": 2,
            "is_foreign": 1,
            "is_failed": 0,
        },
        "model": "IsolationForest",
    }

    monkeypatch.setattr(
        anomaly_router,
        "detect_transaction_anomaly",
        lambda transaction_id: expected_result,
    )

    response = client.get("/anomaly/TXN_ML_10")

    assert response.status_code == 200
    assert response.json() == expected_result


def test_anomaly_endpoint_returns_404_for_unknown_id(
    monkeypatch,
):
    monkeypatch.setattr(
        anomaly_router,
        "detect_transaction_anomaly",
        lambda transaction_id: None,
    )

    response = client.get("/anomaly/TXN_UNKNOWN")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Transaction TXN_UNKNOWN not found"
    }


def test_anomaly_endpoint_returns_503_when_no_data(
    monkeypatch,
):
    monkeypatch.setattr(
        anomaly_router,
        "detect_transaction_anomaly",
        lambda transaction_id: {
            "error": "No transactions available",
            "transaction_id": transaction_id,
        },
    )

    response = client.get("/anomaly/TXN_MISSING")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "No transactions available"
    }
