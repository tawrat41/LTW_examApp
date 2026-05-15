from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.adaptive import AdaptiveExamService
from app.application.student_exam import StudentExamPortalService
from app.infrastructure.adaptive import AdaptiveExamRepository
from app.infrastructure.student_exam import StudentExamPortalRepository


def build_adaptive_exam_service(session: Session) -> AdaptiveExamService:
    return AdaptiveExamService(AdaptiveExamRepository(session))


def build_student_exam_portal_service(session: Session) -> StudentExamPortalService:
    adaptive_service = build_adaptive_exam_service(session)
    return StudentExamPortalService(StudentExamPortalRepository(session), adaptive_service)
