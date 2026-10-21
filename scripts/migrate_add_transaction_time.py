
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_FILE = PROJECT_ROOT / "banking_transactions.db"

def migrate():
    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_FILE}"
        )

    with sqlite3.connect(DATABASE_FILE) as connection:
        columns = connection.execute(
            "PRAGMA table_info(transactions)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        if "transaction_time" in column_names:
            print("transaction_time already exists. No migration needed.")
            return

        connection.execute(
            "ALTER TABLE transactions "
            "ADD COLUMN transaction_time DATETIME"
        )

        print("Added transaction_time column successfully.")


if __name__ == "__main__":
    migrate()
