from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.application.admin import LookupItem
from app.application.question_bank import CreateQuestionInput, QuestionOptionInput, QuestionView, UpdateQuestionInput
from app.presentation.desktop.widgets.common import MessageBanner, PrimaryButton, SectionHeader, card_container


class _OptionRow(QWidget):
    def __init__(self, key: str, text: str = "", is_correct: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        self.setStyleSheet("""
            QWidget {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        
        self.key_edit = QLineEdit(key)
        self.key_edit.setPlaceholderText("A")
        self.key_edit.setFixedWidth(50)
        self.key_edit.setAlignment(Qt.AlignCenter)
        self.key_edit.setStyleSheet("font-weight: 800; color: #4F46E5; background: #EEF2FF; border-color: #C7D2FE;")
        
        self.text_edit = QLineEdit(text)
        self.text_edit.setPlaceholderText("Enter option text...")
        self.text_edit.setStyleSheet("background: #FFFFFF;")
        
        self.correct_check = QCheckBox("Mark as Correct")
        self.correct_check.setChecked(is_correct)
        self.correct_check.setCursor(Qt.PointingHandCursor)
        
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
        self.resize(1000, 850)
        self.setStyleSheet("background: #F8FAFC;")
        self._question = question
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 20, 30, 20)
        title = "Edit Question" if question else "New Question"
        header_layout.addWidget(SectionHeader(title, "Define question stem, options, and metadata."))
        main_layout.addWidget(header_widget)
        
        # Scroll Area for Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(24)
        
        self.banner = MessageBanner()
        content_layout.addWidget(self.banner)
        
        # Section 1: Metadata Card
        meta_card = card_container()
        meta_layout = QGridLayout(meta_card)
        meta_layout.setContentsMargins(20, 20, 20, 20)
        meta_layout.setSpacing(15)
        
        def add_field(label_text, widget, row, col):
            v = QVBoxLayout()
            v.setSpacing(6)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;")
            v.addWidget(lbl)
            v.addWidget(widget)
            meta_layout.addLayout(v, row, col)

        self.exam_combo = QComboBox()
        for item in exam_options:
            self.exam_combo.addItem(item.label, item.id)
        self.section_combo = QComboBox()
        for item in section_options:
            self.section_combo.addItem(item.label, item.id)
            
        self.category_edit = QLineEdit()
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, ...")
        
        self.difficulty_spin = QSpinBox()
        self.difficulty_spin.setRange(1, 10)
        self.marks_spin = QSpinBox()
        self.marks_spin.setRange(1, 100)
        
        add_field("EXAM", self.exam_combo, 0, 0)
        add_field("SECTION", self.section_combo, 0, 1)
        add_field("CATEGORY", self.category_edit, 1, 0)
        add_field("TAGS", self.tags_edit, 1, 1)
        add_field("DIFFICULTY LEVEL", self.difficulty_spin, 2, 0)
        add_field("MARKS", self.marks_spin, 2, 1)
        
        content_layout.addWidget(meta_card)
        
        # Section 2: Question Stem
        stem_card = card_container()
        stem_layout = QVBoxLayout(stem_card)
        stem_lbl = QLabel("QUESTION CONTENT")
        stem_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;")
        self.stem_edit = QPlainTextEdit()
        self.stem_edit.setPlaceholderText("Enter the main question text here...")
        self.stem_edit.setMinimumHeight(120)
        stem_layout.addWidget(stem_lbl)
        stem_layout.addWidget(self.stem_edit)
        content_layout.addWidget(stem_card)
        
        # Section 3: Options
        options_card = card_container()
        options_layout_outer = QVBoxLayout(options_card)
        opt_lbl = QLabel("ANSWER OPTIONS")
        opt_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;")
        options_layout_outer.addWidget(opt_lbl)
        
        self.options_host = QWidget()
        self.options_layout = QVBoxLayout(self.options_host)
        self.options_layout.setContentsMargins(0, 10, 0, 0)
        self.options_layout.setSpacing(10)
        self._option_rows: list[_OptionRow] = []
        options_layout_outer.addWidget(self.options_host)
        content_layout.addWidget(options_card)
        
        # Section 4: Explanation & Visibility
        footer_card = card_container()
        footer_layout = QVBoxLayout(footer_card)
        exp_lbl = QLabel("EXPLANATION (OPTIONAL)")
        exp_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;")
        self.explanation_edit = QPlainTextEdit()
        self.explanation_edit.setPlaceholderText("Provide an explanation for the correct answer...")
        self.explanation_edit.setMinimumHeight(80)
        self.is_active_check = QCheckBox("Question is active and available for exams")
        self.is_active_check.setChecked(True)
        
        footer_layout.addWidget(exp_lbl)
        footer_layout.addWidget(self.explanation_edit)
        footer_layout.addWidget(self.is_active_check)
        content_layout.addWidget(footer_card)
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Dialog Footer
        dialog_footer = QWidget()
        dialog_footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        footer_btn_layout = QHBoxLayout(dialog_footer)
        footer_btn_layout.setContentsMargins(30, 20, 30, 20)
        
        save_btn = PrimaryButton("Save Question")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setFixedWidth(120)
        
        footer_btn_layout.addStretch(1)
        footer_btn_layout.addWidget(cancel_btn)
        footer_btn_layout.addWidget(save_btn)
        main_layout.addWidget(dialog_footer)

        if question is None:
            self._build_default_options()
        else:
            self._load_question(question)

    def _build_default_options(self) -> None:
        for index, key in enumerate(["A", "B", "C", "D"]):
            row = _OptionRow(key)
            self.options_layout.addWidget(row)
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
            self.options_layout.addWidget(row)
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
