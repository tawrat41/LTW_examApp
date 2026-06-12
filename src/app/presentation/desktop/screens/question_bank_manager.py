from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
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
from app.presentation.desktop.widgets.common import (
    Badge,
    LoadingStrip,
    MessageBanner,
    PrimaryButton,
    SectionHeader,
    card_container,
)


class QuestionBankManagerScreen(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        self._questions = []

        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(30, 30, 30, 30)
        
        self.header = SectionHeader("Question Bank Manager", "Review, edit, and filter your adaptive question repository.")
        layout.addWidget(self.header)
        
        self.banner = MessageBanner()
        self.loading = LoadingStrip()
        layout.addWidget(self.banner)
        layout.addWidget(self.loading)

        # Modern Filter Panel
        filter_card = card_container()
        filter_card.setStyleSheet("background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;")
        filter_layout = QVBoxLayout(filter_card)
        filter_layout.setContentsMargins(25, 25, 25, 25)
        filter_layout.setSpacing(20)
        
        # Grid layout for inputs
        grid = QGridLayout()
        grid.setSpacing(20)
        
        def add_filter(label_text, widget, row, col, span=1):
            v = QVBoxLayout()
            v.setSpacing(8)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 1px; border: none; background: transparent;")
            v.addWidget(lbl)
            v.addWidget(widget)
            grid.addLayout(v, row, col, 1, span)

        self.exam_combo = QComboBox()
        self.exam_combo.addItem("All Exams", None)
        self.exam_combo.setMinimumHeight(42)
        
        self.section_combo = QComboBox()
        self.section_combo.addItem("All Sections", None)
        self.section_combo.setMinimumHeight(42)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search question content...")
        self.search_edit.setMinimumHeight(42)
        
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Filter by category...")
        self.category_edit.setMinimumHeight(42)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Filter by tags...")
        self.tags_edit.setMinimumHeight(42)
        
        self.difficulty_spin = QSpinBox()
        self.difficulty_spin.setRange(0, 10)
        self.difficulty_spin.setSpecialValueText("Any Difficulty")
        self.difficulty_spin.setMinimumHeight(42)
        
        add_filter("Exam Type", self.exam_combo, 0, 0)
        add_filter("Section", self.section_combo, 0, 1)
        add_filter("Search Keyword", self.search_edit, 0, 2)
        
        add_filter("Category", self.category_edit, 1, 0)
        add_filter("Tags", self.tags_edit, 1, 1)
        add_filter("Difficulty", self.difficulty_spin, 1, 2)
        
        # Inactive Filter
        self.show_inactive_check = QCheckBox("Show Inactive Questions")
        self.show_inactive_check.setStyleSheet("font-weight: 600; color: #64748B; border: none; background: transparent;")
        
        filter_layout.addLayout(grid)
        
        # Action Row
        btns = QHBoxLayout()
        btns.addWidget(self.show_inactive_check)
        btns.addStretch(1)
        
        self.refresh_button = PrimaryButton("Search Repository")
        self.refresh_button.setFixedWidth(220)
        self.refresh_button.clicked.connect(self.refresh)
        
        btns.addWidget(self.refresh_button)
        filter_layout.addLayout(btns)
        
        layout.addWidget(filter_card)

        # Actions Row
        actions = QHBoxLayout()
        self.add_button = PrimaryButton("+  Add New Question")
        self.add_button.setFixedWidth(180)
        self.edit_button = QPushButton("Edit Selected")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet("color: #DC2626;")
        
        self.add_button.clicked.connect(self._add_question)
        self.edit_button.clicked.connect(self._edit_selected)
        self.delete_button.clicked.connect(self._delete_selected)
        
        actions.addWidget(self.add_button)
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["QUESTION STEM", "CATEGORY", "LEVEL", "TAGS", "MARKS", "STATUS"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { border-radius: 12px; }")
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
            include_inactive=self.show_inactive_check.isChecked(),
        )
        self._questions = self._app_context.question_bank_service.search_questions(filters)
        self.table.setRowCount(0)
        self.table.verticalHeader().setVisible(False)
        
        for question in self._questions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Question Stem (Main info)
            item = QTableWidgetItem(question.stem_text)
            item.setToolTip(question.stem_text)
            self.table.setItem(row, 0, item)
            
            # Category
            self.table.setItem(row, 1, QTableWidgetItem(question.category_name or "General"))
            
            # Difficulty Level as Badge
            level = question.difficulty_level
            level_widget = QWidget()
            level_layout = QHBoxLayout(level_widget)
            level_layout.setContentsMargins(10, 5, 10, 5)
            
            if level >= 3:
                badge = Badge("HARD", color="#DC2626", bg="#FEF2F2")
            elif level == 2:
                badge = Badge("MED", color="#D97706", bg="#FFFBEB")
            else:
                badge = Badge("EASY", color="#16A34A", bg="#F0FDF4")
            
            self.table.setCellWidget(row, 2, badge)
            
            # Tags
            self.table.setItem(row, 3, QTableWidgetItem(", ".join(question.tags)))
            
            # Marks
            marks_item = QTableWidgetItem(f"{question.marks:.1f}")
            marks_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, marks_item)
            
            # Status as Badge
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(10, 5, 10, 5)
            if question.is_active:
                status_badge = Badge("ACTIVE", color="#4F46E5", bg="#EEF2FF")
            else:
                status_badge = Badge("INACTIVE", color="#94A3B8", bg="#F1F5F9")
            self.table.setCellWidget(row, 5, status_badge)

        # Set column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 120)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 120)
        
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
