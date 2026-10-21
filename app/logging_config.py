
import json
import logging
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Format log records as JSON objects."""


    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in (
            "path",
            "method",
            "model_path",
            "model_version",
            "training_rows",
            "transaction_id",
        ):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info:
            log_entry["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_entry)


def configure_logging():
    """Configure structured application logging."""

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers on repeated configuration.
    if not any(
        getattr(handler, "_json_logging_handler", False)
        for handler in root_logger.handlers
    ):
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        handler._json_logging_handler = True
        root_logger.addHandler(handler)
