from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.auth import AuthenticationController, AuthenticationService
from app.infrastructure.auth import (
    InMemorySessionStore,
    PasswordHasher,
    StudentAuthRepository,
    UserAuthRepository,
)


def build_authentication_controller(
    session: Session,
    *,
    session_store: InMemorySessionStore | None = None,
    password_hasher: PasswordHasher | None = None,
) -> AuthenticationController:
    auth_service = AuthenticationService(
        user_repository=UserAuthRepository(session),
        student_repository=StudentAuthRepository(session),
        password_hasher=password_hasher or PasswordHasher(),
        session_store=session_store or InMemorySessionStore(),
    )
    return AuthenticationController(auth_service)
