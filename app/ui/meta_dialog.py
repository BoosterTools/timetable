from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.timetable import TimetableMeta
from app.utils.paths import get_logos_dir


class MetaDialog(QDialog):
    def __init__(self, meta: TimetableMeta, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Header & Footer")
        self.setMinimumWidth(440)
        self._logo_path = meta.logo_path

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.title1_edit = QLineEdit(meta.title_line1)
        form.addRow("Title (line 1):", self.title1_edit)

        self.title2_edit = QLineEdit(meta.title_line2)
        form.addRow("Title (line 2):", self.title2_edit)

        self.footer_left_edit = QLineEdit(meta.footer_left)
        form.addRow("Footer (left):", self.footer_left_edit)

        self.footer_right_edit = QLineEdit(meta.footer_right)
        form.addRow("Footer (right):", self.footer_right_edit)

        layout.addLayout(form)

        logo_row = QHBoxLayout()
        self.logo_status_label = QLabel(self._logo_status_text())
        logo_row.addWidget(self.logo_status_label, 1)
        choose_logo_btn = QPushButton("Choose Logo...")
        choose_logo_btn.clicked.connect(self._on_choose_logo)
        clear_logo_btn = QPushButton("Remove Logo")
        clear_logo_btn.clicked.connect(self._on_clear_logo)
        logo_row.addWidget(choose_logo_btn)
        logo_row.addWidget(clear_logo_btn)
        layout.addLayout(logo_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.result_data: dict = {}

    def _logo_status_text(self) -> str:
        return f"Logo: {Path(self._logo_path).name}" if self._logo_path else "No logo set"

    def _on_choose_logo(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Choose Logo Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path_str:
            return
        try:
            dest_dir = get_logos_dir()
            dest = dest_dir / Path(path_str).name
            if Path(path_str).resolve() != dest.resolve():
                shutil.copyfile(path_str, dest)
            self._logo_path = str(dest)
        except OSError as exc:
            QMessageBox.warning(self, "Could not use image", str(exc))
            return
        self.logo_status_label.setText(self._logo_status_text())

    def _on_clear_logo(self) -> None:
        self._logo_path = ""
        self.logo_status_label.setText(self._logo_status_text())

    def _on_save(self) -> None:
        self.result_data = {
            "title_line1": self.title1_edit.text().strip(),
            "title_line2": self.title2_edit.text().strip(),
            "footer_left": self.footer_left_edit.text().strip(),
            "footer_right": self.footer_right_edit.text().strip(),
            "logo_path": self._logo_path,
        }
        self.accept()
