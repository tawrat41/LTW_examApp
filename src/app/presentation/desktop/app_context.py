from __future__ import annotations

from dataclasses import dataclass

from app.application.admin import AdminQueryService
from app.application.auth import AuthenticationController
from app.application.exams import ExamManagementService
from app.application.importing import QuestionBankImportService
from app.application.question_bank import QuestionBankService
from app.application.reporting import ReportingService
from app.application.students import StudentManagementService


@dataclass(slots=True)
class DesktopAppContext:
    auth_controller: AuthenticationController
    admin_queries: AdminQueryService
    exam_service: ExamManagementService
    question_bank_service: QuestionBankService
    import_service: QuestionBankImportService
    reporting_service: ReportingService
    student_service: StudentManagementService
