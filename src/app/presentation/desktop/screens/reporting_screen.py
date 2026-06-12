from __future__ import annotations
from PySide6.QtCore import Qt

from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.presentation.desktop.widgets.common import Badge, MessageBanner, PrimaryButton, SectionHeader, card_container


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

        # Actions Row
        actions_card = card_container()
        actions_card.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;")
        actions_layout = QHBoxLayout(actions_card)
        actions_layout.setContentsMargins(20, 15, 20, 15)
        actions_layout.setSpacing(15)
        
        refresh_button = QPushButton("↻  Refresh Data")
        refresh_button.setFixedWidth(140)
        
        export_group = QHBoxLayout()
        export_group.setSpacing(10)
        export_results_csv = PrimaryButton("Export Results CSV")
        export_results_html = QPushButton("Printable Results")
        export_group.addWidget(export_results_csv)
        export_group.addWidget(export_results_html)
        
        refresh_button.clicked.connect(self.refresh)
        export_results_csv.clicked.connect(self._export_results_csv)
        export_results_html.clicked.connect(self._export_results_html)
        
        actions_layout.addWidget(refresh_button)
        actions_layout.addStretch(1)
        actions_layout.addLayout(export_group)
        layout.addWidget(actions_card)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #E2E8F0; border-top: none; border-radius: 0 0 12px 12px; background: white; }")
        
        # Student Results Tab
        self.student_table = QTableWidget(0, 9)
        self.student_table.setHorizontalHeaderLabels(
            ["ID", "STUDENT NAME", "EXAM TITLE", "ANS/TOT", "CORR", "WRONG", "SCORE", "PERCENT", "STATUS"]
        )
        self.student_table.horizontalHeader().setStretchLastSection(True)
        self.student_table.setAlternatingRowColors(True)
        self.student_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        student_tab = QWidget()
        student_tab_layout = QVBoxLayout(student_tab)
        student_tab_layout.setContentsMargins(0, 0, 0, 0)
        student_tab_layout.addWidget(self.student_table)

        # Exam Summaries Tab
        self.summary_table = QTableWidget(0, 8)
        self.summary_table.setHorizontalHeaderLabels(
            ["CODE", "EXAM TITLE", "ATTEMPTS", "DONE", "AVG SCORE", "AVG %", "HIGH", "LOW"]
        )
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        summary_tab = QWidget()
        summary_tab_layout = QVBoxLayout(summary_tab)
        summary_tab_layout.setContentsMargins(0, 0, 0, 0)
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
        self.student_table.verticalHeader().setVisible(False)
        for item in self._student_results:
            row = self.student_table.rowCount()
            self.student_table.insertRow(row)
            self.student_table.setItem(row, 0, QTableWidgetItem(item.student_code))
            self.student_table.setItem(row, 1, QTableWidgetItem(item.student_name))
            self.student_table.setItem(row, 2, QTableWidgetItem(item.exam_title))
            
            # Ans/Tot
            ans_item = QTableWidgetItem(f"{item.answered_questions}/{item.total_questions}")
            ans_item.setTextAlignment(Qt.AlignCenter)
            self.student_table.setItem(row, 3, ans_item)
            
            self.table_set_center(row, 4, str(item.correct_answers), self.student_table)
            self.table_set_center(row, 5, str(item.wrong_answers), self.student_table)
            self.table_set_center(row, 6, f"{item.score:.1f}", self.student_table)
            
            # Percentage
            pct_item = QTableWidgetItem(f"{item.percentage:.1f}%")
            pct_item.setTextAlignment(Qt.AlignCenter)
            pct_item.setForeground(Qt.darkGreen if item.percentage >= 50 else Qt.darkRed)
            self.student_table.setItem(row, 7, pct_item)
            
            # Status Badge - Simplify to direct widget for max reliability
            st_raw = str(item.status).upper() if item.status else "PENDING"
            
            if "COMPLETED" in st_raw:
                badge = Badge("COMPLETED", color="#16A34A", bg="#DCFCE7")
            elif "PROGRESS" in st_raw or "STARTED" in st_raw:
                badge = Badge("IN PROGRESS", color="#B45309", bg="#FEF3C7")
            else:
                display_text = st_raw.replace("_", " ") if st_raw != "NONE" else "PENDING"
                badge = Badge(display_text, color="#475569", bg="#F1F5F9")
                
            self.student_table.setCellWidget(row, 8, badge)

        h = self.student_table.horizontalHeader()
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(8, QHeaderView.Fixed)
        self.student_table.setColumnWidth(8, 140)

    def _populate_exam_summaries(self) -> None:
        self.summary_table.setRowCount(0)
        self.summary_table.verticalHeader().setVisible(False)
        for item in self._exam_summaries:
            row = self.summary_table.rowCount()
            self.summary_table.insertRow(row)
            self.summary_table.setItem(row, 0, QTableWidgetItem(item.exam_code))
            self.summary_table.setItem(row, 1, QTableWidgetItem(item.exam_title))
            
            self.table_set_center(row, 2, str(item.total_attempts), self.summary_table)
            self.table_set_center(row, 3, str(item.completed_attempts), self.summary_table)
            self.table_set_center(row, 4, f"{item.average_score:.1f}", self.summary_table)
            self.table_set_center(row, 5, f"{item.average_percentage:.1f}%", self.summary_table)
            self.table_set_center(row, 6, f"{item.highest_score:.1f}", self.summary_table)
            self.table_set_center(row, 7, f"{item.lowest_score:.1f}", self.summary_table)

        h = self.summary_table.horizontalHeader()
        h.setSectionResizeMode(1, QHeaderView.Stretch)

    def table_set_center(self, row: int, col: int, text: str, table: QTableWidget) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, col, item)

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
