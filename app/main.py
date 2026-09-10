"""
Entry point for Timetable Maker.

Run with:  python -m app.main
Or via the packaged .exe built by build.py / PyInstaller.
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config import APP_NAME, ORG_NAME
from app.services.storage import TimetableStorage
from app.ui.main_window import MainWindow
from app.ui.style import LIGHT_STYLESHEET
from app.utils.logger import get_logger


def main() -> int:
    logger = get_logger()
    logger.info("Starting application")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setStyleSheet(LIGHT_STYLESHEET)  # always light — no dark mode anywhere in this app

    storage = TimetableStorage()
    window = MainWindow(storage)
    window.show()

    exit_code = app.exec()
    logger.info("Application exiting")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
