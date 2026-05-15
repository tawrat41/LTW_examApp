from __future__ import annotations

from app.domain.auth import AuthPrincipal, AuthPrincipalType
from app.infrastructure.auth.passwords import PasswordHasher
from app.infrastructure.auth.repositories import StudentAuthRepository, UserAuthRepository
from app.infrastructure.auth.session_store import InMemorySessionStore

from .dto import AuthResult, CurrentSessionView


class AuthenticationError(Exception):
    pass


class AuthenticationService:
    def __init__(
        self,
        user_repository: UserAuthRepository,
        student_repository: StudentAuthRepository,
        password_hasher: PasswordHasher,
        session_store: InMemorySessionStore,
    ) -> None:
        self._user_repository = user_repository
        self._student_repository = student_repository
        self._password_hasher = password_hasher
        self._session_store = session_store

    def login_admin(self, username: str, password: str) -> AuthResult:
        user = self._user_repository.get_by_username(username.strip())
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid username or password.")
        if not self._password_hasher.verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password.")

        principal = AuthPrincipal(
            id=user.id,
            principal_type=AuthPrincipalType.ADMIN,
            username=user.username,
            display_name=user.full_name,
            is_active=user.is_active,
        )
        session = self._session_store.create(principal)
        self._user_repository.update_last_login(user)
        return AuthResult(
            session_id=str(session.session_id),
            principal_id=str(principal.id),
            principal_type=principal.principal_type,
            username=principal.username,
            display_name=principal.display_name,
            expires_at_iso=session.expires_at.isoformat() if session.expires_at else None,
        )

    def login_student(self, student_code: str, password: str) -> AuthResult:
        student = self._student_repository.get_by_student_code(student_code.strip())
        if student is None or not student.is_active:
            raise AuthenticationError("Invalid student ID or password.")
        if not self._password_hasher.verify_password(password, student.password_hash):
            raise AuthenticationError("Invalid student ID or password.")

        principal = AuthPrincipal(
            id=student.id,
            principal_type=AuthPrincipalType.STUDENT,
            username=student.student_code,
            display_name=student.full_name,
            is_active=student.is_active,
        )
        session = self._session_store.create(principal)
        return AuthResult(
            session_id=str(session.session_id),
            principal_id=str(principal.id),
            principal_type=principal.principal_type,
            username=principal.username,
            display_name=principal.display_name,
            expires_at_iso=session.expires_at.isoformat() if session.expires_at else None,
        )

    def logout(self, session_id: str) -> bool:
        return self._session_store.revoke(session_id)

    def get_current_session(self, session_id: str) -> CurrentSessionView:
        session = self._session_store.get(session_id)
        if session is None:
            return CurrentSessionView(
                is_authenticated=False,
                session_id=None,
                principal_id=None,
                principal_type=None,
                username=None,
                display_name=None,
            )

        return CurrentSessionView(
            is_authenticated=True,
            session_id=str(session.session_id),
            principal_id=str(session.principal.id),
            principal_type=session.principal.principal_type,
            username=session.principal.username,
            display_name=session.principal.display_name,
        )
