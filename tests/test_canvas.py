"""
Tests for the paint routine and image export.

These exercise real PySide6 widgets, so they need a Qt platform plugin.
QT_QPA_PLATFORM=offscreen is set as a fallback here (only if not already
set by the environment) so these run headlessly in CI / this sandbox
without needing a real display, while still using whatever the developer
has configured locally otherwise.
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from app.models.timetable import Entry, Timetable


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture
def rendered_image(qapp):
    """Renders a fresh default timetable and returns (canvas, image) with
    interactive hit-test rects populated, for pixel + rect assertions."""
    from app.ui.canvas import TimetableCanvas

    tt = Timetable.new_default()
    canvas = TimetableCanvas()
    canvas.set_timetable(tt)

    width, height = 1800, 600
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("#FFFFFF"))
    painter = QPainter(image)
    canvas._paint(painter, width, height, interactive=True)
    painter.end()

    return canvas, image, tt


def _sample_near_corner(image: QImage, rect) -> QColor:
    point = rect.topLeft() + type(rect.topLeft())(6, 6)
    return image.pixelColor(point)


# ------------------------------------------------------------------ #
# Regression test for the brush-leak bug: a logo placeholder's brush was
# silently overwriting every subsequent cell's fillRect() color via
# drawRect()'s implicit fill. This must never come back.
# ------------------------------------------------------------------ #
def test_day_header_colors_render_correctly(rendered_image):
    canvas, image, tt = rendered_image
    for day in tt.days:
        rect = canvas._day_rects[day.id]
        sampled = _sample_near_corner(image, rect)
        assert sampled.name().lower() == day.header_color.lower(), (
            f"{day.name} header should be {day.header_color}, got {sampled.name()}"
        )


def test_period_row_alternating_colors_render_correctly(rendered_image):
    canvas, image, tt = rendered_image
    for i, period in enumerate(tt.periods):
        rect = canvas._period_rects[period.id]
        sampled = _sample_near_corner(image, rect)
        expected = tt.meta.row_color_a if i % 2 == 0 else tt.meta.row_color_b
        assert sampled.name().lower() == expected.lower()


def test_empty_cell_color_renders_correctly(rendered_image):
    canvas, image, tt = rendered_image
    day, period = tt.days[0], tt.periods[0]
    rect = canvas._cell_rects[(day.id, period.id)]
    sampled = _sample_near_corner(image, rect)
    assert sampled.name().lower() == tt.meta.cell_color.lower()


def test_exported_background_is_always_light(rendered_image):
    """Direct guard for the 'never dark' requirement: every background
    region (page, cells, headers) must be bright, not dark."""
    canvas, image, tt = rendered_image
    points_to_check = [(5, 5)]  # page background corner
    for rect in list(canvas._cell_rects.values())[:5]:
        points_to_check.append((rect.center().x(), rect.center().y() - rect.height() // 2 + 6))
    for x, y in points_to_check:
        color = image.pixelColor(x, y)
        brightness = (color.red() + color.green() + color.blue()) / 3
        assert brightness > 180, f"Found a too-dark pixel at ({x},{y}): {color.name()}"


# ------------------------------------------------------------------ #
# Hit-testing
# ------------------------------------------------------------------ #
def test_hit_test_rects_cover_every_day_and_period(rendered_image):
    canvas, image, tt = rendered_image
    assert len(canvas._day_rects) == len(tt.days)
    assert len(canvas._period_rects) == len(tt.periods)
    assert len(canvas._cell_rects) == len(tt.days) * len(tt.periods)


def test_cell_rects_do_not_overlap(rendered_image):
    canvas, _image, _tt = rendered_image
    rects = list(canvas._cell_rects.values())
    for i, r1 in enumerate(rects):
        for r2 in rects[i + 1 :]:
            assert not r1.intersects(r2) or r1 == r2


# ------------------------------------------------------------------ #
# Export
# ------------------------------------------------------------------ #
def test_export_to_jpg_creates_valid_image(qapp, tmp_path):
    from app.ui.canvas import TimetableCanvas
    from app.ui.export_service import export_canvas_to_image

    tt = Timetable.new_default()
    tt.entries.append(
        Entry(id=1, day_id=tt.days[0].id, period_id=tt.periods[0].id, subject="Test Class", hall="101")
    )
    canvas = TimetableCanvas()
    canvas.set_timetable(tt)

    path = tmp_path / "export.jpg"
    ok = export_canvas_to_image(canvas, path, width=1200)
    assert ok is True
    assert path.exists()
    assert path.stat().st_size > 1000

    image = QImage(str(path))
    assert not image.isNull()
    assert image.width() == 1200


def test_export_to_png_creates_valid_image(qapp, tmp_path):
    from app.ui.canvas import TimetableCanvas
    from app.ui.export_service import export_canvas_to_image

    tt = Timetable.new_default()
    canvas = TimetableCanvas()
    canvas.set_timetable(tt)

    path = tmp_path / "export.png"
    ok = export_canvas_to_image(canvas, path, width=1000)
    assert ok is True
    image = QImage(str(path))
    assert not image.isNull()
    assert image.width() == 1000
