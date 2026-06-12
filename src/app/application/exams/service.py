from __future__ import annotations

from app.infrastructure.exams.repositories import ExamRepository
from app.infrastructure.persistence.models import ExamStatus

from .dto import CreateExamInput, ExamSearchFilters, ExamView, UpdateExamInput


class ExamManagementError(Exception):
    pass


class ExamManagementService:
    def __init__(self, repository: ExamRepository) -> None:
        self._repository = repository

    def add_exam(self, data: CreateExamInput) -> ExamView:
        self._validate_range(data.time_limit_minutes, data.min_questions, data.max_questions, data.passing_score)
        try:
            exam = self._repository.create_exam(data)
        except ValueError as exc:
            raise ExamManagementError(str(exc)) from exc
        return self._to_view(exam)

    def edit_exam(self, exam_id: str, data: UpdateExamInput) -> ExamView:
        exam = self._repository.get_exam(exam_id)
        if exam is None:
            raise ExamManagementError("Exam not found.")
        if (
            data.time_limit_minutes is not None
            or data.min_questions is not None
            or data.max_questions is not None
            or data.passing_score is not None
        ):
            time_limit = data.time_limit_minutes if data.time_limit_minutes is not None else exam.settings.time_limit_minutes
            min_q = data.min_questions if data.min_questions is not None else exam.settings.min_questions
            max_q = data.max_questions if data.max_questions is not None else exam.settings.max_questions
            passing = data.passing_score if data.passing_score is not None else exam.settings.passing_score
            self._validate_range(time_limit, min_q, max_q, passing)
        try:
            exam = self._repository.update_exam(exam_id, data)
        except ValueError as exc:
            raise ExamManagementError(str(exc)) from exc
        return self._to_view(exam)

    def delete_exam(self, exam_id: str) -> None:
        if not self._repository.delete_exam(exam_id):
            raise ExamManagementError("Exam not found.")

    def search_exams(self, filters: ExamSearchFilters) -> list[ExamView]:
        return [self._to_view(item) for item in self._repository.search_exams(filters)]

    def _validate_range(self, time_limit_minutes: int, min_questions: int, max_questions: int, passing_score: float) -> None:
        if time_limit_minutes <= 0:
            raise ExamManagementError("Time limit must be greater than 0.")
        if min_questions < 20:
            raise ExamManagementError("Minimum questions must be at least 20.")
        if max_questions <= 0 or max_questions < min_questions:
            raise ExamManagementError("Question range is invalid.")
        if passing_score < 0:
            raise ExamManagementError("Passing score must be non-negative.")

    def _to_view(self, exam) -> ExamView:
        return ExamView(
            exam_id=str(exam.id),
            code=exam.code,
            title=exam.title,
            description=exam.description,
            subject=exam.subject,
            status=exam.status.value if isinstance(exam.status, ExamStatus) else str(exam.status),
            time_limit_minutes=exam.settings.time_limit_minutes,
            min_questions=exam.settings.min_questions,
            max_questions=exam.settings.max_questions,
            passing_score=float(exam.settings.passing_score),
        )
