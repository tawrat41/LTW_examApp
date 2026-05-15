from __future__ import annotations

from app.domain.adaptive import (
    AdaptiveAnswerRecord,
    AdaptiveExamConfig,
    AdaptiveExamEngine,
    AdaptiveExamState,
    AdaptiveQuestionCandidate,
)
from app.infrastructure.persistence.models import AttemptStatus
from app.infrastructure.adaptive.repositories import AdaptiveExamRepository

from .dto import AdaptiveExamProgress, AdaptiveExamQuestionView, StartAdaptiveExamInput, SubmitAnswerInput


class AdaptiveExamError(Exception):
    pass


class AdaptiveExamService:
    def __init__(
        self,
        repository: AdaptiveExamRepository,
        engine: AdaptiveExamEngine | None = None,
    ) -> None:
        self._repository = repository
        self._engine = engine or AdaptiveExamEngine()

    def start_exam(self, data: StartAdaptiveExamInput) -> AdaptiveExamProgress:
        attempt, question_count = self._repository.create_attempt(
            student_id=data.student_id,
            exam_id=data.exam_id,
            requested_question_count=data.question_count,
        )
        next_question = self._select_next_question(str(attempt.id), question_count)
        return self.get_progress(str(attempt.id), override_next_question=next_question, total_questions=question_count)

    def submit_answer(self, data: SubmitAnswerInput) -> AdaptiveExamProgress:
        attempt = self._repository.get_attempt(data.attempt_id)
        if attempt is None:
            raise AdaptiveExamError("Attempt not found.")
        if attempt.status == AttemptStatus.COMPLETED:
            raise AdaptiveExamError("Attempt is already completed.")
        question_count = attempt.target_question_count
        self._repository.record_answer(
            attempt_id=data.attempt_id,
            question_id=data.question_id,
            selected_option_id=data.selected_option_id,
        )
        next_question = self._select_next_question(data.attempt_id, question_count)
        if next_question is None:
            self._repository.complete_attempt(data.attempt_id)
        return self.get_progress(data.attempt_id, override_next_question=next_question, total_questions=question_count)

    def get_progress(
        self,
        attempt_id: str,
        *,
        override_next_question: AdaptiveExamQuestionView | None = None,
        total_questions: int | None = None,
    ) -> AdaptiveExamProgress:
        attempt = self._repository.get_attempt(attempt_id)
        if attempt is None:
            raise AdaptiveExamError("Attempt not found.")
        configured_count = total_questions or attempt.target_question_count
        answered = len(attempt.answers)
        next_question = override_next_question
        if next_question is None and answered < configured_count:
            next_question = self._select_next_question(attempt_id, configured_count)
        return AdaptiveExamProgress(
            attempt_id=attempt_id,
            total_questions=configured_count,
            answered_questions=answered,
            remaining_questions=max(configured_count - answered, 0),
            is_complete=answered >= configured_count or next_question is None,
            next_question=next_question,
        )

    def finalize_attempt(self, attempt_id: str) -> AdaptiveExamProgress:
        attempt = self._repository.get_attempt(attempt_id)
        if attempt is None:
            raise AdaptiveExamError("Attempt not found.")
        self._repository.complete_attempt(attempt_id)
        return self.get_progress(attempt_id, total_questions=attempt.target_question_count)

    def _select_next_question(self, attempt_id: str, question_count: int) -> AdaptiveExamQuestionView | None:
        candidate_models = self._repository.list_candidates_for_attempt(attempt_id)
        answer_models = self._repository.list_answers_for_attempt(attempt_id)
        state = AdaptiveExamState(
            asked_questions=[
                AdaptiveAnswerRecord(
                    question_id=str(answer.question_id),
                    difficulty_level=answer.question.difficulty_level,
                    category_name=answer.question.category.name if answer.question.category else None,
                    is_correct=bool(answer.is_correct),
                )
                for answer in sorted(answer_models, key=lambda item: item.answered_at or item.created_at)
            ]
        )
        candidates = [
            AdaptiveQuestionCandidate(
                question_id=str(question.id),
                difficulty_level=question.difficulty_level,
                category_name=question.category.name if question.category else None,
                stem_text=question.stem_text,
                external_ref=question.external_ref,
            )
            for question in candidate_models
        ]
        selection = self._engine.select_next_question(
            state=state,
            candidates=candidates,
            config=AdaptiveExamConfig(question_count=question_count, starting_difficulty=2),
        )
        if selection is None:
            return None
        question = self._repository.get_question(selection.question_id)
        if question is None:
            raise AdaptiveExamError("Selected question could not be loaded.")
        return AdaptiveExamQuestionView(
            attempt_id=attempt_id,
            question_id=str(question.id),
            stem_text=question.stem_text,
            category_name=selection.category_name,
            difficulty_level=selection.actual_difficulty,
            sequence_number=len(answer_models) + 1,
            total_questions=question_count,
            options=[
                {
                    "option_id": str(option.id),
                    "key": option.option_key,
                    "text": option.option_text,
                }
                for option in sorted(question.options, key=lambda item: item.display_order)
            ],
        )
