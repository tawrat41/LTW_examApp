from __future__ import annotations

from datetime import timezone, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.persistence.models import Student, User


class UserAuthRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self._session.scalar(stmt)

    def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        self._session.add(user)
        self._session.commit()


class StudentAuthRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_student_code(self, student_code: str) -> Student | None:
        stmt = select(Student).where(Student.student_code == student_code)
        return self._session.scalar(stmt)
