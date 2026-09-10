"""
Persistence for the current timetable.

Mirrors the same crash-safety pattern used elsewhere: every save writes to
a temp file, flushes it to disk, rolls the previous version to a rolling
``.bak``, and only then atomically replaces the real file — so a crash or
power loss mid-save can never leave a half-written, corrupted file behind.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from app.models.timetable import Timetable
from app.utils.logger import get_logger
from app.utils.paths import get_backup_path, get_current_timetable_path

logger = get_logger()


class InvalidTimetableFileError(Exception):
    """Raised with a friendly, user-facing message when a timetable file
    can't be parsed (not valid JSON / wrong shape)."""


def _atomic_write(path: Path, payload: dict, backup_path: Optional[Path] = None) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())

        if backup_path is not None and path.exists():
            try:
                shutil.copyfile(path, backup_path)
            except OSError as exc:
                logger.warning("Could not update rolling backup: %s", type(exc).__name__)

        os.replace(tmp_path, path)
        return True
    except OSError as exc:
        logger.error("Failed to save %s: %s", path.name, type(exc).__name__)
        return False


def _read_json_file(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        logger.error("Could not read %s: %s", path.name, type(exc).__name__)
        return None


class TimetableStorage:
    """Handles the single 'current timetable' that autosaves to the app
    data directory — this is what makes the app remember your work
    between launches without you ever pressing Save."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or get_current_timetable_path()
        self.backup_path = self.path.with_suffix(self.path.suffix + ".bak")

    def load(self) -> Timetable:
        payload = _read_json_file(self.path)
        if payload is None and self.path.exists():
            logger.warning("Primary timetable file is unreadable; trying rolling backup")
        if payload is None:
            payload = _read_json_file(self.backup_path)
        if payload is None:
            return Timetable.new_default()
        try:
            return Timetable.from_dict(payload)
        except Exception:  # pragma: no cover - defensive
            logger.error("Could not parse timetable data; starting from a fresh default")
            return Timetable.new_default()

    def save(self, timetable: Timetable) -> bool:
        return _atomic_write(self.path, timetable.to_dict(), backup_path=self.backup_path)


# ------------------------------------------------------------------ #
# Save As / Open — arbitrary user-chosen file paths
# ------------------------------------------------------------------ #
def save_to_path(timetable: Timetable, path: Path) -> bool:
    return _atomic_write(Path(path), timetable.to_dict(), backup_path=None)


def load_from_path(path: Path) -> Timetable:
    path = Path(path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except json.JSONDecodeError as exc:
        raise InvalidTimetableFileError(
            f"This file isn't valid JSON (line {exc.lineno}, column {exc.colno}): {exc.msg}"
        ) from exc
    except OSError as exc:
        raise InvalidTimetableFileError(f"Could not open the file: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise InvalidTimetableFileError("This file doesn't look like valid UTF-8 text JSON.") from exc

    if not isinstance(payload, dict) or "days" not in payload or "periods" not in payload:
        raise InvalidTimetableFileError("This doesn't look like a Timetable Maker file.")

    return Timetable.from_dict(payload)
