from __future__ import annotations

from dataclasses import dataclass

from app.application.auth import AuthenticationController
from app.application.student_exam import StudentExamPortalService


@dataclass(slots=True)
class StudentDesktopAppContext:
    auth_controller: AuthenticationController
    exam_portal: StudentExamPortalService
