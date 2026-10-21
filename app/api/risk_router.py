from fastapi import APIRouter, Depends, HTTPException
from app.security import require_api_key

from app.services.risk_service import assess_transaction_risk


router = APIRouter(
    prefix="/risk",
    tags=["Risk Assessment"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/{transaction_id}")
def get_transaction_risk(transaction_id: str):
    result = assess_transaction_risk(transaction_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found",
        )

    return result
