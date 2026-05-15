from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
)

from app.application.exams import CreateExamInput, ExamView, UpdateExamInput
from app.presentation.desktop.widgets.common import MessageBanner


class ExamEditorDialog(QDialog):
    def __init__(self, created_by_user_id: str, exam: ExamView | None = None, parent=None) -> None:
        super().__init__(parent)
        self._created_by_user_id = created_by_user_id
        self._exam = exam
        self.setWindowTitle("Exam Editor")
        self.resize(520, 460)
        layout = QVBoxLayout(self)
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        form = QFormLayout()
        self.code_edit = QLineEdit()
        self.title_edit = QLineEdit()
        self.description_edit = QPlainTextEdit()
        self.subject_edit = QLineEdit("English")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["draft", "active", "archived"])
        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setRange(1, 300)
        self.time_limit_spin.setValue(30)
        self.min_questions_spin = QSpinBox()
        self.min_questions_spin.setRange(1, 500)
        self.min_questions_spin.setValue(10)
        self.max_questions_spin = QSpinBox()
        self.max_questions_spin.setRange(1, 500)
        self.max_questions_spin.setValue(20)
        self.passing_score_spin = QDoubleSpinBox()
        self.passing_score_spin.setRange(0, 1000)
        self.passing_score_spin.setDecimals(2)
        form.addRow("Code", self.code_edit)
        form.addRow("Title", self.title_edit)
        form.addRow("Description", self.description_edit)
        form.addRow("Subject", self.subject_edit)
        form.addRow("Status", self.status_combo)
        form.addRow("Time Limit", self.time_limit_spin)
        form.addRow("Min Questions", self.min_questions_spin)
        form.addRow("Max Questions", self.max_questions_spin)
        form.addRow("Passing Score", self.passing_score_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if exam is not None:
            self.code_edit.setText(exam.code)
            self.code_edit.setEnabled(False)
            self.title_edit.setText(exam.title)
            self.description_edit.setPlainText(exam.description or "")
            self.subject_edit.setText(exam.subject)
            self.status_combo.setCurrentText(exam.status)
            self.time_limit_spin.setValue(exam.time_limit_minutes)
            self.min_questions_spin.setValue(exam.min_questions)
            self.max_questions_spin.setValue(exam.max_questions)
            self.passing_score_spin.setValue(exam.passing_score)

    def create_input(self) -> CreateExamInput:
        return CreateExamInput(
            code=self.code_edit.text().strip(),
            title=self.title_edit.text().strip(),
            description=self.description_edit.toPlainText().strip() or None,
            subject=self.subject_edit.text().strip() or "English",
            created_by_user_id=self._created_by_user_id,
            time_limit_minutes=self.time_limit_spin.value(),
            min_questions=self.min_questions_spin.value(),
            max_questions=self.max_questions_spin.value(),
            passing_score=float(self.passing_score_spin.value()),
        )

    def update_input(self) -> UpdateExamInput:
        return UpdateExamInput(
            title=self.title_edit.text().strip(),
            description=self.description_edit.toPlainText().strip() or None,
            subject=self.subject_edit.text().strip() or "English",
            status=self.status_combo.currentText(),
            time_limit_minutes=self.time_limit_spin.value(),
            min_questions=self.min_questions_spin.value(),
            max_questions=self.max_questions_spin.value(),
            passing_score=float(self.passing_score_spin.value()),
        )
