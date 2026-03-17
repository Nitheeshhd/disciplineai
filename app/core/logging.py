from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from app.core.context import request_id_ctx


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter for ingestion by cloud log pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get("-"),
        }
        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(level: str, env: str = "development") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())
    
    handler = logging.StreamHandler()
    
    if env.lower() == "development":
        # Human-readable colors and format for development
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        
        # Enable SQL echoing for SQLAlchemy in dev if needed
        if level.upper() == "DEBUG":
            logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        handler.setFormatter(JsonFormatter())
        
    root.addHandler(handler)
