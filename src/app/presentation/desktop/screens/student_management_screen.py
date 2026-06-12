from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
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
from app.presentation.desktop.widgets.common import Badge, MessageBanner, PrimaryButton, SectionHeader, card_container


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

        # Actions Row
        actions = QHBoxLayout()
        add_button = PrimaryButton("Add Student")
        self.edit_button = QPushButton("Edit Profile")
        self.delete_button = QPushButton("Delete Account")
        add_button.clicked.connect(self._add_student)
        self.edit_button.clicked.connect(self._edit_student)
        self.delete_button.clicked.connect(self._delete_student)
        actions.addWidget(add_button)
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        
        # Search Bar
        search_card = card_container()
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(15, 10, 15, 10)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by student ID, name, or email...")
        self.active_only_check = QCheckBox("Active Students Only")
        self.active_only_check.setChecked(True)
        search_btn = PrimaryButton("Search")
        search_btn.setFixedWidth(120)
        search_btn.clicked.connect(self.refresh)
        search_layout.addWidget(self.search_edit, 1)
        search_layout.addWidget(self.active_only_check)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(actions)
        layout.addWidget(search_card)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "FULL NAME", "EMAIL ADDRESS", "PHONE", "STATUS"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        
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
            self.table.setItem(row, 3, QTableWidgetItem(student.phone or ""))
            
            # Status Badge
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(10, 5, 10, 5)
            if student.is_active:
                badge = Badge("ACTIVE", color="#16A34A", bg="#DCFCE7")
            else:
                badge = Badge("INACTIVE", color="#DC2626", bg="#FEF2F2")
            status_layout.addWidget(badge)
            status_layout.addStretch(1)
            self.table.setCellWidget(row, 4, status_widget)

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
