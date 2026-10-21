
import sys
from pathlib import Path

# Make the project root available for Python imports.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
)

from app.repositories.transaction_repository import get_all
from app.services.anomaly_service import build_features


MODEL_PATH = PROJECT_ROOT / "artifacts" / "isolation_forest.joblib"

LABELS_PATH = (
    PROJECT_ROOT / "data" / "anomaly_evaluation_labels.csv"
)


def evaluate_against_labels(
    evaluation_df: pd.DataFrame,
) -> None:
    """Evaluate predictions against independently reviewed labels."""

    if not LABELS_PATH.exists():
        print(
            "\nGround-truth labels not found. "
            "Precision, recall, and F1-score cannot be calculated."
        )
        print(f"Expected labels file: {LABELS_PATH}")
        return

    labels_df = pd.read_csv(LABELS_PATH)

    required_label_columns = {
        "transaction_id",
        "is_anomaly",
    }

    if not required_label_columns.issubset(labels_df.columns):
        raise ValueError(
            "Labels CSV must contain transaction_id and is_anomaly."
        )

    if labels_df["transaction_id"].isna().any():
        raise ValueError(
            "Ground-truth labels contain missing transaction IDs."
        )

    if labels_df["transaction_id"].duplicated().any():
        raise ValueError(
            "Duplicate transaction IDs in labels CSV."
        )

    # Blank labels remain unevaluated until independently reviewed.
    labels_df = labels_df.dropna(
        subset=["is_anomaly"]
    ).copy()

    if labels_df.empty:
        print(
            "\nNo reviewed ground-truth labels found. "
            "Add 0 or 1 labels after independent review."
        )
        return

    labels_df["is_anomaly"] = pd.to_numeric(
        labels_df["is_anomaly"],
        errors="raise",
    )

    if not labels_df["is_anomaly"].isin([0, 1]).all():
        raise ValueError(
            "is_anomaly must contain only 0 or 1."
        )

    evaluation = evaluation_df[
        ["transaction_id", "prediction"]
    ].merge(
        labels_df[
            ["transaction_id", "is_anomaly"]
        ],
        on="transaction_id",
        how="inner",
        validate="one_to_one",
    )

    if evaluation.empty:
        print(
            "\nNo reviewed transaction IDs matched "
            "the current evaluation data."
        )
        return

    if len(evaluation) < len(labels_df):
        print(
            "Warning: some labeled transactions are not present "
            "in the current evaluation data."
        )

    y_true = evaluation["is_anomaly"].astype(int)

    # Isolation Forest predictions:
    # -1 = anomaly -> 1
    #  1 = inlier  -> 0
    y_pred = (
        evaluation["prediction"] == -1
    ).astype(int)

    print(
        "\n--- Evaluation on Independently Labeled Transactions ---"
    )
    print(
        f"Labeled transactions evaluated: {len(evaluation)}"
    )

    print(
        "\nConfusion matrix "
        "(rows=true, columns=predicted):"
    )
    print("Labels: 0 = inlier, 1 = anomaly")

    print(
        confusion_matrix(
            y_true,
            y_pred,
            labels=[0, 1],
        )
    )

    print("\nClassification report:")

    print(
        classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=["Inlier", "Anomaly"],
            zero_division=0,
        )
    )


def main() -> None:
    """Evaluate the saved Isolation Forest model."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {MODEL_PATH}. "
            "Train the model first."
        )

    artifact = joblib.load(MODEL_PATH)

    required_artifact_keys = {
        "model",
        "feature_columns",
    }

    missing_keys = required_artifact_keys - artifact.keys()

    if missing_keys:
        raise ValueError(
            f"Model artifact is missing keys: {sorted(missing_keys)}"
        )

    model = artifact["model"]
    feature_columns = artifact["feature_columns"]

    records = get_all(
        limit=100000,
        offset=0,
    )

    if not records:
        print("No transactions found in the database.")
        return

    df = pd.DataFrame(records)

    required_columns = [
        "transaction_id",
        "amount",
        "country",
        "status",
        "transaction_time",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Transaction data is missing columns: {missing_columns}"
        )

    # Use the same feature pipeline as application inference.
    # Invalid rows, including transactions with missing timestamps,
    # are excluded by the shared build_features() implementation.
    evaluation_df, features = build_features(records)

    # Preserve the feature order expected by the trained model.
    missing_features = [
        column
        for column in feature_columns
        if column not in features.columns
    ]

    if missing_features:
        raise ValueError(
            f"Required model features are missing: {missing_features}"
        )

    features = features[feature_columns]

    if features.empty:
        print(
            "No transactions have complete, valid model features."
        )
        return

    # Predict only on rows accepted by the shared feature pipeline.
    predictions = model.predict(features)
    scores = -model.decision_function(features)

    evaluation_df["prediction"] = predictions
    evaluation_df["anomaly_score"] = scores

    total = len(evaluation_df)
    anomaly_count = int((predictions == -1).sum())
    inlier_count = int((predictions == 1).sum())
    anomaly_percentage = anomaly_count / total * 100

    print("\n--- Isolation Forest Evaluation ---")
    print(
        f"Model version: "
        f"{artifact.get('model_version', 'unknown')}"
    )
    print(
        f"Training rows: "
        f"{artifact.get('training_rows', 'unknown')}"
    )
    print(f"Transactions evaluated: {total}")
    print(f"Anomalies detected: {anomaly_count}")
    print(f"Inliers detected: {inlier_count}")
    print(
        f"Anomaly percentage: {anomaly_percentage:.2f}%"
    )

    print("\n--- Most Anomalous Transactions ---")

    anomalous_transactions = evaluation_df.loc[
        evaluation_df["prediction"] == -1,
        [
            "transaction_id",
            "amount",
            "prediction",
            "anomaly_score",
        ],
    ].sort_values(
        "anomaly_score",
        ascending=False
    )

    if anomalous_transactions.empty:
        print("No anomalies detected.")
    else:
        print(
            anomalous_transactions.to_string(
                index=False
            )
        )

    # Precision, recall, and F1 require independent ground-truth labels.
    evaluate_against_labels(evaluation_df)


if __name__ == "__main__":
    main()
