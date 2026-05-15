from __future__ import annotations

from app.infrastructure.importers.docx import (
    DocxQuestionBankParser,
    DuplicateQuestionRecord,
    ImportIssue,
    ImportIssueSeverity,
    ImportReport,
    ParsedQuestion,
    QuestionBankValidator,
)


class QuestionBankImportService:
    def __init__(
        self,
        parser: DocxQuestionBankParser | None = None,
        validator: QuestionBankValidator | None = None,
    ) -> None:
        self._parser = parser or DocxQuestionBankParser()
        self._validator = validator or QuestionBankValidator()

    def import_from_docx(self, file_path: str) -> ImportReport:
        parsed_questions, parse_issues = self._parser.parse_file(file_path)
        return self._build_report(parsed_questions, parse_issues)

    def import_from_paragraphs(self, paragraphs: list[str]) -> ImportReport:
        parsed_questions, parse_issues = self._parser.parse_paragraphs(paragraphs)
        return self._build_report(parsed_questions, parse_issues)

    def _build_report(
        self,
        parsed_questions: list[ParsedQuestion],
        parse_issues: list[ImportIssue],
    ) -> ImportReport:
        validation_issues = self._validator.validate(parsed_questions)
        duplicates = self._detect_duplicates(parsed_questions)
        duplicate_issues = [
            ImportIssue(
                sequence_number=duplicate.duplicate_sequence_number,
                severity=ImportIssueSeverity.WARNING,
                message=(
                    f"Duplicate question detected; matches question "
                    f"{duplicate.original_sequence_number} exactly."
                ),
                raw_block=duplicate.question_text,
            )
            for duplicate in duplicates
        ]

        duplicate_sequences = {item.duplicate_sequence_number for item in duplicates}
        filtered_questions = [
            question
            for question in parsed_questions
            if question.sequence_number not in duplicate_sequences
        ]

        return ImportReport(
            parsed_questions=filtered_questions,
            issues=[*parse_issues, *validation_issues, *duplicate_issues],
            duplicates=duplicates,
        )

    def _detect_duplicates(
        self,
        parsed_questions: list[ParsedQuestion],
    ) -> list[DuplicateQuestionRecord]:
        first_seen_by_text: dict[str, ParsedQuestion] = {}
        duplicates: list[DuplicateQuestionRecord] = []

        for question in parsed_questions:
            existing = first_seen_by_text.get(question.question_text)
            if existing is None:
                first_seen_by_text[question.question_text] = question
                continue

            duplicates.append(
                DuplicateQuestionRecord(
                    original_sequence_number=existing.sequence_number,
                    duplicate_sequence_number=question.sequence_number,
                    question_text=question.question_text,
                )
            )

        return duplicates
