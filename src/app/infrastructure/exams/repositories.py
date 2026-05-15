from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.application.exams.dto import CreateExamInput, ExamSearchFilters, UpdateExamInput
from app.infrastructure.persistence.models import Exam, ExamSetting, ExamStatus, Section, User


class ExamRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_exam(self, data: CreateExamInput) -> Exam:
        user = self._session.get(User, uuid.UUID(data.created_by_user_id))
        if user is None:
            raise ValueError("Creator user not found.")
        exam = Exam(
            code=data.code.strip(),
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            subject=data.subject.strip() or "English",
            status=ExamStatus.DRAFT,
            created_by_user_id=user.id,
        )
        exam.settings = ExamSetting(
            time_limit_minutes=data.time_limit_minutes,
            min_questions=data.min_questions,
            max_questions=data.max_questions,
            passing_score=data.passing_score,
        )
        exam.sections = [
            Section(
                name="General",
                description="Default section",
                display_order=1,
            )
        ]
        self._session.add(exam)
        self._session.commit()
        return self.get_exam(str(exam.id))

    def update_exam(self, exam_id: str, data: UpdateExamInput) -> Exam:
        exam = self.get_exam(exam_id)
        if exam is None:
            raise ValueError("Exam not found.")
        if data.title is not None:
            exam.title = data.title.strip()
        if data.description is not None:
            exam.description = data.description.strip() or None
        if data.subject is not None:
            exam.subject = data.subject.strip() or "English"
        if data.status is not None:
            exam.status = ExamStatus(data.status)
        if data.time_limit_minutes is not None:
            exam.settings.time_limit_minutes = data.time_limit_minutes
        if data.min_questions is not None:
            exam.settings.min_questions = data.min_questions
        if data.max_questions is not None:
            exam.settings.max_questions = data.max_questions
        if data.passing_score is not None:
            exam.settings.passing_score = data.passing_score
        self._session.add(exam)
        self._session.commit()
        return self.get_exam(exam_id)

    def delete_exam(self, exam_id: str) -> bool:
        exam = self._session.get(Exam, uuid.UUID(exam_id))
        if exam is None:
            return False
        self._session.delete(exam)
        self._session.commit()
        return True

    def get_exam(self, exam_id: str) -> Exam | None:
        stmt = (
            select(Exam)
            .where(Exam.id == uuid.UUID(exam_id))
            .options(joinedload(Exam.settings))
        )
        return self._session.scalars(stmt).unique().one_or_none()

    def search_exams(self, filters: ExamSearchFilters) -> list[Exam]:
        stmt = select(Exam).options(joinedload(Exam.settings))
        if filters.query:
            pattern = f"%{filters.query.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Exam.code).like(pattern),
                    func.lower(Exam.title).like(pattern),
                    func.lower(func.coalesce(Exam.description, "")).like(pattern),
                )
            )
        if filters.status:
            stmt = stmt.where(Exam.status == ExamStatus(filters.status))
        stmt = stmt.order_by(Exam.created_at.desc())
        return list(self._session.scalars(stmt).unique().all())
