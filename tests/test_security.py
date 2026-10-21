
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint_remains_public():
    response = client.get("/")

    assert response.status_code == 200


def test_protected_endpoint_rejects_missing_api_key(monkeypatch):
    monkeypatch.setenv("BANKING_API_KEY", "expected-test-key")

    response = client.get("/analytics/summary")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key"
    }


def test_protected_endpoint_rejects_invalid_api_key(monkeypatch):
    monkeypatch.setenv("BANKING_API_KEY", "expected-test-key")

    response = client.get(
        "/analytics/summary",
        headers={"X-API-Key": "wrong-test-key"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key"
    }


def test_protected_endpoint_rejects_requests_when_key_is_unconfigured(
    monkeypatch,
):
    monkeypatch.delenv("BANKING_API_KEY", raising=False)

    response = client.get(
        "/analytics/summary",
        headers={"X-API-Key": "some-test-key"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key"
    }
