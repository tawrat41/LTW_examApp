from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.infrastructure.persistence.models import Answer, Attempt, AttemptStatus, Exam, Question, QuestionOption, Student


class AdaptiveExamRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_attempt(self, *, student_id: str, exam_id: str, requested_question_count: int | None) -> tuple[Attempt, int]:
        student = self._session.get(Student, uuid.UUID(student_id))
        exam = self._session.get(Exam, uuid.UUID(exam_id))
        if student is None:
            raise ValueError("Student not found.")
        if exam is None or exam.settings is None:
            raise ValueError("Exam not found.")

        existing_attempts = self._session.scalars(
            select(Attempt).where(Attempt.student_id == student.id, Attempt.exam_id == exam.id)
        ).all()
        question_count = requested_question_count or exam.settings.max_questions
        question_count = max(exam.settings.min_questions, min(question_count, exam.settings.max_questions))
        attempt = Attempt(
            student_id=student.id,
            exam_id=exam.id,
            attempt_number=len(existing_attempts) + 1,
            status=AttemptStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
            target_question_count=question_count,
        )
        self._session.add(attempt)
        self._session.commit()
        return attempt, question_count

    def get_attempt(self, attempt_id: str) -> Attempt | None:
        stmt = (
            select(Attempt)
            .where(Attempt.id == uuid.UUID(attempt_id))
            .options(
                joinedload(Attempt.exam).joinedload(Exam.settings),
                joinedload(Attempt.answers).joinedload(Answer.question).joinedload(Question.category),
            )
        )
        return self._session.scalars(stmt).unique().one_or_none()

    def list_candidates_for_attempt(self, attempt_id: str) -> list[Question]:
        attempt = self.get_attempt(attempt_id)
        if attempt is None:
            raise ValueError("Attempt not found.")
        
        attempt_uuid = uuid.UUID(attempt_id)
        stmt_attempt = (
            select(Question)
            .where(Question.attempt_id == attempt_uuid, Question.is_active.is_(True))
            .options(
                joinedload(Question.category),
                joinedload(Question.options),
            )
        )
        candidates = list(self._session.scalars(stmt_attempt).unique().all())
        if candidates:
            return candidates

        stmt = (
            select(Question)
            .where(
                Question.exam_id == attempt.exam_id,
                Question.attempt_id.is_(None),
                Question.is_active.is_(True)
            )
            .options(
                joinedload(Question.category),
                joinedload(Question.options),
            )
        )
        return list(self._session.scalars(stmt).unique().all())

    def list_answers_for_attempt(self, attempt_id: str) -> list[Answer]:
        stmt = (
            select(Answer)
            .where(Answer.attempt_id == uuid.UUID(attempt_id))
            .options(
                joinedload(Answer.question).joinedload(Question.category),
                joinedload(Answer.selected_option),
            )
        )
        return list(self._session.scalars(stmt).unique().all())

    def get_question(self, question_id: str) -> Question | None:
        stmt = (
            select(Question)
            .where(Question.id == uuid.UUID(question_id))
            .options(joinedload(Question.category), joinedload(Question.options))
        )
        return self._session.scalars(stmt).unique().one_or_none()

    def record_answer(self, *, attempt_id: str, question_id: str, selected_option_id: str | None) -> Answer:
        attempt = self.get_attempt(attempt_id)
        question = self.get_question(question_id)
        if attempt is None:
            raise ValueError("Attempt not found.")
        if question is None:
            raise ValueError("Question not found.")
        existing_answer = self._session.scalar(
            select(Answer).where(Answer.attempt_id == attempt.id, Answer.question_id == question.id)
        )
        if existing_answer is not None:
            raise ValueError("Question already answered in this attempt.")

        selected_option = None
        if selected_option_id is not None:
            selected_option = self._session.get(QuestionOption, uuid.UUID(selected_option_id))
            if selected_option is None or selected_option.question_id != question.id:
                raise ValueError("Selected option is invalid for the question.")

        is_correct = bool(selected_option.is_correct) if selected_option is not None else False
        awarded_marks = float(question.marks) if is_correct else 0.0
        answer = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=selected_option.id if selected_option is not None else None,
            answered_at=datetime.now(timezone.utc),
            is_correct=is_correct,
            awarded_marks=awarded_marks,
        )
        attempt.total_answered += 1
        attempt.current_question_number += 1
        self._session.add(answer)
        self._session.add(attempt)
        self._session.commit()
        return answer

    def complete_attempt(self, attempt_id: str) -> None:
        attempt = self._session.get(Attempt, uuid.UUID(attempt_id))
        if attempt is None:
            raise ValueError("Attempt not found.")
        attempt.status = AttemptStatus.COMPLETED
        attempt.completed_at = datetime.now(timezone.utc)
        self._session.add(attempt)
        self._session.commit()
