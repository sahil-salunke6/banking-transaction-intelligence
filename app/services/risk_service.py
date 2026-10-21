
from app.services.transaction_service import get_transaction_by_id


def calculate_risk(transaction):
    """
    Calculate a rule-based risk score for one transaction.
    """

    risk_score = 0
    risk_factors = []

    # Rule 1: High transaction amount
    if transaction["amount"] > 50000:
        risk_score += 30
        risk_factors.append("High transaction amount")

    # Rule 2: Transaction outside India
    country = (transaction.get("country") or "").strip().lower()

    if country and country != "india":
        risk_score += 25
        risk_factors.append("Foreign transaction")

    # Rule 3: Transaction between midnight and 4:59 AM
    transaction_time = transaction.get("transaction_time")

    if transaction_time:
        from datetime import datetime

        if isinstance(transaction_time, str):
            transaction_time = datetime.fromisoformat(
                transaction_time
            )

        if 0 <= transaction_time.hour < 5:
            risk_score += 15
            risk_factors.append("Unusual transaction hour")

    # Rule 4: Failed transaction
    status = (transaction.get("status") or "").strip().upper()

    if status == "FAILED":
        risk_score += 20
        risk_factors.append("Failed transaction")

    # Keep the score within 0–100
    risk_score = min(risk_score, 100)

    # Convert numeric score into a risk category
    if risk_score >= 60:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "transaction_id": transaction["transaction_id"],
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
    }


def assess_transaction_risk(transaction_id):
    """
    Retrieve a transaction and calculate its risk.
    """

    transaction = get_transaction_by_id(transaction_id)

    if transaction is None:
        return None

    return calculate_risk(transaction)
