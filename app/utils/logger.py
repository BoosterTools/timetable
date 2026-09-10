from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.utils.paths import get_log_path

_LOGGER_NAME = "timetable_maker"
_configured = False


def get_logger() -> logging.Logger:
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if not _configured:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        try:
            file_handler = RotatingFileHandler(
                get_log_path(), maxBytes=1_000_000, backupCount=3, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            pass
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        _configured = True
    return logger
