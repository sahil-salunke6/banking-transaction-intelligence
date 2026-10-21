
from pathlib import Path
import sys

import pandas as pd

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models.transaction import Transaction


CSV_FILE = PROJECT_ROOT / "data" / "ambi_transactions.csv"

REQUIRED_COLUMNS = [
    "transaction_id",
    "customer_id",
    "amount",
    "merchant",
    "merchant_category",
    "status",
    "channel",
    "country",
]


def load_and_clean_data():
    df = pd.read_csv(CSV_FILE)

    # Ensure all required columns exist.
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"CSV is missing columns: {sorted(missing_columns)}"
        )

    # Convert empty or whitespace-only strings into missing values.
    for column in REQUIRED_COLUMNS:
        if df[column].dtype == "object":
            df[column] = df[column].replace(
                r"^\s*$",
                pd.NA,
                regex=True
            )

    # Convert amount to a numeric value.
    # Invalid values such as "abc" become NaN.
    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    # Remove rows with missing required values.
    df = df.dropna(subset=REQUIRED_COLUMNS)

    # A banking transaction must have a positive amount.
    df = df[df["amount"] > 0]

    # Standardize text values.
    text_columns = [
        "transaction_id",
        "customer_id",
        "merchant",
        "merchant_category",
        "status",
        "channel",
    ]

    for column in text_columns:
        df[column] = df[column].str.strip()

    df["transaction_id"] = df["transaction_id"].str.upper()
    df["customer_id"] = df["customer_id"].str.upper()
    df["merchant_category"] = df["merchant_category"].str.upper()
    df["status"] = df["status"].str.upper()
    df["channel"] = df["channel"].str.upper()
    df["country"] = df["country"].str.strip().str.title()
    df["transaction_time"] = pd.to_datetime(df["transaction_time"],errors="coerce")

    # Remove records that became empty after trimming.
    df = df.replace(r"^\s*$", pd.NA, regex=True)
    df = df.dropna(subset=REQUIRED_COLUMNS)

    # Keep the first valid occurrence of each transaction ID.
    df = df.drop_duplicates(
        subset=["transaction_id"],
        keep="first"
    )

    # Select only the columns represented in our SQL model.
    return df[REQUIRED_COLUMNS]


def import_into_database(df):
    imported = 0
    already_exists = 0

    with SessionLocal() as db:
        for record in df.to_dict(orient="records"):
            transaction_time = record["transaction_time"]

            if pd.isna(transaction_time):
                record["transaction_time"] = None
            else:
                record["transaction_time"] = (transaction_time.to_pydatetime())

            transaction_id = record["transaction_id"]

            existing = db.get(Transaction, transaction_id)

            if existing is not None:
                already_exists += 1
                continue

            db.add(Transaction(**record))
            imported += 1

            # Persist all new records in one database transaction.
            db.commit()

    return imported, already_exists


def main():
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"CSV file not found: {CSV_FILE}"
        )

    original_df = pd.read_csv(CSV_FILE)
    cleaned_df = load_and_clean_data()

    print(f"Source rows: {len(original_df)}")
    print(f"Valid unique rows: {len(cleaned_df)}")
    print(f"Rows removed during cleaning: "
          f"{len(original_df) - len(cleaned_df)}")

    imported, already_exists = import_into_database(cleaned_df)

    print(f"New transactions imported: {imported}")
    print(f"Transactions already in database: {already_exists}")


if __name__ == "__main__":
    main()
