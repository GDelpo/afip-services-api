"""Centralized logging configuration — JSON in prod, text in dev."""

import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

try:
    from logtail import LogtailHandler  # type: ignore
except ImportError:  # logtail is optional
    LogtailHandler = None  # type: ignore

from app.config import settings


class JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter compatible with Logtail/Datadog/CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "pid": record.process,
            "file": f"{record.filename}:{record.lineno}",
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        reserved = set(vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys())
        for k, v in record.__dict__.items():
            if k not in reserved and k not in payload:
                try:
                    json.dumps(v)
                    payload[k] = v
                except (TypeError, ValueError):
                    payload[k] = str(v)
        return json.dumps(payload, ensure_ascii=False)


def _text_formatter() -> logging.Formatter:
    return logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


_configured = False


def configure_logging() -> None:
    """Configure the root logger once. Safe to call multiple times."""
    global _configured
    if _configured:
        return

    log_dir = Path(settings.log_dir_path)
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter: logging.Formatter = (
        JsonFormatter() if settings.log_format == "json" else _text_formatter()
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    root_logger.addHandler(console_handler)

    process_handler = RotatingFileHandler(
        filename=log_dir / "process.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    process_handler.setFormatter(formatter)
    process_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    process_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    root_logger.addHandler(process_handler)

    error_handler = RotatingFileHandler(
        filename=log_dir / "error.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    if settings.logtail_token and LogtailHandler is not None:
        try:
            lt_handler = LogtailHandler(source_token=settings.logtail_token)
            lt_handler.setFormatter(formatter)
            lt_handler.setLevel(
                logging.DEBUG if settings.debug else logging.INFO
            )
            root_logger.addHandler(lt_handler)
        except Exception as exc:  # pragma: no cover
            root_logger.warning("Could not initialize LogtailHandler: %s", exc)

    _configured = True
    root_logger.debug(
        "Logging configured (format=%s, debug=%s, pid=%s)",
        settings.log_format,
        settings.debug,
        os.getpid(),
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger by name. Call `configure_logging()` during app startup."""
    return logging.getLogger(name)
