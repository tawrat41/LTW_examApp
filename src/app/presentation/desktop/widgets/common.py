from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setProperty("variant", "primary")
        self.style().polish(self)


class MessageBanner(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self.hide()
        self.setWordWrap(True)

    def show_error(self, message: str) -> None:
        self.setProperty("role", "error")
        self.setText(message)
        self.show()
        self.style().polish(self)

    def show_success(self, message: str) -> None:
        self.setProperty("role", "success")
        self.setText(message)
        self.show()
        self.style().polish(self)

    def clear_message(self) -> None:
        self.clear()
        self.hide()


class SectionHeader(QFrame):
    def __init__(self, title: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("sectionSubtitle")
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)

    def set_text(self, title: str, subtitle: str) -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)


class StatCard(QFrame):
    def __init__(self, title: str, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setObjectName("statCard")
        self._value_label = QLabel("0")
        self._value_label.setStyleSheet(f"font-size: 30px; font-weight: 700; color: {accent};")
        title_label = QLabel(title)
        title_label.setProperty("role", "muted")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(title_label)
        layout.addWidget(self._value_label)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)


class LoadingStrip(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._label = QLabel("Working...")
        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setMaximumHeight(12)
        layout.addWidget(self._label)
        layout.addWidget(self._bar, 1)
        self.hide()

    def start(self, message: str) -> None:
        self._label.setText(message)
        self.show()

    def stop(self) -> None:
        self.hide()


def card_container() -> QFrame:
    frame = QFrame()
    frame.setProperty("class", "card")
    return frame
