from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget


class NavigationRail(QWidget):
    page_requested = Signal(str)

    def __init__(self, items: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addStretch(0)
        for page_id, label in items:
            button = QPushButton(label)
            button.setProperty("nav", "true")
            button.clicked.connect(lambda _checked=False, key=page_id: self.page_requested.emit(key))
            layout.addWidget(button)
            self._buttons[page_id] = button
        layout.addStretch(1)

    def set_active(self, page_id: str) -> None:
        for key, button in self._buttons.items():
            button.setProperty("active", "true" if key == page_id else "false")
            button.style().polish(button)
