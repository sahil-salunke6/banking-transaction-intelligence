
from app.services.risk_service import assess_transaction_risk
from app.services.anomaly_service import detect_transaction_anomaly


def get_transaction_intelligence(transaction_id):
    """
    Combine rule-based risk scoring and ML anomaly detection.
    """

    risk_assessment = assess_transaction_risk(transaction_id)

    # The transaction must exist before we assess it.
    if risk_assessment is None:
        return None

    anomaly_assessment = detect_transaction_anomaly(
        transaction_id
    )

    # A missing transaction should not produce a partial assessment.
    if anomaly_assessment is None:
        return None

    return {
        "transaction_id": transaction_id,
        "risk_assessment": risk_assessment,
        "anomaly_assessment": anomaly_assessment,
    }
