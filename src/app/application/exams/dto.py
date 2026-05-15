from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CreateExamInput:
    code: str
    title: str
    created_by_user_id: str
    description: str | None = None
    subject: str = "English"
    time_limit_minutes: int = 30
    min_questions: int = 10
    max_questions: int = 20
    passing_score: float = 0.0


@dataclass(slots=True, frozen=True)
class UpdateExamInput:
    title: str | None = None
    description: str | None = None
    subject: str | None = None
    status: str | None = None
    time_limit_minutes: int | None = None
    min_questions: int | None = None
    max_questions: int | None = None
    passing_score: float | None = None


@dataclass(slots=True, frozen=True)
class ExamSearchFilters:
    query: str | None = None
    status: str | None = None


@dataclass(slots=True, frozen=True)
class ExamView:
    exam_id: str
    code: str
    title: str
    description: str | None
    subject: str
    status: str
    time_limit_minutes: int
    min_questions: int
    max_questions: int
    passing_score: float
