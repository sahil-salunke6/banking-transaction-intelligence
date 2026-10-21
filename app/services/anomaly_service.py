
from pathlib import Path

import joblib
import pandas as pd

from app.repositories.transaction_repository import get_all

import logging

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "artifacts" / "isolation_forest.joblib"

MINIMUM_TRANSACTIONS = 5


_MODEL_ARTIFACT = None


def load_model_artifact():
    """
    Load the trained model into memory.
    Call this during application startup.
    """

    global _MODEL_ARTIFACT

    if not MODEL_PATH.exists():
        _MODEL_ARTIFACT = None
        print(
            "Anomaly model not found. "
            "Run scripts/train_anomaly_model.py."
        )

        logger.warning(
            "Anomaly model artifact not found",
            extra={"model_path": str(MODEL_PATH)},
        )

        return None

    # Load the artifact from disk once.
    try:
        _MODEL_ARTIFACT = joblib.load(MODEL_PATH)
    except Exception:
        _MODEL_ARTIFACT = None

        logger.exception(
            "Failed to load anomaly model artifact",
            extra={"model_path": str(MODEL_PATH)},
        )

        return None

    print(
        "Anomaly model loaded:",
        _MODEL_ARTIFACT.get("model_version", "unknown"),
    )

    logger.info(
        "Anomaly model loaded",
        extra={
            "model_version": _MODEL_ARTIFACT.get(
                "model_version", "unknown"
            ),
            "training_rows": _MODEL_ARTIFACT.get(
                "training_rows", 0
            ),
        },
    )

    return _MODEL_ARTIFACT


def get_model_artifact():
    """
    Return the cached artifact, loading it if necessary.
    """

    global _MODEL_ARTIFACT

    if _MODEL_ARTIFACT is None:
        return load_model_artifact()

    return _MODEL_ARTIFACT



def build_features(records):
    """
    Convert transaction records into numerical ML features.
    """

    df = pd.DataFrame(records)

    if df.empty:
        return df, pd.DataFrame()

    df["amount"] = pd.to_numeric(
        df["amount"], errors="coerce"
    )

    df["transaction_time"] = pd.to_datetime(
        df["transaction_time"], errors="coerce"
    )

    df["transaction_hour"] = df["transaction_time"].dt.hour

    df["is_foreign"] = (
        df["country"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .ne("india")
        .astype(int)
    )

    df["is_failed"] = (
        df["status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("FAILED")
        .astype(int)
    )

    feature_columns = [
        "amount",
        "transaction_hour",
        "is_foreign",
        "is_failed",
    ]

    features = df[feature_columns].replace(
        [float("inf"), float("-inf")],
        float("nan"),
    )

    valid_rows = features.notna().all(axis=1)

    return (
        df.loc[valid_rows].copy(),
        features.loc[valid_rows].copy(),
    )


def detect_transaction_anomaly(transaction_id):
    """
    Load a previously trained model and assess a transaction.
    Does not train or retrain the model.
    """

    records = get_all()

    if not records:
        return {
            "error": "No transactions available",
            "transaction_id": transaction_id,
        }

    df, features = build_features(records)

    if transaction_id not in df["transaction_id"].values:
        return None


    if len(features) < MINIMUM_TRANSACTIONS:
        return {
            "transaction_id": transaction_id,
            "status": "INSUFFICIENT_DATA",
            "message": (
                    f"At least {MINIMUM_TRANSACTIONS} valid "
                    "transactions are required."
        ),
            "available_transactions": len(features),
    }


    if not MODEL_PATH.exists():
        return {
            "error": (
                "Trained anomaly model not found. "
                "Run scripts/train_anomaly_model.py first."
            ),
            "transaction_id": transaction_id,
        }

    # Load the model artifact saved by the training script.
    artifact = get_model_artifact()

    if artifact is None:
        return {
            "error": (
                "Trained anomaly model not found. "
                "Run scripts/train_anomaly_model.py first."
            ),
            "transaction_id": transaction_id,
    }

    model = artifact["model"]
    feature_columns = artifact["feature_columns"]

    # Find the target transaction's position in the valid dataset.
    matching_position = (
        df["transaction_id"].reset_index(drop=True)
        == transaction_id
    ).to_numpy().nonzero()[0][0]

    target_features = features.iloc[
    [matching_position]
    ][feature_columns]

    prediction = int(model.predict(target_features)[0])
    decision_score = float(
        model.decision_function(target_features)[0]
    )

    logger.info(
        "Transaction anomaly assessment completed",
        extra={
            "transaction_id": transaction_id,
            "model_version": artifact.get(
                "model_version", "unknown"
            ),
        },
    )

    return {
        "transaction_id": transaction_id,
        "anomaly_status": (
            "ANOMALY" if prediction == -1 else "NORMAL"
        ),
        "anomaly_score": round(-decision_score, 4),
        "features": {
            "amount": float(target_features.iloc[0]["amount"]),
            "transaction_hour": int(
                target_features.iloc[0]["transaction_hour"]
            ),
            "is_foreign": int(
                target_features.iloc[0]["is_foreign"]
            ),
            "is_failed": int(
                target_features.iloc[0]["is_failed"]
            ),
        },
        "model": artifact["model_name"],
        "model_version": artifact["model_version"],
        "model_trained_at": artifact["trained_at"],
        "training_rows": artifact["training_rows"],
        "model_configuration": {
            "n_estimators": artifact["n_estimators"],
            "contamination": artifact["contamination"],
        },
    }
