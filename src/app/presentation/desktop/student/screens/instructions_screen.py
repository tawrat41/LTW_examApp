from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from app.application.student_exam import ExamInstructionView
from app.presentation.desktop.widgets.common import InfoField, MessageBanner, PrimaryButton, SectionHeader, card_container


class ExamInstructionsScreen(QWidget):
    start_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._exam: ExamInstructionView | None = None

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        self.header = SectionHeader("Exam Instructions", "Please review everything before starting.")
        layout.addWidget(self.header)
        
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        # Main content card
        content_card = card_container()
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)

        # Top grid for metadata
        self.meta_grid = QHBoxLayout()
        self.meta_grid.setSpacing(40)
        self.duration_info = InfoField("Duration", "0 min", "⏱")
        self.questions_info = InfoField("Questions", "0", "📝")
        self.nav_info = InfoField("Navigation", "Disabled", "🔄")
        self.meta_grid.addWidget(self.duration_info)
        self.meta_grid.addWidget(self.questions_info)
        self.meta_grid.addWidget(self.nav_info)
        self.meta_grid.addStretch(1)
        
        # Description
        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("font-size: 15px; color: #475569; line-height: 150%;")
        
        # Instructions list
        instr_header = QLabel("IMPORTANT INSTRUCTIONS")
        instr_header.setStyleSheet("font-size: 11px; font-weight: 800; color: #94A3B8; letter-spacing: 1px;")
        
        self.instructions_list = QListWidget()
        self.instructions_list.setSpacing(8)
        self.instructions_list.setStyleSheet("border: none; background: #F8FAFC; padding: 15px; border-radius: 12px;")
        
        content_layout.addLayout(self.meta_grid)
        content_layout.addWidget(self.desc_label)
        content_layout.addWidget(instr_header)
        content_layout.addWidget(self.instructions_list, 1)
        
        layout.addWidget(content_card, 1)

        # Footer actions
        actions = QHBoxLayout()
        self.back_button = QPushButton("Cancel & Back")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setFixedHeight(46)
        self.back_button.setStyleSheet("padding: 0 25px;")
        
        self.start_button = PrimaryButton("Start Exam Now")
        self.start_button.setFixedWidth(200)
        
        self.back_button.clicked.connect(self.back_requested.emit)
        self.start_button.clicked.connect(self.start_requested.emit)
        
        actions.addWidget(self.back_button)
        actions.addStretch(1)
        actions.addWidget(self.start_button)
        layout.addLayout(actions)

    def set_exam(self, exam: ExamInstructionView) -> None:
        self._exam = exam
        self.header.set_text("Exam Instructions", f"Preparing for: {exam.title}")
        self.duration_info.val_label.setText(f"{exam.time_limit_minutes} minutes")
        self.questions_info.val_label.setText(str(exam.question_count))
        self.nav_info.val_label.setText("Review Allowed" if exam.allow_previous else "Locked Sequence")
        
        self.desc_label.setText(exam.description or "No additional description provided.")
        
        self.instructions_list.clear()
        for item in exam.instructions:
            self.instructions_list.addItem(f"•  {item}")
