
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TransactionCreate(BaseModel):
    transaction_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    merchant: str = Field(min_length=1)
    merchant_category: str = Field(min_length=1)

    status: Literal["SUCCESS", "FAILED", "PENDING"]

    channel: str = Field(min_length=1)
    country: str = Field(min_length=1)

    transaction_time: datetime | None = None

    @field_validator(
        "transaction_id",
        "customer_id",
        "merchant",
        "merchant_category",
        "status",
        "channel",
        "country",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator(
        "transaction_id",
        "customer_id",
        "merchant_category",
        "status",
        "channel",
        mode="before",
    )
    @classmethod
    def uppercase_text(cls, value):
        if isinstance(value, str):
            return value.strip().upper()

        return value

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value):
        return value.title()
