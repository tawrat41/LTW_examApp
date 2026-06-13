from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LookupItem:
    id: str
    label: str
    questions_count: int | None = None


@dataclass(slots=True, frozen=True)
class DashboardStats:
    exams_count: int
    students_count: int
    questions_count: int
    active_students_count: int
