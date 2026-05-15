from __future__ import annotations

from pathlib import Path

from app.application.auth import AuthenticationController, AuthenticationError, LoginRequest
from app.bootstrap.auth import build_authentication_controller
from app.infrastructure.auth import PasswordHasher
from app.infrastructure.persistence import Student, User, UserRole, create_all, create_session_factory, create_sqlite_engine


def _build_controller(tmp_path: Path) -> AuthenticationController:
    engine = create_sqlite_engine(tmp_path / "auth.db")
    create_all(engine)
    session_factory = create_session_factory(engine)
    session = session_factory()
    return build_authentication_controller(session)


def test_admin_login_logout_flow(tmp_path: Path) -> None:
    controller = _build_controller(tmp_path)
    password_hasher = PasswordHasher()

    user = User(
        username="admin1",
        email="admin1@example.com",
        full_name="Admin User",
        password_hash=password_hasher.hash_password("secret123"),
        role=UserRole.ADMIN,
    )
    controller._auth_service._user_repository._session.add(user)  # type: ignore[attr-defined]
    controller._auth_service._user_repository._session.commit()  # type: ignore[attr-defined]

    result = controller.handle_admin_login(LoginRequest(username="admin1", password="secret123"))

    assert result.username == "admin1"
    assert result.principal_type.value == "admin"
    assert controller.get_session_view(result.session_id).is_authenticated is True
    assert controller.handle_logout(result.session_id) is True
    assert controller.get_session_view(result.session_id).is_authenticated is False


def test_student_login_validation(tmp_path: Path) -> None:
    controller = _build_controller(tmp_path)
    password_hasher = PasswordHasher()

    student = Student(
        student_code="STU-001",
        full_name="Student User",
        email="student1@example.com",
        password_hash=password_hasher.hash_password("pass1234"),
    )
    controller._auth_service._student_repository._session.add(student)  # type: ignore[attr-defined]
    controller._auth_service._student_repository._session.commit()  # type: ignore[attr-defined]

    result = controller.handle_student_login(LoginRequest(username="STU-001", password="pass1234"))

    assert result.principal_type.value == "student"
    assert result.display_name == "Student User"


def test_login_rejects_bad_credentials(tmp_path: Path) -> None:
    controller = _build_controller(tmp_path)
    password_hasher = PasswordHasher()

    user = User(
        username="admin2",
        email="admin2@example.com",
        full_name="Second Admin",
        password_hash=password_hasher.hash_password("correct-password"),
        role=UserRole.ADMIN,
    )
    controller._auth_service._user_repository._session.add(user)  # type: ignore[attr-defined]
    controller._auth_service._user_repository._session.commit()  # type: ignore[attr-defined]

    try:
        controller.handle_admin_login(LoginRequest(username="admin2", password="wrong"))
    except AuthenticationError:
        pass
    else:
        raise AssertionError("Expected authentication failure.")
