from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.application.auth import AuthenticationError, LoginRequest
from app.presentation.desktop.widgets.common import MessageBanner, PrimaryButton, card_container


class StudentLoginScreen(QWidget):
    login_succeeded = Signal(object)

    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        root = QHBoxLayout(self)
        root.setContentsMargins(36, 36, 36, 36)

        intro = QFrame()
        intro.setStyleSheet("background: #16324f; border-radius: 24px;")
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(28, 28, 28, 28)
        title = QLabel("Student Exam Portal")
        title.setObjectName("appTitle")
        subtitle = QLabel("Sign in with your student ID to begin an adaptive English exam.")
        subtitle.setStyleSheet("color: #d9e2ec; font-size: 14px;")
        subtitle.setWordWrap(True)
        intro_layout.addWidget(title)
        intro_layout.addWidget(subtitle)
        intro_layout.addStretch(1)

        form_card = card_container()
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(24, 24, 24, 24)
        heading = QLabel("Student Login")
        heading.setObjectName("sectionTitle")
        self.banner = MessageBanner()
        self.student_id_edit = QLineEdit()
        self.student_id_edit.setPlaceholderText("Student ID")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.login_button = PrimaryButton("Enter Portal")
        self.login_button.clicked.connect(self._attempt_login)
        form_layout.addWidget(heading)
        form_layout.addWidget(self.banner)
        form_layout.addWidget(self.student_id_edit)
        form_layout.addWidget(self.password_edit)
        form_layout.addWidget(self.login_button)
        form_layout.addStretch(1)

        root.addWidget(intro, 3)
        root.addWidget(form_card, 2)

    def _attempt_login(self) -> None:
        self.banner.clear_message()
        try:
            result = self._app_context.auth_controller.handle_student_login(
                LoginRequest(username=self.student_id_edit.text(), password=self.password_edit.text())
            )
        except AuthenticationError as exc:
            self.banner.show_error(str(exc))
            return
        self.login_succeeded.emit(result)
