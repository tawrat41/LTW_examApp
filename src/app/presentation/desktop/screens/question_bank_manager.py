from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.application.question_bank import QuestionBankError, QuestionSearchFilters
from app.presentation.desktop.dialogs.question_editor_dialog import QuestionEditorDialog
from app.presentation.desktop.widgets.common import LoadingStrip, MessageBanner, PrimaryButton, SectionHeader, card_container


class QuestionBankManagerScreen(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        self._questions = []

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("Question Bank Manager", "Manual editing, filtering, and import access."))
        self.banner = MessageBanner()
        self.loading = LoadingStrip()
        layout.addWidget(self.banner)
        layout.addWidget(self.loading)

        filters_card = card_container()
        filters_layout = QHBoxLayout(filters_card)
        self.exam_combo = QComboBox()
        self.section_combo = QComboBox()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search question text or explanation")
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Category")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated tags")
        self.difficulty_spin = QSpinBox()
        self.difficulty_spin.setRange(0, 10)
        self.difficulty_spin.setSpecialValueText("Any")
        self.refresh_button = QPushButton("Search")
        self.refresh_button.clicked.connect(self.refresh)
        filters_layout.addWidget(QLabel("Exam"))
        filters_layout.addWidget(self.exam_combo)
        filters_layout.addWidget(QLabel("Section"))
        filters_layout.addWidget(self.section_combo)
        filters_layout.addWidget(self.search_edit, 2)
        filters_layout.addWidget(self.category_edit)
        filters_layout.addWidget(self.tags_edit)
        filters_layout.addWidget(QLabel("Difficulty"))
        filters_layout.addWidget(self.difficulty_spin)
        filters_layout.addWidget(self.refresh_button)
        layout.addWidget(filters_card)

        actions = QHBoxLayout()
        self.add_button = PrimaryButton("Add Question")
        self.edit_button = QPushButton("Edit Selected")
        self.delete_button = QPushButton("Delete Selected")
        self.add_button.clicked.connect(self._add_question)
        self.edit_button.clicked.connect(self._edit_selected)
        self.delete_button.clicked.connect(self._delete_selected)
        actions.addWidget(self.add_button)
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Question", "Category", "Difficulty", "Tags", "Marks", "Active"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table, 1)

        self.exam_combo.currentIndexChanged.connect(self._reload_sections)

    def refresh(self) -> None:
        self.banner.clear_message()
        self.loading.start("Loading questions...")
        self._load_exam_options()
        if self.exam_combo.currentData() is None:
            self.loading.stop()
            return
        filters = QuestionSearchFilters(
            exam_id=self.exam_combo.currentData(),
            query=self.search_edit.text().strip() or None,
            category_name=self.category_edit.text().strip() or None,
            difficulty_level=self.difficulty_spin.value() or None,
            tags=[item.strip() for item in self.tags_edit.text().split(",") if item.strip()],
        )
        self._questions = self._app_context.question_bank_service.search_questions(filters)
        self.table.setRowCount(0)
        for question in self._questions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(question.stem_text))
            self.table.setItem(row, 1, QTableWidgetItem(question.category_name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(str(question.difficulty_level)))
            self.table.setItem(row, 3, QTableWidgetItem(", ".join(question.tags)))
            self.table.setItem(row, 4, QTableWidgetItem(str(question.marks)))
            self.table.setItem(row, 5, QTableWidgetItem("Yes" if question.is_active else "No"))
        self.loading.stop()

    def _load_exam_options(self) -> None:
        current_exam_id = self.exam_combo.currentData()
        self.exam_combo.blockSignals(True)
        self.exam_combo.clear()
        for exam in self._app_context.admin_queries.list_exam_options():
            self.exam_combo.addItem(exam.label, exam.id)
        if current_exam_id:
            index = self.exam_combo.findData(current_exam_id)
            if index >= 0:
                self.exam_combo.setCurrentIndex(index)
        self.exam_combo.blockSignals(False)
        self._reload_sections()

    def _reload_sections(self) -> None:
        current_exam_id = self.exam_combo.currentData()
        self.section_combo.clear()
        if not current_exam_id:
            return
        for section in self._app_context.admin_queries.list_section_options(current_exam_id):
            self.section_combo.addItem(section.label, section.id)

    def _selected_question(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._questions):
            return None
        return self._questions[row]

    def _add_question(self) -> None:
        if not self.exam_combo.currentData() or not self.section_combo.currentData():
            self.banner.show_error("Create an exam first, then select its section.")
            return
        dialog = QuestionEditorDialog(
            exam_options=[
                item
                for item in self._app_context.admin_queries.list_exam_options()
                if item.id == self.exam_combo.currentData()
            ],
            section_options=[
                item
                for item in self._app_context.admin_queries.list_section_options(self.exam_combo.currentData())
                if item.id == self.section_combo.currentData()
            ]
            if self.exam_combo.currentData() and self.section_combo.currentData()
            else [],
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._app_context.question_bank_service.add_question(dialog.create_input())
        except QuestionBankError as exc:
            QMessageBox.warning(self, "Question Error", str(exc))
            return
        self.banner.show_success("Question added.")
        self.refresh()

    def _edit_selected(self) -> None:
        question = self._selected_question()
        if question is None:
            self.banner.show_error("Select a question first.")
            return
        dialog = QuestionEditorDialog(
            exam_options=[
                item
                for item in self._app_context.admin_queries.list_exam_options()
                if item.id == question.exam_id
            ],
            section_options=[
                item
                for item in self._app_context.admin_queries.list_section_options(question.exam_id)
                if item.id == question.section_id
            ],
            question=question,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._app_context.question_bank_service.edit_question(question.question_id, dialog.update_input())
        except QuestionBankError as exc:
            QMessageBox.warning(self, "Question Error", str(exc))
            return
        self.banner.show_success("Question updated.")
        self.refresh()

    def _delete_selected(self) -> None:
        question = self._selected_question()
        if question is None:
            self.banner.show_error("Select a question first.")
            return
        answer = QMessageBox.question(self, "Delete Question", "Delete the selected question?")
        if answer != QMessageBox.Yes:
            return
        self._app_context.question_bank_service.delete_question(question.question_id)
        self.banner.show_success("Question deleted.")
        self.refresh()
