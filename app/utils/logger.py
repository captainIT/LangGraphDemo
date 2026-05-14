import json
import logging
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "trace_id"):
            payload["trace_id"] = getattr(record, "trace_id")
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def setup_logging(log_level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
