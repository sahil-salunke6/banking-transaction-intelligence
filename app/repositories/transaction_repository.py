
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.transaction import Transaction


def transaction_to_dict(record):
    """Convert a database transaction into a Python dictionary."""
    return {
        "transaction_id": record.transaction_id,
        "customer_id": record.customer_id,
        "amount": record.amount,
        "merchant": record.merchant,
        "merchant_category": record.merchant_category,
        "status": record.status,
        "channel": record.channel,
        "country": record.country,
        "transaction_time": (
            record.transaction_time.isoformat()
            if record.transaction_time is not None
            else None
        ),
    }



def get_all(limit: int = 100, offset: int = 0):
    """Retrieve a paginated list of transactions from the database."""
    with SessionLocal() as db:
        records = (
            db.query(Transaction)
            .order_by(Transaction.transaction_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            transaction_to_dict(record)
            for record in records
        ]


def get_by_id(transaction_id):
    """Retrieve one transaction by its primary key."""
    with SessionLocal() as db:
        record = db.get(Transaction, transaction_id)

        if record is None:
            return None

        return transaction_to_dict(record)


def save(transaction_data):
    """Insert a transaction into the database."""
    with SessionLocal() as db:
        record = Transaction(**transaction_data)

        db.add(record)

        try:
            db.commit()
            db.refresh(record)

        except IntegrityError as error:
            db.rollback()
            raise ValueError(
                "Transaction ID already exists"
            ) from error

        return transaction_to_dict(record)
