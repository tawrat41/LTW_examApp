from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class StudentResultView:
    attempt_id: str
    student_id: str
    student_code: str
    student_name: str
    exam_id: str
    exam_code: str
    exam_title: str
    completed_at_iso: str | None
    total_questions: int
    answered_questions: int
    correct_answers: int
    wrong_answers: int
    unanswered_questions: int
    score: float
    percentage: float
    status: str


@dataclass(slots=True, frozen=True)
class ExamSummaryView:
    exam_id: str
    exam_code: str
    exam_title: str
    total_attempts: int
    completed_attempts: int
    average_score: float
    average_percentage: float
    highest_score: float
    lowest_score: float
