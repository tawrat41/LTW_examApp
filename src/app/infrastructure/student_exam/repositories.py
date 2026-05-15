from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.infrastructure.persistence.models import Attempt, Exam, ExamStatus


class StudentExamPortalRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_active_exams(self) -> list[Exam]:
        stmt = (
            select(Exam)
            .where(Exam.status == ExamStatus.ACTIVE)
            .options(joinedload(Exam.settings))
            .order_by(Exam.title.asc())
        )
        return list(self._session.scalars(stmt).unique().all())

    def get_exam(self, exam_id: str) -> Exam | None:
        stmt = (
            select(Exam)
            .where(Exam.id == uuid.UUID(exam_id))
            .options(joinedload(Exam.settings))
        )
        return self._session.scalars(stmt).unique().one_or_none()

    def get_attempt(self, attempt_id: str) -> Attempt | None:
        stmt = (
            select(Attempt)
            .where(Attempt.id == uuid.UUID(attempt_id))
            .options(
                joinedload(Attempt.exam).joinedload(Exam.settings),
                joinedload(Attempt.answers),
            )
        )
        return self._session.scalars(stmt).unique().one_or_none()
