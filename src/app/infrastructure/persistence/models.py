from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, GUID, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    EXAMINER = "examiner"
    OPERATOR = "operator"


class ExamStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class AttemptStatus(enum.StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ImportJobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username"),
        UniqueConstraint("email"),
        Index("ix_users_role_is_active", "role", "is_active"),
    )

    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        nullable=False,
        default=UserRole.OPERATOR,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_exams: Mapped[list[Exam]] = relationship(back_populates="created_by_user")
    imported_files: Mapped[list[ImportedFile]] = relationship(back_populates="uploaded_by_user")
    import_jobs: Mapped[list[ImportJob]] = relationship(back_populates="created_by_user")


class Student(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("student_code"),
        UniqueConstraint("email"),
        Index("ix_students_full_name", "full_name"),
        Index("ix_students_is_active", "is_active"),
    )

    student_code: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    attempts: Mapped[list[Attempt]] = relationship(back_populates="student")
    results: Mapped[list[Result]] = relationship(back_populates="student")


class Exam(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exams"
    __table_args__ = (
        UniqueConstraint("code"),
        Index("ix_exams_status", "status"),
        Index("ix_exams_subject_status", "subject", "status"),
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, default="English")
    status: Mapped[ExamStatus] = mapped_column(
        Enum(ExamStatus, native_enum=False, length=20),
        nullable=False,
        default=ExamStatus.DRAFT,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_by_user: Mapped[User] = relationship(back_populates="created_exams")
    settings: Mapped[ExamSetting | None] = relationship(
        back_populates="exam",
        cascade="all, delete-orphan",
        uselist=False,
    )
    sections: Mapped[list[Section]] = relationship(
        back_populates="exam",
        cascade="all, delete-orphan",
    )
    questions: Mapped[list[Question]] = relationship(back_populates="exam")
    attempts: Mapped[list[Attempt]] = relationship(back_populates="exam")
    results: Mapped[list[Result]] = relationship(back_populates="exam")
    imported_files: Mapped[list[ImportedFile]] = relationship(back_populates="exam")


class ExamSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exam_settings"
    __table_args__ = (
        UniqueConstraint("exam_id"),
        CheckConstraint("time_limit_minutes > 0", name="time_limit_minutes_positive"),
        CheckConstraint("max_questions > 0", name="max_questions_positive"),
        CheckConstraint("min_questions > 0", name="min_questions_positive"),
        CheckConstraint("max_questions >= min_questions", name="question_range_valid"),
        CheckConstraint("passing_score >= 0", name="passing_score_non_negative"),
    )

    exam_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    time_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    min_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    max_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    passing_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    allow_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    adaptive_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    starting_difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    exam: Mapped[Exam] = relationship(back_populates="settings")


class Section(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("exam_id", "name"),
        UniqueConstraint("exam_id", "display_order"),
        CheckConstraint("display_order >= 1", name="display_order_positive"),
        Index("ix_sections_exam_display_order", "exam_id", "display_order"),
    )

    exam_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    exam: Mapped[Exam] = relationship(back_populates="sections")
    categories: Mapped[list[Category]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
    )
    questions: Mapped[list[Question]] = relationship(back_populates="section")


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("section_id", "name"),
        Index("ix_categories_section_name", "section_id", "name"),
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    section: Mapped[Section] = relationship(back_populates="categories")
    questions: Mapped[list[Question]] = relationship(back_populates="category")


class Question(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("exam_id", "external_ref"),
        CheckConstraint("difficulty_level >= 1", name="difficulty_level_min"),
        CheckConstraint("marks > 0", name="marks_positive"),
        Index("ix_questions_exam_section", "exam_id", "section_id"),
        Index("ix_questions_category", "category_id"),
        Index("ix_questions_difficulty", "difficulty_level"),
        Index("ix_questions_is_active", "is_active"),
    )

    exam_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("sections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("categories.id", ondelete="SET NULL"),
    )
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=True,
    )
    external_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    stem_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_text: Mapped[str | None] = mapped_column(Text)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    exam: Mapped[Exam] = relationship(back_populates="questions")
    section: Mapped[Section] = relationship(back_populates="questions")
    category: Mapped[Category | None] = relationship(back_populates="questions")
    attempt: Mapped[Attempt | None] = relationship(back_populates="questions")
    options: Mapped[list[QuestionOption]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[QuestionTag]] = relationship(
        secondary="question_tag_links",
        back_populates="questions",
    )
    tag_links: Mapped[list[QuestionTagLink]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        overlaps="tags",
    )
    answers: Mapped[list[Answer]] = relationship(back_populates="question")


class QuestionOption(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "question_options"
    __table_args__ = (
        UniqueConstraint("question_id", "option_key"),
        UniqueConstraint("question_id", "display_order"),
        CheckConstraint("display_order >= 1", name="option_display_order_positive"),
        Index("ix_question_options_question_display_order", "question_id", "display_order"),
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_key: Mapped[str] = mapped_column(String(10), nullable=False)
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    question: Mapped[Question] = relationship(back_populates="options")
    answers: Mapped[list[Answer]] = relationship(back_populates="selected_option")


class QuestionTag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "question_tags"
    __table_args__ = (
        UniqueConstraint("name"),
        Index("ix_question_tags_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    questions: Mapped[list[Question]] = relationship(
        secondary="question_tag_links",
        back_populates="tags",
        overlaps="tag_links",
    )
    question_links: Mapped[list[QuestionTagLink]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
        overlaps="questions,tags",
    )


class QuestionTagLink(Base):
    __tablename__ = "question_tag_links"
    __table_args__ = (
        UniqueConstraint("question_id", "tag_id"),
        Index("ix_question_tag_links_tag_id", "tag_id"),
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("question_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    question: Mapped[Question] = relationship(back_populates="tag_links", overlaps="questions,tags")
    tag: Mapped[QuestionTag] = relationship(back_populates="question_links", overlaps="questions,tags")


class Attempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("student_id", "exam_id", "attempt_number"),
        CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        CheckConstraint("target_question_count >= 1", name="target_question_count_positive"),
        CheckConstraint("current_question_number >= 0", name="current_question_number_non_negative"),
        CheckConstraint("total_answered >= 0", name="total_answered_non_negative"),
        Index("ix_attempts_student_status", "student_id", "status"),
        Index("ix_attempts_exam_status", "exam_id", "status"),
        Index("ix_attempts_started_at", "started_at"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("exams.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, native_enum=False, length=20),
        nullable=False,
        default=AttemptStatus.NOT_STARTED,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    target_question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_question_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_answered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ability_estimate: Mapped[float | None] = mapped_column(Numeric(8, 4))

    student: Mapped[Student] = relationship(back_populates="attempts")
    exam: Mapped[Exam] = relationship(back_populates="attempts")
    answers: Mapped[list[Answer]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )
    questions: Mapped[list[Question]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )
    result: Mapped[Result | None] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Answer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id"),
        CheckConstraint("response_time_seconds >= 0", name="response_time_non_negative"),
        CheckConstraint("awarded_marks >= 0", name="awarded_marks_non_negative"),
        Index("ix_answers_attempt_answered_at", "attempt_id", "answered_at"),
        Index("ix_answers_question", "question_id"),
        Index("ix_answers_selected_option", "selected_option_id"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    selected_option_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("question_options.id", ondelete="SET NULL"),
    )
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_time_seconds: Mapped[int | None] = mapped_column(Integer)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    awarded_marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)

    attempt: Mapped[Attempt] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship(back_populates="answers")
    selected_option: Mapped[QuestionOption | None] = relationship(back_populates="answers")


class Result(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "results"
    __table_args__ = (
        UniqueConstraint("attempt_id"),
        CheckConstraint("total_questions >= 0", name="total_questions_non_negative"),
        CheckConstraint("correct_answers >= 0", name="correct_answers_non_negative"),
        CheckConstraint("wrong_answers >= 0", name="wrong_answers_non_negative"),
        CheckConstraint("unanswered_questions >= 0", name="unanswered_questions_non_negative"),
        CheckConstraint("score >= 0", name="score_non_negative"),
        CheckConstraint("percentage >= 0 AND percentage <= 100", name="percentage_range"),
        Index("ix_results_exam_passed", "exam_id", "passed"),
        Index("ix_results_student", "student_id"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("exams.id", ondelete="RESTRICT"),
        nullable=False,
    )
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wrong_answers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unanswered_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    proficiency_level: Mapped[str | None] = mapped_column(String(50))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    attempt: Mapped[Attempt] = relationship(back_populates="result")
    student: Mapped[Student] = relationship(back_populates="results")
    exam: Mapped[Exam] = relationship(back_populates="results")


class ImportedFile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "imported_files"
    __table_args__ = (
        UniqueConstraint("file_hash"),
        Index("ix_imported_files_exam", "exam_id"),
        Index("ix_imported_files_uploaded_by", "uploaded_by_user_id"),
    )

    exam_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("exams.id", ondelete="SET NULL"),
    )
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    exam: Mapped[Exam | None] = relationship(back_populates="imported_files")
    uploaded_by_user: Mapped[User] = relationship(back_populates="imported_files")
    import_jobs: Mapped[list[ImportJob]] = relationship(back_populates="imported_file")


class ImportJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        CheckConstraint("total_rows >= 0", name="total_rows_non_negative"),
        CheckConstraint("successful_rows >= 0", name="successful_rows_non_negative"),
        CheckConstraint("failed_rows >= 0", name="failed_rows_non_negative"),
        Index("ix_import_jobs_status", "status"),
        Index("ix_import_jobs_imported_file", "imported_file_id"),
        Index("ix_import_jobs_created_by", "created_by_user_id"),
    )

    imported_file_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("imported_files.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[ImportJobStatus] = mapped_column(
        Enum(ImportJobStatus, native_enum=False, length=20),
        nullable=False,
        default=ImportJobStatus.PENDING,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    report_path: Mapped[str | None] = mapped_column(String(500))

    imported_file: Mapped[ImportedFile] = relationship(back_populates="import_jobs")
    created_by_user: Mapped[User] = relationship(back_populates="import_jobs")
