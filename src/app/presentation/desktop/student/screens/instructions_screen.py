from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget

from app.application.student_exam import ExamInstructionView
from app.presentation.desktop.widgets.common import MessageBanner, PrimaryButton, SectionHeader, card_container


class ExamInstructionsScreen(QWidget):
    start_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._exam: ExamInstructionView | None = None

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        self.header = SectionHeader("Exam Instructions", "Review the instructions before you begin.")
        layout.addWidget(self.header)
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        info_card = card_container()
        info_layout = QVBoxLayout(info_card)
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-size: 14px;")
        self.instructions_list = QListWidget()
        info_layout.addWidget(self.summary_label)
        info_layout.addWidget(self.instructions_list)
        layout.addWidget(info_card, 1)

        self.back_button = PrimaryButton("Back")
        self.back_button.setProperty("variant", "")
        self.start_button = PrimaryButton("Start Exam")
        self.back_button.clicked.connect(self.back_requested.emit)
        self.start_button.clicked.connect(self.start_requested.emit)
        layout.addWidget(self.back_button)
        layout.addWidget(self.start_button)

    def set_exam(self, exam: ExamInstructionView) -> None:
        self._exam = exam
        self.summary_label.setText(
            f"{exam.title} ({exam.code})\n"
            f"Duration: {exam.time_limit_minutes} minutes\n"
            f"Questions: {exam.question_count}\n"
            f"Previous navigation: {'Allowed' if exam.allow_previous else 'Disabled'}\n\n"
            f"{exam.description or ''}"
        )
        self.instructions_list.clear()
        for item in exam.instructions:
            self.instructions_list.addItem(item)
