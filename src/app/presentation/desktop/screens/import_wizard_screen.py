from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.question_bank import BulkImportRequest
from app.presentation.desktop.dialogs.import_preview_dialog import ImportPreviewDialog
from app.presentation.desktop.widgets.common import LoadingStrip, MessageBanner, PrimaryButton, SectionHeader, card_container


class ImportWizardScreen(QWidget):
    def __init__(self, app_context, on_import_completed, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_context = app_context
        self._on_import_completed = on_import_completed
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader("Import Wizard", "Choose a DOCX file, preview parsed questions, then import."))
        self.banner = MessageBanner()
        self.loading = LoadingStrip()
        layout.addWidget(self.banner)
        layout.addWidget(self.loading)

        card = card_container()
        card_layout = QVBoxLayout(card)
        row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Select a DOCX file")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._browse_file)
        row.addWidget(QLabel("DOCX File"))
        row.addWidget(self.file_edit, 1)
        row.addWidget(browse_button)
        card_layout.addLayout(row)

        row2 = QHBoxLayout()
        self.exam_combo = QComboBox()
        self.section_combo = QComboBox()
        row2.addWidget(QLabel("Exam"))
        row2.addWidget(self.exam_combo)
        row2.addWidget(QLabel("Section"))
        row2.addWidget(self.section_combo)
        card_layout.addLayout(row2)

        actions = QHBoxLayout()
        self.preview_button = QPushButton("Preview")
        self.import_button = PrimaryButton("Import Questions")
        self.preview_button.clicked.connect(self._preview)
        self.import_button.clicked.connect(self._import)
        actions.addWidget(self.preview_button)
        actions.addWidget(self.import_button)
        actions.addStretch(1)
        card_layout.addLayout(actions)

        layout.addWidget(card)
        layout.addStretch(1)
        self.exam_combo.currentIndexChanged.connect(self._reload_sections)

    def refresh(self) -> None:
        current_exam_id = self.exam_combo.currentData()
        self.exam_combo.blockSignals(True)
        self.exam_combo.clear()
        for item in self._app_context.admin_queries.list_exam_options():
            self.exam_combo.addItem(item.label, item.id)
        if current_exam_id:
            index = self.exam_combo.findData(current_exam_id)
            if index >= 0:
                self.exam_combo.setCurrentIndex(index)
        self.exam_combo.blockSignals(False)
        self._reload_sections()

    def _reload_sections(self) -> None:
        self.section_combo.clear()
        exam_id = self.exam_combo.currentData()
        if not exam_id:
            return
        for item in self._app_context.admin_queries.list_section_options(exam_id):
            self.section_combo.addItem(item.label, item.id)

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select DOCX File", "", "Word Documents (*.docx)")
        if path:
            self.file_edit.setText(path)

    def _preview(self) -> None:
        self.banner.clear_message()
        if not self.file_edit.text().strip():
            self.banner.show_error("Choose a DOCX file first.")
            return
        report = self._app_context.import_service.import_from_docx(self.file_edit.text().strip())
        dialog = ImportPreviewDialog(report.parsed_questions, report.issues, self)
        dialog.exec()

    def _import(self) -> None:
        if not self.file_edit.text().strip():
            self.banner.show_error("Choose a DOCX file first.")
            return
        if not self.exam_combo.currentData() or not self.section_combo.currentData():
            self.banner.show_error("Choose an exam and section.")
            return
        self.loading.start("Importing questions...")
        result = self._app_context.question_bank_service.bulk_import_from_docx(
            self.file_edit.text().strip(),
            request=BulkImportRequest(
                exam_id=self.exam_combo.currentData(),
                section_id=self.section_combo.currentData(),
            ),
        )
        self.loading.stop()
        QMessageBox.information(
            self,
            "Import Complete",
            f"Imported {len(result.imported_questions)} questions.\nIssues: {len(result.issues)}",
        )
        self.banner.show_success("Import completed.")
        self._on_import_completed()
