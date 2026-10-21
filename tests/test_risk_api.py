
from fastapi.testclient import TestClient

from app.main import app
from app.api import risk_router

import pytest


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch):
    monkeypatch.setenv("BANKING_API_KEY", "test-api-key")

client = TestClient(
    app,
    headers={"X-API-Key": "test-api-key"},
)


def test_risk_endpoint_returns_assessment(monkeypatch):
    expected_result = {
        "transaction_id": "TXN_TEST_API",
        "risk_score": 70,
        "risk_level": "HIGH",
        "risk_factors": [
            "High transaction amount",
            "Foreign transaction",
            "Unusual transaction hour",
        ],
    }

    def fake_assessment(transaction_id):
        assert transaction_id == "TXN_TEST_API"
        return expected_result

    monkeypatch.setattr(
        risk_router,
        "assess_transaction_risk",
        fake_assessment,
    )

    response = client.get("/risk/TXN_TEST_API")

    assert response.status_code == 200
    assert response.json() == expected_result


def test_risk_endpoint_returns_404_for_missing_transaction(
    monkeypatch,
):
    monkeypatch.setattr(
        risk_router,
        "assess_transaction_risk",
        lambda transaction_id: None,
    )

    response = client.get("/risk/TXN_DOES_NOT_EXIST")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Transaction TXN_DOES_NOT_EXIST not found"
    }
