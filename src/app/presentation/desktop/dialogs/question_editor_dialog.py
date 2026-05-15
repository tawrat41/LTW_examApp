from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.application.admin import LookupItem
from app.application.question_bank import CreateQuestionInput, QuestionOptionInput, QuestionView, UpdateQuestionInput
from app.presentation.desktop.widgets.common import MessageBanner


class _OptionRow(QWidget):
    def __init__(self, key: str, text: str = "", is_correct: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.key_edit = QLineEdit(key)
        self.key_edit.setMaximumWidth(60)
        self.text_edit = QLineEdit(text)
        self.correct_check = QCheckBox("Correct")
        self.correct_check.setChecked(is_correct)
        layout.addWidget(QLabel("Key"))
        layout.addWidget(self.key_edit)
        layout.addWidget(self.text_edit, 1)
        layout.addWidget(self.correct_check)

    def to_input(self) -> QuestionOptionInput:
        return QuestionOptionInput(
            key=self.key_edit.text().strip().upper(),
            text=self.text_edit.text().strip(),
            is_correct=self.correct_check.isChecked(),
        )


class QuestionEditorDialog(QDialog):
    def __init__(
        self,
        *,
        exam_options: list[LookupItem],
        section_options: list[LookupItem],
        question: QuestionView | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Question Editor")
        self.resize(860, 620)
        self._question = question
        layout = QVBoxLayout(self)
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignTop)
        self.exam_combo = QComboBox()
        for item in exam_options:
            self.exam_combo.addItem(item.label, item.id)
        self.section_combo = QComboBox()
        for item in section_options:
            self.section_combo.addItem(item.label, item.id)
        self.exam_combo.setEnabled(len(exam_options) > 1)
        self.section_combo.setEnabled(len(section_options) > 1)
        self.category_edit = QLineEdit()
        self.tags_edit = QLineEdit()
        self.difficulty_spin = QSpinBox()
        self.difficulty_spin.setRange(1, 10)
        self.marks_spin = QSpinBox()
        self.marks_spin.setRange(1, 100)
        self.stem_edit = QPlainTextEdit()
        self.explanation_edit = QPlainTextEdit()
        self.is_active_check = QCheckBox("Active")
        self.is_active_check.setChecked(True)

        form.addRow("Exam", self.exam_combo)
        form.addRow("Section", self.section_combo)
        form.addRow("Category", self.category_edit)
        form.addRow("Tags", self.tags_edit)
        form.addRow("Difficulty", self.difficulty_spin)
        form.addRow("Marks", self.marks_spin)
        form.addRow("Question", self.stem_edit)
        form.addRow("Explanation", self.explanation_edit)
        form.addRow("", self.is_active_check)
        layout.addLayout(form)

        options_label = QLabel("Options")
        options_label.setStyleSheet("font-weight: 700;")
        layout.addWidget(options_label)
        self.options_host = QWidget()
        self.options_layout = QGridLayout(self.options_host)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setHorizontalSpacing(12)
        self._option_rows: list[_OptionRow] = []
        layout.addWidget(self.options_host)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if question is None:
            self._build_default_options()
        else:
            self._load_question(question)

    def _build_default_options(self) -> None:
        for index, key in enumerate(["A", "B", "C", "D"]):
            row = _OptionRow(key)
            self.options_layout.addWidget(row, index // 2, index % 2)
            self._option_rows.append(row)
        self.marks_spin.setValue(1)
        self.difficulty_spin.setValue(1)

    def _load_question(self, question: QuestionView) -> None:
        self.stem_edit.setPlainText(question.stem_text)
        self.category_edit.setText(question.category_name or "")
        self.tags_edit.setText(", ".join(question.tags))
        self.difficulty_spin.setValue(question.difficulty_level)
        self.marks_spin.setValue(int(question.marks))
        self.explanation_edit.setPlainText(question.explanation_text or "")
        self.is_active_check.setChecked(question.is_active)
        for index in range(self.exam_combo.count()):
            if self.exam_combo.itemData(index) == question.exam_id:
                self.exam_combo.setCurrentIndex(index)
                break
        for index in range(self.section_combo.count()):
            if self.section_combo.itemData(index) == question.section_id:
                self.section_combo.setCurrentIndex(index)
                break
        for index, option in enumerate(question.options):
            row = _OptionRow(option.key, option.text, option.is_correct)
            self.options_layout.addWidget(row, index // 2, index % 2)
            self._option_rows.append(row)
        self.exam_combo.setEnabled(False)
        self.section_combo.setEnabled(False)

    def create_input(self) -> CreateQuestionInput:
        return CreateQuestionInput(
            exam_id=self.exam_combo.currentData(),
            section_id=self.section_combo.currentData(),
            stem_text=self.stem_edit.toPlainText().strip(),
            options=[row.to_input() for row in self._option_rows],
            category_name=self.category_edit.text().strip() or None,
            difficulty_level=self.difficulty_spin.value(),
            explanation_text=self.explanation_edit.toPlainText().strip() or None,
            tags=[tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()],
            marks=float(self.marks_spin.value()),
            is_active=self.is_active_check.isChecked(),
        )

    def update_input(self) -> UpdateQuestionInput:
        return UpdateQuestionInput(
            stem_text=self.stem_edit.toPlainText().strip(),
            options=[row.to_input() for row in self._option_rows],
            category_name=self.category_edit.text().strip() or None,
            difficulty_level=self.difficulty_spin.value(),
            explanation_text=self.explanation_edit.toPlainText().strip() or None,
            tags=[tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()],
            marks=float(self.marks_spin.value()),
            is_active=self.is_active_check.isChecked(),
        )
