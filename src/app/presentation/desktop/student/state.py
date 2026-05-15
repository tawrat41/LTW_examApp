from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.application.adaptive import AdaptiveExamQuestionView
from app.application.student_exam import ExamInstructionView


@dataclass(slots=True)
class QuestionHistoryEntry:
    question: AdaptiveExamQuestionView
    selected_option_id: str | None = None
    submitted: bool = False


@dataclass(slots=True)
class StudentExamSessionState:
    attempt_id: str
    exam: ExamInstructionView
    history: list[QuestionHistoryEntry] = field(default_factory=list)
    current_index: int = 0
    ends_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        attempt_id: str,
        exam: ExamInstructionView,
        first_question: AdaptiveExamQuestionView | None,
    ) -> "StudentExamSessionState":
        history = [QuestionHistoryEntry(first_question)] if first_question is not None else []
        return cls(
            attempt_id=attempt_id,
            exam=exam,
            history=history,
            current_index=0,
            ends_at=datetime.now() + timedelta(minutes=exam.time_limit_minutes),
        )

    @property
    def current_entry(self) -> QuestionHistoryEntry | None:
        if not self.history:
            return None
        return self.history[self.current_index]

    @property
    def latest_index(self) -> int:
        return max(len(self.history) - 1, 0)
