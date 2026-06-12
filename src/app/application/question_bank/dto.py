from __future__ import annotations

from dataclasses import dataclass, field

from app.infrastructure.importers.docx import ImportIssue


@dataclass(slots=True, frozen=True)
class QuestionOptionInput:
    key: str
    text: str
    is_correct: bool = False


@dataclass(slots=True, frozen=True)
class CreateQuestionInput:
    exam_id: str
    section_id: str
    stem_text: str
    options: list[QuestionOptionInput]
    category_name: str | None = None
    difficulty_level: int = 1
    explanation_text: str | None = None
    tags: list[str] = field(default_factory=list)
    marks: float = 1.0
    external_ref: str | None = None
    is_active: bool = True
    attempt_id: str | None = None


@dataclass(slots=True, frozen=True)
class UpdateQuestionInput:
    stem_text: str | None = None
    options: list[QuestionOptionInput] | None = None
    category_name: str | None = None
    difficulty_level: int | None = None
    explanation_text: str | None = None
    tags: list[str] | None = None
    marks: float | None = None
    is_active: bool | None = None


@dataclass(slots=True, frozen=True)
class QuestionSearchFilters:
    exam_id: str
    query: str | None = None
    category_name: str | None = None
    difficulty_level: int | None = None
    tags: list[str] = field(default_factory=list)
    include_inactive: bool = False


@dataclass(slots=True, frozen=True)
class QuestionView:
    question_id: str
    exam_id: str
    section_id: str
    category_name: str | None
    external_ref: str
    stem_text: str
    difficulty_level: int
    explanation_text: str | None
    tags: list[str]
    marks: float
    is_active: bool
    options: list[QuestionOptionInput]


@dataclass(slots=True, frozen=True)
class BulkImportRequest:
    exam_id: str
    section_id: str
    default_marks: float = 1.0
    is_active: bool = True


@dataclass(slots=True, frozen=True)
class BulkImportResult:
    imported_questions: list[QuestionView]
    issues: list[ImportIssue]
