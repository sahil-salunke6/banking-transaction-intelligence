
from sqlalchemy import func, case

from app.database import SessionLocal
from app.models.transaction import Transaction




def get_summary():
    """Return transaction summary using a single SQL query."""

    with SessionLocal() as db:
        result = db.query(
            func.count(
                Transaction.transaction_id
            ).label("total_transactions"),

            func.coalesce(
                func.sum(Transaction.amount), 0
            ).label("total_amount"),

            func.coalesce(
                func.sum(
                    case(
                        (Transaction.status == "SUCCESS", 1),
                        else_=0,
                    )
                ),
                0,
            ).label("successful_transactions"),

            func.coalesce(
                func.sum(
                    case(
                        (Transaction.status == "FAILED", 1),
                        else_=0,
                    )
                ),
                0,
            ).label("failed_transactions"),
        ).one()

        return {
            "total_transactions": result.total_transactions,
            "total_amount": float(result.total_amount or 0),
            "successful_transactions": result.successful_transactions,
            "failed_transactions": result.failed_transactions,
        }


def get_customer_summary():
    with SessionLocal() as db:
        rows = db.query(
            Transaction.customer_id,
            func.count(Transaction.transaction_id).label(
                "transaction_count"
            ),
            func.sum(Transaction.amount).label(
                "total_amount"
            ),
            func.avg(Transaction.amount).label(
                "average_amount"
            ),
        ).group_by(
            Transaction.customer_id
        ).order_by(
            func.sum(Transaction.amount).desc()
        ).all()

        return [
            {
                "customer_id": row.customer_id,
                "transaction_count": row.transaction_count,
                "total_amount": float(row.total_amount or 0),
                "average_amount": float(row.average_amount or 0),
            }
            for row in rows
        ]



def get_hourly_summary():
    """Count transactions by hour directly in SQLite."""

    with SessionLocal() as db:
        rows = db.query(
            func.strftime(
                "%H",
                Transaction.transaction_time,
            ).label("transaction_hour"),
            func.count(
                Transaction.transaction_id
            ).label("transaction_count"),
        ).filter(
            Transaction.transaction_time.isnot(None),
            func.strftime(
                "%H",
                Transaction.transaction_time,
            ).isnot(None),
        ).group_by(
            func.strftime(
                "%H",
                Transaction.transaction_time,
            )
        ).order_by(
            func.strftime(
                "%H",
                Transaction.transaction_time,
            )
        ).all()

        return [
            {
                "transaction_hour": int(row.transaction_hour),
                "transaction_count": row.transaction_count,
            }
            for row in rows
        ]
