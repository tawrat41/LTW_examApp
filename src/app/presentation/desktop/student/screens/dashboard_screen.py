from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.presentation.desktop.widgets.common import MessageBanner, PrimaryButton, SectionHeader, card_container


class StudentDashboardScreen(QWidget):
    exam_selected = Signal(str)

    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        self._exams = []

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        self.header = SectionHeader("Dashboard", "Available active exams.")
        layout.addWidget(self.header)
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        actions_card = card_container()
        actions_layout = QHBoxLayout(actions_card)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        self.start_button = PrimaryButton("View Instructions")
        self.start_button.clicked.connect(self._open_selected_exam)
        actions_layout.addWidget(QLabel("Select an active exam to continue."))
        actions_layout.addStretch(1)
        actions_layout.addWidget(self.refresh_button)
        actions_layout.addWidget(self.start_button)
        layout.addWidget(actions_card)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Code", "Title", "Subject", "Duration", "Questions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.doubleClicked.connect(lambda *_args: self._open_selected_exam())
        layout.addWidget(self.table, 1)

    def set_student_name(self, name: str) -> None:
        self.header.set_text("Dashboard", f"Signed in as {name}.")

    def refresh(self) -> None:
        self.banner.clear_message()
        self._exams = self._app_context.exam_portal.list_available_exams()
        self.table.setRowCount(0)
        for exam in self._exams:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(exam.code))
            self.table.setItem(row, 1, QTableWidgetItem(exam.title))
            self.table.setItem(row, 2, QTableWidgetItem(exam.subject))
            self.table.setItem(row, 3, QTableWidgetItem(f"{exam.time_limit_minutes} min"))
            self.table.setItem(row, 4, QTableWidgetItem(str(exam.question_count)))
        if not self._exams:
            self.banner.show_error("No active exams are available right now.")

    def _open_selected_exam(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._exams):
            self.banner.show_error("Select an exam first.")
            return
        self.exam_selected.emit(self._exams[row].exam_id)
