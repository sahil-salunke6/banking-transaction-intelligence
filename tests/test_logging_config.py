
import json
import logging

from app.logging_config import JSONFormatter


def test_json_formatter_outputs_structured_log():
    record = logging.LogRecord(
        name="app.services.anomaly_service",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Anomaly model loaded",
        args=(),
        exc_info=None,
    )

    record.model_version = "1.0.0+test"
    record.training_rows = 100

    output = JSONFormatter().format(record)
    log_entry = json.loads(output)

    assert log_entry["level"] == "INFO"
    assert log_entry["logger"] == (
        "app.services.anomaly_service"
    )
    assert log_entry["message"] == "Anomaly model loaded"
    assert log_entry["model_version"] == "1.0.0+test"
    assert log_entry["training_rows"] == 100
    assert "timestamp" in log_entry


def test_json_formatter_includes_exception_details():
    try:
        raise ValueError("Test exception")
    except ValueError:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname=__file__,
            lineno=30,
            msg="Operation failed",
            args=(),
            exc_info=__import__("sys").exc_info(),
        )

    output = JSONFormatter().format(record)
    log_entry = json.loads(output)

    assert log_entry["level"] == "ERROR"
    assert log_entry["message"] == "Operation failed"
    assert "exception" in log_entry
    assert "ValueError" in log_entry["exception"]
