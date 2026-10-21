
from sqlalchemy import Column, Float, String, DateTime

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(
        String,
        primary_key=True,
        index=True
    )

    customer_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    merchant = Column(String, nullable=False)
    merchant_category = Column(String, nullable=False)
    status = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    country = Column(String, nullable=False)

    transaction_time = Column(DateTime, nullable=True)