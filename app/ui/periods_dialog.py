from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.timetable import Period, Timetable


class _PeriodEditDialog(QDialog):
    def __init__(self, period: Period | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Period" if period else "Add Period")
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.label_edit = QLineEdit(period.label if period else "")
        self.label_edit.setPlaceholderText("e.g. 1, or Break")
        form.addRow("Label:", self.label_edit)

        self.start_edit = QLineEdit(period.start_time if period else "")
        self.start_edit.setPlaceholderText("e.g. 9:00")
        form.addRow("Start time:", self.start_edit)

        self.end_edit = QLineEdit(period.end_time if period else "")
        self.end_edit.setPlaceholderText("e.g. 10:00")
        form.addRow("End time:", self.end_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.result_data: dict = {}

    def _on_save(self) -> None:
        label = self.label_edit.text().strip()
        if not label:
            QMessageBox.warning(self, "Label required", "Please enter a label for this period.")
            return
        self.result_data = {
            "label": label,
            "start_time": self.start_edit.text().strip(),
            "end_time": self.end_edit.text().strip(),
        }
        self.accept()


class PeriodsManagerDialog(QDialog):
    """Add/edit/delete/reorder the timetable's rows (time periods)."""

    def __init__(self, timetable: Timetable, parent: QWidget | None = None):
        super().__init__(parent)
        self.timetable = timetable
        self.changed = False
        self.setWindowTitle("Manage Periods")
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
        up_btn = QPushButton("▲ Move Up")
        up_btn.clicked.connect(lambda: self._on_move(-1))
        down_btn = QPushButton("▼ Move Down")
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
        for period in self.timetable.periods:
            text = f"{period.label}   {period.start_time}–{period.end_time}".strip()
            item = QListWidgetItem(text)
            item.setData(256, period.id)
            self.list_widget.addItem(item)

    def _selected_period(self) -> Period | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        period_id = item.data(256)
        return next((p for p in self.timetable.periods if p.id == period_id), None)

    def _on_add(self) -> None:
        dialog = _PeriodEditDialog(parent=self)
        if dialog.exec():
            new_period = Period(id=self.timetable.next_period_id(), **dialog.result_data)
            self.timetable.periods.append(new_period)
            self.changed = True
            self.refresh()

    def _on_edit(self) -> None:
        period = self._selected_period()
        if period is None:
            return
        dialog = _PeriodEditDialog(period, parent=self)
        if dialog.exec():
            period.label = dialog.result_data["label"]
            period.start_time = dialog.result_data["start_time"]
            period.end_time = dialog.result_data["end_time"]
            self.changed = True
            self.refresh()

    def _on_delete(self) -> None:
        period = self._selected_period()
        if period is None:
            return
        affected = [e for e in self.timetable.entries if e.period_id == period.id]
        message = f'Delete period "{period.label}"?'
        if affected:
            message += f"\n\nThis will also delete {len(affected)} class(es) scheduled in this period."
        choice = QMessageBox.question(
            self,
            "Delete period",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        self.timetable.periods = [p for p in self.timetable.periods if p.id != period.id]
        self.timetable.entries = [e for e in self.timetable.entries if e.period_id != period.id]
        self.changed = True
        self.refresh()

    def _on_move(self, direction: int) -> None:
        period = self._selected_period()
        if period is None:
            return
        periods = self.timetable.periods
        idx = periods.index(period)
        new_idx = idx + direction
        if 0 <= new_idx < len(periods):
            periods[idx], periods[new_idx] = periods[new_idx], periods[idx]
            self.changed = True
            self.refresh()
            self.list_widget.setCurrentRow(new_idx)
