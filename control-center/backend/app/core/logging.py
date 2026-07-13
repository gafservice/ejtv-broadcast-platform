"""Configuración centralizada de logging."""

import logging
import logging.config
from pathlib import Path

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configura salida por consola y archivo."""

    log_directory = Path(settings.log_directory).resolve()
    log_directory.mkdir(parents=True, exist_ok=True)

    log_file = log_directory / "control-center-backend.log"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s | %(levelname)s | "
                    "%(name)s | %(message)s"
                ),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": settings.log_level.upper(),
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": str(log_file),
                "maxBytes": 5_000_000,
                "backupCount": 5,
                "encoding": "utf-8",
                "level": settings.log_level.upper(),
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": settings.log_level.upper(),
        },
    }

    logging.config.dictConfig(logging_config)
