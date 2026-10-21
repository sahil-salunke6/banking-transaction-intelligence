
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models.transaction import Transaction

CSV_FILE = (
    PROJECT_ROOT
    / "data"
    / "ambi_transactions.csv"
)


def backfill_timestamps():
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"CSV file not found: {CSV_FILE}. "
            "Update CSV_FILE to the actual source file."
        )

    # Read the source data.
    df = pd.read_csv(CSV_FILE)

    required_columns = {
        "transaction_id",
        "transaction_time",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"CSV is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # Normalize IDs so whitespace/capitalization do not
    # prevent matching.
    df["transaction_id"] = (
        df["transaction_id"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # Parse timestamps. Invalid values become NaT.
    df["transaction_time"] = pd.to_datetime(
        df["transaction_time"],
        errors="coerce"
    )

    # Ignore records without a usable ID or timestamp.
    df = df.dropna(
        subset=["transaction_id", "transaction_time"]
    )

    # Keep the first valid timestamp for each transaction ID.
    df = df.drop_duplicates(
        subset=["transaction_id"],
        keep="first"
    )

    updated = 0
    already_has_timestamp = 0
    not_found = 0

    with SessionLocal() as db:
        for row in df.to_dict(orient="records"):
            transaction_id = row["transaction_id"]

            # Convert Pandas Timestamp to Python datetime.
            transaction_time = (
                row["transaction_time"].to_pydatetime()
            )

            # Match an existing database record.
            transaction = db.get(
                Transaction,
                transaction_id
            )

            if transaction is None:
                not_found += 1
                continue

            # Never overwrite an existing timestamp.
            if transaction.transaction_time is not None:
                already_has_timestamp += 1
                continue

            transaction.transaction_time = transaction_time
            updated += 1

        # Save all timestamp updates together.
        db.commit()

    print("\nTimestamp backfill completed.")
    print(f"CSV records with valid timestamps: {len(df)}")
    print(f"Database records updated: {updated}")
    print(f"Records already having timestamps: {already_has_timestamp}")
    print(f"Transaction IDs not found in database: {not_found}")


if __name__ == "__main__":
    backfill_timestamps()
