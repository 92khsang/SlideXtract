from __future__ import annotations

import logging
import logging.config
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"


def get_logging_config(log_level: str = "DEBUG", enable_file_logging: bool = False):
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        }
    }

    if enable_file_logging:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": str(LOG_FILE),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf8",
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
            }
        },
        "handlers": handlers,
        "loggers": {"": {"level": log_level, "handlers": list(handlers.keys())}},
    }


def setup_logging(log_level: str = "INFO", enable_file_logging: bool = False):
    logging.config.dictConfig(get_logging_config(log_level, enable_file_logging))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


setup_logging()
