from __future__ import annotations

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QTableWidget, QTableWidgetItem, QVBoxLayout

from app.infrastructure.importers.docx import ImportIssue, ParsedQuestion


class ImportPreviewDialog(QDialog):
    def __init__(self, questions: list[ParsedQuestion], issues: list[ImportIssue], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import Preview")
        self.resize(900, 620)
        layout = QVBoxLayout(self)
        summary = QLabel(f"Valid questions: {len(questions)} | Issues: {len(issues)}")
        summary.setStyleSheet("font-weight: 700;")
        layout.addWidget(summary)

        split = QHBoxLayout()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "Question", "Category", "Difficulty"])
        self.table.horizontalHeader().setStretchLastSection(True)
        for item in questions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(item.sequence_number)))
            self.table.setItem(row, 1, QTableWidgetItem(item.question_text))
            self.table.setItem(row, 2, QTableWidgetItem(item.category or ""))
            self.table.setItem(row, 3, QTableWidgetItem(item.difficulty or ""))
        split.addWidget(self.table, 2)

        self.issues_list = QListWidget()
        for issue in issues:
            self.issues_list.addItem(
                f"{issue.severity.upper()} | #{issue.sequence_number or '-'} | {issue.message}"
            )
        split.addWidget(self.issues_list, 1)
        layout.addLayout(split)
