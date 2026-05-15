from __future__ import annotations

import uuid

from app.application.importing import QuestionBankImportService
from app.infrastructure.importers.docx import ParsedQuestion
from app.infrastructure.question_bank.repositories import QuestionBankRepository

from .dto import (
    BulkImportRequest,
    BulkImportResult,
    CreateQuestionInput,
    QuestionOptionInput,
    QuestionSearchFilters,
    QuestionView,
    UpdateQuestionInput,
)


class QuestionBankError(Exception):
    pass


class QuestionBankService:
    def __init__(
        self,
        repository: QuestionBankRepository,
        import_service: QuestionBankImportService | None = None,
    ) -> None:
        self._repository = repository
        self._import_service = import_service or QuestionBankImportService()

    def add_question(self, data: CreateQuestionInput) -> QuestionView:
        self._validate_question_input(data.stem_text, data.options, data.difficulty_level, data.marks)
        try:
            question = self._repository.create_question(data)
        except ValueError as exc:
            raise QuestionBankError(str(exc)) from exc
        return self._to_view(question)

    def edit_question(self, question_id: str, data: UpdateQuestionInput) -> QuestionView:
        if data.stem_text is not None and not data.stem_text.strip():
            raise QuestionBankError("Question text is required.")
        if data.difficulty_level is not None and data.difficulty_level < 1:
            raise QuestionBankError("Difficulty level must be at least 1.")
        if data.marks is not None and data.marks <= 0:
            raise QuestionBankError("Marks must be greater than 0.")
        if data.options is not None:
            self._validate_question_input(
                data.stem_text or "existing",
                data.options,
                data.difficulty_level or 1,
                data.marks if data.marks is not None else 1.0,
            )
        try:
            question = self._repository.update_question(question_id, data)
        except ValueError as exc:
            raise QuestionBankError(str(exc)) from exc
        if question is None:
            raise QuestionBankError("Question not found.")
        return self._to_view(question)

    def delete_question(self, question_id: str) -> None:
        deleted = self._repository.delete_question(question_id)
        if not deleted:
            raise QuestionBankError("Question not found.")

    def search_questions(self, filters: QuestionSearchFilters) -> list[QuestionView]:
        return [self._to_view(question) for question in self._repository.search_questions(filters)]

    def bulk_import_from_paragraphs(
        self,
        paragraphs: list[str],
        request: BulkImportRequest,
    ) -> BulkImportResult:
        report = self._import_service.import_from_paragraphs(paragraphs)
        return self._persist_imported_questions(report.parsed_questions, report.issues, request)

    def bulk_import_from_docx(
        self,
        file_path: str,
        request: BulkImportRequest,
    ) -> BulkImportResult:
        report = self._import_service.import_from_docx(file_path)
        return self._persist_imported_questions(report.parsed_questions, report.issues, request)

    def _persist_imported_questions(
        self,
        parsed_questions: list[ParsedQuestion],
        issues: list,
        request: BulkImportRequest,
    ) -> BulkImportResult:
        imported_questions: list[QuestionView] = []
        for parsed_question in parsed_questions:
            create_input = CreateQuestionInput(
                exam_id=request.exam_id,
                section_id=request.section_id,
                stem_text=parsed_question.question_text,
                options=[
                    QuestionOptionInput(
                        key=key,
                        text=text,
                        is_correct=(key == parsed_question.correct_answer),
                    )
                    for key, text in parsed_question.options.items()
                ],
                category_name=parsed_question.category,
                difficulty_level=self._map_difficulty(parsed_question.difficulty),
                explanation_text=parsed_question.explanation,
                tags=[],
                marks=request.default_marks,
                external_ref=f"import-{parsed_question.sequence_number}-{uuid.uuid4().hex[:8]}",
                is_active=request.is_active,
            )
            imported_questions.append(self.add_question(create_input))

        return BulkImportResult(imported_questions=imported_questions, issues=list(issues))

    def _map_difficulty(self, difficulty: str | None) -> int:
        if difficulty is None:
            return 1
        normalized = difficulty.strip().lower()
        if normalized == "easy":
            return 1
        if normalized == "medium":
            return 2
        if normalized == "hard":
            return 3
        return 1

    def _validate_question_input(
        self,
        stem_text: str,
        options: list[QuestionOptionInput],
        difficulty_level: int,
        marks: float,
    ) -> None:
        if not stem_text.strip():
            raise QuestionBankError("Question text is required.")
        if difficulty_level < 1:
            raise QuestionBankError("Difficulty level must be at least 1.")
        if marks <= 0:
            raise QuestionBankError("Marks must be greater than 0.")
        if len(options) < 2:
            raise QuestionBankError("At least two options are required.")

        correct_count = sum(1 for option in options if option.is_correct)
        if correct_count != 1:
            raise QuestionBankError("Exactly one option must be marked correct.")

        normalized_keys = [option.key.strip().upper() for option in options]
        if len(normalized_keys) != len(set(normalized_keys)):
            raise QuestionBankError("Option keys must be unique.")

    def _to_view(self, question) -> QuestionView:
        return QuestionView(
            question_id=str(question.id),
            exam_id=str(question.exam_id),
            section_id=str(question.section_id),
            category_name=question.category.name if question.category else None,
            external_ref=question.external_ref,
            stem_text=question.stem_text,
            difficulty_level=question.difficulty_level,
            explanation_text=question.explanation_text,
            tags=sorted(tag.name for tag in question.tags),
            marks=float(question.marks),
            is_active=question.is_active,
            options=[
                QuestionOptionInput(
                    key=option.option_key,
                    text=option.option_text,
                    is_correct=option.is_correct,
                )
                for option in sorted(question.options, key=lambda item: item.display_order)
            ],
        )
