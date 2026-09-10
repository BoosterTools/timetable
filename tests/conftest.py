from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Must happen BEFORE any `app.*` module is imported — several modules
# (e.g. the logger) resolve their file paths at import time, earlier than
# any fixture ever runs, so this guarantees tests never touch the real
# user app-data directory.
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="timetablemaker-test-")
os.environ["TIMETABLE_DATA_DIR"] = _TEST_DATA_DIR

import pytest

from app.models.timetable import Timetable
from app.services.storage import TimetableStorage


@pytest.fixture
def storage_path(tmp_path):
    return tmp_path / "timetable.json"


@pytest.fixture
def storage(storage_path):
    return TimetableStorage(storage_path)


@pytest.fixture
def blank_timetable():
    return Timetable.new_default()
