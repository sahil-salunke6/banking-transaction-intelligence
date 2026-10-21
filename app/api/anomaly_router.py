from fastapi import APIRouter, Depends, HTTPException
from app.security import require_api_key

from app.services.anomaly_service import (
    detect_transaction_anomaly,
)


router = APIRouter(
    prefix="/anomaly",
    tags=["Anomaly Detection"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/{transaction_id}")
def get_transaction_anomaly(transaction_id: str):
    result = detect_transaction_anomaly(transaction_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found",
        )

    if "error" in result:
        raise HTTPException(
            status_code=503,
            detail=result["error"],
        )

    return result
