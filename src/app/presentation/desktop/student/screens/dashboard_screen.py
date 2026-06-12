from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QGridLayout,
)

from app.presentation.desktop.widgets.common import ExamCard, MessageBanner, PrimaryButton, SectionHeader, card_container


class StudentDashboardScreen(QWidget):
    exam_selected = Signal(str)

    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        self._exams = []

        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Top Header
        self.header = SectionHeader("Dashboard", "Welcome! Select an active exam to begin.")
        layout.addWidget(self.header)
        
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        # Scroll area for cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(30)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

        # Footer actions
        footer_card = card_container()
        footer_card.setFixedHeight(70)
        footer_layout = QHBoxLayout(footer_card)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        
        self.refresh_button = QPushButton("↻  Refresh Exam List")
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.setFixedWidth(180)
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.clicked.connect(self.refresh)
        
        footer_layout.addWidget(QLabel("Don't see your exam? Try refreshing."))
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.refresh_button)
        layout.addWidget(footer_card)

    def set_student_name(self, name: str) -> None:
        self.header.set_text("Dashboard", f"Welcome back, {name}! Ready for your next challenge?")

    def refresh(self) -> None:
        self.banner.clear_message()
        self._exams = self._app_context.exam_portal.list_available_exams()
        
        # Clear current grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        if not self._exams:
            self.banner.show_error("No active exams are available right now. Check back later!")
            return

        for index, exam in enumerate(self._exams):
            card = ExamCard(
                exam_id=exam.exam_id,
                title=exam.title,
                code=exam.code,
                subject=exam.subject,
                duration=exam.time_limit_minutes,
                questions=exam.question_count
            )
            card.clicked.connect(self.exam_selected.emit)
            
            # 3 columns grid
            self.grid_layout.addWidget(card, index // 3, index % 3)
