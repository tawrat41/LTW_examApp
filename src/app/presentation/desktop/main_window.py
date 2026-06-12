from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.presentation.desktop.app_context import DesktopAppContext
from app.presentation.desktop.screens.dashboard_screen import DashboardScreen
from app.presentation.desktop.screens.exam_management_screen import ExamManagementScreen
from app.presentation.desktop.screens.import_wizard_screen import ImportWizardScreen
from app.presentation.desktop.screens.login_screen import LoginScreen
from app.presentation.desktop.screens.question_bank_manager import QuestionBankManagerScreen
from app.presentation.desktop.screens.reporting_screen import ReportingScreen
from app.presentation.desktop.screens.student_management_screen import StudentManagementScreen
from app.presentation.desktop.theme import build_stylesheet
from app.presentation.desktop.widgets.navigation import NavigationRail


class AdminMainWindow(QMainWindow):
    def __init__(self, app_context: DesktopAppContext) -> None:
        super().__init__()
        self._app_context = app_context
        self._session_id: str | None = None
        self._principal_id: str | None = None
        self._principal_name: str | None = None
        self.setWindowTitle("Adaptive Exam Admin")
        self.resize(1440, 900)
        self.setStyleSheet(build_stylesheet())

        root = QStackedWidget()
        self.setCentralWidget(root)
        self._root_stack = root

        self.login_screen = LoginScreen(app_context)
        self.login_screen.login_succeeded.connect(self._on_login_succeeded)
        root.addWidget(self.login_screen)

        self.shell = self._build_shell()
        root.addWidget(self.shell)
        root.setCurrentWidget(self.login_screen)

    def _build_shell(self) -> QWidget:
        shell = QWidget()
        layout = QHBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        brand = QLabel("Admin Console")
        brand.setObjectName("appTitle")
        brand.setStyleSheet("font-size: 20px; color: #F1F5F9; font-weight: 800; background: transparent; border: none;")
        self.user_label = QLabel("")
        self.user_label.setStyleSheet("color: #94A3B8; background: transparent; border: none;")
        
        v_label = QLabel("v1.0.6 - UI PREMIUM")
        v_label.setStyleSheet("color: #475569; font-size: 10px; font-weight: 700; background: transparent; border: none;")
        
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(self.user_label)
        sidebar_layout.addWidget(v_label)

        self.nav = NavigationRail(
            [
                ("dashboard", "Dashboard"),
                ("questions", "Question Bank"),
                ("import", "Import Wizard"),
                ("reports", "Reports"),
                ("students", "Students"),
                ("exams", "Exams"),
            ]
        )
        self.nav.page_requested.connect(self._show_page)
        sidebar_layout.addWidget(self.nav)
        logout_button = QPushButton("Logout")
        logout_button.clicked.connect(self._logout)
        sidebar_layout.addWidget(logout_button)
        layout.addWidget(sidebar, 0)

        content_shell = QFrame()
        content_shell.setObjectName("contentShell")
        content_layout = QVBoxLayout(content_shell)
        content_layout.setContentsMargins(18, 18, 18, 18)
        self.page_stack = QStackedWidget()
        content_layout.addWidget(self.page_stack)
        layout.addWidget(content_shell, 1)

        self.dashboard_screen = DashboardScreen(self._app_context)
        self.question_bank_screen = QuestionBankManagerScreen(self._app_context)
        self.import_screen = ImportWizardScreen(self._app_context, self._refresh_question_bound_views)
        self.reporting_screen = ReportingScreen(self._app_context)
        self.student_screen = StudentManagementScreen(self._app_context)
        self.exam_screen = ExamManagementScreen(self._app_context, self._get_current_user_id, self._refresh_question_bound_views)

        for key, screen in [
            ("dashboard", self.dashboard_screen),
            ("questions", self.question_bank_screen),
            ("import", self.import_screen),
            ("reports", self.reporting_screen),
            ("students", self.student_screen),
            ("exams", self.exam_screen),
        ]:
            scroller = QScrollArea()
            scroller.setWidgetResizable(True)
            scroller.setFrameShape(QFrame.NoFrame)
            scroller.setWidget(screen)
            self.page_stack.addWidget(scroller)
            scroller.setProperty("page_id", key)

        return shell

    def _find_page_index(self, page_id: str) -> int:
        for index in range(self.page_stack.count()):
            widget = self.page_stack.widget(index)
            if widget.property("page_id") == page_id:
                return index
        return 0

    def _show_page(self, page_id: str) -> None:
        self.page_stack.setCurrentIndex(self._find_page_index(page_id))
        self.nav.set_active(page_id)
        self._refresh_active_page(page_id)

    def _refresh_active_page(self, page_id: str) -> None:
        if page_id == "dashboard":
            self.dashboard_screen.refresh()
        elif page_id == "questions":
            self.question_bank_screen.refresh()
        elif page_id == "import":
            self.import_screen.refresh()
        elif page_id == "students":
            self.student_screen.refresh()
        elif page_id == "reports":
            self.reporting_screen.refresh()
        elif page_id == "exams":
            self.exam_screen.refresh()

    def _on_login_succeeded(self, auth_result) -> None:
        self._session_id = auth_result.session_id
        self._principal_id = auth_result.principal_id
        self._principal_name = auth_result.display_name
        self.user_label.setText(f"Signed in as {auth_result.display_name}")
        self._root_stack.setCurrentWidget(self.shell)
        self._show_page("dashboard")

    def _logout(self) -> None:
        if self._session_id:
            self._app_context.auth_controller.handle_logout(self._session_id)
        self._session_id = None
        self._principal_id = None
        self._principal_name = None
        self._root_stack.setCurrentWidget(self.login_screen)

    def _get_current_user_id(self) -> str | None:
        return self._principal_id

    def _refresh_question_bound_views(self) -> None:
        self.question_bank_screen.refresh()
        self.import_screen.refresh()
        self.reporting_screen.refresh()
        self.dashboard_screen.refresh()
        self.exam_screen.refresh()


def launch_admin_window(app_context: DesktopAppContext) -> int:
    app = QApplication.instance() or QApplication([])
    window = AdminMainWindow(app_context)
    window.show()
    return app.exec()
