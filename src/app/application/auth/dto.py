from __future__ import annotations

from dataclasses import dataclass

from app.domain.auth import AuthPrincipalType


@dataclass(slots=True, frozen=True)
class LoginRequest:
    username: str
    password: str


@dataclass(slots=True, frozen=True)
class AuthResult:
    session_id: str
    principal_id: str
    principal_type: AuthPrincipalType
    username: str
    display_name: str
    expires_at_iso: str | None


@dataclass(slots=True, frozen=True)
class CurrentSessionView:
    is_authenticated: bool
    session_id: str | None
    principal_id: str | None
    principal_type: AuthPrincipalType | None
    username: str | None
    display_name: str | None
