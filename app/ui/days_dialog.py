from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import DEFAULT_DAY_COLOR_BRIGHT, DEFAULT_DAY_COLOR_PALE
from app.models.timetable import Day, Timetable


class _DayEditDialog(QDialog):
    def __init__(self, day: Day | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Day" if day else "Add Day")
        self._color = day.header_color if day else DEFAULT_DAY_COLOR_PALE

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit(day.name if day else "")
        self.name_edit.setPlaceholderText("e.g. Friday")
        form.addRow("Name:", self.name_edit)
        layout.addLayout(form)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Header color:"))
        self.pale_btn = QPushButton("Pale")
        self.pale_btn.setStyleSheet(f"background:{DEFAULT_DAY_COLOR_PALE};")
        self.pale_btn.clicked.connect(lambda: self._set_color(DEFAULT_DAY_COLOR_PALE))
        self.bright_btn = QPushButton("Bright")
        self.bright_btn.setStyleSheet(f"background:{DEFAULT_DAY_COLOR_BRIGHT};")
        self.bright_btn.clicked.connect(lambda: self._set_color(DEFAULT_DAY_COLOR_BRIGHT))
        self.custom_btn = QPushButton("Custom...")
        self.custom_btn.clicked.connect(self._pick_custom)
        color_row.addWidget(self.pale_btn)
        color_row.addWidget(self.bright_btn)
        color_row.addWidget(self.custom_btn)
        color_row.addStretch(1)
        layout.addLayout(color_row)

        self.preview = QPushButton()
        self.preview.setEnabled(False)
        self.preview.setFixedHeight(28)
        layout.addWidget(self.preview)
        self._set_color(self._color)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.result_data: dict = {}

    def _set_color(self, color: str) -> None:
        self._color = color
        self.preview.setStyleSheet(f"background:{color}; border: 1px solid #999;")

    def _pick_custom(self) -> None:
        color = QColorDialog.getColor(QColor(self._color), self, "Choose Header Color")
        if color.isValid():
            self._set_color(color.name())

    def _on_save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Name required", "Please enter a day name.")
            return
        self.result_data = {"name": name, "header_color": self._color}
        self.accept()


class DaysManagerDialog(QDialog):
    """Add/edit/delete/reorder the timetable's columns (days)."""

    def __init__(self, timetable: Timetable, parent: QWidget | None = None):
        super().__init__(parent)
        self.timetable = timetable
        self.changed = False
        self.setWindowTitle("Manage Days")
        self.setMinimumSize(360, 420)

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        button_row = QHBoxLayout()
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(self._on_add)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._on_edit)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._on_delete)
        up_btn = QPushButton("◀ Move Left")
        up_btn.clicked.connect(lambda: self._on_move(-1))
        down_btn = QPushButton("▶ Move Right")
        down_btn.clicked.connect(lambda: self._on_move(1))
        for btn in (add_btn, edit_btn, delete_btn, up_btn, down_btn):
            button_row.addWidget(btn)
        layout.addLayout(button_row)

        close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_buttons.rejected.connect(self.accept)
        close_buttons.accepted.connect(self.accept)
        layout.addWidget(close_buttons)

        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        for day in self.timetable.days:
            item = QListWidgetItem(day.name)
            item.setData(256, day.id)
            self.list_widget.addItem(item)

    def _selected_day(self) -> Day | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        day_id = item.data(256)
        return next((d for d in self.timetable.days if d.id == day_id), None)

    def _on_add(self) -> None:
        dialog = _DayEditDialog(parent=self)
        if dialog.exec():
            new_day = Day(id=self.timetable.next_day_id(), **dialog.result_data)
            self.timetable.days.append(new_day)
            self.changed = True
            self.refresh()

    def _on_edit(self) -> None:
        day = self._selected_day()
        if day is None:
            return
        dialog = _DayEditDialog(day, parent=self)
        if dialog.exec():
            day.name = dialog.result_data["name"]
            day.header_color = dialog.result_data["header_color"]
            self.changed = True
            self.refresh()

    def _on_delete(self) -> None:
        day = self._selected_day()
        if day is None:
            return
        affected = [e for e in self.timetable.entries if e.day_id == day.id]
        message = f'Delete "{day.name}"?'
        if affected:
            message += f"\n\nThis will also delete {len(affected)} class(es) scheduled on this day."
        choice = QMessageBox.question(
            self,
            "Delete day",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        self.timetable.days = [d for d in self.timetable.days if d.id != day.id]
        self.timetable.entries = [e for e in self.timetable.entries if e.day_id != day.id]
        self.changed = True
        self.refresh()

    def _on_move(self, direction: int) -> None:
        day = self._selected_day()
        if day is None:
            return
        days = self.timetable.days
        idx = days.index(day)
        new_idx = idx + direction
        if 0 <= new_idx < len(days):
            days[idx], days[new_idx] = days[new_idx], days[idx]
            self.changed = True
            self.refresh()
            self.list_widget.setCurrentRow(new_idx)
