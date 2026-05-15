from __future__ import annotations

from .dto import AuthResult, CurrentSessionView, LoginRequest
from .service import AuthenticationService


class AuthenticationController:
    """UI-facing hook layer for future PySide6 screens/viewmodels."""

    def __init__(self, auth_service: AuthenticationService) -> None:
        self._auth_service = auth_service

    def handle_admin_login(self, request: LoginRequest) -> AuthResult:
        return self._auth_service.login_admin(
            username=request.username,
            password=request.password,
        )

    def handle_student_login(self, request: LoginRequest) -> AuthResult:
        return self._auth_service.login_student(
            student_code=request.username,
            password=request.password,
        )

    def handle_logout(self, session_id: str) -> bool:
        return self._auth_service.logout(session_id)

    def get_session_view(self, session_id: str) -> CurrentSessionView:
        return self._auth_service.get_current_session(session_id)
