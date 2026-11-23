import json
import logging
import sys
from typing import Any
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

class RedactingJsonFormatter(logging.Formatter):
    """Structured JSON formatter with request ID and privacy redaction."""
    REDACTED_KEYS = {"transcript", "text", "words", "raw_response", "audio_bytes", "quote"}

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }

        # Redact any sensitive fields attached to extra
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            for k, v in record.extra.items():
                if k in self.REDACTED_KEYS:
                    log_obj[k] = "[REDACTED]"
                else:
                    log_obj[k] = v

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

def setup_logging(level: str = "INFO"):
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    for h in logger.handlers[:]:
        logger.removeHandler(h)
        
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(RedactingJsonFormatter())
    logger.addHandler(handler)
