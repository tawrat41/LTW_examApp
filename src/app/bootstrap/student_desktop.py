from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.bootstrap.auth import build_authentication_controller
from app.bootstrap.student_services import build_student_exam_portal_service
from app.infrastructure.auth.passwords import PasswordHasher
from app.infrastructure.persistence.models import Student
from app.infrastructure.persistence.session import create_all, create_session_factory, create_sqlite_engine
def build_student_desktop_app_context(database_path: str | Path) -> StudentDesktopAppContext:
    from app.presentation.desktop.student.app_context import StudentDesktopAppContext
    engine = create_sqlite_engine(database_path)
    create_all(engine)
    session = create_session_factory(engine)()
    _seed_default_student(session)
    return StudentDesktopAppContext(
        auth_controller=build_authentication_controller(session),
        exam_portal=build_student_exam_portal_service(session),
    )


def run_student_desktop(database_path: str | Path) -> int:
    from app.presentation.desktop.student.main_window import launch_student_window
    return launch_student_window(build_student_desktop_app_context(database_path))


def _seed_default_student(session) -> None:
    existing_student = session.scalar(select(Student).limit(1))
    if existing_student is not None:
        return
    session.add(
        Student(
            student_code="student1",
            full_name="Sample Student",
            password_hash=PasswordHasher().hash_password("student123"),
            email="student1@local.exam",
            is_active=True,
        )
    )
    session.commit()
