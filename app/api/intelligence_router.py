from fastapi import APIRouter, Depends, HTTPException
from app.security import require_api_key

from app.services.intelligence_service import (
    get_transaction_intelligence,
)


router = APIRouter(
    prefix="/intelligence",
    tags=["Transaction Intelligence"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/{transaction_id}")
def transaction_intelligence(transaction_id: str):
    result = get_transaction_intelligence(transaction_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found",
        )

    return result
