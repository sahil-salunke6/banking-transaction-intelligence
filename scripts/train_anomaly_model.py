
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import joblib
from sklearn.ensemble import IsolationForest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.repositories.transaction_repository import get_all
from app.services.anomaly_service import build_features


ARTIFACT_DIR = PROJECT_ROOT / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "isolation_forest.joblib"

MINIMUM_TRANSACTIONS = 5

FEATURE_COLUMNS = [
    "amount",
    "transaction_hour",
    "is_foreign",
    "is_failed",
]


def train_model():
    print("Loading transactions from the database...")

    records = get_all()

    if not records:
        raise SystemExit(
            "Training stopped: no transactions are available."
        )

    df, features = build_features(records)

    if len(features) < MINIMUM_TRANSACTIONS:
        raise SystemExit(
            f"Training stopped: need at least "
            f"{MINIMUM_TRANSACTIONS} valid transactions; "
            f"found {len(features)}."
        )

    print(f"Valid training transactions: {len(features)}")

    trained_at = datetime.now(timezone.utc)
    model_version = trained_at.strftime(
        "1.0.0+%Y%m%dT%H%M%SZ"
    )

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
    )

    print("Training Isolation Forest...")
    model.fit(features[FEATURE_COLUMNS])

    artifact = {
        "model": model,
        "model_name": "IsolationForest",
        "model_version": model_version,
        "feature_columns": FEATURE_COLUMNS,
        "training_rows": len(features),
        "trained_at": trained_at.isoformat(),
        "contamination": 0.1,
        "n_estimators": 100,
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        # Create the temporary file in the same directory
        # so replacement happens on the same filesystem.
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".joblib.tmp",
            prefix="isolation_forest_",
            dir=ARTIFACT_DIR,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        joblib.dump(artifact, temporary_path)

        # Replace the active artifact only after saving succeeds.
        os.replace(temporary_path, MODEL_PATH)
        temporary_path = None

    finally:
        # Remove the temporary file if saving or replacement fails.
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()

    print("Training completed successfully.")
    print(f"Model version: {model_version}")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Training rows: {len(features)}")
    print(f"Features: {FEATURE_COLUMNS}")
    print(f"Trained at: {trained_at.isoformat()}")


if __name__ == "__main__":
    train_model()
