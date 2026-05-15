from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.application.students.dto import StudentSearchFilters
from app.infrastructure.persistence.models import Student


class StudentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_student(
        self,
        *,
        student_code: str,
        full_name: str,
        password_hash: str,
        email: str | None,
        phone: str | None,
        is_active: bool,
    ) -> Student:
        student = Student(
            student_code=student_code,
            full_name=full_name,
            password_hash=password_hash,
            email=email,
            phone=phone,
            is_active=is_active,
        )
        self._session.add(student)
        self._session.commit()
        return student

    def update_student(
        self,
        *,
        student_id: str,
        full_name: str | None,
        password_hash: str | None,
        email: str | None,
        phone: str | None,
        is_active: bool | None,
    ) -> Student:
        student = self._session.get(Student, uuid.UUID(student_id))
        if student is None:
            raise ValueError("Student not found.")
        if full_name is not None:
            student.full_name = full_name
        if password_hash is not None:
            student.password_hash = password_hash
        if email is not None:
            student.email = email
        if phone is not None:
            student.phone = phone
        if is_active is not None:
            student.is_active = is_active
        self._session.add(student)
        self._session.commit()
        return student

    def delete_student(self, student_id: str) -> bool:
        student = self._session.get(Student, uuid.UUID(student_id))
        if student is None:
            return False
        self._session.delete(student)
        self._session.commit()
        return True

    def search_students(self, filters: StudentSearchFilters) -> list[Student]:
        stmt = select(Student)
        if filters.query:
            pattern = f"%{filters.query.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Student.student_code).like(pattern),
                    func.lower(Student.full_name).like(pattern),
                    func.lower(func.coalesce(Student.email, "")).like(pattern),
                )
            )
        if filters.is_active is not None:
            stmt = stmt.where(Student.is_active.is_(filters.is_active))
        stmt = stmt.order_by(Student.created_at.desc())
        return list(self._session.scalars(stmt).all())
