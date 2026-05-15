from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from app.presentation.desktop.widgets.common import SectionHeader, StatCard


class DashboardScreen(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("Dashboard", "Operational overview for the desktop admin console."))
        grid = QGridLayout()
        grid.setSpacing(16)
        self._cards = {
            "exams": StatCard("Exams", "#d96c06"),
            "students": StatCard("Students", "#127fbf"),
            "questions": StatCard("Questions", "#0f9d58"),
            "active_students": StatCard("Active Students", "#7c3aed"),
        }
        grid.addWidget(self._cards["exams"], 0, 0)
        grid.addWidget(self._cards["students"], 0, 1)
        grid.addWidget(self._cards["questions"], 1, 0)
        grid.addWidget(self._cards["active_students"], 1, 1)
        layout.addLayout(grid)
        layout.addStretch(1)

    def refresh(self) -> None:
        stats = self._app_context.admin_queries.get_dashboard_stats()
        self._cards["exams"].set_value(str(stats.exams_count))
        self._cards["students"].set_value(str(stats.students_count))
        self._cards["questions"].set_value(str(stats.questions_count))
        self._cards["active_students"].set_value(str(stats.active_students_count))
