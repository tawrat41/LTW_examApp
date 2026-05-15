from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
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

from app.application.students import StudentManagementError, StudentSearchFilters
from app.presentation.desktop.dialogs.student_editor_dialog import StudentEditorDialog
from app.presentation.desktop.widgets.common import MessageBanner, PrimaryButton, SectionHeader, card_container


class StudentManagementScreen(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        self._students = []
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("Student Management", "Create, update, search, and disable student accounts."))
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        filters_card = card_container()
        filters_layout = QHBoxLayout(filters_card)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by student ID, name, or email")
        self.active_only_check = QCheckBox("Active only")
        self.active_only_check.setChecked(True)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.refresh)
        filters_layout.addWidget(self.search_edit, 1)
        filters_layout.addWidget(self.active_only_check)
        filters_layout.addWidget(search_button)
        layout.addWidget(filters_card)

        actions = QHBoxLayout()
        add_button = PrimaryButton("Add Student")
        edit_button = QPushButton("Edit Selected")
        delete_button = QPushButton("Delete Selected")
        add_button.clicked.connect(self._add_student)
        edit_button.clicked.connect(self._edit_student)
        delete_button.clicked.connect(self._delete_student)
        actions.addWidget(add_button)
        actions.addWidget(edit_button)
        actions.addWidget(delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Student ID", "Name", "Email", "Phone", "Active"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        filters = StudentSearchFilters(
            query=self.search_edit.text().strip() or None,
            is_active=True if self.active_only_check.isChecked() else None,
        )
        self._students = self._app_context.student_service.search_students(filters)
        self.table.setRowCount(0)
        for student in self._students:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(student.student_code))
            self.table.setItem(row, 1, QTableWidgetItem(student.full_name))
            self.table.setItem(row, 2, QTableWidgetItem(student.email or ""))
            self.table.setItem(row, 3, QTableWidgetItem(student.phone or ""))
            self.table.setItem(row, 4, QTableWidgetItem("Yes" if student.is_active else "No"))

    def _selected_student(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._students):
            return None
        return self._students[row]

    def _add_student(self) -> None:
        dialog = StudentEditorDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._app_context.student_service.add_student(dialog.create_input())
        except StudentManagementError as exc:
            QMessageBox.warning(self, "Student Error", str(exc))
            return
        self.banner.show_success("Student added.")
        self.refresh()

    def _edit_student(self) -> None:
        student = self._selected_student()
        if student is None:
            self.banner.show_error("Select a student first.")
            return
        dialog = StudentEditorDialog(student=student, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self._app_context.student_service.edit_student(student.student_id, dialog.update_input())
        except StudentManagementError as exc:
            QMessageBox.warning(self, "Student Error", str(exc))
            return
        self.banner.show_success("Student updated.")
        self.refresh()

    def _delete_student(self) -> None:
        student = self._selected_student()
        if student is None:
            self.banner.show_error("Select a student first.")
            return
        if QMessageBox.question(self, "Delete Student", "Delete the selected student?") != QMessageBox.Yes:
            return
        self._app_context.student_service.delete_student(student.student_id)
        self.banner.show_success("Student deleted.")
        self.refresh()
