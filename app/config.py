"""
Central constants. Note the palette below is deliberately the ONLY set of
background colors the app ever uses — always light/pastel, never dark —
per an explicit requirement: the app must not default to (or offer) a
dark background anywhere in the timetable itself.
"""
from __future__ import annotations

APP_NAME = "Timetable Maker"
ORG_NAME = "TimetableMaker"

DEFAULT_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

DEFAULT_PERIODS = [
    ("9:00", "10:00"),
    ("10:00", "11:00"),
    ("11:00", "12:00"),
    ("12:00", "1:00"),
    ("1:00", "2:00"),
    ("2:00", "3:00"),
    ("3:00", "4:00"),
]

# Light, professional defaults — matching the pale-yellow / cyan / gold
# look of the reference timetable, never anything dark.
DEFAULT_DAY_COLOR_BRIGHT = "#FFF200"
DEFAULT_DAY_COLOR_PALE = "#FDF6B2"
DEFAULT_CELL_COLOR = "#FFFDE7"
DEFAULT_ROW_COLOR_A = "#CFF3F3"  # pale cyan
DEFAULT_ROW_COLOR_B = "#F5C242"  # soft gold
DEFAULT_GRID_LINE_COLOR = "#333333"
DEFAULT_PAGE_BACKGROUND = "#FFFFFF"

# A curated set of accent-bar colors offered in the entry editor (plus a
# full color picker for anyone who wants something else). These are only
# ever used as a thin accent bar/tag on a card, never as a full-page
# background, so they don't conflict with the "never dark" rule.
ACCENT_PALETTE = [
    "#8E44AD",  # purple
    "#C0392B",  # red
    "#F5CBA7",  # cream / tan
    "#2E86C1",  # blue
    "#229954",  # green
    "#D68910",  # amber
    "#16A085",  # teal
    "#7F8C8D",  # neutral gray
]

KEYBOARD_SHORTCUTS = [
    ("Ctrl+N", "New Timetable"),
    ("Ctrl+O", "Open Timetable"),
    ("Ctrl+S", "Save As..."),
    ("Ctrl+Shift+E", "Export as Image"),
    ("Esc", "Close Dialog"),
]
