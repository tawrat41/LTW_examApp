from __future__ import annotations

from app.infrastructure.auth.passwords import PasswordHasher
from app.infrastructure.students.repositories import StudentRepository

from .dto import CreateStudentInput, StudentSearchFilters, StudentView, UpdateStudentInput


class StudentManagementError(Exception):
    pass


class StudentManagementService:
    def __init__(self, repository: StudentRepository, password_hasher: PasswordHasher | None = None) -> None:
        self._repository = repository
        self._password_hasher = password_hasher or PasswordHasher()

    def add_student(self, data: CreateStudentInput) -> StudentView:
        self._validate_create(data)
        student = self._repository.create_student(
            student_code=data.student_code.strip(),
            full_name=data.full_name.strip(),
            password_hash=self._password_hasher.hash_password(data.password),
            email=self._normalize_optional(data.email),
            phone=self._normalize_optional(data.phone),
            is_active=data.is_active,
        )
        return self._to_view(student)

    def edit_student(self, student_id: str, data: UpdateStudentInput) -> StudentView:
        if data.full_name is not None and not data.full_name.strip():
            raise StudentManagementError("Student name is required.")
        password_hash = (
            self._password_hasher.hash_password(data.password)
            if data.password is not None and data.password.strip()
            else None
        )
        try:
            student = self._repository.update_student(
                student_id=student_id,
                full_name=data.full_name.strip() if data.full_name is not None else None,
                password_hash=password_hash,
                email=self._normalize_optional(data.email) if data.email is not None else None,
                phone=self._normalize_optional(data.phone) if data.phone is not None else None,
                is_active=data.is_active,
            )
        except ValueError as exc:
            raise StudentManagementError(str(exc)) from exc
        return self._to_view(student)

    def delete_student(self, student_id: str) -> None:
        if not self._repository.delete_student(student_id):
            raise StudentManagementError("Student not found.")

    def search_students(self, filters: StudentSearchFilters) -> list[StudentView]:
        return [self._to_view(item) for item in self._repository.search_students(filters)]

    def _validate_create(self, data: CreateStudentInput) -> None:
        if not data.student_code.strip():
            raise StudentManagementError("Student ID is required.")
        if not data.full_name.strip():
            raise StudentManagementError("Student name is required.")
        if not data.password.strip():
            raise StudentManagementError("Password is required.")

    def _normalize_optional(self, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def _to_view(self, student) -> StudentView:
        return StudentView(
            student_id=str(student.id),
            student_code=student.student_code,
            full_name=student.full_name,
            email=student.email,
            phone=student.phone,
            is_active=student.is_active,
        )
