from __future__ import annotations

from app.models.timetable import Day, Entry, Period, Timetable, TimetableMeta


def test_new_default_has_five_days_and_seven_periods():
    tt = Timetable.new_default()
    assert len(tt.days) == 5
    assert len(tt.periods) == 7
    assert [d.name for d in tt.days] == ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    assert tt.periods[0].start_time == "9:00"
    assert tt.entries == []


def test_add_entry_and_get_entry(blank_timetable):
    tt = blank_timetable
    day = tt.days[0]
    period = tt.periods[0]
    entry = Entry(id=tt.next_entry_id(), day_id=day.id, period_id=period.id, subject="Math")
    tt.entries.append(entry)

    found = tt.get_entry(day.id, period.id)
    assert found is not None
    assert found.subject == "Math"

    missing = tt.get_entry(day.id, tt.periods[1].id)
    assert missing is None


def test_next_id_helpers_never_collide(blank_timetable):
    tt = blank_timetable
    e1_id = tt.next_entry_id()
    tt.entries.append(Entry(id=e1_id, day_id=tt.days[0].id, period_id=tt.periods[0].id, subject="A"))
    e2_id = tt.next_entry_id()
    assert e2_id != e1_id
    assert e2_id > e1_id


def test_to_dict_from_dict_round_trip(blank_timetable):
    tt = blank_timetable
    tt.meta.title_line1 = "Fall Semester"
    tt.meta.title_line2 = "Level 4"
    entry = Entry(
        id=tt.next_entry_id(),
        day_id=tt.days[0].id,
        period_id=tt.periods[0].id,
        subject="Translation into English I",
        hall="115",
        group="A.L. Hashm",
        section_label="4.TR",
        section_hall="106",
        color="#8E44AD",
    )
    tt.entries.append(entry)

    data = tt.to_dict()
    restored = Timetable.from_dict(data)

    assert restored.meta.title_line1 == "Fall Semester"
    assert restored.meta.title_line2 == "Level 4"
    assert len(restored.entries) == 1
    restored_entry = restored.entries[0]
    assert restored_entry.subject == "Translation into English I"
    assert restored_entry.hall == "115"
    assert restored_entry.section_hall == "106"
    assert restored_entry.color == "#8E44AD"


def test_entries_referencing_deleted_day_or_period_are_dropped_on_load():
    tt = Timetable.new_default()
    data = tt.to_dict()
    data["entries"] = [
        {"id": 1, "day_id": 999, "period_id": tt.periods[0].id, "subject": "Orphaned by day"},
        {"id": 2, "day_id": tt.days[0].id, "period_id": 999, "subject": "Orphaned by period"},
        {"id": 3, "day_id": tt.days[0].id, "period_id": tt.periods[0].id, "subject": "Valid entry"},
    ]
    restored = Timetable.from_dict(data)
    assert len(restored.entries) == 1
    assert restored.entries[0].subject == "Valid entry"


def test_entry_without_title_is_dropped_not_kept_as_blank():
    tt = Timetable.new_default()
    data = tt.to_dict()
    data["entries"] = [
        {"id": 1, "day_id": tt.days[0].id, "period_id": tt.periods[0].id, "subject": ""},
        {"id": 2, "day_id": tt.days[0].id, "period_id": tt.periods[0].id},  # no subject key at all
    ]
    restored = Timetable.from_dict(data)
    assert restored.entries == []


def test_completely_empty_or_garbage_data_falls_back_to_default_grid():
    restored = Timetable.from_dict({})
    assert len(restored.days) == 5
    assert len(restored.periods) == 7

    restored2 = Timetable.from_dict("not even a dict")
    assert len(restored2.days) == 5


def test_malformed_single_period_or_day_is_skipped_not_fatal():
    tt = Timetable.new_default()
    data = tt.to_dict()
    data["periods"].append("not a valid period object")
    data["days"].append(12345)
    restored = Timetable.from_dict(data)
    # Original 7 periods / 5 days survive; the garbage entries are dropped.
    assert len(restored.periods) == 7
    assert len(restored.days) == 5


def test_invalid_color_falls_back_to_default():
    day = Day.from_dict({"id": 1, "name": "Sunday", "header_color": "not-a-color"}, fallback_id=1)
    assert day.header_color.startswith("#")

    entry = Entry.from_dict(
        {"id": 1, "day_id": 1, "period_id": 1, "subject": "X", "color": "javascript:alert(1)"},
        fallback_id=1,
    )
    assert entry.color.startswith("#")
