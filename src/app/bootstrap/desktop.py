from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.infrastructure.auth.passwords import PasswordHasher
from app.infrastructure.persistence.models import User, UserRole
from app.bootstrap.admin_services import (
    build_admin_query_service,
    build_exam_management_service,
    build_question_bank_service,
    build_reporting_service,
    build_student_management_service,
)
from app.bootstrap.auth import build_authentication_controller
from app.presentation.desktop.app_context import DesktopAppContext
from app.presentation.desktop.main_window import launch_admin_window
from app.infrastructure.persistence.session import create_all, create_session_factory, create_sqlite_engine
from app.application.importing import QuestionBankImportService


def build_desktop_app_context(database_path: str | Path) -> DesktopAppContext:
    engine = create_sqlite_engine(database_path)
    create_all(engine)
    session = create_session_factory(engine)()
    _seed_default_admin(session)
    return DesktopAppContext(
        auth_controller=build_authentication_controller(session),
        admin_queries=build_admin_query_service(session),
        exam_service=build_exam_management_service(session),
        question_bank_service=build_question_bank_service(session),
        import_service=QuestionBankImportService(),
        reporting_service=build_reporting_service(session),
        student_service=build_student_management_service(session),
    )


def run_admin_desktop(database_path: str | Path) -> int:
    return launch_admin_window(build_desktop_app_context(database_path))


def _seed_default_admin(session) -> None:
    existing_user = session.scalar(select(User).limit(1))
    if existing_user is not None:
        return
    hasher = PasswordHasher()
    session.add(
        User(
            username="admin",
            email="admin@local.exam",
            full_name="System Administrator",
            password_hash=hasher.hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
    )
    session.commit()
