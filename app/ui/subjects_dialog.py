from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.timetable import Timetable


class SubjectsManagerDialog(QDialog):
    """Add/rename/delete saved subject names offered in the Subject
    dropdown when adding or editing a class. This list is just a set of
    suggestions — renaming or deleting one here never changes the text of
    classes already placed on the grid."""

    def __init__(self, timetable: Timetable, parent: QWidget | None = None):
        super().__init__(parent)
        self.timetable = timetable
        self.changed = False
        self.setWindowTitle("Manage Subjects")
        self.setMinimumSize(360, 420)

        layout = QVBoxLayout(self)

        note = QLabel(
            "These are the names offered in the Subject dropdown. Renaming or "
            "deleting one here only changes future suggestions — it never "
            "changes classes already placed on the timetable."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #666;")
        layout.addWidget(note)

        add_row = QHBoxLayout()
        self.new_edit = QLineEdit()
        self.new_edit.setPlaceholderText("New subject name...")
        add_btn = QPushButton("+ Add")
        add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self.new_edit, 1)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        button_row = QHBoxLayout()
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self._on_rename)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._on_delete)
        button_row.addWidget(rename_btn)
        button_row.addWidget(delete_btn)
        layout.addLayout(button_row)

        close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_buttons.rejected.connect(self.accept)
        close_buttons.accepted.connect(self.accept)
        layout.addWidget(close_buttons)

        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        for name in self.timetable.list_subjects():
            usage = sum(1 for e in self.timetable.entries if e.subject.lower() == name.lower())
            suffix = f"   (used by {usage})" if usage else "   (unused)"
            item = QListWidgetItem(name + suffix)
            item.setData(256, name)
            self.list_widget.addItem(item)

    def _selected_name(self) -> str | None:
        item = self.list_widget.currentItem()
        return item.data(256) if item else None

    def _on_add(self) -> None:
        name = self.new_edit.text().strip()
        if not name:
            return
        self.timetable.add_subject(name)
        self.new_edit.clear()
        self.changed = True
        self.refresh()

    def _on_rename(self) -> None:
        old_name = self._selected_name()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Subject", "New name:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            self.timetable.rename_subject(old_name, new_name.strip())
            self.changed = True
            self.refresh()

    def _on_delete(self) -> None:
        name = self._selected_name()
        if not name:
            return
        choice = QMessageBox.question(
            self,
            "Delete subject",
            f'Remove "{name}" from the saved subject list?\n\n'
            "This only affects the dropdown — any classes already using this "
            "subject name are not changed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        self.timetable.delete_subject(name)
        self.changed = True
        self.refresh()
