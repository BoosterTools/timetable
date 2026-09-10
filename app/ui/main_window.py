from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QToolBar,
)

from app.config import APP_NAME
from app.models.timetable import Entry, Timetable
from app.services.storage import InvalidTimetableFileError, TimetableStorage, load_from_path, save_to_path
from app.ui.canvas import TimetableCanvas
from app.ui.days_dialog import DaysManagerDialog
from app.ui.entry_dialog import EntryDialog
from app.ui.export_service import export_canvas_to_image
from app.ui.meta_dialog import MetaDialog
from app.ui.periods_dialog import PeriodsManagerDialog
from app.ui.subjects_dialog import SubjectsManagerDialog
from app.utils.logger import get_logger

logger = get_logger()


def _sanitize_filename(text: str) -> str:
    safe = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in text).strip()
    return safe or "timetable"


class MainWindow(QMainWindow):
    def __init__(self, storage: TimetableStorage):
        super().__init__()
        self.storage = storage
        self.timetable: Timetable = storage.load()

        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)

        self.canvas = TimetableCanvas()
        self.canvas.set_timetable(self.timetable)
        self.canvas.cell_clicked.connect(self._on_cell_clicked)
        self.canvas.day_header_clicked.connect(self._on_day_header_clicked)
        self.canvas.period_label_clicked.connect(self._on_period_label_clicked)
        self.canvas.title_clicked.connect(self._on_meta_clicked)
        self.canvas.logo_clicked.connect(self._on_meta_clicked)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)
        self.setCentralWidget(scroll)

        self._build_toolbar()
        self.statusBar().showMessage(
            "Tip: click the title, logo, a day header, a period, or any cell to edit it.", 6000
        )

    # ------------------------------------------------------------------ #
    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        def add_button(text: str, handler, primary: bool = False) -> None:
            btn = QPushButton(text)
            if primary:
                btn.setObjectName("Primary")
            btn.clicked.connect(handler)
            toolbar.addWidget(btn)

        add_button("New", self._on_new)
        add_button("Open...", self._on_open)
        add_button("Save As...", self._on_save_as)
        toolbar.addSeparator()
        add_button("Export as Image...", self._on_export_image, primary=True)
        toolbar.addSeparator()
        add_button("Manage Periods...", self._on_manage_periods)
        add_button("Manage Days...", self._on_manage_days)
        add_button("Manage Subjects...", self._on_manage_subjects)
        add_button("Header && Footer...", self._on_meta_clicked)

    # ------------------------------------------------------------------ #
    def _save_and_refresh(self) -> None:
        self.storage.save(self.timetable)
        self.canvas.set_timetable(self.timetable)

    # ------------------------------------------------------------------ #
    # Click-to-edit handlers
    # ------------------------------------------------------------------ #
    def _on_cell_clicked(self, day_id: int, period_id: int) -> None:
        entry = self.timetable.get_entry(day_id, period_id)
        dialog = EntryDialog(self.timetable, day_id, period_id, entry=entry, parent=self)
        if not dialog.exec():
            return

        if dialog.delete_requested and entry is not None:
            self.timetable.entries = [e for e in self.timetable.entries if e.id != entry.id]
        elif entry is not None:
            data = dialog.result_data
            entry.day_id = data["day_id"]
            entry.period_id = data["period_id"]
            entry.subject = data["subject"]
            entry.hall = data["hall"]
            entry.group = data["group"]
            entry.section_label = data["section_label"]
            entry.section_hall = data["section_hall"]
            entry.color = data["color"]
        else:
            new_entry = Entry(id=self.timetable.next_entry_id(), **dialog.result_data)
            self.timetable.entries.append(new_entry)

        self._save_and_refresh()

    def _on_day_header_clicked(self, day_id: int) -> None:
        dialog = DaysManagerDialog(self.timetable, parent=self)
        for i in range(dialog.list_widget.count()):
            if dialog.list_widget.item(i).data(256) == day_id:
                dialog.list_widget.setCurrentRow(i)
                break
        dialog.exec()
        if dialog.changed:
            self._save_and_refresh()

    def _on_period_label_clicked(self, period_id: int) -> None:
        dialog = PeriodsManagerDialog(self.timetable, parent=self)
        for i in range(dialog.list_widget.count()):
            if dialog.list_widget.item(i).data(256) == period_id:
                dialog.list_widget.setCurrentRow(i)
                break
        dialog.exec()
        if dialog.changed:
            self._save_and_refresh()

    def _on_meta_clicked(self) -> None:
        dialog = MetaDialog(self.timetable.meta, parent=self)
        if dialog.exec():
            data = dialog.result_data
            self.timetable.meta.title_line1 = data["title_line1"]
            self.timetable.meta.title_line2 = data["title_line2"]
            self.timetable.meta.footer_left = data["footer_left"]
            self.timetable.meta.footer_right = data["footer_right"]
            self.timetable.meta.logo_path = data["logo_path"]
            self._save_and_refresh()

    # ------------------------------------------------------------------ #
    # Toolbar handlers
    # ------------------------------------------------------------------ #
    def _on_manage_periods(self) -> None:
        dialog = PeriodsManagerDialog(self.timetable, parent=self)
        dialog.exec()
        if dialog.changed:
            self._save_and_refresh()

    def _on_manage_days(self) -> None:
        dialog = DaysManagerDialog(self.timetable, parent=self)
        dialog.exec()
        if dialog.changed:
            self._save_and_refresh()

    def _on_manage_subjects(self) -> None:
        dialog = SubjectsManagerDialog(self.timetable, parent=self)
        dialog.exec()
        if dialog.changed:
            self._save_and_refresh()

    def _on_new(self) -> None:
        choice = QMessageBox.question(
            self,
            "New timetable",
            "Start a new blank timetable? Your current one will no longer be the active "
            "document (use \"Save As...\" first if you want to keep a copy).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        self.timetable = Timetable.new_default()
        self._save_and_refresh()

    def _on_open(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Open Timetable", "", "Timetable JSON (*.json)"
        )
        if not path_str:
            return
        try:
            loaded = load_from_path(Path(path_str))
        except InvalidTimetableFileError as exc:
            QMessageBox.critical(self, "Could not open file", str(exc))
            return

        choice = QMessageBox.question(
            self,
            "Open timetable",
            "Replace the currently open timetable with this file? "
            "(Use \"Save As...\" first if you want to keep the current one.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return

        self.timetable = loaded
        self._save_and_refresh()

    def _on_save_as(self) -> None:
        default_name = _sanitize_filename(self.timetable.meta.title_line1) + ".json"
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Save Timetable As", default_name, "Timetable JSON (*.json)"
        )
        if not path_str:
            return
        ok = save_to_path(self.timetable, Path(path_str))
        if ok:
            QMessageBox.information(self, "Saved", f"Timetable saved to:\n{path_str}")
        else:
            QMessageBox.critical(self, "Save failed", "Could not save the file. Check the location and try again.")

    def _on_export_image(self) -> None:
        default_name = _sanitize_filename(self.timetable.meta.title_line1) + ".jpg"
        path_str, selected_filter = QFileDialog.getSaveFileName(
            self, "Export as Image", default_name, "JPEG Image (*.jpg);;PNG Image (*.png)"
        )
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix == "":
            path = path.with_suffix(".png" if "PNG" in selected_filter else ".jpg")

        ok = export_canvas_to_image(self.canvas, path, width=1800)
        if ok:
            QMessageBox.information(self, "Exported", f"Timetable image saved to:\n{path}")
        else:
            QMessageBox.critical(
                self, "Export failed", "Could not save the image. Check the location and try again."
            )

    # ------------------------------------------------------------------ #
    def closeEvent(self, event: QCloseEvent) -> None:
        self.storage.save(self.timetable)
        event.accept()
