from fastapi import APIRouter, Depends
from app.security import require_api_key

from app.repositories.analytics_repository import (
    get_summary,
    get_customer_summary,
)
from app.services.analytics_service import get_hourly_summary


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/summary")
def transaction_summary():
    return get_summary()


@router.get("/customers")
def customer_summary():
    return get_customer_summary()


@router.get("/hourly")
def hourly_summary():
    return get_hourly_summary()
