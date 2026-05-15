from __future__ import annotations

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from app.presentation.desktop.student.app_context import StudentDesktopAppContext
from app.presentation.desktop.student.screens.dashboard_screen import StudentDashboardScreen
from app.presentation.desktop.student.screens.exam_screen import StudentExamScreen
from app.presentation.desktop.student.screens.instructions_screen import ExamInstructionsScreen
from app.presentation.desktop.student.screens.login_screen import StudentLoginScreen
from app.presentation.desktop.student.screens.result_screen import StudentResultScreen
from app.presentation.desktop.student.state import StudentExamSessionState
from app.presentation.desktop.theme import build_stylesheet


class StudentMainWindow(QMainWindow):
    def __init__(self, app_context: StudentDesktopAppContext) -> None:
        super().__init__()
        self._app_context = app_context
        self._session_id: str | None = None
        self._student_id: str | None = None
        self._student_name: str | None = None
        self._selected_exam_id: str | None = None
        self._exam_state: StudentExamSessionState | None = None

        self.setWindowTitle("Adaptive Exam Student Portal")
        self.resize(1280, 840)
        self.setStyleSheet(build_stylesheet())

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_screen = StudentLoginScreen(app_context)
        self.dashboard_screen = StudentDashboardScreen(app_context)
        self.instructions_screen = ExamInstructionsScreen()
        self.exam_screen = StudentExamScreen(app_context)
        self.result_screen = StudentResultScreen()

        self.login_screen.login_succeeded.connect(self._on_login_succeeded)
        self.dashboard_screen.exam_selected.connect(self._open_instructions)
        self.instructions_screen.back_requested.connect(self._show_dashboard)
        self.instructions_screen.start_requested.connect(self._start_exam)
        self.exam_screen.exam_finished.connect(self._show_result)
        self.result_screen.back_to_dashboard_requested.connect(self._return_to_dashboard)

        for widget in [
            self.login_screen,
            self.dashboard_screen,
            self.instructions_screen,
            self.exam_screen,
            self.result_screen,
        ]:
            self.stack.addWidget(widget)
        self.stack.setCurrentWidget(self.login_screen)

    def _on_login_succeeded(self, auth_result) -> None:
        self._session_id = auth_result.session_id
        self._student_id = auth_result.principal_id
        self._student_name = auth_result.display_name
        self.dashboard_screen.set_student_name(auth_result.display_name)
        self._show_dashboard()

    def _show_dashboard(self) -> None:
        self.showNormal()
        self.dashboard_screen.refresh()
        self.stack.setCurrentWidget(self.dashboard_screen)

    def _open_instructions(self, exam_id: str) -> None:
        self._selected_exam_id = exam_id
        exam = self._app_context.exam_portal.get_exam_instructions(exam_id)
        self.instructions_screen.set_exam(exam)
        self.stack.setCurrentWidget(self.instructions_screen)

    def _start_exam(self) -> None:
        if self._student_id is None or self._selected_exam_id is None:
            return
        session_view = self._app_context.exam_portal.start_exam(
            student_id=self._student_id,
            exam_id=self._selected_exam_id,
        )
        self._exam_state = StudentExamSessionState.create(
            attempt_id=session_view.attempt_id,
            exam=session_view.exam,
            first_question=session_view.current_question,
        )
        self.exam_screen.load_session(self._exam_state)
        self.stack.setCurrentWidget(self.exam_screen)
        self.showFullScreen()

    def _show_result(self, attempt_id: str) -> None:
        self.showNormal()
        result = self._app_context.exam_portal.get_result(attempt_id)
        self.result_screen.set_result(result)
        self.stack.setCurrentWidget(self.result_screen)

    def _return_to_dashboard(self) -> None:
        self._exam_state = None
        self._selected_exam_id = None
        self._show_dashboard()


def launch_student_window(app_context: StudentDesktopAppContext) -> int:
    app = QApplication.instance() or QApplication([])
    window = StudentMainWindow(app_context)
    window.show()
    return app.exec()
