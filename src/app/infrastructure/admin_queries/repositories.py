from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.admin.dto import DashboardStats, LookupItem
from app.infrastructure.persistence.models import Exam, Question, Section, Student


class AdminQueryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_dashboard_stats(self) -> DashboardStats:
        exams_count = self._session.scalar(select(func.count()).select_from(Exam)) or 0
        students_count = self._session.scalar(select(func.count()).select_from(Student)) or 0
        questions_count = self._session.scalar(select(func.count()).select_from(Question)) or 0
        active_students_count = (
            self._session.scalar(select(func.count()).select_from(Student).where(Student.is_active.is_(True))) or 0
        )
        return DashboardStats(
            exams_count=int(exams_count),
            students_count=int(students_count),
            questions_count=int(questions_count),
            active_students_count=int(active_students_count),
        )

    def list_exam_options(self) -> list[LookupItem]:
        stmt = select(Exam.id, Exam.title, Exam.code).order_by(Exam.title.asc())
        return [
            LookupItem(id=str(row.id), label=f"{row.title} ({row.code})")
            for row in self._session.execute(stmt)
        ]

    def list_section_options(self, exam_id: str) -> list[LookupItem]:
        stmt = (
            select(Section.id, Section.name)
            .where(Section.exam_id == uuid.UUID(exam_id))
            .order_by(Section.display_order.asc(), Section.name.asc())
        )
        return [LookupItem(id=str(row.id), label=row.name) for row in self._session.execute(stmt)]
