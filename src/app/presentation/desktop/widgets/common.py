from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class Badge(QLabel):
    def __init__(self, text: str, color: str = "#4F46E5", bg: str = "#EEF2FF", parent: QWidget | None = None) -> None:
        super().__init__(text.upper(), parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(24)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {color};
                border-radius: 12px;
                padding: 0px 15px;
                font-size: 11px;
                font-weight: 800;
                border: 1px solid {color}44;
            }}
        """)


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #6366F1);
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 10px 24px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #4338CA;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338CA, stop:1 #4F46E5);
            }
            QPushButton:pressed {
                background-color: #3730A3;
            }
        """)
        self.style().polish(self)


class MessageBanner(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self.hide()
        self.setWordWrap(True)
        self.setMinimumHeight(50)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("font-weight: 600; border-radius: 12px; font-size: 14px;")

    def show_error(self, message: str) -> None:
        self.setProperty("role", "error")
        self.setText(f"⚠  {message}")
        self.show()
        self.style().polish(self)

    def show_success(self, message: str) -> None:
        self.setProperty("role", "success")
        self.setText(f"✓  {message}")
        self.show()
        self.style().polish(self)

    def clear_message(self) -> None:
        self.clear()
        self.hide()


class SectionHeader(QFrame):
    def __init__(self, title: str, subtitle: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(8)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 32px; font-weight: 800; color: #0F172A; letter-spacing: -1px; background: transparent; border: none;")
        self.title_label.setAlignment(Qt.AlignLeft)
        
        # Add a subtle gradient line under the title
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 transparent); max-height: 4px; border: none; min-width: 80px; max-width: 80px; border-radius: 2px;")
        
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("font-size: 15px; font-weight: 500; color: #64748B; background: transparent; border: none;")
        self.subtitle_label.setAlignment(Qt.AlignLeft)
        
        layout.addWidget(self.title_label)
        layout.addWidget(line)
        layout.addWidget(self.subtitle_label)

    def set_text(self, title: str, subtitle: str) -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)


class StatsWidget(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setStyleSheet("background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(20)
        
        self.answered_lbl = InfoField("Answered", "0", "✅")
        self.remaining_lbl = InfoField("Remaining", "0", "⏳")
        
        layout.addWidget(self.answered_lbl)
        # Vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("background: #E2E8F0; max-width: 1px; border: none;")
        layout.addWidget(sep)
        layout.addWidget(self.remaining_lbl)

    def update_stats(self, answered: int, total: int) -> None:
        self.answered_lbl.val_label.setText(str(answered))
        self.remaining_lbl.val_label.setText(str(total - answered))


class StatCard(QFrame):
    def __init__(self, title: str, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setObjectName("statCard")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(Qt.GlobalColor.black if hasattr(Qt, 'GlobalColor') else Qt.black)
        shadow.color().setAlpha(20)
        self.setGraphicsEffect(shadow)

        self._value_label = QLabel("0")
        self._value_label.setStyleSheet(f"font-size: 36px; font-weight: 800; color: {accent}; letter-spacing: -1.5px;")
        
        title_label = QLabel(title.upper())
        title_label.setProperty("role", "muted")
        title_label.setStyleSheet("font-size: 11px; font-weight: 800; letter-spacing: 1px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)
        layout.addWidget(title_label)
        layout.addWidget(self._value_label)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)


class LoadingStrip(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 10px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(15)
        self._label = QLabel("Working...")
        self._label.setStyleSheet("font-weight: 700; color: #4338CA;")
        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setMaximumHeight(6)
        layout.addWidget(self._label)
        layout.addWidget(self._bar, 1)
        self.hide()

    def start(self, message: str) -> None:
        self._label.setText(message)
        self.show()

    def stop(self) -> None:
        self.hide()


class InfoField(QFrame):
    def __init__(self, label: str, value: str, icon: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        lbl = QLabel(label.upper())
        lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748B; letter-spacing: 1px;")
        
        val_layout = QHBoxLayout()
        val_layout.setContentsMargins(0, 0, 0, 0)
        val_layout.setSpacing(8)
        if icon:
            ico = QLabel(icon)
            ico.setFixedSize(20, 20)
            ico.setAlignment(Qt.AlignCenter)
            ico.setStyleSheet("font-size: 14px; background: #F1F5F9; border-radius: 4px;")
            val_layout.addWidget(ico)
        
        self.val_label = QLabel(value)
        self.val_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1E293B;")
        val_layout.addWidget(self.val_label)
        val_layout.addStretch(1)
        
        layout.addWidget(lbl)
        layout.addLayout(val_layout)


class ExamCard(QFrame):
    clicked = Signal(str)

    def __init__(self, exam_id: str, title: str, code: str, subject: str, duration: int, questions: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.exam_id = exam_id
        self.setProperty("class", "card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(320, 200)
        self.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
            QFrame:hover {
                border: 2px solid #6366F1;
                background: #F8FAFC;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(0)

        # Header: Title and Code Badge
        header = QHBoxLayout()
        header.setSpacing(10)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A; border: none; background: transparent;")
        header.addWidget(self.title_label)
        header.addStretch(1)
        
        self.code_badge = Badge(code, color="#6366F1", bg="#EEF2FF")
        header.addWidget(self.code_badge)
        main_layout.addLayout(header)
        
        main_layout.addSpacing(25)
        
        # Content Grid for metadata
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.addWidget(InfoField("Subject", subject, "📚"), 0, 0)
        grid.addWidget(InfoField("Time Limit", f"{duration} min", "⏱"), 1, 0)
        grid.addWidget(InfoField("Questions", f"{questions} items", "📝"), 1, 1)
        
        main_layout.addLayout(grid)
        main_layout.addStretch(1)

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        self.clicked.emit(self.exam_id)


class ActionCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, subtitle: str, icon: str, color: str = "#4F46E5", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(120)
        self.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }}
            QFrame:hover {{
                border: 2px solid {color};
                background: {color}05;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        ico = QLabel(icon)
        ico.setFixedSize(50, 50)
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet(f"font-size: 24px; background: {color}15; border-radius: 12px; color: {color};")
        
        txt_layout = QVBoxLayout()
        txt_layout.setSpacing(4)
        
        ttl = QLabel(title)
        ttl.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A; background: transparent; border: none;")
        
        sub = QLabel(subtitle)
        sub.setStyleSheet("font-size: 13px; font-weight: 500; color: #64748B; background: transparent; border: none;")
        
        txt_layout.addStretch(1)
        txt_layout.addWidget(ttl)
        txt_layout.addWidget(sub)
        txt_layout.addStretch(1)
        
        layout.addWidget(ico)
        layout.addLayout(txt_layout)
        layout.addStretch(1)
        
        arr = QLabel("→")
        arr.setStyleSheet(f"font-size: 20px; color: {color}; font-weight: 800; background: transparent; border: none;")
        layout.addWidget(arr)

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        self.clicked.emit()


class QuickLink(QPushButton):
    def __init__(self, text: str, icon: str, parent: QWidget | None = None) -> None:
        super().__init__(f" {icon}  {text}", parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QPushButton {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                color: #475569;
                font-weight: 600;
                text-align: left;
                padding: 0 15px;
            }
            QPushButton:hover {
                background: #F1F5F9;
                border-color: #CBD5E1;
                color: #1E293B;
            }
        """)


def card_container() -> QFrame:
    frame = QFrame()
    frame.setProperty("class", "card")
    return frame
