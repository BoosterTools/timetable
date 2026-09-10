from __future__ import annotations

from app.models.timetable import Entry, Timetable
from app.services.storage import InvalidTimetableFileError, load_from_path, save_to_path


def test_save_then_load_round_trip(storage, blank_timetable):
    blank_timetable.meta.title_line1 = "Round Trip Test"
    assert storage.save(blank_timetable) is True

    loaded = storage.load()
    assert loaded.meta.title_line1 == "Round Trip Test"
    assert len(loaded.days) == 5
    assert len(loaded.periods) == 7


def test_save_creates_rolling_backup_of_previous_version(storage, blank_timetable):
    blank_timetable.meta.title_line1 = "version one"
    storage.save(blank_timetable)

    blank_timetable.meta.title_line1 = "version two"
    storage.save(blank_timetable)

    assert storage.backup_path.exists()
    from app.services.storage import _read_json_file

    backup_data = _read_json_file(storage.backup_path)
    assert backup_data["meta"]["title_line1"] == "version one"

    current = storage.load()
    assert current.meta.title_line1 == "version two"


def test_load_falls_back_to_backup_when_primary_is_corrupt(storage, blank_timetable):
    blank_timetable.meta.title_line1 = "good data"
    storage.save(blank_timetable)
    blank_timetable.meta.title_line1 = "newer good data"
    storage.save(blank_timetable)

    storage.path.write_text("{not valid json!!", encoding="utf-8")

    loaded = storage.load()
    assert loaded.meta.title_line1 == "good data"


def test_load_returns_default_grid_when_no_file_exists(storage):
    loaded = storage.load()
    assert len(loaded.days) == 5
    assert len(loaded.periods) == 7
    assert loaded.entries == []


def test_entries_persist_across_reinstantiation(storage_path, blank_timetable):
    from app.services.storage import TimetableStorage

    s1 = TimetableStorage(storage_path)
    tt = blank_timetable
    tt.entries.append(
        Entry(id=1, day_id=tt.days[0].id, period_id=tt.periods[0].id, subject="Persisted Class")
    )
    s1.save(tt)

    s2 = TimetableStorage(storage_path)
    loaded = s2.load()
    assert len(loaded.entries) == 1
    assert loaded.entries[0].subject == "Persisted Class"


def test_save_as_and_open_arbitrary_path(tmp_path, blank_timetable):
    path = tmp_path / "my_export.ttm.json"
    blank_timetable.meta.title_line1 = "Exported Copy"
    assert save_to_path(blank_timetable, path) is True

    loaded = load_from_path(path)
    assert loaded.meta.title_line1 == "Exported Copy"


def test_load_from_path_rejects_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ not json", encoding="utf-8")
    try:
        load_from_path(path)
        assert False, "should have raised"
    except InvalidTimetableFileError:
        pass


def test_load_from_path_rejects_wrong_shape(tmp_path):
    import json

    path = tmp_path / "wrong.json"
    path.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
    try:
        load_from_path(path)
        assert False, "should have raised"
    except InvalidTimetableFileError:
        pass
