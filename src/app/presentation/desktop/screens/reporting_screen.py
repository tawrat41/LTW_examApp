from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.presentation.desktop.widgets.common import MessageBanner, PrimaryButton, SectionHeader, card_container


class ReportingScreen(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        self._student_results = []
        self._exam_summaries = []

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("Reports", "Student results, exam summaries, CSV export, and printable reports."))
        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        actions_card = card_container()
        actions_layout = QHBoxLayout(actions_card)
        refresh_button = QPushButton("Refresh")
        export_results_csv = PrimaryButton("Export Results CSV")
        export_summaries_csv = QPushButton("Export Summaries CSV")
        export_results_html = PrimaryButton("Printable Results")
        export_summaries_html = QPushButton("Printable Summaries")
        refresh_button.clicked.connect(self.refresh)
        export_results_csv.clicked.connect(self._export_results_csv)
        export_summaries_csv.clicked.connect(self._export_summaries_csv)
        export_results_html.clicked.connect(self._export_results_html)
        export_summaries_html.clicked.connect(self._export_summaries_html)
        actions_layout.addWidget(refresh_button)
        actions_layout.addStretch(1)
        actions_layout.addWidget(export_results_csv)
        actions_layout.addWidget(export_summaries_csv)
        actions_layout.addWidget(export_results_html)
        actions_layout.addWidget(export_summaries_html)
        layout.addWidget(actions_card)

        self.tabs = QTabWidget()
        self.student_table = QTableWidget(0, 9)
        self.student_table.setHorizontalHeaderLabels(
            ["Student ID", "Student", "Exam", "Answered", "Correct", "Wrong", "Score", "Percent", "Status"]
        )
        self.student_table.horizontalHeader().setStretchLastSection(True)
        student_tab = QWidget()
        student_tab_layout = QVBoxLayout(student_tab)
        student_tab_layout.addWidget(self.student_table)

        self.summary_table = QTableWidget(0, 8)
        self.summary_table.setHorizontalHeaderLabels(
            ["Code", "Exam", "Attempts", "Completed", "Avg Score", "Avg %", "High", "Low"]
        )
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        summary_tab = QWidget()
        summary_tab_layout = QVBoxLayout(summary_tab)
        summary_tab_layout.addWidget(self.summary_table)

        self.tabs.addTab(student_tab, "Student Results")
        self.tabs.addTab(summary_tab, "Exam Summaries")
        layout.addWidget(self.tabs, 1)

    def refresh(self) -> None:
        self.banner.clear_message()
        self._student_results = self._app_context.reporting_service.list_student_results()
        self._exam_summaries = self._app_context.reporting_service.list_exam_summaries()
        self._populate_student_results()
        self._populate_exam_summaries()

    def _populate_student_results(self) -> None:
        self.student_table.setRowCount(0)
        for item in self._student_results:
            row = self.student_table.rowCount()
            self.student_table.insertRow(row)
            self.student_table.setItem(row, 0, QTableWidgetItem(item.student_code))
            self.student_table.setItem(row, 1, QTableWidgetItem(item.student_name))
            self.student_table.setItem(row, 2, QTableWidgetItem(item.exam_title))
            self.student_table.setItem(row, 3, QTableWidgetItem(f"{item.answered_questions}/{item.total_questions}"))
            self.student_table.setItem(row, 4, QTableWidgetItem(str(item.correct_answers)))
            self.student_table.setItem(row, 5, QTableWidgetItem(str(item.wrong_answers)))
            self.student_table.setItem(row, 6, QTableWidgetItem(f"{item.score:.2f}"))
            self.student_table.setItem(row, 7, QTableWidgetItem(f"{item.percentage:.2f}%"))
            self.student_table.setItem(row, 8, QTableWidgetItem(item.status))

    def _populate_exam_summaries(self) -> None:
        self.summary_table.setRowCount(0)
        for item in self._exam_summaries:
            row = self.summary_table.rowCount()
            self.summary_table.insertRow(row)
            self.summary_table.setItem(row, 0, QTableWidgetItem(item.exam_code))
            self.summary_table.setItem(row, 1, QTableWidgetItem(item.exam_title))
            self.summary_table.setItem(row, 2, QTableWidgetItem(str(item.total_attempts)))
            self.summary_table.setItem(row, 3, QTableWidgetItem(str(item.completed_attempts)))
            self.summary_table.setItem(row, 4, QTableWidgetItem(f"{item.average_score:.2f}"))
            self.summary_table.setItem(row, 5, QTableWidgetItem(f"{item.average_percentage:.2f}%"))
            self.summary_table.setItem(row, 6, QTableWidgetItem(f"{item.highest_score:.2f}"))
            self.summary_table.setItem(row, 7, QTableWidgetItem(f"{item.lowest_score:.2f}"))

    def _export_results_csv(self) -> None:
        self._export_file("student-results.csv", self._app_context.reporting_service.export_student_results_csv)

    def _export_summaries_csv(self) -> None:
        self._export_file("exam-summaries.csv", self._app_context.reporting_service.export_exam_summaries_csv)

    def _export_results_html(self) -> None:
        self._export_file("student-results-report.html", self._app_context.reporting_service.export_printable_student_results)

    def _export_summaries_html(self) -> None:
        self._export_file("exam-summaries-report.html", self._app_context.reporting_service.export_printable_exam_summaries)

    def _export_file(self, suggested_name: str, exporter) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            str(Path(suggested_name)),
            "CSV Files (*.csv);;HTML Files (*.html)",
        )
        if not path:
            return
        try:
            written_path = exporter(path)
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", str(exc))
            return
        self.banner.show_success(f"Exported report to {written_path}")
