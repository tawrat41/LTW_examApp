from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class StartAdaptiveExamInput:
    student_id: str
    exam_id: str
    question_count: int | None = None
    generate_ai_questions: bool = True


@dataclass(slots=True, frozen=True)
class SubmitAnswerInput:
    attempt_id: str
    question_id: str
    selected_option_id: str | None


@dataclass(slots=True, frozen=True)
class AdaptiveExamQuestionView:
    attempt_id: str
    question_id: str
    stem_text: str
    category_name: str | None
    difficulty_level: int
    sequence_number: int
    total_questions: int
    options: list[dict[str, str | bool]]


@dataclass(slots=True, frozen=True)
class AdaptiveExamProgress:
    attempt_id: str
    total_questions: int
    answered_questions: int
    remaining_questions: int
    is_complete: bool
    next_question: AdaptiveExamQuestionView | None
