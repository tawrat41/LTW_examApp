from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CreateStudentInput:
    student_code: str
    full_name: str
    password: str
    email: str | None = None
    phone: str | None = None
    is_active: bool = True


@dataclass(slots=True, frozen=True)
class UpdateStudentInput:
    full_name: str | None = None
    password: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None


@dataclass(slots=True, frozen=True)
class StudentSearchFilters:
    query: str | None = None
    is_active: bool | None = None


@dataclass(slots=True, frozen=True)
class StudentView:
    student_id: str
    student_code: str
    full_name: str
    email: str | None
    phone: str | None
    is_active: bool
