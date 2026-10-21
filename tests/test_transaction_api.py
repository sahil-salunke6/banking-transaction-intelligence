
from fastapi.testclient import TestClient

from app.main import app

import pytest


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch):
    monkeypatch.setenv("BANKING_API_KEY", "test-api-key")


client = TestClient(
    app,
    headers={"X-API-Key": "test-api-key"},
)


def test_invalid_status_returns_422():
    response = client.post(
        "/transactions/",
        json={
            "transaction_id": "TXN_TEST_INVALID",
            "customer_id": "CUST101",
            "amount": 5000,
            "merchant": "Amazon",
            "merchant_category": "ECOMMERCE",
            "status": "COMPLETED",
            "channel": "UPI",
            "country": "India",
        },
    )

    assert response.status_code == 422
