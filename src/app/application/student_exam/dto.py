from __future__ import annotations

from dataclasses import dataclass

from app.application.adaptive import AdaptiveExamQuestionView


@dataclass(slots=True, frozen=True)
class AvailableExamView:
    exam_id: str
    code: str
    title: str
    description: str | None
    subject: str
    time_limit_minutes: int
    question_count: int
    allow_previous: bool


@dataclass(slots=True, frozen=True)
class ExamInstructionView:
    exam_id: str
    code: str
    title: str
    description: str | None
    subject: str
    time_limit_minutes: int
    question_count: int
    allow_previous: bool
    instructions: list[str]


@dataclass(slots=True, frozen=True)
class StudentExamSessionView:
    attempt_id: str
    exam: ExamInstructionView
    current_question: AdaptiveExamQuestionView | None
    answered_questions: int
    remaining_questions: int
    is_complete: bool


@dataclass(slots=True, frozen=True)
class ExamResultView:
    attempt_id: str
    exam_title: str
    total_questions: int
    answered_questions: int
    correct_answers: int
    wrong_answers: int
    score: float
    percentage: float
