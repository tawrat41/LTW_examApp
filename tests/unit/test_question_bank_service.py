from __future__ import annotations

import uuid
from pathlib import Path

from app.application.question_bank import (
    BulkImportRequest,
    CreateQuestionInput,
    QuestionOptionInput,
    QuestionSearchFilters,
    QuestionBankService,
    UpdateQuestionInput,
)
from app.infrastructure.persistence import (
    Exam,
    ExamStatus,
    Section,
    User,
    UserRole,
    create_all,
    create_session_factory,
    create_sqlite_engine,
)
from app.infrastructure.auth.passwords import PasswordHasher
from app.infrastructure.question_bank import QuestionBankRepository


def _build_service(tmp_path: Path) -> tuple[QuestionBankService, str, str]:
    engine = create_sqlite_engine(tmp_path / "question_bank.db")
    create_all(engine)
    session_factory = create_session_factory(engine)
    session = session_factory()

    hasher = PasswordHasher()
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin",
        password_hash=hasher.hash_password("secret123"),
        role=UserRole.ADMIN,
    )
    session.add(user)
    session.flush()

    exam = Exam(
        code="ENG-001",
        title="English Exam",
        subject="English",
        status=ExamStatus.DRAFT,
        created_by_user_id=user.id,
    )
    session.add(exam)
    session.flush()

    section = Section(
        exam_id=exam.id,
        name="Vocabulary",
        display_order=1,
    )
    session.add(section)
    session.commit()

    repository = QuestionBankRepository(session)
    return QuestionBankService(repository), str(exam.id), str(section.id)


def test_add_edit_search_and_delete_question(tmp_path: Path) -> None:
    service, exam_id, section_id = _build_service(tmp_path)

    created = service.add_question(
        CreateQuestionInput(
            exam_id=exam_id,
            section_id=section_id,
            stem_text='What is the synonym of "happy"?',
            options=[
                QuestionOptionInput(key="A", text="Angry"),
                QuestionOptionInput(key="B", text="Joyful", is_correct=True),
                QuestionOptionInput(key="C", text="Sad"),
            ],
            category_name="Vocabulary",
            difficulty_level=2,
            explanation_text="Joyful is closest in meaning.",
            tags=["synonym", "vocabulary"],
        )
    )

    assert created.category_name == "Vocabulary"
    assert created.tags == ["synonym", "vocabulary"]

    updated = service.edit_question(
        created.question_id,
        UpdateQuestionInput(
            difficulty_level=3,
            tags=["advanced", "synonym"],
            options=[
                QuestionOptionInput(key="A", text="Angry"),
                QuestionOptionInput(key="B", text="Joyful", is_correct=True),
                QuestionOptionInput(key="C", text="Tired"),
                QuestionOptionInput(key="D", text="Cold"),
            ],
        ),
    )

    assert updated.difficulty_level == 3
    assert updated.tags == ["advanced", "synonym"]
    assert len(updated.options) == 4

    results = service.search_questions(
        QuestionSearchFilters(
            exam_id=exam_id,
            query="happy",
            category_name="Vocabulary",
            difficulty_level=3,
            tags=["synonym"],
        )
    )

    assert len(results) == 1
    assert results[0].question_id == created.question_id

    service.delete_question(created.question_id)
    assert service.search_questions(QuestionSearchFilters(exam_id=exam_id)) == []


def test_bulk_import_persists_valid_questions(tmp_path: Path) -> None:
    service, exam_id, section_id = _build_service(tmp_path)

    result = service.bulk_import_from_paragraphs(
        [
            "Question:",
            'What is the synonym of "happy"?',
            "Options:",
            "A. Angry",
            "B. Joyful",
            "C. Sad",
            "Correct Answer: B",
            "Difficulty: Medium",
            "Category: Vocabulary",
            "",
            "Question: Broken item",
            "Options:",
            "A. Single option",
            "Correct Answer: A",
        ],
        BulkImportRequest(exam_id=exam_id, section_id=section_id),
    )

    assert len(result.imported_questions) == 1
    assert result.imported_questions[0].difficulty_level == 2
    assert any(issue.sequence_number == 2 for issue in result.issues)
