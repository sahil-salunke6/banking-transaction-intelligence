from fastapi import APIRouter, Depends, HTTPException, status
from app.security import require_api_key

from app.services.transaction_service import (
    get_transactions,
    create_transaction as create_transaction_service,
    get_transaction_by_id,
)
from app.schema.transaction_schema import TransactionCreate
from fastapi import Query


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    dependencies=[Depends(require_api_key)],
)


# --- Get all transactions ---
@router.get("/")
def get_transaction(limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    return get_transactions(
        limit=limit,
        offset=offset,
    )


# -- Get transaction by id ---
@router.get("/{transaction_id}")
def get_transaction(transaction_id: str):
    transaction = get_transaction_by_id(transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found"
        )

    return transaction


# --- Create a new transaction ---
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: TransactionCreate):
    try:
        saved_transaction = create_transaction_service(transaction)

        return {
            "message": "Transaction created successfully",
            "transaction": saved_transaction
        }

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )
