from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.domain.auth import AuthPrincipal, AuthSession


class InMemorySessionStore:
    """Process-local session store for the desktop runtime."""

    def __init__(self, *, ttl_minutes: int | None = 480) -> None:
        self._ttl_minutes = ttl_minutes
        self._sessions: dict[str, AuthSession] = {}

    def create(self, principal: AuthPrincipal) -> AuthSession:
        created_at = datetime.now(timezone.utc)
        expires_at = (
            created_at + timedelta(minutes=self._ttl_minutes)
            if self._ttl_minutes is not None
            else None
        )
        session = AuthSession(
            session_id=uuid.uuid4(),
            principal=principal,
            created_at=created_at,
            expires_at=expires_at,
        )
        self._sessions[str(session.session_id)] = session
        return session

    def get(self, session_id: str) -> AuthSession | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.expires_at and session.expires_at <= datetime.now(timezone.utc):
            self._sessions.pop(session_id, None)
            return None
        return session

    def revoke(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None
