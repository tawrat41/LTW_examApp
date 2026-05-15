from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout

from app.application.students import CreateStudentInput, StudentView, UpdateStudentInput
from app.presentation.desktop.widgets.common import MessageBanner


class StudentEditorDialog(QDialog):
    def __init__(self, student: StudentView | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Student Editor")
        self.resize(420, 340)
        self._student = student
        layout = QVBoxLayout(self)
        self.banner = MessageBanner()
        layout.addWidget(self.banner)
        form = QFormLayout()
        self.code_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.is_active_check = QCheckBox("Active")
        self.is_active_check.setChecked(True)
        form.addRow("Student ID", self.code_edit)
        form.addRow("Name", self.name_edit)
        form.addRow("Email", self.email_edit)
        form.addRow("Phone", self.phone_edit)
        form.addRow("Password", self.password_edit)
        form.addRow("", self.is_active_check)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if student is not None:
            self.code_edit.setText(student.student_code)
            self.code_edit.setEnabled(False)
            self.name_edit.setText(student.full_name)
            self.email_edit.setText(student.email or "")
            self.phone_edit.setText(student.phone or "")
            self.is_active_check.setChecked(student.is_active)

    def create_input(self) -> CreateStudentInput:
        return CreateStudentInput(
            student_code=self.code_edit.text().strip(),
            full_name=self.name_edit.text().strip(),
            password=self.password_edit.text().strip(),
            email=self.email_edit.text().strip() or None,
            phone=self.phone_edit.text().strip() or None,
            is_active=self.is_active_check.isChecked(),
        )

    def update_input(self) -> UpdateStudentInput:
        return UpdateStudentInput(
            full_name=self.name_edit.text().strip(),
            password=self.password_edit.text().strip() or None,
            email=self.email_edit.text().strip() or None,
            phone=self.phone_edit.text().strip() or None,
            is_active=self.is_active_check.isChecked(),
        )
