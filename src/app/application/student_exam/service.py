from __future__ import annotations

from app.application.adaptive import AdaptiveExamService, StartAdaptiveExamInput, SubmitAnswerInput
from app.infrastructure.student_exam.repositories import StudentExamPortalRepository

from .dto import AvailableExamView, ExamInstructionView, ExamResultView, StudentExamSessionView


class StudentExamPortalError(Exception):
    pass


class StudentExamPortalService:
    def __init__(
        self,
        repository: StudentExamPortalRepository,
        adaptive_service: AdaptiveExamService,
    ) -> None:
        self._repository = repository
        self._adaptive_service = adaptive_service

    def list_available_exams(self) -> list[AvailableExamView]:
        exams = self._repository.list_active_exams()
        return [
            AvailableExamView(
                exam_id=str(exam.id),
                code=exam.code,
                title=exam.title,
                description=exam.description,
                subject=exam.subject,
                time_limit_minutes=exam.settings.time_limit_minutes,
                question_count=exam.settings.max_questions,
                allow_previous=exam.settings.allow_review,
            )
            for exam in exams
        ]

    def get_exam_instructions(self, exam_id: str) -> ExamInstructionView:
        exam = self._repository.get_exam(exam_id)
        if exam is None or exam.settings is None:
            raise StudentExamPortalError("Exam not found.")
        return ExamInstructionView(
            exam_id=str(exam.id),
            code=exam.code,
            title=exam.title,
            description=exam.description,
            subject=exam.subject,
            time_limit_minutes=exam.settings.time_limit_minutes,
            question_count=exam.settings.max_questions,
            allow_previous=exam.settings.allow_review,
            instructions=[
                "Read each question carefully before selecting an answer.",
                "The exam adapts difficulty based on your responses.",
                "Only one question is shown at a time.",
                "Use keyboard shortcuts to navigate efficiently.",
                "Submitting the exam will finalize your attempt.",
            ],
        )

    def start_exam(self, *, student_id: str, exam_id: str) -> StudentExamSessionView:
        instructions = self.get_exam_instructions(exam_id)
        progress = self._adaptive_service.start_exam(
            StartAdaptiveExamInput(
                student_id=student_id,
                exam_id=exam_id,
                question_count=instructions.question_count,
                generate_ai_questions=False,
            )
        )
        return StudentExamSessionView(
            attempt_id=progress.attempt_id,
            exam=instructions,
            current_question=progress.next_question,
            answered_questions=progress.answered_questions,
            remaining_questions=progress.remaining_questions,
            is_complete=progress.is_complete,
        )

    def get_result(self, attempt_id: str) -> ExamResultView:
        attempt = self._repository.get_attempt(attempt_id)
        if attempt is None:
            raise StudentExamPortalError("Attempt not found.")
        answers = list(attempt.answers)
        correct_answers = len([answer for answer in answers if answer.is_correct is True])
        wrong_answers = len([answer for answer in answers if answer.is_correct is False])
        score = float(sum(float(answer.awarded_marks) for answer in answers))
        total_questions = attempt.target_question_count
        percentage = (score / total_questions) * 100 if total_questions else 0.0
        return ExamResultView(
            attempt_id=attempt_id,
            exam_title=attempt.exam.title,
            total_questions=total_questions,
            answered_questions=len(answers),
            correct_answers=correct_answers,
            wrong_answers=wrong_answers,
            score=score,
            percentage=percentage,
        )

    def finalize_attempt(self, attempt_id: str) -> ExamResultView:
        self._adaptive_service.finalize_attempt(attempt_id)
        return self.get_result(attempt_id)

    def submit_answer(
        self,
        *,
        attempt_id: str,
        question_id: str,
        selected_option_id: str | None,
    ):
        return self._adaptive_service.submit_answer(
            SubmitAnswerInput(
                attempt_id=attempt_id,
                question_id=question_id,
                selected_option_id=selected_option_id,
            )
        )
