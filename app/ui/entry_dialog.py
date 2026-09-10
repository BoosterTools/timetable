from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import ACCENT_PALETTE
from app.models.timetable import Entry, Timetable


class _ColorPicker(QWidget):
    def __init__(self, initial: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._color = initial

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._swatch_buttons: list[QPushButton] = []
        for hex_color in ACCENT_PALETTE:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setCheckable(True)
            btn.setStyleSheet(
                f"background:{hex_color}; border-radius: 12px; border: 2px solid transparent;"
            )
            btn.clicked.connect(lambda _checked, c=hex_color: self._set_color(c))
            layout.addWidget(btn)
            self._swatch_buttons.append(btn)

        custom_btn = QPushButton("Custom...")
        custom_btn.clicked.connect(self._pick_custom)
        layout.addWidget(custom_btn)
        layout.addStretch(1)

        self._set_color(initial, emit_new=False)

    def _set_color(self, color: str, emit_new: bool = True) -> None:
        self._color = color
        for btn in self._swatch_buttons:
            btn.setChecked(False)
        for btn, hex_color in zip(self._swatch_buttons, ACCENT_PALETTE):
            if hex_color.lower() == color.lower():
                btn.setChecked(True)
                btn.setStyleSheet(
                    f"background:{hex_color}; border-radius: 12px; border: 2px solid #333333;"
                )
            else:
                btn.setStyleSheet(
                    f"background:{hex_color}; border-radius: 12px; border: 2px solid transparent;"
                )

    def _pick_custom(self) -> None:
        color = QColorDialog.getColor(QColor(self._color), self, "Choose Accent Color")
        if color.isValid():
            self._set_color(color.name())

    def color(self) -> str:
        return self._color


class EntryDialog(QDialog):
    def __init__(
        self,
        timetable: Timetable,
        day_id: int,
        period_id: int,
        entry: Optional[Entry] = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.timetable = timetable
        self.entry = entry
        self.result_data: dict = {}
        self.delete_requested = False

        self.setWindowTitle("Edit Class" if entry else "Add Class")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.subject_edit = QLineEdit(entry.subject if entry else "")
        self.subject_edit.setPlaceholderText("e.g. Translation into English I")
        form.addRow("Subject:", self.subject_edit)

        self.hall_edit = QLineEdit(entry.hall if entry else "")
        self.hall_edit.setPlaceholderText("e.g. 115")
        form.addRow("Hall / Room:", self.hall_edit)

        self.group_edit = QLineEdit(entry.group if entry else "")
        self.group_edit.setPlaceholderText("e.g. instructor name or group code")
        form.addRow("Instructor / Group:", self.group_edit)

        self.section_label_edit = QLineEdit(entry.section_label if entry else "")
        self.section_label_edit.setPlaceholderText("optional, e.g. 4.TR")
        form.addRow("Section Tag (optional):", self.section_label_edit)

        self.section_hall_edit = QLineEdit(entry.section_hall if entry else "")
        self.section_hall_edit.setPlaceholderText("optional, e.g. a second room number")
        form.addRow("Section Hall (optional):", self.section_hall_edit)

        self.day_combo = QComboBox()
        for day in timetable.days:
            self.day_combo.addItem(day.name, day.id)
        self._set_combo_by_data(self.day_combo, day_id)
        form.addRow("Day:", self.day_combo)

        self.period_combo = QComboBox()
        for period in timetable.periods:
            label = f"{period.label}  ({period.start_time}-{period.end_time})".strip()
            self.period_combo.addItem(label, period.id)
        self._set_combo_by_data(self.period_combo, period_id)
        form.addRow("Period:", self.period_combo)

        layout.addLayout(form)

        layout.addWidget(QLabel("Accent Color:"))
        self.color_picker = _ColorPicker(entry.color if entry else ACCENT_PALETTE[0])
        layout.addWidget(self.color_picker)

        self.conflict_label = QLabel("")
        self.conflict_label.setStyleSheet("color: #C0392B;")
        self.conflict_label.setWordWrap(True)
        layout.addWidget(self.conflict_label)

        button_row = QHBoxLayout()
        if entry is not None:
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("color: #C0392B;")
            delete_btn.clicked.connect(self._on_delete)
            button_row.addWidget(delete_btn)
        button_row.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        button_row.addWidget(buttons)
        layout.addLayout(button_row)

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, data_value: int) -> None:
        idx = combo.findData(data_value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _on_delete(self) -> None:
        self.delete_requested = True
        self.accept()

    def _on_save(self) -> None:
        subject = self.subject_edit.text().strip()
        if not subject:
            QMessageBox.warning(self, "Subject required", "Please enter a subject name.")
            return

        target_day_id = self.day_combo.currentData()
        target_period_id = self.period_combo.currentData()

        existing = self.timetable.get_entry(target_day_id, target_period_id)
        if existing is not None and (self.entry is None or existing.id != self.entry.id):
            self.conflict_label.setText(
                f'That day/period already has "{existing.subject}". '
                "Choose a different day/period, or edit that class instead."
            )
            return

        self.result_data = {
            "day_id": target_day_id,
            "period_id": target_period_id,
            "subject": subject,
            "hall": self.hall_edit.text().strip(),
            "group": self.group_edit.text().strip(),
            "section_label": self.section_label_edit.text().strip(),
            "section_hall": self.section_hall_edit.text().strip(),
            "color": self.color_picker.color(),
        }
        self.accept()
