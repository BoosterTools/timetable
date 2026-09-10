"""
The timetable data model.

Everything is keyed by small integer ids (not array position), so periods,
days, and entries can be freely reordered, inserted, or deleted without
ever having to renumber or re-link anything else. ``from_dict`` on every
class is defensive — a missing or malformed field falls back to a safe
default rather than raising, so a hand-edited or partially-corrupt save
file degrades gracefully instead of crashing the app or losing everything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.config import (
    ACCENT_PALETTE,
    DEFAULT_CELL_COLOR,
    DEFAULT_DAY_COLOR_BRIGHT,
    DEFAULT_DAY_COLOR_PALE,
    DEFAULT_DAYS,
    DEFAULT_GRID_LINE_COLOR,
    DEFAULT_PERIODS,
    DEFAULT_ROW_COLOR_A,
    DEFAULT_ROW_COLOR_B,
)


def _safe_str(value, default: str = "") -> str:
    return str(value) if value is not None else default


def _safe_color(value, default: str) -> str:
    text = _safe_str(value, default).strip()
    if text.startswith("#") and len(text) in (4, 7):
        return text
    return default


@dataclass
class Period:
    id: int
    label: str  # usually "1", "2", ... but can be renamed (e.g. "Break")
    start_time: str = ""
    end_time: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "start_time": self.start_time, "end_time": self.end_time}

    @classmethod
    def from_dict(cls, data: dict, fallback_id: int) -> "Period":
        if not isinstance(data, dict):
            data = {}
        try:
            period_id = int(data.get("id", fallback_id))
        except (TypeError, ValueError):
            period_id = fallback_id
        return cls(
            id=period_id,
            label=_safe_str(data.get("label"), str(fallback_id)),
            start_time=_safe_str(data.get("start_time")),
            end_time=_safe_str(data.get("end_time")),
        )


@dataclass
class Day:
    id: int
    name: str
    header_color: str = DEFAULT_DAY_COLOR_PALE

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "header_color": self.header_color}

    @classmethod
    def from_dict(cls, data: dict, fallback_id: int) -> "Day":
        if not isinstance(data, dict):
            data = {}
        try:
            day_id = int(data.get("id", fallback_id))
        except (TypeError, ValueError):
            day_id = fallback_id
        return cls(
            id=day_id,
            name=_safe_str(data.get("name"), f"Day {fallback_id}"),
            header_color=_safe_color(data.get("header_color"), DEFAULT_DAY_COLOR_PALE),
        )


@dataclass
class Entry:
    id: int
    day_id: int
    period_id: int
    subject: str
    hall: str = ""
    group: str = ""           # instructor / section / group label
    section_label: str = ""   # e.g. "4.TR" small secondary tag
    section_hall: str = ""    # e.g. a second room number shown alongside section_label
    color: str = ACCENT_PALETTE[0]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "day_id": self.day_id,
            "period_id": self.period_id,
            "subject": self.subject,
            "hall": self.hall,
            "group": self.group,
            "section_label": self.section_label,
            "section_hall": self.section_hall,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict, fallback_id: int) -> Optional["Entry"]:
        if not isinstance(data, dict):
            return None
        subject = _safe_str(data.get("subject")).strip()
        if not subject:
            return None
        try:
            entry_id = int(data.get("id", fallback_id))
            day_id = int(data["day_id"])
            period_id = int(data["period_id"])
        except (TypeError, ValueError, KeyError):
            return None
        return cls(
            id=entry_id,
            day_id=day_id,
            period_id=period_id,
            subject=subject,
            hall=_safe_str(data.get("hall")),
            group=_safe_str(data.get("group")),
            section_label=_safe_str(data.get("section_label")),
            section_hall=_safe_str(data.get("section_hall")),
            color=_safe_color(data.get("color"), ACCENT_PALETTE[0]),
        )


@dataclass
class TimetableMeta:
    title_line1: str = "My Timetable"
    title_line2: str = ""
    footer_left: str = ""
    footer_right: str = "Made with Timetable Maker"
    logo_path: str = ""
    day_color_bright: str = DEFAULT_DAY_COLOR_BRIGHT
    day_color_pale: str = DEFAULT_DAY_COLOR_PALE
    cell_color: str = DEFAULT_CELL_COLOR
    row_color_a: str = DEFAULT_ROW_COLOR_A
    row_color_b: str = DEFAULT_ROW_COLOR_B
    grid_line_color: str = DEFAULT_GRID_LINE_COLOR

    def to_dict(self) -> dict:
        return {
            "title_line1": self.title_line1,
            "title_line2": self.title_line2,
            "footer_left": self.footer_left,
            "footer_right": self.footer_right,
            "logo_path": self.logo_path,
            "day_color_bright": self.day_color_bright,
            "day_color_pale": self.day_color_pale,
            "cell_color": self.cell_color,
            "row_color_a": self.row_color_a,
            "row_color_b": self.row_color_b,
            "grid_line_color": self.grid_line_color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimetableMeta":
        if not isinstance(data, dict):
            data = {}
        defaults = cls()
        return cls(
            title_line1=_safe_str(data.get("title_line1"), defaults.title_line1),
            title_line2=_safe_str(data.get("title_line2"), defaults.title_line2),
            footer_left=_safe_str(data.get("footer_left"), defaults.footer_left),
            footer_right=_safe_str(data.get("footer_right"), defaults.footer_right),
            logo_path=_safe_str(data.get("logo_path"), defaults.logo_path),
            day_color_bright=_safe_color(data.get("day_color_bright"), defaults.day_color_bright),
            day_color_pale=_safe_color(data.get("day_color_pale"), defaults.day_color_pale),
            cell_color=_safe_color(data.get("cell_color"), defaults.cell_color),
            row_color_a=_safe_color(data.get("row_color_a"), defaults.row_color_a),
            row_color_b=_safe_color(data.get("row_color_b"), defaults.row_color_b),
            grid_line_color=_safe_color(data.get("grid_line_color"), defaults.grid_line_color),
        )


@dataclass
class Timetable:
    meta: TimetableMeta = field(default_factory=TimetableMeta)
    periods: list[Period] = field(default_factory=list)
    days: list[Day] = field(default_factory=list)
    entries: list[Entry] = field(default_factory=list)
    subjects: list[str] = field(default_factory=list)  # saved names offered in the subject dropdown

    # ------------------------------------------------------------------ #
    @classmethod
    def new_default(cls) -> "Timetable":
        """A ready-to-use blank grid: 5 weekdays x 7 periods, matching a
        typical university timetable, with no entries yet."""
        days = [
            Day(id=i + 1, name=name, header_color=_alternate_day_color(i))
            for i, name in enumerate(DEFAULT_DAYS)
        ]
        periods = [
            Period(id=i + 1, label=str(i + 1), start_time=start, end_time=end)
            for i, (start, end) in enumerate(DEFAULT_PERIODS)
        ]
        return cls(meta=TimetableMeta(), periods=periods, days=days, entries=[])

    # ------------------------------------------------------------------ #
    def get_entry(self, day_id: int, period_id: int) -> Optional[Entry]:
        return next(
            (e for e in self.entries if e.day_id == day_id and e.period_id == period_id), None
        )

    def next_entry_id(self) -> int:
        return max((e.id for e in self.entries), default=0) + 1

    def next_period_id(self) -> int:
        return max((p.id for p in self.periods), default=0) + 1

    def next_day_id(self) -> int:
        return max((d.id for d in self.days), default=0) + 1

    # ------------------------------------------------------------------ #
    # Subject catalog — a simple, loosely-coupled list of names offered in
    # the subject dropdown. Entries store their own copy of the subject
    # text (not a foreign key), so renaming/deleting a catalog entry only
    # changes future suggestions and never risks altering or losing
    # existing classes already on the grid.
    # ------------------------------------------------------------------ #
    def list_subjects(self) -> list[str]:
        return sorted(self.subjects, key=str.lower)

    def add_subject(self, name: str) -> None:
        name = (name or "").strip()
        if not name:
            return
        if not any(existing.lower() == name.lower() for existing in self.subjects):
            self.subjects.append(name)

    def rename_subject(self, old: str, new: str) -> None:
        new = (new or "").strip()
        if not new:
            return
        for i, existing in enumerate(self.subjects):
            if existing.lower() == old.lower():
                self.subjects[i] = new
                return

    def delete_subject(self, name: str) -> None:
        self.subjects = [s for s in self.subjects if s.lower() != (name or "").lower()]

    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "version": 1,
            "meta": self.meta.to_dict(),
            "periods": [p.to_dict() for p in self.periods],
            "days": [d.to_dict() for d in self.days],
            "entries": [e.to_dict() for e in self.entries],
            "subjects": list(self.subjects),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Timetable":
        if not isinstance(data, dict):
            data = {}

        meta = TimetableMeta.from_dict(data.get("meta"))

        periods: list[Period] = []
        for i, raw in enumerate(data.get("periods") or []):
            if not isinstance(raw, dict):
                continue
            try:
                periods.append(Period.from_dict(raw, fallback_id=i + 1))
            except Exception:
                continue

        days: list[Day] = []
        for i, raw in enumerate(data.get("days") or []):
            if not isinstance(raw, dict):
                continue
            try:
                days.append(Day.from_dict(raw, fallback_id=i + 1))
            except Exception:
                continue

        valid_day_ids = {d.id for d in days}
        valid_period_ids = {p.id for p in periods}

        entries: list[Entry] = []
        for i, raw in enumerate(data.get("entries") or []):
            entry = Entry.from_dict(raw, fallback_id=i + 1)
            if entry is None:
                continue
            # Drop entries that point at a day/period that no longer
            # exists, rather than letting them reference a dangling id.
            if entry.day_id in valid_day_ids and entry.period_id in valid_period_ids:
                entries.append(entry)

        if not periods and not days:
            # Completely empty/unreadable save — hand back a fresh default
            # grid rather than an unusable blank timetable with no rows.
            return cls.new_default()

        raw_subjects = data.get("subjects")
        subjects: list[str] = []
        if isinstance(raw_subjects, list):
            for item in raw_subjects:
                if not isinstance(item, str):
                    continue
                name = item.strip()
                if name and not any(s.lower() == name.lower() for s in subjects):
                    subjects.append(name)
        else:
            # Backward compatibility: files saved before this feature
            # existed have no "subjects" key at all. Auto-populate the
            # catalog from whatever subjects are already used on the grid,
            # so existing timetables get a useful dropdown immediately
            # instead of starting empty.
            for entry in entries:
                name = entry.subject.strip()
                if name and not any(s.lower() == name.lower() for s in subjects):
                    subjects.append(name)

        return cls(meta=meta, periods=periods, days=days, entries=entries, subjects=subjects)


def _alternate_day_color(index: int) -> str:
    return DEFAULT_DAY_COLOR_BRIGHT if index % 2 == 1 else DEFAULT_DAY_COLOR_PALE
