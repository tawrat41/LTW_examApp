from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.admin import AdminQueryService
from app.application.exams import ExamManagementService
from app.application.importing import QuestionBankImportService
from app.application.question_bank import QuestionBankService
from app.application.reporting import ReportingService
from app.application.students import StudentManagementService
from app.infrastructure.admin_queries import AdminQueryRepository
from app.infrastructure.exams import ExamRepository
from app.infrastructure.question_bank import QuestionBankRepository
from app.infrastructure.reporting import ReportingRepository
from app.infrastructure.students import StudentRepository


def build_question_bank_service(session: Session) -> QuestionBankService:
    return QuestionBankService(QuestionBankRepository(session), QuestionBankImportService())


def build_student_management_service(session: Session) -> StudentManagementService:
    return StudentManagementService(StudentRepository(session))


def build_exam_management_service(session: Session) -> ExamManagementService:
    return ExamManagementService(ExamRepository(session))


def build_admin_query_service(session: Session) -> AdminQueryService:
    return AdminQueryService(AdminQueryRepository(session))


def build_reporting_service(session: Session) -> ReportingService:
    return ReportingService(ReportingRepository(session))
