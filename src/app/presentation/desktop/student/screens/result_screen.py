from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.application.student_exam import ExamResultView
from app.presentation.desktop.widgets.common import PrimaryButton, SectionHeader, StatCard


class StudentResultScreen(QWidget):
    back_to_dashboard_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        self.header = SectionHeader("Result", "Your exam attempt is complete.")
        layout.addWidget(self.header)
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        self.score_card = StatCard("Score", "#0f9d58")
        self.percent_card = StatCard("Percentage", "#127fbf")
        self.correct_card = StatCard("Correct Answers", "#d96c06")
        layout.addWidget(self.score_card)
        layout.addWidget(self.percent_card)
        layout.addWidget(self.correct_card)
        self.back_button = PrimaryButton("Back to Dashboard")
        self.back_button.clicked.connect(self.back_to_dashboard_requested.emit)
        layout.addWidget(self.back_button)
        layout.addStretch(1)

    def set_result(self, result: ExamResultView) -> None:
        self.summary_label.setText(
            f"{result.exam_title}\n"
            f"Answered: {result.answered_questions}/{result.total_questions}\n"
            f"Wrong answers: {result.wrong_answers}"
        )
        self.score_card.set_value(f"{result.score:.2f}")
        self.percent_card.set_value(f"{result.percentage:.1f}%")
        self.correct_card.set_value(str(result.correct_answers))
