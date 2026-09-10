"""
The timetable canvas.

This widget owns ONE painting routine (``_paint``) used for both the live
on-screen display and image export — so what you see is always exactly
what you get in the exported JPG/PNG, with no risk of the two drifting
apart. It also tracks the on-screen rectangle of every clickable region
(title, logo, each day header, each period label, each cell) so a click
can be mapped straight back to "what did the user click on" without any
separate hit-testing model to keep in sync.

The canvas background is always white/light — this is intentional and
non-configurable, matching the requirement that the app must never default
to (or drift into) a dark background.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from app.models.timetable import Entry, Timetable

MARGIN = 18
LOGO_SIZE = 56
TITLE_HEIGHT = 66
HEADER_HEIGHT = 52
FOOTER_HEIGHT = 26
LABEL_COL_WIDTH = 96
MIN_ROW_HEIGHT = 60

BORDER_COLOR = "#FFFFFF"  # widget's own background, always white


class TimetableCanvas(QWidget):
    cell_clicked = Signal(int, int)  # day_id, period_id
    day_header_clicked = Signal(int)  # day_id
    period_label_clicked = Signal(int)  # period_id
    title_clicked = Signal()
    logo_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.timetable: Optional[Timetable] = None
        self.setMinimumSize(760, 520)
        self.setMouseTracking(True)
        self.setStyleSheet(f"background: {BORDER_COLOR};")

        self._cell_rects: dict[tuple[int, int], QRect] = {}
        self._day_rects: dict[int, QRect] = {}
        self._period_rects: dict[int, QRect] = {}
        self._title_rect = QRect()
        self._logo_rect = QRect()

    # ------------------------------------------------------------------ #
    def set_timetable(self, timetable: Timetable) -> None:
        self.timetable = timetable
        self.update()

    def natural_height_for_width(self, width: int) -> int:
        """A good export height for a given width, based on row/column
        counts, so exported images aren't awkwardly stretched."""
        if not self.timetable:
            return int(width * 0.6)
        rows = max(len(self.timetable.periods), 1)
        content_height = TITLE_HEIGHT + HEADER_HEIGHT + rows * MIN_ROW_HEIGHT + FOOTER_HEIGHT
        return content_height + MARGIN * 2

    # ------------------------------------------------------------------ #
    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint(painter, self.width(), self.height(), interactive=True)
        painter.end()

    def render_to_image(self, width: int = 1600, height: Optional[int] = None) -> QImage:
        """Renders the SAME layout used on-screen at an arbitrary target
        resolution, for crisp JPG/PNG export."""
        if height is None:
            scale = width / max(self.width(), 1)
            height = max(int(self.natural_height_for_width(width)), int(self.height() * scale))
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor("#FFFFFF"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint(painter, width, height, interactive=False)
        painter.end()
        return image

    # ------------------------------------------------------------------ #
    def _paint(self, painter: QPainter, width: int, height: int, interactive: bool) -> None:
        if interactive:
            self._cell_rects = {}
            self._day_rects = {}
            self._period_rects = {}

        painter.fillRect(0, 0, width, height, QColor("#FFFFFF"))

        tt = self.timetable
        if tt is None or not tt.days or not tt.periods:
            painter.setPen(QPen(QColor("#999999")))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(QRect(0, 0, width, height), Qt.AlignmentFlag.AlignCenter, "No timetable loaded")
            return

        content_width = max(width - MARGIN * 2, 200)

        # --- Title + logo -------------------------------------------------------
        title_rect = QRect(MARGIN, MARGIN, content_width, TITLE_HEIGHT)
        if interactive:
            self._title_rect = title_rect

        logo_rect = QRect(MARGIN, MARGIN + (TITLE_HEIGHT - LOGO_SIZE) // 2, LOGO_SIZE, LOGO_SIZE)
        if interactive:
            self._logo_rect = logo_rect
        self._paint_logo(painter, logo_rect, tt.meta.logo_path)

        painter.setPen(QPen(QColor("#111111")))
        painter.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        painter.drawText(
            QRect(MARGIN, MARGIN, content_width, 32),
            Qt.AlignmentFlag.AlignCenter,
            tt.meta.title_line1,
        )
        painter.setFont(QFont("Arial", 13))
        painter.drawText(
            QRect(MARGIN, MARGIN + 32, content_width, 28),
            Qt.AlignmentFlag.AlignCenter,
            tt.meta.title_line2,
        )

        # --- Grid geometry ---------------------------------------------------------
        grid_top = MARGIN + TITLE_HEIGHT + 6
        grid_bottom = height - MARGIN - FOOTER_HEIGHT
        grid_height = max(grid_bottom - grid_top, HEADER_HEIGHT + MIN_ROW_HEIGHT)

        num_days = max(len(tt.days), 1)
        num_periods = max(len(tt.periods), 1)
        day_col_width = max((content_width - LABEL_COL_WIDTH) / num_days, 40)
        row_height = max((grid_height - HEADER_HEIGHT) / num_periods, MIN_ROW_HEIGHT)

        # Empty corner above the period-label column
        painter.fillRect(QRect(MARGIN, grid_top, LABEL_COL_WIDTH, HEADER_HEIGHT), QColor("#FFFFFF"))

        # --- Day headers -------------------------------------------------------------
        x = MARGIN + LABEL_COL_WIDTH
        for day in tt.days:
            rect = QRect(int(x), grid_top, int(day_col_width), HEADER_HEIGHT)
            painter.fillRect(rect, QColor(day.header_color))
            painter.setPen(QPen(QColor(tt.meta.grid_line_color)))
            painter.setBrush(Qt.BrushStyle.NoBrush)  # drawRect below must only stroke, never re-fill
            painter.drawRect(rect)
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#111111")))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, day.name)
            if interactive:
                self._day_rects[day.id] = rect
            x += day_col_width

        # --- Period rows + cells -----------------------------------------------------
        y = grid_top + HEADER_HEIGHT
        for pi, period in enumerate(tt.periods):
            label_rect = QRect(MARGIN, int(y), LABEL_COL_WIDTH, int(row_height))
            row_color = tt.meta.row_color_a if pi % 2 == 0 else tt.meta.row_color_b
            painter.fillRect(label_rect, QColor(row_color))
            painter.setPen(QPen(QColor(tt.meta.grid_line_color)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(label_rect)

            painter.setPen(QPen(QColor("#111111")))
            painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            painter.drawText(
                QRect(label_rect.x(), label_rect.y() + 4, label_rect.width(), 22),
                Qt.AlignmentFlag.AlignHCenter,
                period.label,
            )
            painter.setFont(QFont("Arial", 9))
            time_text = f"{period.start_time}\n{period.end_time}".strip()
            painter.drawText(
                QRect(label_rect.x(), label_rect.y() + 26, label_rect.width(), label_rect.height() - 28),
                Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap,
                time_text,
            )
            if interactive:
                self._period_rects[period.id] = label_rect

            cx = MARGIN + LABEL_COL_WIDTH
            for day in tt.days:
                cell_rect = QRect(int(cx), int(y), int(day_col_width), int(row_height))
                painter.fillRect(cell_rect, QColor(tt.meta.cell_color))
                painter.setPen(QPen(QColor(tt.meta.grid_line_color)))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(cell_rect)

                entry = tt.get_entry(day.id, period.id)
                if entry is not None:
                    self._paint_entry(painter, cell_rect, entry)

                if interactive:
                    self._cell_rects[(day.id, period.id)] = cell_rect
                cx += day_col_width
            y += row_height

        # --- Footer -----------------------------------------------------------------
        footer_y = height - MARGIN - FOOTER_HEIGHT
        painter.setFont(QFont("Arial", 8))
        painter.setPen(QPen(QColor("#666666")))
        half = content_width // 2
        painter.drawText(
            QRect(MARGIN, footer_y, half, FOOTER_HEIGHT),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            tt.meta.footer_left,
        )
        painter.drawText(
            QRect(MARGIN + half, footer_y, content_width - half, FOOTER_HEIGHT),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            tt.meta.footer_right,
        )

    # ------------------------------------------------------------------ #
    def _paint_logo(self, painter: QPainter, rect: QRect, logo_path: str) -> None:
        if logo_path and Path(logo_path).exists():
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    rect.width(),
                    rect.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                px = rect.x() + (rect.width() - scaled.width()) // 2
                py = rect.y() + (rect.height() - scaled.height()) // 2
                painter.drawPixmap(px, py, scaled)
                return
        # Placeholder: a soft dashed circle, hinting "click to add a logo"
        painter.setPen(QPen(QColor("#CCCCCC"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QColor("#FAFAFA"))
        painter.drawEllipse(rect)
        painter.setBrush(Qt.BrushStyle.NoBrush)  # don't let this leak into later drawRect() calls

    def _paint_entry(self, painter: QPainter, cell_rect: QRect, entry: Entry) -> None:
        bar_width = 6
        bar_rect = QRect(cell_rect.x(), cell_rect.y(), bar_width, cell_rect.height())
        painter.fillRect(bar_rect, QColor(entry.color))

        text_x = cell_rect.x() + bar_width + 5
        text_w = max(cell_rect.width() - bar_width - 9, 10)
        cursor_y = cell_rect.y() + 3

        if entry.hall:
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#111111")))
            painter.drawText(QRect(text_x, cursor_y, text_w, 14), Qt.AlignmentFlag.AlignLeft, entry.hall)
            cursor_y += 15

        bottom_reserved = 16 if (entry.group or entry.section_label or entry.section_hall) else 4
        subject_rect = QRect(text_x, cursor_y, text_w, max(cell_rect.bottom() - cursor_y - bottom_reserved, 10))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#111111")))
        painter.drawText(
            subject_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            entry.subject,
        )

        bottom_y = cell_rect.bottom() - 14
        if entry.group:
            painter.setFont(QFont("Arial", 7))
            painter.setPen(QPen(QColor("#333333")))
            painter.drawText(QRect(text_x, bottom_y, text_w, 14), Qt.AlignmentFlag.AlignLeft, entry.group)
        if entry.section_label or entry.section_hall:
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#111111")))
            tag = entry.section_hall or entry.section_label
            painter.drawText(QRect(text_x, bottom_y, text_w, 14), Qt.AlignmentFlag.AlignRight, tag)
            if entry.section_label and entry.section_hall:
                painter.setFont(QFont("Arial", 6))
                painter.drawText(
                    QRect(text_x, bottom_y - 10, text_w, 10),
                    Qt.AlignmentFlag.AlignRight,
                    entry.section_label,
                )

    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()

        if self._title_rect.contains(pos):
            self.title_clicked.emit()
            return
        if self._logo_rect.contains(pos):
            self.logo_clicked.emit()
            return
        for day_id, rect in self._day_rects.items():
            if rect.contains(pos):
                self.day_header_clicked.emit(day_id)
                return
        for period_id, rect in self._period_rects.items():
            if rect.contains(pos):
                self.period_label_clicked.emit(period_id)
                return
        for (day_id, period_id), rect in self._cell_rects.items():
            if rect.contains(pos):
                self.cell_clicked.emit(day_id, period_id)
                return

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()
        clickable = (
            self._title_rect.contains(pos)
            or self._logo_rect.contains(pos)
            or any(r.contains(pos) for r in self._day_rects.values())
            or any(r.contains(pos) for r in self._period_rects.values())
            or any(r.contains(pos) for r in self._cell_rects.values())
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor if clickable else Qt.CursorShape.ArrowCursor)
