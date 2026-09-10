from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "TimetableMaker"


def get_app_data_dir() -> Path:
    override = os.environ.get("TIMETABLE_DATA_DIR")
    if override:
        path = Path(override)
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home())
        path = Path(base) / APP_DIR_NAME
    else:
        path = Path.home() / f".{APP_DIR_NAME.lower()}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_current_timetable_path() -> Path:
    return get_app_data_dir() / "current_timetable.json"


def get_backup_path() -> Path:
    return get_app_data_dir() / "current_timetable.json.bak"


def get_log_path() -> Path:
    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


def get_logos_dir() -> Path:
    logos_dir = get_app_data_dir() / "logos"
    logos_dir.mkdir(parents=True, exist_ok=True)
    return logos_dir
