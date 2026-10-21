
import pandas as pd

from app.services.anomaly_service import build_features
from app.services import anomaly_service
from pathlib import Path

#------------------------------------------
#   Tests for feature transformation
#------------------------------------------

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


def test_build_features_creates_numeric_columns():
    records = [make_transaction()]

    df, features = build_features(records)

    assert len(df) == 1
    assert list(features.columns) == [
        "amount",
        "transaction_hour",
        "is_foreign",
        "is_failed",
    ]


def test_build_features_extracts_transaction_hour():
    records = [
        make_transaction(
            transaction_time="2026-10-14T02:30:00"
        )
    ]

    _, features = build_features(records)

    assert features.iloc[0]["transaction_hour"] == 2


def test_build_features_identifies_foreign_transaction():
    records = [
        make_transaction(country="United States")
    ]

    _, features = build_features(records)

    assert features.iloc[0]["is_foreign"] == 1


def test_build_features_identifies_failed_transaction():
    records = [make_transaction(status="FAILED")]

    _, features = build_features(records)

    assert features.iloc[0]["is_failed"] == 1


def test_build_features_removes_invalid_amount():
    records = [
        make_transaction(amount="not-a-number"),
        make_transaction(
            transaction_id="TXN_TEST_02",
            amount=2500,
        ),
    ]

    df, features = build_features(records)

    assert len(df) == 1
    assert len(features) == 1
    assert features.iloc[0]["amount"] == 2500


def test_build_features_handles_empty_records():
    df, features = build_features([])

    assert df.empty
    assert features.empty



def test_build_features_excludes_missing_timestamp():
    records = [make_transaction(transaction_time=None)]

    df, features = build_features(records)

    assert df.empty
    assert features.empty





#------------------------------------------
#   Anamoly service tests
#------------------------------------------

def make_transactions(count=5):
    records = []

    for i in range(count):
        records.append({
            "transaction_id": f"TXN_ML_{i + 1}",
            "customer_id": f"CUST{i + 1}",
            "amount": 1000 + (i * 100),
            "merchant": "Amazon",
            "merchant_category": "ECOMMERCE",
            "status": "SUCCESS",
            "channel": "UPI",
            "country": "India",
            "transaction_time": (
                f"2026-10-14T{10 + i:02d}:00:00"
            ),
        })

    return records


def test_anomaly_service_returns_insufficient_data(
    monkeypatch,
):
    records = make_transactions(count=4)

    monkeypatch.setattr(
        anomaly_service,
        "get_all",
        lambda: records,
    )

    result = anomaly_service.detect_transaction_anomaly(
        "TXN_ML_1"
    )

    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["available_transactions"] == 4


def test_anomaly_service_returns_none_for_unknown_id(
    monkeypatch,
):
    records = make_transactions(count=5)

    monkeypatch.setattr(
        anomaly_service,
        "get_all",
        lambda: records,
    )

    result = anomaly_service.detect_transaction_anomaly(
        "TXN_UNKNOWN"
    )

    assert result is None


def test_anomaly_service_handles_empty_database(
    monkeypatch,
):
    monkeypatch.setattr(
        anomaly_service,
        "get_all",
        lambda: [],
    )

    result = anomaly_service.detect_transaction_anomaly(
        "TXN_MISSING"
    )

    assert result["error"] == "No transactions available"



def test_anomaly_service_returns_assessment(monkeypatch):
    import numpy as np

    records = make_transactions(count=10)

    # Include an unusually large transaction.
    records[9]["amount"] = 500000
    records[9]["country"] = "United States"
    records[9]["transaction_time"] = "2026-10-14T02:00:00"

    class FakeModel:
        def predict(self, features):
            return np.array([-1])

        def decision_function(self, features):
            return np.array([-0.75])

    fake_artifact = {
        "model": FakeModel(),
        "feature_columns": [
            "amount",
            "transaction_hour",
            "is_foreign",
            "is_failed",
        ],
        "model_name": "IsolationForest",
        "model_version": "test-version",
        "trained_at": "2026-10-14T00:00:00",
        "training_rows": 10,
        "n_estimators": 100,
        "contamination": 0.1,
    }

    monkeypatch.setattr(
        anomaly_service,
        "get_all",
        lambda: records,
    )
    
    fake_model_path = Path("fake-model.joblib")
    monkeypatch.setattr(
        anomaly_service,
        "MODEL_PATH",
        fake_model_path,
    )

    original_exists = Path.exists

    monkeypatch.setattr(
        anomaly_service.Path,
        "exists",
        lambda self: (
            True
            if self == fake_model_path
            else original_exists(self)
        ),
    )
    monkeypatch.setattr(
        anomaly_service,
        "get_model_artifact",
        lambda: fake_artifact,
    )

    result = anomaly_service.detect_transaction_anomaly(
        "TXN_ML_10"
    )

    assert result["transaction_id"] == "TXN_ML_10"
    assert result["anomaly_status"] == "ANOMALY"
    assert isinstance(result["anomaly_score"], float)
    assert result["model"] == "IsolationForest"
    assert set(result["features"]) == {
        "amount",
        "transaction_hour",
        "is_foreign",
        "is_failed",
    }

