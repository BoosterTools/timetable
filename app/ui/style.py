"""
A single, permanent light stylesheet for the whole application.

There is deliberately no dark variant and no theme switch anywhere in this
app — every window, dialog, and widget always uses this light palette,
regardless of the OS's own dark-mode setting, so the app can never
accidentally end up looking dark.
"""
from __future__ import annotations

LIGHT_STYLESHEET = """
* {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #1D1E24;
}
QMainWindow, QDialog, QWidget {
    background: #F7F7FA;
}
QToolBar {
    background: #FFFFFF;
    border-bottom: 1px solid #E3E5EC;
    spacing: 6px;
    padding: 6px;
}
QStatusBar {
    background: #FFFFFF;
    border-top: 1px solid #E3E5EC;
}
QPushButton {
    background: #FFFFFF;
    border: 1px solid #D6D8E0;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover {
    background: #F0F0F5;
}
QPushButton:pressed {
    background: #E4E4EC;
}
QPushButton#Primary {
    background: #6C5CE7;
    color: white;
    border: none;
    font-weight: 600;
}
QPushButton#Primary:hover {
    background: #7C6CF5;
}
QLineEdit, QComboBox, QListWidget, QPlainTextEdit {
    background: #FFFFFF;
    border: 1px solid #D6D8E0;
    border-radius: 6px;
    padding: 5px 8px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #6C5CE7;
}
QScrollArea {
    background: #FFFFFF;
    border: none;
}
QMenu {
    background: #FFFFFF;
    border: 1px solid #D6D8E0;
}
QMenu::item:selected {
    background: #6C5CE7;
    color: white;
}
QToolTip {
    background: #FFFFFF;
    color: #1D1E24;
    border: 1px solid #D6D8E0;
    padding: 4px 8px;
}
"""
