from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ImportIssueSeverity(StrEnum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True, frozen=True)
class ParsedQuestion:
    sequence_number: int
    question_text: str
    options: dict[str, str]
    correct_answer: str
    difficulty: str | None = None
    category: str | None = None
    explanation: str | None = None


@dataclass(slots=True, frozen=True)
class ImportIssue:
    sequence_number: int | None
    severity: ImportIssueSeverity
    message: str
    raw_block: str | None = None


@dataclass(slots=True, frozen=True)
class DuplicateQuestionRecord:
    original_sequence_number: int
    duplicate_sequence_number: int
    question_text: str


@dataclass(slots=True)
class ImportReport:
    parsed_questions: list[ParsedQuestion] = field(default_factory=list)
    issues: list[ImportIssue] = field(default_factory=list)
    duplicates: list[DuplicateQuestionRecord] = field(default_factory=list)

    @property
    def successful_count(self) -> int:
        return len(self.parsed_questions)

    @property
    def skipped_count(self) -> int:
        return len([issue for issue in self.issues if issue.severity == ImportIssueSeverity.ERROR])
