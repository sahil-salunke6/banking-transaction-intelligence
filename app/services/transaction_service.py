
from app.repositories.transaction_repository import (
    get_all,
    get_by_id,
    save,
)


def get_transactions(limit: int = 100, offset: int = 0):
    return get_all(
        limit=limit,
        offset=offset,
    )


def create_transaction(transaction):
    transaction_data = transaction.model_dump()

    existing = get_by_id(
        transaction_data["transaction_id"]
    )

    if existing is not None:
        raise ValueError("Transaction ID already exists")

    return save(transaction_data)


def get_transaction_by_id(transaction_id):
    return get_by_id(transaction_id)
