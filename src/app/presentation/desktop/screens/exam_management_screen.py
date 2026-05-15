from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.application.exams import ExamManagementError, ExamSearchFilters
from app.presentation.desktop.dialogs.exam_editor_dialog import ExamEditorDialog
from app.presentation.desktop.widgets.common import MessageBanner, PrimaryButton, SectionHeader, card_container


class ExamManagementScreen(QWidget):
    def __init__(self, app_context, get_current_user_id, on_exams_changed, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        self._get_current_user_id = get_current_user_id
        self._on_exams_changed = on_exams_changed
        self._exams = []

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("Exam Management", "Manage exam definitions and baseline settings."))
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        filters_card = card_container()
        filters_layout = QHBoxLayout(filters_card)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search code, title, or description")
        self.status_combo = QComboBox()
        self.status_combo.addItem("Any", None)
        self.status_combo.addItem("Draft", "draft")
        self.status_combo.addItem("Active", "active")
        self.status_combo.addItem("Archived", "archived")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.refresh)
        filters_layout.addWidget(self.search_edit, 1)
        filters_layout.addWidget(self.status_combo)
        filters_layout.addWidget(search_button)
        layout.addWidget(filters_card)

        actions = QHBoxLayout()
        add_button = PrimaryButton("Add Exam")
        edit_button = QPushButton("Edit Selected")
        delete_button = QPushButton("Delete Selected")
        add_button.clicked.connect(self._add_exam)
        edit_button.clicked.connect(self._edit_exam)
        delete_button.clicked.connect(self._delete_exam)
        actions.addWidget(add_button)
        actions.addWidget(edit_button)
        actions.addWidget(delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Code", "Title", "Status", "Time", "Questions", "Passing"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        self._exams = self._app_context.exam_service.search_exams(
            ExamSearchFilters(
                query=self.search_edit.text().strip() or None,
                status=self.status_combo.currentData(),
            )
        )
        self.table.setRowCount(0)
        for exam in self._exams:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(exam.code))
            self.table.setItem(row, 1, QTableWidgetItem(exam.title))
            self.table.setItem(row, 2, QTableWidgetItem(exam.status))
            self.table.setItem(row, 3, QTableWidgetItem(f"{exam.time_limit_minutes} min"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{exam.min_questions}-{exam.max_questions}"))
            self.table.setItem(row, 5, QTableWidgetItem(str(exam.passing_score)))

    def _selected_exam(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._exams):
            return None
        return self._exams[row]

    def _add_exam(self) -> None:
        user_id = self._get_current_user_id()
        if user_id is None:
            self.banner.show_error("Login session not available.")
            return
        dialog = ExamEditorDialog(created_by_user_id=user_id, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._app_context.exam_service.add_exam(dialog.create_input())
        except ExamManagementError as exc:
            QMessageBox.warning(self, "Exam Error", str(exc))
            return
        self.banner.show_success("Exam added.")
        self.refresh()
        self._on_exams_changed()

    def _edit_exam(self) -> None:
        exam = self._selected_exam()
        if exam is None:
            self.banner.show_error("Select an exam first.")
            return
        dialog = ExamEditorDialog(created_by_user_id=self._get_current_user_id() or "", exam=exam, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._app_context.exam_service.edit_exam(exam.exam_id, dialog.update_input())
        except ExamManagementError as exc:
            QMessageBox.warning(self, "Exam Error", str(exc))
            return
        self.banner.show_success("Exam updated.")
        self.refresh()
        self._on_exams_changed()

    def _delete_exam(self) -> None:
        exam = self._selected_exam()
        if exam is None:
            self.banner.show_error("Select an exam first.")
            return
        if QMessageBox.question(self, "Delete Exam", "Delete the selected exam?") != QMessageBox.Yes:
            return
        self._app_context.exam_service.delete_exam(exam.exam_id)
        self.banner.show_success("Exam deleted.")
        self.refresh()
        self._on_exams_changed()
