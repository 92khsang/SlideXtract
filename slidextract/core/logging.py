from __future__ import annotations

import logging
import logging.config
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


def get_logging_config(log_level: str = "DEBUG"):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": str(LOG_FILE),
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {"": {"level": log_level, "handlers": ["console", "file"]}},
    }


def setup_logging(log_level: str = "INFO"):
    logging.config.dictConfig(get_logging_config(log_level))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


setup_logging()
